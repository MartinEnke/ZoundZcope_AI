// ✅ Cleaned version of your app.js with separate flat DOMContentLoaded blocks

console.log("✅ app.js loaded");

// ==========================================================
// 🔠 Text Animation: Type letter-by-letter
// ==========================================================
function typeText(targetElement, text, speed = 10) {
  return new Promise((resolve) => {
    let i = 0;
    function typeChar() {
      if (i < text.length) {
        const span = document.createElement("span");
        span.textContent = text.charAt(i);
        span.classList.add("sparkle-letter");
        targetElement.appendChild(span);
        i++;
        setTimeout(typeChar, speed);
      } else {
        resolve();
      }
    }
    typeChar();
  });
}



// ==========================================================
// 🔁 Ask AI Follow-Up Logic
// ==========================================================
document.getElementById("askAIButton").addEventListener("click", async () => {
  const question = document.getElementById("customQuestion").value.trim();
  const outputBox = document.getElementById("aiFollowupResponse");

  if (!question) {
    alert("Please enter a question.");
    return;
  }

  // Prepare prompt with existing feedback + question
  const feedback = document.getElementById("gptResponse")?.innerText || "";
  const metrics = document.getElementById("analysisOutput")?.innerText || "";

  // UI loading state
  outputBox.classList.remove("hidden");
  outputBox.innerHTML = "<p class='text-white/60 italic'>Thinking...</p>";

  try {
    const res = await fetch("/chat/ask-followup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        analysis_text: metrics,
        feedback_text: feedback,
        user_question: question,
        session_id: document.getElementById("session_id").value,
        track_id: document.getElementById("track-select")?.value || "",
        feedback_profile: document.getElementById("profile-input")?.value || "",
      }),
    });

    const data = await res.json();
    outputBox.innerHTML = `<p>${data.answer}</p>`;

    // ✅ Save follow-up to localStorage
    localStorage.setItem("zoundzcope_last_followup", outputBox.innerHTML);

    try {
  const raw = localStorage.getItem("zoundzcope_history") || "[]";
  const history = JSON.parse(raw);

  if (history.length > 0) {
    // Ensure followup is an array
    if (!Array.isArray(history[0].followup)) {
      history[0].followup = history[0].followup
        ? [history[0].followup]
        : [];
    }

    // Add the new follow-up if it's not already in
    if (!history[0].followup.includes(outputBox.innerHTML)) {
      history[0].followup.push(outputBox.innerHTML);
    }

    localStorage.setItem("zoundzcope_history", JSON.stringify(history));
  }
} catch (err) {
  console.error("❌ Failed to store follow-up in history:", err);
}


    // ✅ Save follow-up to localStorage
    localStorage.setItem("zoundzcope_last_followup", outputBox.innerHTML);

  } catch (err) {
    console.error("Follow-up failed:", err);
    outputBox.innerHTML = "<p class='text-red-400'>Something went wrong. Try again.</p>";
  }
});

