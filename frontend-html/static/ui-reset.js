// ui-reset.js
import { isExportDone } from "./export-feedback.js";

export function hideSummarizeButton() {
  const summarizeBtn = document.getElementById("manualSummarizeBtn");
  if (summarizeBtn) {
    summarizeBtn.style.display = "none";
  }
}

export function showSummarizeButton() {
  const summarizeBtn = document.getElementById("manualSummarizeBtn");
  if (summarizeBtn) {
    summarizeBtn.style.display = "inline-block";
  }
}

export function clearQuickFollowupButtons() {
  const container = document.getElementById("quick-followup");
  if (!container) return;
  container.innerHTML = "";
  container.classList.add("hidden");
}



export function resetExportButton() {
  const exportBtn = document.getElementById("exportFeedbackBtn");
  if (!exportBtn) return;

  const sessionId = window.lastSessionId || "";
  const trackId = window.lastTrackId || "";

  if (sessionId && trackId && isExportDone(sessionId, trackId)) {
    exportBtn.disabled = true;
    exportBtn.textContent = "Feedback + Presets Exported";
    exportBtn.classList.add("opacity-60", "cursor-not-allowed");
  } else {
    exportBtn.disabled = false;
    exportBtn.textContent = "Export Feedback & Presets";
    exportBtn.classList.remove("opacity-60", "cursor-not-allowed");
  }
}

export function resetRMSDisplay() {
  const rmsDisplay = document.getElementById("rms-display");
  if (rmsDisplay) {
    rmsDisplay.innerText = "Current RMS: --";
  }
}


export function resetWaveformDisplay() {
  const waveformDiv = document.getElementById("waveform");
  if (waveformDiv) {
    waveformDiv.innerHTML = "";
    waveformDiv.classList.remove("waveform-playing");
  }

  if (window.wavesurfer) {
    window.wavesurfer.destroy();
    window.wavesurfer = null;
  }
}


export function resetReferenceWaveform() {
  const wrapper = document.getElementById("ref-waveform-wrapper");
  if (wrapper) {
    wrapper.style.display = "none";  // 👈 Hide the whole wrapper
  }

  const refWaveformDiv = document.getElementById("ref-waveform");
  if (refWaveformDiv) {
    refWaveformDiv.innerHTML = "";
    refWaveformDiv.classList.remove("waveform-playing");
  }

  if (window.refWavesurfer) {
    window.refWavesurfer.destroy();
    window.refWavesurfer = null;
  }
}