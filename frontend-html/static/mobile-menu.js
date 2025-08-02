// mobile-menu.js

export function setupMobileMenu() {
  const menuBtn = document.getElementById("mobile-menu-button");
  const dropdown = document.getElementById("mobile-menu-dropdown");

  if (!menuBtn || !dropdown) return;

  menuBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.classList.toggle("hidden");
  });

  document.addEventListener("click", (e) => {
    if (!dropdown.contains(e.target) && !menuBtn.contains(e.target)) {
      dropdown.classList.add("hidden");
    }
  });
}
