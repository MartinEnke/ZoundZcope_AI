// profile-dropdown.js

export function setupProfileDropdown() {
  const profileButton = document.getElementById("profile-button");
  const profileOptions = document.getElementById("profile-options");

  if (!profileButton || !profileOptions) return;

  document.addEventListener("click", (e) => {
    if (!profileButton.contains(e.target) && !profileOptions.contains(e.target)) {
      profileOptions.classList.add("hidden");
    }
  });
}