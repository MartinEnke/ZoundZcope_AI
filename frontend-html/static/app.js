// app.js
import { renderRecentFeedbackPanel, toggleFollowup } from "./recent-feedback.js";
import { initUploadUI } from "./upload-ui.js";
import { createSessionInBackend, loadSessionTracks } from "./session-api.js";
import { renderFeedbackAnalysis } from "./feedback-render.js";
import { setupUploadHandler } from "./upload-handler.js";
import { setupTrackSelectHandler } from './track-feedback-loader.js';
import { setupExportButton } from "./export-feedback.js";
import { setupProfileDropdown } from "./profile-dropdown.js";
import { setupMobileMenu } from "./mobile-menu.js";

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

  setupExportButton();
  setupProfileDropdown();
  setupMobileMenu();

});

// ============================
// ✅ Page Show (Back/Forward Cache)
// ============================
window.addEventListener("pageshow", (e) => {
  if (e.persisted) {
    renderRecentFeedbackPanel();

  }
});
