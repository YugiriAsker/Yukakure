
/* 在 DOM 就绪后初始化；如果 DOM 已经就绪，则立即执行 */
function initializeFooterDisclosure() {
  const button = document.querySelector(".site-footer__toggle");
  const content = document.querySelector("#site-footer-content");
  const icon = document.querySelector(".site-footer__toggle-icon");

  if (button && content && !button.dataset.disclosureInitialized) {
    button.dataset.disclosureInitialized = "true";

    button.addEventListener("click", () => {
      const expanded = button.getAttribute("aria-expanded") === "true";

      button.setAttribute("aria-expanded", String(!expanded));
      content.hidden = expanded;

      if (icon) {
        icon.textContent = expanded ? "+" : "−";
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

    if (!trigger || !noteContent || trigger.dataset.noteInitialized) return;

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

    trigger.addEventListener("click", (event) => {
      // 电脑端使用悬停交互，不再额外切换
      if (canHover.matches) return;

      event.preventDefault();
      toggle();
    });

    note.addEventListener("mouseenter", () => {
      if (canHover.matches) open();
    });

    note.addEventListener("mouseleave", () => {
      if (canHover.matches) close();
    });

    note.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        close();
        trigger.focus();
      }
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeFooterDisclosure);
} else {
  initializeFooterDisclosure();
}
