

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

const fileInput = document.getElementById('file-upload');
const fileNameSpan = document.getElementById('file-name');
fileInput.addEventListener('change', () => {
  fileNameSpan.textContent = fileInput.files.length > 0
    ? fileInput.files[0].name
    : 'Click to upload your track';
});

// ✅ Upload form with backend session creation
const form = document.getElementById("uploadForm");
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData(form);
  const sessionName = document.getElementById("session_name").value.trim();

  if (!sessionName) {
    alert("Please enter a session name.");
    return;
  }

  // ✅ Create the session in backend and get real session_id
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



  // ✅ Fix empty or placeholder track name
  const trackName = formData.get("track_name");
  if (!trackName || trackName.trim() === "" || trackName.trim().toLowerCase() === "string") {
    formData.set("track_name", "string");
  }

  try {
    const response = await fetch("/upload/", {
      method: "POST",
      body: formData,
    });

    const raw = await response.text();
    const result = JSON.parse(raw);

    if (response.ok) {
      await loadSessionTracks(sessionId); // ✅ refresh dropdown

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

      const lines = result.feedback.split("\n").map(line => line.trim()).filter(Boolean);
      for (const line of lines) {
        const li = document.createElement("li");
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

// ✅ Inline async function to create session in backend
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
    return result; // ✅ returns full object
  } catch (err) {
    console.error("❌ Session creation fetch failed", err);
    return null;
  }
}






document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("type-button");
  const options = document.getElementById("type-options");
  const hiddenInput = document.getElementById("type-input");
  const selectedText = document.getElementById("type-selected");

  button.addEventListener("click", () => {
    options.classList.toggle("hidden");
  });

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

  document.addEventListener("click", (e) => {
    if (!button.contains(e.target) && !options.contains(e.target)) {
      options.classList.add("hidden");
    }
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const genreButton = document.getElementById("genre-button");
  const genreOptions = document.getElementById("genre-options");
  const genreInput = document.getElementById("genre-input");
  const genreSelected = document.getElementById("genre-selected");

  genreButton.addEventListener("click", () => {
    genreOptions.classList.toggle("hidden");
  });

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

  document.addEventListener("click", (e) => {
    if (!genreButton.contains(e.target) && !genreOptions.contains(e.target)) {
      genreOptions.classList.add("hidden");
    }
  });
});


// load and display all tracks in the current session
// Fetch and populate session track names in dropdown, and display their analysis + feedback on selection
async function loadSessionTracks(sessionId) {
  try {
    const response = await fetch(`/sessions/${sessionId}/tracks`);

    // ✅ Debug output to inspect raw response
    const rawText = await response.clone().text();
    console.log("Session tracks response:", rawText);

    const tracks = JSON.parse(rawText);

    const dropdownContainer = document.getElementById("sessionTrackSelector");
    const dropdown = document.getElementById("session-tracks");
    const resultsEl = document.getElementById("results");
    const feedbackEl = document.getElementById("feedback");
    const feedbackBox = document.getElementById("gptResponse");
    const output = document.getElementById("analysisOutput");

    dropdown.innerHTML = "";

    if (tracks.length === 0) {
      dropdown.innerHTML = `<option value="">No tracks yet</option>`;
    } else {
      dropdown.innerHTML = `<option value="">Select a track...</option>`;
      tracks.forEach((track) => {
        const option = document.createElement("option");
        option.value = track.id;
        option.textContent = track.track_name || "Unnamed Track";
        option.dataset.track = JSON.stringify(track);
        dropdown.appendChild(option);
      });
    }

    dropdownContainer.classList.remove("hidden");

    // ✅ Prevent multiple duplicate listeners
    if (!dropdown.dataset.listenerAttached) {
      dropdown.addEventListener("change", (e) => {
        const selectedOption = e.target.selectedOptions[0];
        const track = JSON.parse(selectedOption.dataset.track || null);
        if (!track) return;

        resultsEl.classList.remove("hidden");
        feedbackEl.classList.remove("hidden");
        feedbackEl.classList.add("fade-in-up");

        const a = track.analysis;
        if (!a) return;

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

        // ✅ Feedback fallback to handle undefined/null
        feedbackBox.innerHTML = "";
        const subheading = document.createElement("p");
        subheading.className = track.type === "mixdown"
          ? "text-pink-400 text-lg font-semibold"
          : "text-blue-400 text-lg font-semibold";
        subheading.textContent = track.type === "mixdown"
          ? "Mixdown Suggestions:" : "Mastering Advice:";
        feedbackBox.appendChild(subheading);

        const ul = document.createElement("ul");
        ul.className = "list-disc list-inside mt-2 text-white/90 space-y-1";
        feedbackBox.appendChild(ul);

        const lines = (track.feedback || "").split("\n").map(l => l.trim()).filter(Boolean);
        if (lines.length > 0) {
          for (const line of lines) {
            const li = document.createElement("li");
            li.textContent = line;
            ul.appendChild(li);
          }
        } else {
          ul.innerHTML = "<li>No feedback available.</li>";
        }
      });

      // ✅ Flag so we don't attach more than once
      dropdown.dataset.listenerAttached = "true";
    }

  } catch (error) {
    console.error("Error loading session tracks:", error);
  }
}


// Only call this once a session was created
// This is now done dynamically after upload

// ✅ Fetch and populate session dropdown
async function fetchSessions() {
  const res = await fetch("/sessions");
  const sessions = await res.json();
  const sessionDropdown = document.getElementById("session-select");
  sessionDropdown.innerHTML = '<option value="">Choose Session</option>';
  sessions.forEach(session => {
    const opt = document.createElement("option");
    opt.value = session.id;
    opt.textContent = session.session_name;
    sessionDropdown.appendChild(opt);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  fetchSessions();

  document.getElementById("session-select").addEventListener("change", async (e) => {
    const sessionId = e.target.value;
    const trackDropdown = document.getElementById("track-select");

    // Reset track dropdown
    trackDropdown.innerHTML = '<option value="">-- Select a session first --</option>';
    trackDropdown.disabled = true;

    if (!sessionId) return;

    try {
      const res = await fetch(`/sessions/${sessionId}/tracks`);
      if (!res.ok) {
        const errorText = await res.text();
        console.error("❌ Failed to fetch tracks:", errorText);
        return;
      }

      const tracks = await res.json();
      if (!Array.isArray(tracks)) {
        console.error("❌ Expected array of tracks, got:", tracks);
        return;
      }

      trackDropdown.innerHTML = '<option value="">Choose Track</option>';
      tracks.forEach(track => {
        const opt = document.createElement("option");
        opt.value = track.id;
        opt.textContent = track.track_name || "Untitled Track";
        trackDropdown.appendChild(opt);
      });

      trackDropdown.disabled = false;
    } catch (err) {
      console.error("❌ Error during fetchTracksForSession:", err);
    }
  });
});

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("track-select").addEventListener("change", async (e) => {
    const trackId = e.target.value;
    if (!trackId) return;

    try {
      const res = await fetch(`/tracks/${trackId}/messages`);
      const messages = await res.json();

      const feedbackBox = document.getElementById("gptResponse");
      feedbackBox.innerHTML = ""; // Clear previous

      if (messages.length === 0) {
        feedbackBox.innerHTML = "<p>No feedback yet for this track.</p>";
      } else {
        messages.forEach(msg => {
          const msgEl = document.createElement("div");
          msgEl.className = msg.sender === "assistant" ? "text-blue-400" : "text-white";
          msgEl.innerHTML = `
            <p><strong>${msg.track_name} – ${msg.type || "unknown"} – ${msg.feedback_profile || "default"}</strong></p>
            <p>${msg.message}</p>
          `;
          feedbackBox.appendChild(msgEl);
        });
      }

      document.getElementById("feedback").classList.remove("hidden");
    } catch (err) {
      console.error("Failed to fetch chat messages:", err);
    }
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const profileButton = document.getElementById("profile-button");
  const profileOptions = document.getElementById("profile-options");
  const profileInput = document.getElementById("profile-input");
  const profileSelected = document.getElementById("profile-selected");

  profileButton.addEventListener("click", () => {
    profileOptions.classList.toggle("hidden");
  });

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

  document.addEventListener("click", (e) => {
    if (!profileButton.contains(e.target) && !profileOptions.contains(e.target)) {
      profileOptions.classList.add("hidden");
    }
  });
});

