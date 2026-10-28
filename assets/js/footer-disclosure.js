document.addEventListener("DOMContentLoaded", () => {
  const button = document.querySelector(".site-footer__toggle");
  const content = document.querySelector("#site-footer-content");
  const icon = document.querySelector(".site-footer__toggle-icon");

  if (!button || !content) return;

  button.addEventListener("click", () => {
    const expanded = button.getAttribute("aria-expanded") === "true";

    button.setAttribute("aria-expanded", String(!expanded));
    content.hidden = expanded;

    if (icon) {
      icon.textContent = expanded ? "+" : "−";
    }
  });
});


/* 正文注释：电脑悬停展开，手机点击展开 */
document.addEventListener("DOMContentLoaded", () => {
  const notes = document.querySelectorAll("[data-inline-note]");
  const canHover = window.matchMedia(
    "(hover: hover) and (pointer: fine)"
  );

  notes.forEach((note) => {
    const trigger = note.querySelector(".inline-note__trigger");
    const content = note.querySelector(".inline-note__content");

    if (!trigger || !content) return;

    const open = () => {
      content.hidden = false;
      trigger.setAttribute("aria-expanded", "true");
    };

    const close = () => {
      content.hidden = true;
      trigger.setAttribute("aria-expanded", "false");
    };

    const toggle = () => {
      if (content.hidden) {
        open();
      } else {
        close();
      }
    };

    trigger.addEventListener("click", (event) => {
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
});
