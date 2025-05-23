// ==========================================================
// 🔸 Track Selection State
// ==========================================================
let currentSelectedTrack = null;

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
// ✅ Add this separately — do not replace your existing trackSelect block!
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

  const formData = new FormData(form);
  const sessionName = document.getElementById("session_name").value.trim();

  if (!sessionName) {
    alert("Please enter a session name.");
    return;
  }

  // ✅ Create session in backend
  const sessionResult = await createSessionInBackend(sessionName);
  if (!sessionResult || !sessionResult.id) {
    console.warn("⚠️ sessionResult:", sessionResult);
    alert("Session creation failed.");
    return;
  }

  const sessionId = sessionResult.id;
  formData.set("session_id", sessionId);

  const feedbackProfile = document.getElementById("profile-input").value;
  formData.set("feedback_profile", feedbackProfile);


  // ✅ Use custom track name if provided
  const customTrackName = document.getElementById("track_name").value.trim();
  formData.set("track_name", customTrackName || "");


  try {
    const response = await fetch("/upload/", {
      method: "POST",
      body: formData,
    });

    const raw = await response.text();
    const result = JSON.parse(raw);

    if (response.ok) {
      await loadSessionTracks(sessionId); // ✅ Refresh dropdown

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

      const lines = result.feedback
        .split("\n")
        .map(line => line.replace(/^[-•\s]+/, "").trim())
        .filter(Boolean);

      for (const [index, line] of lines.entries()) {
        const li = document.createElement("li");
        li.style.display = "list-item";
        if (index > 0) li.style.marginTop = "0.75rem";
        ul.appendChild(li);
        await typeText(li, line, 10);
      }

      feedbackBox.classList.remove("pulsing-feedback");

    } else {
      console.error("Upload failed response:", result);
      alert("Upload failed: " + JSON.stringify(result));
    }

  } catch (err) {
    console.error("Fetch error:", err);
    alert("An error occurred during upload.");
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

