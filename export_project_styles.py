#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scan a web project and export its structure, style files, and related source/config
files into one Markdown report. Read-only: does not modify project files.

Usage:
  python export_project_styles.py
  python export_project_styles.py "D:/path/to/your/hugo-site"
  python export_project_styles.py . --output project-code-report.md
  python export_project_styles.py . --all-text

By default, includes style files plus likely-relevant templates, scripts, and config
files. Use --all-text to include other text files (still skips ignored directories).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Iterable

STYLE_EXTS = {
    ".css", ".scss", ".sass", ".less", ".styl", ".pcss", ".postcss"
}
RELATED_EXTS = {
    ".html", ".htm", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
    ".json", ".toml", ".yaml", ".yml", ".xml", ".md", ".mdx",
    ".go", ".tmpl", ".php", ".vue", ".svelte", ".astro"
}
CONFIG_NAMES = {
    "config", "hugo", "package", "postcss.config", "tailwind.config",
    "vite.config", "webpack.config", "gulpfile", "netlify", "vercel.json",
    "wrangler.toml", "tsconfig", "eslint.config", ".gitignore"
}
IGNORE_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build",
    "public", ".hugo_build.lock", ".vercel", ".next", ".nuxt", ".output",
    "coverage", "tmp", "temp", "__pycache__", ".idea", ".vscode"
}
IGNORE_FILES = {
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb",
    "Cargo.lock", "Gemfile.lock", "poetry.lock", "uv.lock"
}
MAX_FILE_BYTES = 1_500_000
MAX_REPORT_FILE_BYTES = 1_500_000
TEXT_EXTS = STYLE_EXTS | RELATED_EXTS | {
    ".txt", ".conf", ".ini", ".sh", ".bat", ".ps1", ".env.example"
}

