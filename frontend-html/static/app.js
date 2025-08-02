// app.js
import { renderRecentFeedbackPanel, toggleFollowup } from "./recent-feedback.js";
import { initUploadUI } from "./upload-ui.js";
import { createSessionInBackend, loadSessionTracks } from "./session-api.js";
import {
  hideSummarizeButton,
  showSummarizeButton,
  clearQuickFollowupButtons,
  resetExportButton,
  resetRMSDisplay,
  resetWaveformDisplay,
  resetReferenceWaveform
} from "./ui-reset.js";
import { renderFeedbackAnalysis } from "./feedback-render.js";


let refTrackAnalysisData = null;


// ==========================================================
// 🔸 Upload Form Submission Logic (UPDATED)
// ==========================================================
const form = document.getElementById("uploadForm");
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

// ==========================================================
// 🔸 Display Feedback for Selected Track
// Fetches messages and shows styled feedback history
// ==========================================================
document.addEventListener("DOMContentLoaded", () => {
  const trackSelect = document.getElementById("track-select");
  if (!trackSelect) {
    console.warn("⚠️ track-select element not found");
    return;
  }

  trackSelect.addEventListener("change", async (e) => {
    const trackId = e.target.value;
    if (!trackId) return;

    try {
      const trackRes = await fetch(`/tracks/${trackId}`);
      if (!trackRes.ok) throw new Error("Failed to fetch track data");
      const track = await trackRes.json();

      const msgRes = await fetch(`/tracks/${trackId}/messages`);
      if (!msgRes.ok) throw new Error("Failed to fetch messages");
      const messages = await msgRes.json();

      const feedbackBox = document.getElementById("gptResponse");
      feedbackBox.innerHTML = "";

      if (messages.length === 0) {
        feedbackBox.innerHTML = "<p>No feedback yet for this track.</p>";
      } else {
        messages.forEach(msg => {
          const trackName = track?.track_name || "Unnamed Track";
          const type = track?.type
            ? track.type.charAt(0).toUpperCase() + track.type.slice(1)
            : "Unknown";
          const profile = msg.feedback_profile
            ? msg.feedback_profile.replace(/[_-]/g, " ").replace(/\b\w/g, l => l.toUpperCase())
            : "Default";

          const msgEl = document.createElement("div");
          msgEl.className = "mb-4";

          // 🎨 Colored track info heading
          const heading = document.createElement("p");
          heading.className = `font-semibold ${
            type.toLowerCase() === "mixdown"
              ? "text-pink-400"
              : type.toLowerCase() === "master"
              ? "text-blue-400"
              : "text-white"
          }`;
          heading.textContent = `Track: ${trackName} | Type: ${type} | Profile: ${profile}`;
          msgEl.appendChild(heading);

          // 💬 Feedback content in white bullets
          const ul = document.createElement("ul");
          ul.className = "list-disc list-inside text-white/90 text-base space-y-2 mt-2";

          const lines = msg.message
            .split("\n")
            .map(line => line.replace(/^[-•\s]+/, "").trim())
            .filter(Boolean);

          lines.forEach(line => {
            const li = document.createElement("li");
            li.textContent = line;
            ul.appendChild(li);
          });

          msgEl.appendChild(ul);
          feedbackBox.appendChild(msgEl);
        });
      }

      document.getElementById("feedback").classList.remove("hidden");
    } catch (err) {
      console.error("❌ Error displaying chat feedback:", err);
    }
  });

// === Add new export button listener here ===
document.addEventListener("DOMContentLoaded", () => {
console.log("DOMContentLoaded event fired for export button setup");
  const exportBtn = document.getElementById("exportFeedbackBtn");
  console.log("Export button found:", exportBtn);
  if (!exportBtn) return;

  exportBtn.addEventListener("click", async () => {
  console.log("Export button clicked");

  const sessionId = window.lastSessionId || "";
  const trackId = window.lastTrackId || "";

  if (!sessionId || !trackId) {
  console.log("Export blocked — missing session or track:", { sessionId, trackId });
    alert("No session or track available to export. Please analyze first.");
    return;
  }

  exportBtn.disabled = true;
  exportBtn.textContent = "Exporting...";
  console.log(`Fetching PDF for session ${sessionId} and track ${trackId}`);

  try {
    const response = await fetch(`/export/export-feedback-presets?session_id=${encodeURIComponent(sessionId)}&track_id=${encodeURIComponent(trackId)}`, {
      method: "GET",
      headers: {
        "Accept": "application/pdf"
      }
    });

    if (!response.ok) {
      throw new Error("Failed to export feedback and presets.");
    }

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
});

// ==========================================================
// 🔁 Restore Last Analysis, Feedback & Follow-up (incl. browser back nav)
// ==========================================================
function restoreZoundzcopeState() {
  const output = document.getElementById("analysisOutput");
  const feedbackBox = document.getElementById("gptResponse");
  const followupBox = document.getElementById("aiFollowupResponse");
  const resultsSection = document.getElementById("results");
  const feedbackSection = document.getElementById("feedback");
  const subheadingHTML = localStorage.getItem("zoundzcope_last_subheading");

  const lastAnalysis = localStorage.getItem("zoundzcope_last_analysis");
  const lastFeedback = localStorage.getItem("zoundzcope_last_feedback");
  const lastFollowup = localStorage.getItem("zoundzcope_last_followup");

  if (lastAnalysis && lastFeedback) {
    output.innerHTML = lastAnalysis;
    feedbackBox.innerHTML = ""; // ← just the list, no subheading
const subheading = document.createElement("p");
    feedbackBox.innerHTML += lastFeedback;
    resultsSection.classList.remove("hidden");
    feedbackSection.classList.remove("hidden");
  }

  if (lastFollowup) {
    followupBox.innerHTML = lastFollowup;
    followupBox.classList.remove("hidden");
  }
}

// 🔁 Works on normal load + browser back/forward navigation
window.addEventListener("DOMContentLoaded", restoreZoundzcopeState);
window.addEventListener("pageshow", (event) => {
  if (event.persisted) {
    // This means the page was loaded from the back/forward cache
    restoreZoundzcopeState();
  }
});


  // ==========================================================
  // 🔸 Hide Profile Options on Outside Click
  // ==========================================================
  const profileButton = document.getElementById("profile-button");
  const profileOptions = document.getElementById("profile-options");

  document.addEventListener("click", (e) => {
    if (!profileButton.contains(e.target) && !profileOptions.contains(e.target)) {
      profileOptions.classList.add("hidden");
    }
  });


});


window.addEventListener("DOMContentLoaded", renderRecentFeedbackPanel);
window.addEventListener("pageshow", (e) => {
  if (e.persisted) renderRecentFeedbackPanel();
});


document.addEventListener("DOMContentLoaded", () => {
  initUploadUI();
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








