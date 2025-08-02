// upload-handler.js
import {
  hideSummarizeButton,
  showSummarizeButton,
  clearQuickFollowupButtons,
  resetExportButton,
  resetRMSDisplay,
  resetWaveformDisplay,
  resetReferenceWaveform
} from "./ui-reset.js";

import { createSessionInBackend, loadSessionTracks } from "./session-api.js";
import { renderFeedbackAnalysis } from "./feedback-render.js";

let refTrackAnalysisData = null;
let followupThread = [];
let followupGroupIndex = 0;
let lastManualSummaryGroup = -1;

export function setupUploadHandler() {
  const form = document.getElementById("uploadForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    hideSummarizeButton();
    resetRMSDisplay();
    resetExportButton();
    clearQuickFollowupButtons();
    resetWaveformDisplay();
    resetReferenceWaveform();

    const feedbackBox = document.getElementById("gptResponse");
    if (feedbackBox) feedbackBox.innerHTML = "";

    const followupResponseBox = document.getElementById("aiFollowupResponse");
    if (followupResponseBox) followupResponseBox.innerHTML = "";

    localStorage.removeItem("zoundzcope_last_analysis");
    localStorage.removeItem("zoundzcope_last_feedback");
    localStorage.removeItem("zoundzcope_last_followup");
    localStorage.removeItem("zoundzcope_last_subheading");

    const followupContainer = document.getElementById("followupSection");
    const manualSummaryContainer = document.getElementById("manualSummarySection");
    if (followupContainer) followupContainer.innerHTML = "";
    if (manualSummaryContainer) manualSummaryContainer.innerHTML = "";

    const analyzeButton = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);

    const type = document.getElementById("type-input")?.value;
    console.log("📤 Submitting type:", type);

    const sessionIdInput = document.getElementById("session_id");
    const newSessionInput = document.getElementById("new-session-input");
    const isNewSession = !newSessionInput.classList.contains("hidden");
    const newSessionName = newSessionInput.value.trim();

    let sessionId = sessionIdInput.value;

    if (isNewSession && !newSessionName) {
      alert("Please enter a session name.");
      return;
    }

    analyzeButton.classList.add("analyze-loading");
    analyzeButton.disabled = true;

    if (isNewSession) {
      const sessionResult = await createSessionInBackend(newSessionName);
      if (!sessionResult || !sessionResult.id) {
        alert("Session creation failed.");
        analyzeButton.classList.remove("analyze-loading");
        analyzeButton.disabled = false;
        return;
      }
      sessionId = sessionResult.id;
    }

    if (!sessionId) {
      alert("Please choose or create a session.");
      analyzeButton.classList.remove("analyze-loading");
      analyzeButton.disabled = false;
      return;
    }

    formData.set("session_id", sessionId);

    const feedbackProfile = document.getElementById("profile-input").value;
    const selectedGenre = document.getElementById("genre-input").value;
    formData.set("genre", selectedGenre);

    const customSubgenre = document.getElementById("custom-subgenre-input").value.trim();
    if (customSubgenre) {
      formData.set("subgenre", customSubgenre.toLowerCase());
    } else {
      const selectedSubgenre = document.getElementById("subgenre-input").value;
      formData.set("subgenre", selectedSubgenre);
    }

    const fileInput = document.getElementById("file-upload");
    let finalTrackName = "Untitled Track";
    if (fileInput && fileInput.files.length > 0) {
      const fullName = fileInput.files[0].name;
      finalTrackName = fullName.replace(/\.[^/.]+$/, "");
    }

    formData.set("track_name", finalTrackName);
    formData.set("feedback_profile", feedbackProfile);

    const refFileInput = document.getElementById("ref-file-upload");
    if (refFileInput && refFileInput.files.length > 0) {
      formData.append("ref_file", refFileInput.files[0]);
    }

    try {
      const response = await fetch("/upload/", {
        method: "POST",
        body: formData,
      });

      const raw = await response.text();
      const result = JSON.parse(raw);

      refTrackAnalysisData = result.ref_analysis || null;

      if (response.ok) {
        const tracks = await loadSessionTracks(sessionId);
        console.log("Tracks loaded after upload:", tracks);
        console.log("Setting window.lastTrackId to:", tracks[0]?.id);

        window.lastSessionId = sessionId;
        window.lastTrackId = tracks[0]?.id || "";

        if (sessionIdInput) {
          sessionIdInput.value = sessionId;
        }

        followupThread = [];
        followupGroupIndex = 0;
        lastManualSummaryGroup = -1;

        renderFeedbackAnalysis(result, refTrackAnalysisData);
      } else {
        console.error("Upload failed response:", result);
        alert("Upload failed: " + JSON.stringify(result));
      }
    } catch (err) {
      console.error("Fetch error:", err);
      alert("An error occurred during upload.");
    } finally {
      analyzeButton.classList.remove("analyze-loading");
      analyzeButton.disabled = false;
    }
  });
}