def is_probably_text(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTS:
        return True
    name = path.name.lower()
    if name in CONFIG_NAMES or any(name.startswith(n + ".") for n in CONFIG_NAMES):
        return True
    # Include extensionless text/config files, but skip obvious binaries by checking bytes.
    try:
        sample = path.read_bytes()[:4096]
    except OSError:
        return False
    return b"\x00" not in sample

def ignored(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    if any(part in IGNORE_DIRS for part in rel.parts[:-1]):
        return True
    if path.name in IGNORE_FILES:
        return True
    if path.name.endswith((".min.css", ".min.js", ".map")):
        return True
    if path.name.startswith(".env") and path.name != ".env.example":
        return True
    return False

def read_text(path: Path) -> tuple[str | None, str | None]:
    try:
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            return None, f"文件过大（{size:,} bytes），未写入内容"
        raw = path.read_bytes()
        # Try common encodings; replacement fallback keeps report generation robust.
        for encoding in ("utf-8-sig", "utf-8", "gb18030", "latin-1"):
            try:
                return raw.decode(encoding), None
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="replace"), "部分字符可能因编码问题被替换"
    except OSError as exc:
        return None, f"读取失败：{exc}"

def tree_text(root: Path, files: list[Path]) -> str:
    included_dirs: set[Path] = {root}
    for file in files:
        parent = file.parent
        while parent != root and root in parent.parents:
            included_dirs.add(parent)
            parent = parent.parent
    lines = [root.name + "/"]
    children: dict[Path, list[Path]] = {}
    for d in included_dirs:
        if d == root:
            continue
        children.setdefault(d.parent, []).append(d)
    file_children: dict[Path, list[Path]] = {}
    for f in files:
        file_children.setdefault(f.parent, []).append(f)

    def walk(directory: Path, prefix: str = "") -> None:
        dirs = sorted(children.get(directory, []), key=lambda p: p.name.lower())
        fs = sorted(file_children.get(directory, []), key=lambda p: p.name.lower())
        entries: list[tuple[Path, bool]] = [(d, True) for d in dirs] + [(f, False) for f in fs]
        for i, (entry, is_dir) in enumerate(entries):
            last = i == len(entries) - 1
            lines.append(prefix + ("└── " if last else "├── ") + entry.name + ("/" if is_dir else ""))
            if is_dir:
                walk(entry, prefix + ("    " if last else "│   "))
    walk(root)
    return "\n".join(lines)

def extract_refs(path: Path, content: str, root: Path) -> list[str]:
    refs: list[str] = []
    suffix = path.suffix.lower()
    patterns = []
    if suffix in STYLE_EXTS:
        patterns = [
            (r'@import\s+(?:url\()?["\']([^"\']+)["\']', "import"),
            (r'url\(\s*["\']?([^"\')]+)', "url"),
        ]
    elif suffix in {".html", ".htm", ".go", ".tmpl", ".vue", ".svelte", ".astro", ".php"}:
        patterns = [
            (r'<link\b[^>]*\bhref=["\']([^"\']+)["\']', "link"),
            (r'<script\b[^>]*\bsrc=["\']([^"\']+)["\']', "script"),
            (r'{{\s*<[^>]*?["\']([^"\']+\.(?:css|scss|js))["\']', "template"),
        ]
    elif suffix in {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}:
        patterns = [
            (r'(?:import|require\()\s*(?:[^"\']*?\s+from\s+)?["\']([^"\']+)["\']', "import"),
        ]
    for pattern, label in patterns:
        for match in re.finditer(pattern, content, flags=re.IGNORECASE):
            value = match.group(1).strip()
            if value and not value.startswith(("http://", "https://", "data:", "#", "//")):
                refs.append(f"{label}: {value}")
    return list(dict.fromkeys(refs))

def choose_files(root: Path, all_text: bool) -> list[Path]:
    result = []
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted([d for d in dirs if d not in IGNORE_DIRS])
        current_path = Path(current)
        for name in sorted(names):
            path = current_path / name
            if ignored(path, root):
                continue
            ext = path.suffix.lower()
            base = path.name.lower()
            is_config = base in CONFIG_NAMES or any(base.startswith(n + ".") for n in CONFIG_NAMES)
            if ext in STYLE_EXTS or is_config or (all_text and is_probably_text(path)):
                result.append(path)
            elif ext in RELATED_EXTS and path.stat().st_size <= MAX_FILE_BYTES:
                # Keep project glue, but avoid dumping every Markdown article by default.
                if ext not in {".md", ".mdx"} or path.name.lower() in {"readme.md", "readme.mdx"}:
                    result.append(path)
    return sorted(set(result), key=lambda p: str(p.relative_to(root)).lower())

def main() -> int:
    parser = argparse.ArgumentParser(description="Export project structure and source files to one Markdown report.")
    parser.add_argument("root", nargs="?", default=".", help="项目根目录，默认当前目录")
    parser.add_argument("--output", default="project-code-report.md", help="报告输出路径")
    parser.add_argument("--all-text", action="store_true", help="尽可能包含所有文本文件（可能生成很大的报告）")
    parser.add_argument("--styles-only", action="store_true", help="只导出样式文件和项目配置")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"错误：目录不存在或不是目录：{root}", file=sys.stderr)
        return 2

    output = Path(args.output).expanduser()
    if not output.is_absolute():
        output = (Path.cwd() / output).resolve()
    # Never include the report itself in the scan if it is inside the project.
    files = choose_files(root, args.all_text)
    files = [p for p in files if p.resolve() != output.resolve()]
    if args.styles_only:
        files = [p for p in files if p.suffix.lower() in STYLE_EXTS or
                 p.name.lower() in CONFIG_NAMES or
                 any(p.name.lower().startswith(n + ".") for n in CONFIG_NAMES)]

    styles = [p for p in files if p.suffix.lower() in STYLE_EXTS]
    report: list[str] = [
        f"# 项目代码与样式分析资料\n",
        f"- 项目目录：`{root}`",
        f"- 生成时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- 纳入文件：{len(files)} 个；样式文件：{len(styles)} 个",
        "- 说明：本报告由脚本自动生成；文件内容按路径分节。默认会跳过依赖目录、构建产物、压缩文件和锁文件。",
        "- 安全提醒：脚本会跳过常见 `.env` 文件，但请在分享前检查报告是否包含令牌、密码、私有 URL 或其他敏感信息。",
        "\n## 1. 目录结构\n",
        "```text\n" + tree_text(root, files) + "\n```",
        "\n## 2. 样式文件清单\n",
    ]
    if styles:
        for p in styles:
            text_content, err = read_text(p)
            rel = p.relative_to(root).as_posix()
            line_count = text_content.count("\n") + 1 if text_content is not None else "未知"
            report.append(f"- `{rel}` — {line_count} 行" + (f"（{err}）" if err else ""))
    else:
        report.append("未发现样式文件。")

    report.append("\n## 3. 文件引用线索（自动提取，需结合代码核实）\n")
    any_refs = False
    for p in files:
        content, _ = read_text(p)
        if content is None:
            continue
        refs = extract_refs(p, content, root)
        if refs:
            any_refs = True
            report.append(f"### `{p.relative_to(root).as_posix()}`")
            report.extend(f"- `{ref}`" for ref in refs)
            report.append("")
    if not any_refs:
        report.append("没有提取到明显的本地引用。")

    report.append("\n## 4. 文件完整内容\n")
    for index, p in enumerate(files, start=1):
        rel = p.relative_to(root).as_posix()
        content, err = read_text(p)
        report.append(f"\n### {index}. `{rel}`\n")
        if content is None:
            report.append(f"> {err or '无法读取文件内容'}\n")
            continue
        if err:
            report.append(f"> 注意：{err}\n")
        lang = {
            ".css": "css", ".scss": "scss", ".sass": "sass", ".less": "less",
            ".styl": "stylus", ".html": "html", ".htm": "html", ".js": "javascript",
            ".mjs": "javascript", ".cjs": "javascript", ".ts": "typescript",
            ".tsx": "tsx", ".jsx": "jsx", ".json": "json", ".toml": "toml",
            ".yaml": "yaml", ".yml": "yaml", ".xml": "xml", ".md": "markdown",
            ".mdx": "mdx", ".go": "go", ".php": "php", ".vue": "vue",
            ".svelte": "svelte", ".astro": "astro", ".sh": "bash", ".ps1": "powershell",
            ".bat": "bat", ".txt": "text", ".conf": "ini", ".ini": "ini"
        }.get(p.suffix.lower(), "text")
        # Fence length is longer than any run of backticks in file content.
        longest = max((len(m.group(0)) for m in re.finditer(r"`+", content)), default=0)
        fence = "`" * max(3, longest + 1)
        report.append(f"{fence}{lang}\n{content.rstrip()}\n{fence}\n")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"完成！报告已生成：{output}")
    print(f"共收集 {len(files)} 个文件，其中样式文件 {len(styles)} 个。")
    print("分享前请检查报告中的敏感信息；如果报告过大，可使用 --styles-only。")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
