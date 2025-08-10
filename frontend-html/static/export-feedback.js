// export-feedback.js
let exportInProgress = false;

function exportKey(sessionId, trackId) {
  return `z_export_done_${sessionId}_${trackId}`;
}
export function isExportDone(sessionId, trackId) {
  return !!localStorage.getItem(exportKey(sessionId, trackId));
}
export function markExportDone(sessionId, trackId) {
  localStorage.setItem(exportKey(sessionId, trackId), "1");
}

export function setupExportButton() {
  if (window.__exportFeedbackBtnInit) return;
  window.__exportFeedbackBtnInit = true;

  const btn = document.getElementById("exportFeedbackBtn");
  if (!btn) return;

  btn.setAttribute("type", "button");

  const fresh = btn.cloneNode(true);
  btn.parentNode.replaceChild(fresh, btn);

  // Initialize state based on current selection (if available)
  const initState = () => {
    const sessionId = window.lastSessionId || "";
    const trackId = window.lastTrackId || "";
    if (sessionId && trackId && isExportDone(sessionId, trackId)) {
      fresh.disabled = true;
      fresh.textContent = "Feedback + Presets Exported";
      fresh.classList.add("opacity-60", "cursor-not-allowed");
    } else {
      fresh.disabled = false;
      fresh.textContent = "Export Feedback & Presets";
      fresh.classList.remove("opacity-60", "cursor-not-allowed");
    }
  };
  initState();

  fresh.addEventListener("click", async (e) => {
    e.preventDefault();
    if (exportInProgress) return;

    const sessionId = window.lastSessionId || "";
    const trackId = window.lastTrackId || "";
    if (!sessionId || !trackId) {
      alert("No session or track available to export. Please analyze first.");
      return;
    }

    // Already exported? Block it.
    if (isExportDone(sessionId, trackId)) return;

    exportInProgress = true;
    fresh.disabled = true;
    fresh.textContent = "Exporting...";

    try {
      const url = `/export/export-feedback-presets?session_id=${encodeURIComponent(sessionId)}&track_id=${encodeURIComponent(trackId)}`;
      const res = await fetch(url, { method: "GET", headers: { Accept: "application/pdf" } });
      if (!res.ok) throw new Error("Failed to export feedback and presets.");

      const blob = await res.blob();
      const cd = res.headers.get("Content-Disposition");
      let filename = "Zoundzcope_AI-Report.pdf";
      const m = cd && cd.match(/filename="?([^"]+)"?/);
      if (m && m[1]) filename = m[1];

      const objUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = objUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(objUrl);

      // ✅ Mark as done + freeze the button
      markExportDone(sessionId, trackId);
      fresh.textContent = "Feedback + Presets Exported";
      fresh.classList.add("opacity-60", "cursor-not-allowed");
    } catch (err) {
      alert("Error exporting feedback and presets: " + err.message);
      console.error(err);
      // roll back disabled state on failure
      fresh.disabled = false;
      fresh.textContent = "Export Feedback & Presets";
    } finally {
      exportInProgress = false;
    }
  });

  // Optional: re-init state when the app updates lastSessionId/lastTrackId
  // Call window.refreshExportButtonState?.() after track/session change.
  window.refreshExportButtonState = initState;
}