// ==========================================================
// 💡 Smart Predefined Follow-Up Buttons (Based on Context)
// ==========================================================
const predefinedFollowupQuestions = {
  mixdown: [
    "Which element is clashing most in this mix?",
    "Which plugin could improve transient clarity on the snare?",
    "How can I better use stereo panning to separate instruments?",
    "Should I apply multiband compression on the drum bus?"
  ],
  master: [
    "Would this track match the loudness of Daft Punk's 'Random Access Memories'?",
    "Which limiter plugin gives transparent results for this style?",
    "Is a dynamic EQ needed to tame harshness here?",
    "Could widening the stereo field improve spatial depth?",
    "Does this master need a low-shelf boost below 80Hz?"
  ],
  electronic: [
    "Does this mix have the punch of Flume’s productions?",
    "How can I make the drop hit harder?",
    "Which synth plugin would enhance the lead’s texture?",
    "Should I automate filter cutoff for more movement?",
    "How can I tighten the sidechain compression?"
  ],
  hiphop: [
    "Are the vocals sitting right like in Kendrick Lamar’s mixes?",
    "What plugin is best to glue the drums?",
    "Should I try parallel compression on the rap vocal?",
    "How do I add analog warmth to the beat?",
    "Would a CLA plugin chain help here?"
  ],
  rock: [
    "How does the guitar layer compare to Foo Fighters’ mixes?",
    "Should I try an API-style EQ on the drums?",
    "How can I make the bass more audible without clashing with the kick?",
    "Does this need tape saturation on the mix bus?",
    "Is the vocal presence comparable to Green Day’s tracks?"
  ],
  ambient: [
    "How can I widen the stereo field without blurring elements?",
    "Should I use Valhalla or Eventide reverb for this?",
    "Does this track have the subtle dynamics of Brian Eno’s work?",
    "Is the low-end too heavy for ambient?",
    "Which plugin would help create deeper textures?"
  ],
  classic: [
    "Would referencing a Deutsche Grammophon master help dynamics?",
    "How do I preserve orchestral space while enhancing clarity?",
    "Is this reverb tail appropriate for the room size?",
    "Should I avoid compression on classical recordings?",
    "Would linear-phase EQ benefit this arrangement?"
  ],
  punk: [
    "Does the energy match early Ramones or Sex Pistols?",
    "Is the guitar tone too clean for this style?",
    "Would a Neve-style preamp plugin improve grit?",
    "Should I push the vocal compression harder?",
    "Is the rawness authentic or too harsh?"
  ],
  simple: [
    "What is the first thing I should fix?",
    "Which plugin would improve the sound quickly?",
    "Is this mix good enough to upload?",
    "Should I turn anything down?",
    "How do I fix muddy sound easily?"
  ],
  detailed: [
    "Is the spectral balance consistent across the frequency range?",
    "Which plugin chain would optimize glue on the master bus?",
    "How would you approach surgical EQ here?",
    "Are the transients crisp enough on the snare?"
  ],
  pro: [
    "Which plugin chain gives best results for mastering this genre?",
    "Should I use MS processing on the midrange?",
    "Would a clipper enhance perceived loudness before the limiter?",
    "Is the multiband compression transparent enough?",
    "Which frequency range could benefit from harmonic saturation?"
  ]
};


function loadQuickFollowupButtons(type, genre, profile) {
  const container = document.getElementById("quick-followup");
  if (!container) return;

  container.innerHTML = `
    <p class="text-white/70 text-sm mb-1">Quick Follow-Up Questions:</p>
    <div class="flex flex-wrap gap-2"></div>
  `;

  const btnWrapper = container.querySelector("div");
  const uniqueQuestions = new Set([
    ...(predefinedFollowupQuestions[type] || []),
    ...(predefinedFollowupQuestions[genre] || []),
    ...(predefinedFollowupQuestions[profile] || [])
  ]);

  Array.from(uniqueQuestions).slice(0, 15).forEach((q) => {
    const btn = document.createElement("button");
    btn.textContent = q;
    btn.className = `
  px-4 py-1 rounded-full
  bg-white/5 hover:bg-white/10
  text-white text-[0.75rem]
  shadow-sm hover:shadow-md
  border border-white/10 hover:border-white/20
  backdrop-blur-sm transition-all duration-150
`;
btn.style.fontSize = "0.78rem";

btn.style.fontSize = "0.825rem";
    btn.addEventListener("click", () => {
      document.getElementById("customQuestion").value = q;
      document.getElementById("askAIButton").click();
    });
    btnWrapper.appendChild(btn);
  });
    // ✅ Show it now
  container.classList.remove("hidden");
}


