// upload-handler.js
import { saveZoundZcopeState } from "./state-persistence.js";
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

function showUploadError(message) {
  const box = document.getElementById("uploadError");
  if (!box) {
    alert(message);
    return;
  }
  box.textContent = message;
  box.classList.remove("hidden");
  setTimeout(() => {
    box.classList.add("hidden");
    box.textContent = "";
  }, 6000);
}

function baseName(filename) {
  return filename.replace(/\.[^/.]+$/, "");
}

export function setupUploadHandler() {
  const form = document.getElementById("uploadForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    // --- Reset UI pieces ---
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
    const summaryBox = document.getElementById("aiSummaryResponse");
    if (summaryBox) summaryBox.innerHTML = "";

    // clear persisted last state
    localStorage.removeItem("zoundzcope_last_analysis");
    localStorage.removeItem("zoundzcope_last_feedback");
    localStorage.removeItem("zoundzcope_last_followup");
    localStorage.removeItem("zoundzcope_last_subheading");

    const followupContainer = document.getElementById("followupSection");
    const manualSummaryContainer = document.getElementById("manualSummarySection");
    if (followupContainer) followupContainer.innerHTML = "";
    if (manualSummaryContainer) manualSummaryContainer.innerHTML = "";

    const analyzeButton = document.getElementById("analyze-button");
    analyzeButton?.classList.add("analyze-loading");
    if (analyzeButton) analyzeButton.disabled = true;

    try {
      // --- Gather inputs ---
      const fileInput = document.getElementById("file-upload");
      const refFileInput = document.getElementById("ref-file-upload");
      const sessionIdInput = document.getElementById("session_id");
      const newSessionInput = document.getElementById("new-session-input");
      const isNewSession = newSessionInput && !newSessionInput.classList.contains("hidden");
      const newSessionName = (newSessionInput?.value || "").trim();

      const typeVal = document.getElementById("type-input")?.value?.trim();
      const genreVal = document.getElementById("genre-input")?.value?.trim();
      const subgenreSelected = document.getElementById("subgenre-input")?.value?.trim();
      const customSub = document.getElementById("custom-subgenre-input")?.value?.trim();
      const profileVal = document.getElementById("profile-input")?.value?.trim();

      // --- Client-side validations ---
      if (!fileInput || fileInput.files.length === 0) {
        showUploadError("Please choose a file to upload.");
        return;
      }
      if (!typeVal) {
        showUploadError("Please choose a track context (Mixdown / Mastering / Master Review).");
        return;
      }
      if (!genreVal) {
        showUploadError("Please choose a genre.");
        return;
      }
      if (!profileVal) {
        showUploadError("Please choose a feedback profile.");
        return;
      }
      if (isNewSession && !newSessionName) {
        showUploadError("Please enter a session name.");
        return;
      }

      // --- Ensure a session id ---
      let sessionId = sessionIdInput?.value;
      if (isNewSession) {
        const sessionResult = await createSessionInBackend(newSessionName);
        if (!sessionResult || !sessionResult.id) {
          showUploadError("Session creation failed.");
          return;
        }
        sessionId = sessionResult.id;
        if (sessionIdInput) sessionIdInput.value = sessionId;
      }
      if (!sessionId) {
        showUploadError("Please choose or create a session.");
        return;
      }

      // --- Build FormData explicitly (avoid relying on DOM names) ---
      const formData = new FormData();
      // main file
      const mainFile = fileInput.files[0];
      formData.set("file", mainFile);

      // optional reference
      if (refFileInput && refFileInput.files.length > 0) {
        formData.set("ref_file", refFileInput.files[0]);
      }

      // session + labels
      formData.set("session_id", sessionId);
      if (isNewSession) {
        formData.set("session_name", newSessionName);
      }

      // metadata
      formData.set("type", typeVal);
      formData.set("genre", genreVal);

      const finalSub = customSub ? customSub.toLowerCase() : (subgenreSelected || "");
      if (finalSub) formData.set("subgenre", finalSub);

      const fullName = mainFile.name;
      const trackDisplayName = baseName(fullName) || "Untitled Track";
      formData.set("track_name", trackDisplayName);

      formData.set("feedback_profile", profileVal);

      // --- Update filename labels (UX nicety) ---
      const fileLabel = document.getElementById("file-name");
      if (fileLabel) {
        fileLabel.textContent = fullName;
        fileLabel.className = "text-gray-400";
        localStorage.setItem("zoundzcope_file_name", fullName);
        localStorage.setItem("zoundzcope_file_name_color", fileLabel.className);
      }
      const refLabel = document.getElementById("ref-file-name");
      if (refLabel && refFileInput?.files?.[0]) {
        const refDisplayName = refFileInput.files[0].name;
        refLabel.textContent = refDisplayName;
        refLabel.className = "text-gray-400";
        localStorage.setItem("zoundzcope_ref_file_name", refDisplayName);
        localStorage.setItem("zoundzcope_ref_file_name_color", refLabel.className);
      }

      // --- Debug: show exactly what we send ---
      for (const [k, v] of formData.entries()) {
        console.log("[FormData]", k, v instanceof File ? `(file) ${v.name}` : v);
      }

      // --- Send request ---
      const response = await fetch("/upload/", {
        method: "POST",
        body: formData,
      });

      // tolerate non-JSON error pages
      const result = await response.json().catch(() => null);

      if (!response.ok) {
        // Prefer structured detail
        let msg = "Upload failed.";
        if (result?.detail) {
          if (Array.isArray(result.detail)) {
            // FastAPI 422 (validation error) shape
            msg = result.detail.map(d => d.msg || d.detail || JSON.stringify(d)).join("; ");
          } else {
            msg = result.detail;
          }
        } else if (result) {
          msg = JSON.stringify(result);
        }
        console.error("Upload failed response:", result);
        showUploadError(msg || "The file is wrong, corrupted, or too big.");
        return;
      }

      if (!result) {
        showUploadError("Upload failed: invalid server response.");
        return;
      }

      // --- Success path ---
      refTrackAnalysisData = result.ref_analysis || null;

      // refresh tracks for this session (so we can store lastTrackId)
      const tracks = await loadSessionTracks(sessionId);
      console.log("Tracks loaded after upload:", tracks);

      window.lastSessionId = sessionId;
      window.lastTrackId = tracks?.[0]?.id || "";
      localStorage.setItem("zoundzcope_last_track_id", window.lastTrackId);

      resetExportButton();

      // render analysis + feedback
      renderFeedbackAnalysis(result, refTrackAnalysisData);

      // persist UI state for restore
      saveZoundZcopeState({
        analysisHTML: document.getElementById("analysisOutput")?.innerHTML || "",
        feedbackHTML: document.getElementById("gptResponse")?.innerHTML || "",
        followupHTML: document.getElementById("aiFollowupResponse")?.innerHTML || "",
        summaryHTML: document.getElementById("aiSummaryResponse")?.innerHTML || "",
        trackPath: result.track_path,
        rmsPath: result.rms_path,
        genre: genreVal,
        subgenre: finalSub || "",
        type: typeVal,
        profile: profileVal,
        sessionId: sessionId,
      });

    } catch (err) {
      console.error("Fetch error:", err);
      showUploadError("An unexpected error occurred during upload.");
    } finally {
      analyzeButton?.classList.remove("analyze-loading");
      if (analyzeButton) analyzeButton.disabled = false;
    }
  });
}
