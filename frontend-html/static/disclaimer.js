// /static/disclaimer.js
(function () {
  const MODAL_ID = "zz-disclaimer";
  const CLOSE_ID = "zz-disclaimer-close";
  const ACCEPT_ID = "zz-disclaimer-accept";
  const NEVER_ID = "zz-disclaimer-never";
  const STORAGE_KEY = "zz_ack_disclaimer"; // set to "true" if user opts out

  const modal = document.getElementById(MODAL_ID);
  const btnClose = document.getElementById(CLOSE_ID);
  const btnAccept = document.getElementById(ACCEPT_ID);
  const never = document.getElementById(NEVER_ID);
  const dialog = modal?.querySelector(".zz-modal-card");

  if (!modal || !btnClose || !btnAccept || !dialog) return;

  function lockScroll(lock) {
    document.documentElement.style.overflow = lock ? "hidden" : "";
  }

  function openDisclaimer() {
    modal.classList.remove("hidden");
    lockScroll(true);
    // Focus the primary button for accessibility
    setTimeout(() => btnAccept.focus(), 40);
  }

  function closeDisclaimer() {
    if (never && never.checked) {
      localStorage.setItem(STORAGE_KEY, "true");
    }
    modal.classList.add("hidden");
    lockScroll(false);
  }

  // Show logic:
  // - If user checked "Don't show again": skip
  // - Else: show on every load/refresh
  window.addEventListener("DOMContentLoaded", () => {
    const acknowledged = localStorage.getItem(STORAGE_KEY) === "true";

    if (!acknowledged) {
      // Allow your intro loader to finish; then show
      setTimeout(openDisclaimer, 650);
    }
  });

  // Close handlers
  btnClose.addEventListener("click", closeDisclaimer);
  btnAccept.addEventListener("click", closeDisclaimer);

  // Click outside to close
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeDisclaimer();
  });

  // ESC to close
  document.addEventListener("keydown", (e) => {
    if (!modal.classList.contains("hidden") && e.key === "Escape") {
      closeDisclaimer();
    }
  });

  // Basic focus trap (lightweight)
  modal.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const f = modal.querySelectorAll("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])");
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
