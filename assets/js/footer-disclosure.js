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