// state-persistence.js
// Handles saving and restoring ZoundZcope frontend state

export function saveZoundZcopeState({
  analysisHTML,
  feedbackHTML,
  followupHTML,
  summaryHTML,
  trackPath,
  rmsPath,
  genre,
  subgenre,
  type,
  profile,
  sessionId
}) {
  localStorage.setItem("zoundzcope_last_analysis", analysisHTML);
  localStorage.setItem("zoundzcope_last_feedback", feedbackHTML);
  localStorage.setItem("zoundzcope_last_followup", followupHTML);
  localStorage.setItem("zoundzcope_last_followup_summary", summaryHTML);
  localStorage.setItem("zoundzcope_waveform_path", trackPath);
  localStorage.setItem("zoundzcope_rms_path", rmsPath);
  localStorage.setItem("zoundzcope_genre", genre);
  localStorage.setItem("zoundzcope_subgenre", subgenre);
  localStorage.setItem("zoundzcope_type", type);
  localStorage.setItem("zoundzcope_profile", profile);
  localStorage.setItem("zoundzcope_session", sessionId);
}

export function restoreZoundZcopeState() {
  const analysisHTML = localStorage.getItem("zoundzcope_last_analysis");
  const feedbackHTML = localStorage.getItem("zoundzcope_last_feedback");
  const followupHTML = localStorage.getItem("zoundzcope_last_followup");
  const summaryHTML = localStorage.getItem("zoundzcope_last_followup_summary");

  const output = document.getElementById("analysisOutput");
  const feedbackBox = document.getElementById("gptResponse");
  const followupBox = document.getElementById("aiFollowupResponse");
  const summaryBox = document.getElementById("aiSummaryResponse");
  const customSection = document.getElementById("custom-ai-section");

  if (analysisHTML) {
    output.innerHTML = analysisHTML;
    document.getElementById("results").classList.remove("hidden");
  }

  if (feedbackHTML) {
    feedbackBox.innerHTML = feedbackHTML;
    document.getElementById("feedback").classList.remove("hidden");
  }

  let customVisible = false;

if (followupHTML) {
  followupBox.innerHTML = followupHTML;
  followupBox.classList.remove("hidden");
  customVisible = true;
}

if (summaryHTML) {
  summaryBox.innerHTML = summaryHTML;
  summaryBox.classList.remove("hidden");
  customVisible = true;
}

// ⬇️ Also show custom section if feedback exists (even without followups/summaries)
if (feedbackHTML && !customVisible) {
  customVisible = true;
}

if (customVisible && customSection) {
  customSection.classList.remove("hidden");
}


  // Restore dropdown values
  const map = [
    ["genre-input", "zoundzcope_genre"],
    ["subgenre-input", "zoundzcope_subgenre"],
    ["type-input", "zoundzcope_type"],
    ["profile-input", "zoundzcope_profile"],
    ["session_id", "zoundzcope_session"]
  ];
  map.forEach(([id, key]) => {
    const val = localStorage.getItem(key);
    if (val) document.getElementById(id).value = val;
  });

  // Restore waveform
  const waveformPath = localStorage.getItem("zoundzcope_waveform_path");
  const rmsPath = localStorage.getItem("zoundzcope_rms_path");

  if (waveformPath && typeof initMainWaveform === "function") {
    requestAnimationFrame(() => {
      initMainWaveform({ track_path: waveformPath, rms_path: rmsPath });

      const waveformEl = document.getElementById("waveform");
      if (waveformEl) {
        waveformEl.classList.remove("hidden");
        waveformEl.parentElement?.classList.remove("hidden");
      }
    });
  }

  // Restore quick follow-up chips
  const genre = localStorage.getItem("zoundzcope_genre");
  const type = localStorage.getItem("zoundzcope_type");
  const profile = localStorage.getItem("zoundzcope_profile");

  if (genre && type && profile && typeof window.ZoundZcope?.loadQuickFollowupButtons === "function") {
    window.ZoundZcope.loadQuickFollowupButtons(type, genre, profile);
  }

  // Restore backend linkage
  window.lastTrackId = localStorage.getItem("zoundzcope_last_track_id");
  window.lastSessionId = localStorage.getItem("zoundzcope_session");
}

export function clearZoundZcopeState() {
  const keys = [
    "zoundzcope_last_analysis",
    "zoundzcope_last_feedback",
    "zoundzcope_last_followup",
    "zoundzcope_last_followup_summary",
    "zoundzcope_genre",
    "zoundzcope_subgenre",
    "zoundzcope_type",
    "zoundzcope_profile",
    "zoundzcope_session",
    "zoundzcope_waveform_path",
    "zoundzcope_rms_path",
    "zoundzcope_last_track_id"
  ];
  keys.forEach(key => localStorage.removeItem(key));
  console.log("🧹 ZoundZcope state cleared.");
}
