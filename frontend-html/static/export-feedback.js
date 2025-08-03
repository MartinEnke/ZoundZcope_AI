// export-feedback.js

let exportButtonInitialized = false;

export function setupExportButton() {
  console.log("Export button clicked");
  const exportBtn = document.getElementById("exportFeedbackBtn");
  if (!exportBtn || exportButtonInitialized) return;

  exportButtonInitialized = true;

  exportBtn.addEventListener("click", async () => {
    const sessionId = window.lastSessionId || "";
    const trackId = window.lastTrackId || "";

    if (!sessionId || !trackId) {
      alert("No session or track available to export. Please analyze first.");
      return;
    }

    exportBtn.disabled = true;
    exportBtn.textContent = "Exporting...";

    try {
      const response = await fetch(`/export/export-feedback-presets?session_id=${encodeURIComponent(sessionId)}&track_id=${encodeURIComponent(trackId)}`, {
        method: "GET",
        headers: { "Accept": "application/pdf" }
      });

      if (!response.ok) throw new Error("Failed to export feedback and presets.");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `feedback_presets_${sessionId}_${trackId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Error exporting feedback and presets: " + err.message);
      console.error(err);
    } finally {
      exportBtn.disabled = false;
      exportBtn.textContent = "Export Feedback & Presets";
    }
  });
}
