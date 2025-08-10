// app.js
import { renderRecentFeedbackPanel, toggleFollowup } from './recent-feedback.js';
import { initUploadUI } from './upload-ui.js';
import { createSessionInBackend, loadSessionTracks } from './session-api.js';
import { renderFeedbackAnalysis } from './feedback-render.js';
import { setupUploadHandler } from './upload-handler.js';
import { setupTrackSelectHandler } from './track-feedback-loader.js';
import { setupExportButton } from './export-feedback.js';
import { setupProfileDropdown } from './profile-dropdown.js';
import { setupMobileMenu } from './mobile-menu.js';
import { restoreZoundZcopeState, clearZoundZcopeState } from './state-persistence.js';

let refTrackAnalysisData = null;

setupUploadHandler();

// ============================
// DOMContentLoaded Block
// ============================
document.addEventListener('DOMContentLoaded', () => {
  restoreZoundZcopeState(); // Load persistent state
  initUploadUI();
  setupTrackSelectHandler();
  renderRecentFeedbackPanel();
  setupExportButton();
  setupProfileDropdown();
  setupMobileMenu();
});

document.getElementById('resetStateBtn')?.addEventListener('click', () => {
  if (confirm('Are you sure you want to reset all analysis and session data?')) {
    clearZoundZcopeState();
    location.reload(); // optional: refresh to fully reset
  }
});

// ============================
// Page Show (Back/Forward Cache)
// ============================
window.addEventListener('pageshow', (e) => {
  if (e.persisted) {
    restoreZoundZcopeState();
    renderRecentFeedbackPanel();
  }
});
