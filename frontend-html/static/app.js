// app.js
import { renderRecentFeedbackPanel, toggleFollowup } from "./recent-feedback.js";



let refTrackAnalysisData = null;


document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("session-dropdown-button");
  const options = document.getElementById("session-dropdown-options");
  const label = document.getElementById("session-dropdown-label");
  const input = document.getElementById("new-session-input");
  const hiddenInput = document.getElementById("session_id");
  const trackSelect = document.getElementById("track-select"); // Add this to update tracks

  async function populateSessionDropdown() {
    const res = await fetch("/sessions");
    const sessions = await res.json();

    options.innerHTML = "";

    // ✅ First: New Session
    const createNew = document.createElement("li");
    createNew.textContent = "New Session";
    createNew.className =
      "dropdown-option px-4 py-2 cursor-pointer hover:bg-purple-500/10 transition text-purple-300";
    createNew.addEventListener("click", () => {
      label.textContent = "New Session";
      hiddenInput.value = "";
      input.classList.remove("hidden");
      options.classList.add("hidden");
      // Clear track dropdown when new session selected
      if (trackSelect) {
        trackSelect.innerHTML = '<option value="">Choose Track</option>';
      }
    });
    options.appendChild(createNew);

    // ✅ Then: Existing sessions
    sessions.forEach((session) => {
      const li = document.createElement("li");
      li.className =
        "dropdown-option px-4 py-2 cursor-pointer hover:bg-white/10 transition";
      li.textContent = session.session_name;
      li.addEventListener("click", async () => {
        label.textContent = session.session_name;
        hiddenInput.value = session.id;
        input.classList.add("hidden");
        options.classList.add("hidden");

        // NEW: Load tracks for this session and update track dropdown
        if (trackSelect) {
          try {
            await loadSessionTracks(session.id);
          } catch (err) {
            console.error("Failed to load tracks for session:", err);
            // Optionally show user feedback
          }
        }
      });
      options.appendChild(li);
    });
  }

  // 🧠 Populate list on load
  populateSessionDropdown();

  // 🎯 Toggle dropdown on click
  button.addEventListener("click", (e) => {
    e.stopPropagation();
    options.classList.toggle("hidden");
  });

  // 🚫 Close if clicked outside
  document.addEventListener("click", (e) => {
    if (!options.contains(e.target) && !button.contains(e.target)) {
      options.classList.add("hidden");
    }
  });
});


// ==========================================================
// 🔸 Dropdown Logic for Track Type Selector
// ==========================================================
document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("type-button");
  const options = document.getElementById("type-options");
  const hiddenInput = document.getElementById("type-input");
  const selectedText = document.getElementById("type-selected");

  // Toggle dropdown visibility on button click
  button.addEventListener("click", () => {
    options.classList.toggle("hidden");
  });

  // Handle option selection
  document.querySelectorAll("#type-options li").forEach((item) => {
    item.addEventListener("click", () => {
      const value = item.getAttribute("data-value");
      const label = item.textContent;

      selectedText.textContent = label;
      hiddenInput.value = value;
      options.classList.add("hidden");
      button.classList.add("selected-field");
    });
  });

  // Hide dropdown when clicking outside
  document.addEventListener("click", (e) => {
    if (!button.contains(e.target) && !options.contains(e.target)) {
      options.classList.add("hidden");
    }
  });
});

