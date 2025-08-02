// ui-reset.js

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
  if (exportBtn) {
    exportBtn.disabled = false;
    exportBtn.textContent = "Export Feedback & Presets";
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