// ==========================================================
// 🔁 Session Dropdown Logic (Populate + Toggle New Input)
// ==========================================================
document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("session-dropdown-button");
  const options = document.getElementById("session-dropdown-options");
  const label = document.getElementById("session-dropdown-label");
  const input = document.getElementById("new-session-input");
  const hiddenInput = document.getElementById("session_id");

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
    });
    options.appendChild(createNew);

    // ✅ Then: Existing sessions
    sessions.forEach((session) => {
      const li = document.createElement("li");
      li.className =
        "dropdown-option px-4 py-2 cursor-pointer hover:bg-white/10 transition";
      li.textContent = session.session_name;
      li.addEventListener("click", () => {
        label.textContent = session.session_name;
        hiddenInput.value = session.id;
        input.classList.add("hidden");
        options.classList.add("hidden");
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
// 🔸 Dropdown Logic for Genre Selector
// ==========================================================
document.addEventListener("DOMContentLoaded", () => {
  const genreButton = document.getElementById("genre-button");
  const genreOptions = document.getElementById("genre-options");
  const genreInput = document.getElementById("genre-input");
  const genreSelected = document.getElementById("genre-selected");

  // Toggle dropdown visibility on button click
  genreButton.addEventListener("click", () => {
    genreOptions.classList.toggle("hidden");
  });

  // Handle option selection
  document.querySelectorAll("#genre-options li").forEach((item) => {
    item.addEventListener("click", () => {
      const value = item.getAttribute("data-value");
      const label = item.textContent;

      genreSelected.textContent = label;
      genreInput.value = value;
      genreOptions.classList.add("hidden");
      genreButton.classList.add("selected-field");
    });
  });

  // Hide dropdown when clicking outside
  document.addEventListener("click", (e) => {
    if (!genreButton.contains(e.target) && !genreOptions.contains(e.target)) {
      genreOptions.classList.add("hidden");
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
  const fileInput = document.getElementById("file-upload");
  const fileNameSpan = document.getElementById("file-name");

  if (fileInput && fileNameSpan) {
    fileInput.addEventListener("change", () => {
      fileNameSpan.textContent = fileInput.files.length > 0
        ? fileInput.files[0].name
        : "Click to upload your track";
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
const fileInput = document.getElementById('file-upload');
const fileNameSpan = document.getElementById('file-name');
fileInput.addEventListener('change', () => {
  fileNameSpan.textContent = fileInput.files.length > 0
    ? fileInput.files[0].name
    : 'Click to upload your track';
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
  } catch (err) {
    console.error("❌ Error loading session tracks:", err);
  }
}
console.log("loadSessionTracks is", loadSessionTracks);
// ==========================================================
// 🔸 Upload Form Submission Logic
// ==========================================================
const form = document.getElementById("uploadForm");
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  localStorage.removeItem("zoundzcope_last_analysis");
  localStorage.removeItem("zoundzcope_last_feedback");
  localStorage.removeItem("zoundzcope_last_followup");
  localStorage.removeItem("zoundzcope_last_subheading");

  const analyzeButton = form.querySelector('button[type="submit"]');
  const formData = new FormData(form);

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
const customTrackName = document.getElementById("track_name").value.trim();
const fileInput = document.getElementById("file-upload");

let finalTrackName = customTrackName;

if (!finalTrackName && fileInput && fileInput.files.length > 0) {
  const fullName = fileInput.files[0].name;
  finalTrackName = fullName.replace(/\.[^/.]+$/, "");  // ✅ strip extension
}

formData.set("feedback_profile", feedbackProfile);
formData.set("track_name", finalTrackName || "Untitled Track");


  try {
    const response = await fetch("/upload/", {
      method: "POST",
      body: formData,
    });

    const raw = await response.text();
    const result = JSON.parse(raw);

    if (response.ok) {
      await loadSessionTracks(sessionId);

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
          <p><strong>Peak db:</strong> ${r(a.peak_db)}</p>
          <p><strong>RMS db:</strong> ${r(a.rms_db)}</p>
          <p><strong>LUFS:</strong> ${r(a.lufs)}</p>
          <p><strong>Dynamic Range:</strong> ${r(a.dynamic_range)}</p>
          <p><strong>Stereo Width Ratio:</strong> ${r(a.stereo_width_ratio)}</p>
          <p><strong>Stereo Width:</strong> ${a.stereo_width}</p>
          <p><strong>Low End Energy Ratio:</strong> ${r(a.low_end_energy_ratio)}</p>
          <p><strong>Bass Profile:</strong> ${a.bass_profile}</p>
          <div class="md:col-span-2">
            <strong>Band Energies:</strong>
            <pre class="whitespace-pre-wrap">${JSON.stringify(a.band_energies, null, 2)}</pre>
          </div>
        </div>
      `;

      feedbackBox.innerHTML = "";
      feedbackBox.classList.add("pulsing-feedback");

      const trackType = result.type?.toLowerCase();
      const subheading = document.createElement("p");
      subheading.className = trackType === "mixdown"
        ? "text-pink-400 text-lg font-semibold"
        : "text-blue-400 text-lg font-semibold";
      subheading.textContent = trackType === "mixdown"
        ? "Mixdown Suggestions:"
        : "Mastering Advice:";
      feedbackBox.appendChild(subheading);

      const ul = document.createElement("ul");
      ul.className = "list-disc list-inside mt-2 text-white/90 space-y-1";
      feedbackBox.appendChild(ul);

      analyzeButton.classList.remove("analyze-loading");
      analyzeButton.disabled = false;

      const lines = result.feedback
        .split("\n")
        .map(line => line.replace(/^[-•\s]+/, "").trim())
        .filter(Boolean);

      for (const [index, line] of lines.entries()) {
  const li = document.createElement("li");
  li.style.display = "list-item";
  if (index > 0) li.style.marginTop = "0.75rem";
  ul.appendChild(li);
  await typeText(li, line, 5);  // 🧠 This types each line slowly
}

// 🔥 Unhide follow-up input after typing is complete
document.getElementById("custom-ai-section")?.classList.remove("hidden");

// 👇 Add after typing out AI feedback (after showing the follow-up section)
const type = document.getElementById("type-input")?.value;
const genre = document.getElementById("genre-input")?.value;
const profile = document.getElementById("profile-input")?.value?.toLowerCase();

loadQuickFollowupButtons(type, genre, profile);



feedbackBox.classList.remove("pulsing-feedback");

// ✅ Now save everything after feedback is typed out
localStorage.setItem("zoundzcope_last_analysis", output.innerHTML);
localStorage.setItem("zoundzcope_last_feedback", ul.outerHTML); // only list
localStorage.setItem("zoundzcope_last_subheading", subheading?.outerHTML || "");
localStorage.setItem("zoundzcope_last_followup", ""); // default for fresh entry


      // 🔁 Save to zoundzcope_history (max 3)
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
function renderRecentFeedbackPanel() {
  console.log("✅ renderRecentFeedbackPanel() called");

  const container = document.getElementById("recent-feedback-container");
  const panel = document.getElementById("recentFeedbackPanel");

  if (!container || !panel) return;

  let history = [];
  try {
    history = JSON.parse(localStorage.getItem("zoundzcope_history")) || [];
    console.log("🧠 Loaded history:", history);
  } catch (err) {
    console.error("🧠 Failed to parse feedback history:", err);
  }

  container.innerHTML = "";

  if (!history || history.length === 0) {
    console.warn("⚠️ No feedback history found.");
    panel.classList.add("hidden");
    return;
  }

  const recent = history.slice(0, 5);
  recent.forEach((entry, i) => {
    const box = document.createElement("div");
    box.className = "bg-white/5 p-4 rounded-lg shadow-md space-y-2 border border-white/10";

    const subheadingText = entry.subheading?.replace(/<[^>]+>/g, "").trim() || "Previous Feedback";
    const trackName = entry.track_name || "Untitled Track";
    const dateStr = entry.timestamp ? new Date(entry.timestamp).toLocaleDateString() : "";

    // Remove subheading from feedback if duplicated
    let feedbackHTML = entry.feedback || "<div class='text-white/60'>No feedback content.</div>";
    const headingRegex = new RegExp(`<p[^>]*>${subheadingText}</p>`, "i");
    feedbackHTML = feedbackHTML.replace(headingRegex, "").trim();

    const followupId = `followup-${i}`;
    const hasFollowup = entry.followup && Array.isArray(entry.followup) && entry.followup.length > 0;

    const followupToggleHTML = hasFollowup
      ? `<button class="text-xs text-purple-300 underline" onclick="toggleFollowup('${followupId}')">Show Follow-up</button>`
      : "";

    const followupHTML = hasFollowup
      ? `<div id="${followupId}" class="mt-2 text-sm text-white/70 border-t border-white/10 pt-2 hidden">
          ${entry.followup.map(f => `<p>${f}</p>`).join("")}
        </div>`
      : "";

    const headingHTML = `
      <div class="flex justify-between items-center mb-1">
        <div class="flex items-baseline gap-2">
          <p class="text-pink-400 text-lg font-bold">${subheadingText}</p>
          <span class="text-white font-semibold text-sm">${trackName}</span>
        </div>
        <span class="text-white/50 text-xs">${dateStr}</span>
      </div>
    `;

    box.innerHTML = `
      <div class="text-white/90 text-sm space-y-2">
        ${headingHTML}
        ${feedbackHTML}
        ${followupToggleHTML}
        ${followupHTML}
      </div>
    `;

    container.appendChild(box);
  });

  panel.classList.remove("hidden");
}

function toggleFollowup(id) {
  const el = document.getElementById(id);
  const btn = el?.previousElementSibling;
  if (el && btn) {
    const isHidden = el.classList.contains("hidden");
    el.classList.toggle("hidden");
    btn.textContent = isHidden ? "Hide Follow-up" : "Show Follow-up";
  }
}



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