// ==========================================================
// 🔸 Dropdown Logic for Genre + Subgenre Selector
// ==========================================================
document.addEventListener("DOMContentLoaded", () => {
  const subgenres = {
    electronic: ["Techno", "House", "Drum and Bass", "Dubstep", "Trance", "Psytrance", "Electro", "Ambient", "Synthwave", "IDM"],
    pop: ["Electropop", "Dance Pop", "Indie Pop", "Synthpop", "Teen Pop", "Pop Rock", "K-Pop", "J-Pop", "Art Pop", "Power Pop"],
    rock: ["Classic Rock", "Alternative Rock", "Hard Rock", "Indie Rock", "Progressive Rock", "Psychedelic Rock", "Garage Rock", "Blues Rock", "Punk Rock", "Grunge"],
    hiphop: ["Trap", "Boom Bap", "Gangsta Rap", "Lo-fi Hip Hop", "Crunk", "Cloud Rap", "East Coast", "West Coast", "Drill", "Mumble Rap"],
    indie: ["Indie Rock", "Indie Pop", "Indie Folk", "Indietronica", "Lo-fi Indie", "Dream Pop", "Shoegaze", "Chamber Pop", "Baroque Pop"],
    punk: ["Hardcore Punk", "Post-Punk", "Pop Punk", "Garage Punk", "Oi!", "Skate Punk", "Anarcho-Punk", "Crust Punk", "Street Punk", "Queercore"],
    metal: ["Heavy Metal", "Death Metal", "Black Metal", "Thrash Metal", "Doom Metal", "Power Metal", "Symphonic Metal", "Progressive Metal", "Metalcore", "Nu Metal"],
    jazz: ["Smooth Jazz", "Bebop", "Cool Jazz", "Swing", "Fusion", "Free Jazz", "Latin Jazz", "Gypsy Jazz", "Modal Jazz", "Vocal Jazz"],
    raggae: ["Roots Reggae", "Dancehall", "Dub", "Rocksteady", "Lovers Rock", "Reggaeton", "Ragga", "Ska", "Conscious Reggae", "Digital Reggae"],
    funk: ["P-Funk", "Funk Rock", "Electro Funk", "Jazz Funk", "Go-Go", "Boogie", "Disco Funk", "Psychedelic Funk", "Afro Funk", "Neo-Funk"],
    rnb: ["Contemporary R&B", "Neo Soul", "Funk R&B", "Hip Hop Soul", "Quiet Storm", "Alternative R&B", "Classic Soul", "Trap Soul", "New Jack Swing", "Urban R&B"],
    soul: ["Northern Soul", "Southern Soul", "Neo Soul", "Blue-Eyed Soul", "Motown", "Gospel Soul", "Psychedelic Soul", "Funk Soul", "Contemporary Soul", "Deep Soul"],
    country: ["Classic Country", "Outlaw Country", "Bluegrass", "Country Pop", "Alt-Country", "Country Rock", "Americana", "Honky Tonk", "Contemporary Country", "Western Swing"],
    folk: ["Indie Folk", "Folk Rock", "Traditional Folk", "Americana", "Celtic Folk", "Contemporary Folk", "Acoustic Folk", "Folk Pop", "Neo-Folk", "Country Folk"],
    classic: ["Baroque", "Romantic", "Modern Classical", "Contemporary Classical", "Opera", "Chamber Music", "Minimalism", "Orchestral", "Symphonic", "Choral"]
  };

  const genreOptionsList = document.getElementById("genre-options");
  const genreInput = document.getElementById("genre-input");
  const genreSelected = document.getElementById("genre-selected");

  const subgenreWrapper = document.getElementById("subgenre-wrapper");
  const subgenreButton = document.getElementById("subgenre-button");
  const subgenreOptions = document.getElementById("subgenre-options");
  const subgenreInput = document.getElementById("subgenre-input");
  const subgenreSelected = document.getElementById("subgenre-selected");
  const customSubgenreInput = document.getElementById("custom-subgenre-input");

  // Populate genre list
  Object.keys(subgenres).forEach(genre => {
    const li = document.createElement("li");
    li.setAttribute("data-value", genre);
    li.className = "dropdown-option px-4 py-2 cursor-pointer transition";
    li.textContent = genre.charAt(0).toUpperCase() + genre.slice(1);
    genreOptionsList.appendChild(li);
  });

  document.getElementById("genre-button").addEventListener("click", () => {
    genreOptionsList.classList.toggle("hidden");
  });

  genreOptionsList.addEventListener("click", (e) => {
    if (e.target.tagName === "LI") {
      const genreKey = e.target.getAttribute("data-value");
      const genreLabel = e.target.textContent;

      genreSelected.textContent = genreLabel;
      genreInput.value = genreKey;
      genreOptionsList.classList.add("hidden");

      // Show subgenre options
      subgenreOptions.innerHTML = "";

      // Add "Enter Subgenre" first
      const enterSubgenre = document.createElement("li");
      enterSubgenre.textContent = "Enter Subgenre";
      enterSubgenre.className = "dropdown-option px-4 py-2 cursor-pointer hover:bg-purple-500/10 transition text-purple-300";
      enterSubgenre.addEventListener("click", () => {
        subgenreSelected.textContent = "Custom Subgenre";
        subgenreInput.value = "";
        subgenreOptions.classList.add("hidden");
        customSubgenreInput.classList.remove("hidden");
      });
      subgenreOptions.appendChild(enterSubgenre);

      subgenres[genreKey].forEach(sub => {
        const li = document.createElement("li");
        li.className = "dropdown-option px-4 py-2 cursor-pointer transition";
        li.textContent = sub;
        li.setAttribute("data-value", sub.toLowerCase());
        li.addEventListener("click", () => {
          subgenreSelected.textContent = sub;
          subgenreInput.value = sub.toLowerCase();
          subgenreOptions.classList.add("hidden");
          subgenreButton.classList.add("selected-field");
          customSubgenreInput.classList.add("hidden");
        });
        subgenreOptions.appendChild(li);
      });

      subgenreSelected.textContent = "Select Subgenre";
      subgenreInput.value = "";
      customSubgenreInput.classList.add("hidden");
    }
  });

  subgenreButton.addEventListener("click", () => {
    subgenreOptions.classList.toggle("hidden");
  });

  document.addEventListener("click", (e) => {
    if (!document.getElementById("genre-button").contains(e.target) && !genreOptionsList.contains(e.target)) {
      genreOptionsList.classList.add("hidden");
    }
    if (!subgenreButton.contains(e.target) && !subgenreOptions.contains(e.target)) {
      subgenreOptions.classList.add("hidden");
    }
  });
});



