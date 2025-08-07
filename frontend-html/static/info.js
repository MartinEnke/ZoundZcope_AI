async function updateTokenStats() {
  try {
    const res = await fetch("/api/token-stats");
    const data = await res.json();

    const statsElement = document.getElementById("live-token-stats");
    if (statsElement) {
      statsElement.innerHTML = `
        <strong>Live Usage</strong><br />
        Tokens used: ${data.total_tokens}<br />
        Estimated cost: $${data.total_cost.toFixed(4)}
      `;
    }
  } catch (err) {
    console.error("Failed to load token stats", err);
  }
}

async function resetTokenStats() {
  await fetch("/api/reset-token-stats", { method: "POST" });
  updateTokenStats();
}

// Update on page load
document.addEventListener("DOMContentLoaded", updateTokenStats);
