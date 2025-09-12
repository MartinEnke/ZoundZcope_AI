// /static/disclaimer.js
(function () {
  const MODAL_ID = "zz-disclaimer";
  const ACCEPT_ID = "zz-disclaimer-accept";

  const modal = document.getElementById(MODAL_ID);
  const btnAccept = document.getElementById(ACCEPT_ID);
  const dialog = modal?.querySelector(".zz-modal-card");
  const backdrop = modal?.querySelector(".zz-modal-backdrop");

  if (!modal || !btnAccept || !dialog) return;

  function lockScroll(lock) {
    document.documentElement.style.overflow = lock ? "hidden" : "";
  }

  function openDisclaimer() {
    modal.classList.remove("hidden");
    lockScroll(true);
    setTimeout(() => btnAccept.focus(), 40);
  }

  function closeDisclaimer() {
    modal.classList.add("hidden");
    lockScroll(false);
    window.dispatchEvent(new CustomEvent("zz:disclaimerAccepted"));
  }

  // Always show on each page load/refresh (no "never show again")
  window.addEventListener("DOMContentLoaded", () => {
    setTimeout(openDisclaimer, 650); // give your loader a moment first
  });

  // Only way to dismiss is Accept
  btnAccept.addEventListener("click", closeDisclaimer);

  // Ignore backdrop clicks (don’t close)
  backdrop?.addEventListener("click", (e) => e.stopPropagation());

  // Block ESC key while visible
  document.addEventListener("keydown", (e) => {
    if (!modal.classList.contains("hidden") && e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
    }
  });

  // Lightweight focus trap
  modal.addEventListener("keydown", (e) => {
    if (e.key !== "Tab" || modal.classList.contains("hidden")) return;
    const f = modal.querySelectorAll(
      "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
    );
    const focusable = Array.prototype.slice.call(f).filter(el => !el.hasAttribute("disabled"));
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (e.shiftKey) {
      if (document.activeElement === first) { last.focus(); e.preventDefault(); }
    } else {
      if (document.activeElement === last) { first.focus(); e.preventDefault(); }
    }
  });
})();