// ==========================================================
// 🔸 Dropdown Logic for Feedback Profile Selector
// ==========================================================
document.addEventListener("DOMContentLoaded", () => {
  const profileButton = document.getElementById("profile-button");
  const profileOptions = document.getElementById("profile-options");
  const profileInput = document.getElementById("profile-input");
  const profileSelected = document.getElementById("profile-selected");

  // Toggle dropdown visibility on button click
  profileButton.addEventListener("click", () => {
    profileOptions.classList.toggle("hidden");
  });

  // Handle option selection
  document.querySelectorAll("#profile-options li").forEach((item) => {
    item.addEventListener("click", () => {
      const value = item.getAttribute("data-value");
      const label = item.textContent;

      profileSelected.textContent = label;
      profileInput.value = value;
      profileOptions.classList.add("hidden");
      profileButton.classList.add("selected-field");
    });
  });

  // Hide dropdown when clicking outside
  document.addEventListener("click", (e) => {
    if (!profileButton.contains(e.target) && !profileOptions.contains(e.target)) {
      profileOptions.classList.add("hidden");
    }
  });
});

// ==========================================================
// 📥 File Input Handling + Placeholder Logic
// ==========================================================
document.addEventListener("DOMContentLoaded", () => {
  // Original track input and filename span
  const fileInput = document.getElementById("file-upload");
  const fileNameSpan = document.getElementById("file-name");

  if (fileInput && fileNameSpan) {
    fileInput.addEventListener("change", () => {
      if (fileInput.files.length > 0) {
        fileNameSpan.textContent = fileInput.files[0].name;
        fileNameSpan.style.color = "#2196f3";  // blue tone for original track
      } else {
        fileNameSpan.textContent = "Click to upload your track";
        fileNameSpan.style.color = ""; // reset color to default
      }
    });
  }

  // Reference track input and filename span
  const refFileInput = document.getElementById("ref-file-upload");
  const refFileNameSpan = document.getElementById("ref-file-name");

  if (refFileInput && refFileNameSpan) {
    refFileInput.addEventListener("change", () => {
      if (refFileInput.files.length > 0) {
        refFileNameSpan.textContent = refFileInput.files[0].name;
        refFileNameSpan.style.color = "#8b5cf6";  // violet tone for reference track (Tailwind purple-600)
      } else {
        refFileNameSpan.textContent = "Choose Reference Track";
        refFileNameSpan.style.color = ""; // reset color to default
      }
    });
  }

  const input = document.getElementById("track_name");
  const fakePlaceholder = document.getElementById("track-fake-placeholder");

  if (input && fakePlaceholder) {
    function toggleFakePlaceholder() {
      fakePlaceholder.style.display = input.value.trim() === "" ? "flex" : "none";
    }

    input.addEventListener("input", toggleFakePlaceholder);
    input.addEventListener("focus", toggleFakePlaceholder);
    input.addEventListener("blur", toggleFakePlaceholder);

    toggleFakePlaceholder();
  }
});

