// app.js
import { renderRecentFeedbackPanel, toggleFollowup } from "./recent-feedback.js";
import { initUploadUI } from "./upload-ui.js";
import { createSessionInBackend, loadSessionTracks } from "./session-api.js";
import { renderFeedbackAnalysis } from "./feedback-render.js";
import { setupUploadHandler } from "./upload-handler.js";
import { setupTrackSelectHandler } from './track-feedback-loader.js';

let refTrackAnalysisData = null;

setupUploadHandler();

function restoreZoundzcopeState() {
  const output = document.getElementById("analysisOutput");
  const feedbackBox = document.getElementById("gptResponse");
  const followupBox = document.getElementById("aiFollowupResponse");
  const resultsSection = document.getElementById("results");
  const feedbackSection = document.getElementById("feedback");

  const lastAnalysis = localStorage.getItem("zoundzcope_last_analysis");
  const lastFeedback = localStorage.getItem("zoundzcope_last_feedback");
  const lastFollowup = localStorage.getItem("zoundzcope_last_followup");

  if (lastAnalysis && lastFeedback) {
    output.innerHTML = lastAnalysis;
    feedbackBox.innerHTML = lastFeedback;
    resultsSection.classList.remove("hidden");
    feedbackSection.classList.remove("hidden");
  }

  if (lastFollowup) {
    followupBox.innerHTML = lastFollowup;
    followupBox.classList.remove("hidden");
  }
}

// ============================
// ✅ DOMContentLoaded Block
// ============================
document.addEventListener("DOMContentLoaded", () => {
  initUploadUI();
  setupTrackSelectHandler();
  renderRecentFeedbackPanel();
  restoreZoundzcopeState();

  // 🔸 Export Button
  const exportBtn = document.getElementById("exportFeedbackBtn");
  if (exportBtn) {
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

  // 🔸 Profile Dropdown Hide
  const profileButton = document.getElementById("profile-button");
  const profileOptions = document.getElementById("profile-options");
  if (profileButton && profileOptions) {
    document.addEventListener("click", (e) => {
      if (!profileButton.contains(e.target) && !profileOptions.contains(e.target)) {
        profileOptions.classList.add("hidden");
      }
    });
  }

  // 🔸 Mobile Menu
  const menuBtn = document.getElementById("mobile-menu-button");
  const dropdown = document.getElementById("mobile-menu-dropdown");
  if (menuBtn && dropdown) {
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
});

// ============================
// ✅ Page Show (Back/Forward Cache)
// ============================
window.addEventListener("pageshow", (e) => {
  if (e.persisted) {
    renderRecentFeedbackPanel();
    restoreZoundzcopeState();
  }
});
