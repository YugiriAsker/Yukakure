
/* 初始化页脚展开与正文注释 */
function initializeFooterDisclosure() {
  /* 页脚展开与收起 */
  const button = document.querySelector(".site-footer__toggle");
  const content = document.querySelector("#site-footer-content");
  const icon = document.querySelector(".site-footer__toggle-icon");

  if (
    button &&
    content &&
    button.dataset.footerBound !== "true"
  ) {
    button.dataset.footerBound = "true";

    button.addEventListener("click", () => {
      const isExpanded =
        button.getAttribute("aria-expanded") === "true";

      button.setAttribute("aria-expanded", String(!isExpanded));
      content.hidden = isExpanded;

      if (icon) {
        icon.textContent = isExpanded ? "+" : "−";
      }
    });
  }

  /* 正文注释：电脑悬停展开，触屏设备点击展开 */
  const notes = document.querySelectorAll("[data-inline-note]");
  const canHover = window.matchMedia(
    "(hover: hover) and (pointer: fine)"
  );

  notes.forEach((note) => {
    const trigger = note.querySelector(".inline-note__trigger");
    const noteContent = note.querySelector(".inline-note__content");

    if (
      !trigger ||
      !noteContent ||
      trigger.dataset.noteInitialized === "true"
    ) {
      return;
    }

    trigger.dataset.noteInitialized = "true";

    const open = () => {
      noteContent.hidden = false;
      trigger.setAttribute("aria-expanded", "true");
    };

    const close = () => {
      noteContent.hidden = true;
      trigger.setAttribute("aria-expanded", "false");
    };

    const toggle = () => {
      if (noteContent.hidden) {
        open();
      } else {
        close();
      }
    };

    // 触屏设备：点击展开或收起
    trigger.addEventListener("click", (event) => {
      if (canHover.matches) return;

      event.preventDefault();
      toggle();
    });

    // 电脑：悬停展开，移开收起
    note.addEventListener("mouseenter", () => {
      if (canHover.matches) open();
    });

    note.addEventListener("mouseleave", () => {
      if (canHover.matches) close();
    });

    // 按 Escape 收起注释
    note.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        close();
        trigger.focus();
      }
    });
  });
}

/* 兼容脚本在 DOM 加载前后执行 */
if (document.readyState === "loading") {
  document.addEventListener(
    "DOMContentLoaded",
    initializeFooterDisclosure
  );
} else {
  initializeFooterDisclosure();
}