// ==========================================================
// 🔸 File Upload Filename Preview
// ==========================================================
document.addEventListener("DOMContentLoaded", () => {
  const fileInput = document.getElementById("file-upload");
  const fileNameSpan = document.getElementById("file-name");

  if (fileInput && fileNameSpan) {
    fileInput.addEventListener("change", () => {
      fileNameSpan.textContent = fileInput.files.length > 0
        ? fileInput.files[0].name
        : "Click to upload your track";
    });
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const refFileInput = document.getElementById("ref-file-upload");
  const refFileNameSpan = document.getElementById("ref-file-name");

  if (refFileInput && refFileNameSpan) {
    refFileInput.addEventListener("change", () => {
      refFileNameSpan.textContent = refFileInput.files.length > 0
        ? refFileInput.files[0].name
        : "Choose Reference Track";
    });
  }
});
// ==========================================================
// 🔁 Helper: Load Session Tracks After Upload
// ==========================================================
async function loadSessionTracks(sessionId) {
  try {
    const response = await fetch(`/sessions/${sessionId}/tracks`);
    if (!response.ok) throw new Error("Failed to fetch tracks");

    const tracks = await response.json();
    const latestTrack = tracks[0]; // 🔄 assumes latest uploaded is first

    // Update dropdown if present
    const trackSelect = document.getElementById("track-select");
    if (trackSelect) {
      trackSelect.innerHTML = '<option value="">Choose Track</option>';
      tracks.forEach(track => {
        const opt = document.createElement("option");
        opt.value = track.id;
        opt.textContent = track.track_name || "Untitled Track";
        trackSelect.appendChild(opt);
      });
      trackSelect.value = latestTrack?.id || "";
    }

    return tracks;
  } catch (err) {
    console.error("❌ Error loading session tracks:", err);
    return [];
  }
}


// ==========================================================
// 🔁 Helper: Hide old Elements after Analyze
// ==========================================================


function showSummarizeButton() {
  const summarizeBtn = document.getElementById("manualSummarizeBtn");
  if (summarizeBtn) {
    summarizeBtn.style.display = "inline-block";
  }
}

function hideSummarizeButton() {
  const summarizeBtn = document.getElementById("manualSummarizeBtn");
  if (summarizeBtn) {
    summarizeBtn.style.display = "none";
  }
}


function clearQuickFollowupButtons() {
  const container = document.getElementById("quick-followup");
  if (!container) return;
  container.innerHTML = "";       // komplett leeren
  container.classList.add("hidden");  // ausblenden (optional)
}

function resetExportButton() {
  const exportBtn = document.getElementById("exportFeedbackBtn");
  if (exportBtn) {
    exportBtn.disabled = false;                            // Button aktivieren
    exportBtn.textContent = "Export Feedback & Presets";  // Button-Text zurücksetzen
    // exportBtn.style.display = "inline-block";           // Falls nötig: Sichtbar machen
    // exportBtn.dataset.listenerAdded = "";               // Nur zurücksetzen, wenn du Listener neu hinzufügen willst
  }
}

function resetRMSDisplay() {
  const rmsDisplay = document.getElementById("rms-display");
  if (rmsDisplay) {
    rmsDisplay.innerText = "Current RMS: --";  // Oder leer setzen: ""
  }
}
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

  const feedbackBox = document.getElementById("gptResponse");
  if (feedbackBox) feedbackBox.innerHTML = "";

  const followupResponseBox = document.getElementById("aiFollowupResponse");
  if (followupResponseBox) followupResponseBox.innerHTML = "";

  const waveformDiv = document.getElementById("waveform");
  if (waveformDiv) {
    waveformDiv.innerHTML = "";
    waveformDiv.classList.remove("waveform-playing");
  }

  if (window.wavesurfer) {
    window.wavesurfer.destroy();
    window.wavesurfer = null;
  }

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

      const sessionIdInput = document.getElementById("session_id");
      if (sessionIdInput) {
        sessionIdInput.value = sessionId;
      }

      followupThread = [];
      followupGroupIndex = 0;
      lastManualSummaryGroup = -1;

      const resultsEl = document.getElementById("results");
      const feedbackEl = document.getElementById("feedback");
      const feedbackBox = document.getElementById("gptResponse");

      resultsEl.classList.remove("hidden");
      feedbackEl.classList.remove("hidden");

      feedbackEl.classList.remove("fade-in-up");
      void feedbackEl.offsetWidth;
      feedbackEl.classList.add("fade-in-up");

      const output = document.getElementById("analysisOutput");
      const a = result.analysis;

      function r(v) {
        return Number(v).toFixed(2);
      }

      output.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2 text-sm">
          <p><strong>Tempo:</strong> ${a.tempo} BPM</p>
          <p><strong>Key:</strong> ${a.key}</p>
          <p><strong>Peak Level:</strong> ${r(a.peak_db)} dB</p>
          <p><strong>Peak Issue:</strong> ${a.peak_issue}</p>
          <p><strong>RMS Peak:</strong> ${r(a.rms_db_peak)} dB</p>
          <p><strong>LUFS:</strong> ${r(a.lufs)} LUFS</p>
          <p><strong>Dynamic Range:</strong> ${r(a.dynamic_range)} dB</p>
          <p><strong>Stereo Width:</strong> ${a.stereo_width}</p>
          <p class="md:col-span-2"><strong>Low-End:</strong> ${a.low_end_description}</p>
          <p class="md:col-span-2"><strong>Spectral Balance:</strong> ${a.spectral_balance_description}</p>
          <div class="md:col-span-2">
            <strong>Band Energies:</strong>
            <pre class="whitespace-pre-wrap">${JSON.stringify(a.band_energies, null, 2)}</pre>
          </div>
        </div>
      `;

      if (refTrackAnalysisData) {
        const refContainer = document.createElement("div");
        refContainer.className = "mt-8 space-y-2 text-sm border-t border-white/10 pt-4";

        const ra = refTrackAnalysisData;

        refContainer.innerHTML = `
          <h2 class="text-lg font-semibold text-white mt-8 mb-4">Reference Track Analysis</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <p><strong>Tempo:</strong> ${ra.tempo} BPM</p>
            <p><strong>Key:</strong> ${ra.key}</p>
            <p><strong>Peak Level:</strong> ${r(ra.peak_db)} dB</p>
            <p><strong>Peak Issue:</strong> ${ra.peak_issue}</p>
            <p><strong>RMS Peak:</strong> ${r(ra.rms_db_peak)} dB</p>
            <p><strong>LUFS:</strong> ${r(ra.lufs)} LUFS</p>
            <p><strong>Dynamic Range:</strong> ${r(ra.dynamic_range)} dB</p>
            <p><strong>Stereo Width:</strong> ${ra.stereo_width}</p>
            <p class="md:col-span-2"><strong>Low-End:</strong> ${ra.low_end_description}</p>
            <p class="md:col-span-2"><strong>Spectral Balance:</strong> ${ra.spectral_balance_description}</p>
            <div class="md:col-span-2">
              <strong>Band Energies:</strong>
              <pre class="whitespace-pre-wrap">${JSON.stringify(ra.band_energies, null, 2)}</pre>
            </div>
          </div>
        `;
        output.appendChild(refContainer);
      }

      feedbackBox.innerHTML = "";
      feedbackBox.classList.add("pulsing-feedback");

      const trackType = result.type?.toLowerCase();
      const subheading = document.createElement("p");
      subheading.className = "text-lg font-semibold";

      if (trackType === "mixdown") {
        subheading.classList.add("text-pink-400");
        subheading.textContent = "Mixdown Suggestions:";
      } else if (trackType === "mastering") {
        subheading.classList.add("text-blue-400");
        subheading.textContent = "Mastering Suggestions:";
      } else if (trackType === "master") {
        subheading.classList.add("text-blue-400");
        subheading.textContent = "Master Review:";
      } else {
        subheading.classList.add("text-white/70");
        subheading.textContent = "AI Feedback:";
      }
      feedbackBox.appendChild(subheading);

      const ul = document.createElement("ul");
      ul.className = "list-disc list-inside mt-2 text-white/90 space-y-1";
      feedbackBox.appendChild(ul);

      const lines = result.feedback
        .split("\n")
        .map(line => line.replace(/^[-•\s]+/, "").trim())
        .filter(Boolean);

      for (const [index, line] of lines.entries()) {
        const li = document.createElement("li");
        li.style.display = "list-item";
        if (index > 0) li.style.marginTop = "0.75rem";

        const issueMatch = line.match(/ISSUE:\s*([\s\S]*?)(?:IMPROVEMENT:\s*([\s\S]*))?$/i);
        if (issueMatch) {
          const issueText = issueMatch[1].trim();
          const improvementText = issueMatch[2] ? issueMatch[2].replace(/^IMPROVEMENT:\s*/i, '').trim() : "";
          li.innerHTML = `
            <strong class="issue-label">ISSUE:</strong>
            <span class="issue-text">${issueText}</span>
            ${improvementText ? `<br><strong class="improvement-label">IMPROVEMENT:</strong> <span class="improvement-text">${improvementText}</span>` : ''}
          `;
        } else {
          li.textContent = line;
        }
        ul.appendChild(li);
      }

      // ✅ Waveform logic moved to external file
      initMainWaveform(result);
      loadReferenceWaveform();

      document.getElementById("custom-ai-section")?.classList.remove("hidden");

      const exportBtn = document.getElementById("exportFeedbackBtn");
      if (exportBtn && !exportBtn.dataset.listenerAdded) {
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

            if (!response.ok) {
              const errorText = await response.text();
              throw new Error(errorText || "Failed to export feedback and presets.");
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
        exportBtn.dataset.listenerAdded = "true";
      }

      const genre = document.getElementById("genre-input")?.value;
      const profile = document.getElementById("profile-input")?.value?.toLowerCase();
      loadQuickFollowupButtons(type, genre, profile);

      feedbackBox.classList.remove("pulsing-feedback");

      localStorage.setItem("zoundzcope_last_analysis", output.innerHTML);
      localStorage.setItem("zoundzcope_last_feedback", ul.outerHTML);
      localStorage.setItem("zoundzcope_last_subheading", subheading?.outerHTML || "");
      localStorage.setItem("zoundzcope_last_followup", "");

      try {
        const current = {
          analysis: output.innerHTML,
          feedback: feedbackBox.innerHTML,
          subheading: subheading?.outerHTML || "",
          followup: "",
          track_name: finalTrackName,
          timestamp: Date.now()
        };

        const rawHistory = localStorage.getItem("zoundzcope_history") || "[]";
        const history = JSON.parse(rawHistory);

        const duplicate = history.find(h => JSON.stringify(h) === JSON.stringify(current));
        if (!duplicate) {
          history.unshift(current);
          if (history.length > 3) history.length = 3;
          localStorage.setItem("zoundzcope_history", JSON.stringify(history));
        }
      } catch (err) {
        console.error("❌ Failed to store history:", err);
      }

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
// 🔸 Session Creation via Backend
// ==========================================================
async function createSessionInBackend(sessionName) {
  const userId = 1;
  try {
    const response = await fetch("/sessions/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_name: sessionName, user_id: userId }),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error("Session creation failed with:", error);
      return null;
    }

    const result = await response.json();
    console.log("✅ Created session:", result);
    return result;

  } catch (err) {
    console.error("❌ Session creation fetch failed", err);
    return null;
  }
}

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








