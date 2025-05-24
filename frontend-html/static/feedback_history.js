// ==========================================================
// 🔸 Load Tracks When a Session Is Selected
// Fetch session list on page load,
// then populate tracks dropdown based on selected session
// ==========================================================
document.addEventListener("DOMContentLoaded", () => {
  // 🔸 Fetch sessions and populate the dropdown
  fetchSessions();

  // 🔧 Also load the Manage section on page load
  loadManageSection();

  // 🔄 Handle session dropdown changes
  const sessionDropdown = document.getElementById("session-select");
  const trackDropdown = document.getElementById("track-select");

  sessionDropdown.addEventListener("change", async (e) => {
    const sessionId = e.target.value;

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


// ==========================================================
// 🔸 Load and Display All Tracks in the Current Session
// Fetch and populate session track names in dropdown,
// and display their analysis + feedback on selection
// ==========================================================
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

    // ==========================================================
    // 🔹 Populate Track Dropdown
    // ==========================================================
    if (tracks.length === 0) {
      dropdown.innerHTML = `<option value="">No tracks yet</option>`;
    } else {
      dropdown.innerHTML = `<option value="">Select a track...</option>`;
      tracks.forEach(track => {
        const opt = document.createElement("option");
        opt.value = track.id;
        opt.textContent = track.track_name || "Unnamed Track";
        opt.dataset.track = JSON.stringify(track); // ✅ required for chat display
        trackDropdown.appendChild(opt);
      });
    }

    dropdownContainer.classList.remove("hidden");

    // ==========================================================
    // 🔹 Prevent Multiple Listeners and Handle Selection
    // ==========================================================
    if (!dropdown.dataset.listenerAttached) {
      dropdown.addEventListener("change", (e) => {
        const selectedOption = e.target.selectedOptions[0];

        if (!selectedOption || !selectedOption.dataset.track) {
          console.warn("⚠️ Missing dataset.track on selected option");
          return;
        }

        try {
          const parsedTrack = JSON.parse(selectedOption.dataset.track);
          currentSelectedTrack = parsedTrack;
        } catch (error) {
          console.error("❌ Failed to parse dataset.track:", error);
          return;
        }

        const track = currentSelectedTrack;
        if (!track || !track.analysis) return;

        resultsEl.classList.remove("hidden");
        feedbackEl.classList.remove("hidden");
        feedbackEl.classList.add("fade-in-up");

        const a = track.analysis;
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

        // ==========================================================
        // 🔹 Feedback Display Section
        // ==========================================================
        // ⬇️ Optional divider before feedback history
        const divider = document.createElement("hr");
        divider.className = "my-6 border-t border-white/20";
        feedbackBox.appendChild(divider);

        // ⬇️ Feedback History heading
        const historyHeading = document.createElement("h2");
        historyHeading.textContent = "Feedback History";
        historyHeading.className = "text-xl font-bold text-white mb-2";
        feedbackBox.appendChild(historyHeading);

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




document.addEventListener("DOMContentLoaded", () => {
  const sessionButton = document.getElementById("session-button");
  const sessionOptions = document.getElementById("session-options");
  const sessionInput = document.getElementById("session-input");
  const sessionSelected = document.getElementById("session-selected");

  const trackButton = document.getElementById("track-button");
  const trackOptions = document.getElementById("track-options");
  const trackInput = document.getElementById("track-input");
  const trackSelected = document.getElementById("track-selected");

  // Toggle dropdowns
  sessionButton.addEventListener("click", () => sessionOptions.classList.toggle("hidden"));
  trackButton.addEventListener("click", () => trackOptions.classList.toggle("hidden"));

  // Hide dropdowns on outside click
  document.addEventListener("click", (e) => {
    if (!sessionButton.contains(e.target)) sessionOptions.classList.add("hidden");
    if (!trackButton.contains(e.target)) trackOptions.classList.add("hidden");
  });

  // Load session list
  async function fetchSessions() {
    const res = await fetch("/sessions");
    const sessions = await res.json();

    sessionOptions.innerHTML = "";
    sessions.forEach(session => {
      const li = document.createElement("li");
      li.className = "dropdown-option px-4 py-2 cursor-pointer transition";
      li.textContent = session.session_name;
      li.dataset.sessionId = session.id;

      li.addEventListener("click", () => {
        sessionInput.value = session.id;
        sessionSelected.textContent = session.session_name;
        sessionOptions.classList.add("hidden");
        fetchTracks(session.id); // 🔄 Load tracks for this session
      });

      sessionOptions.appendChild(li);
    });
  }

  // Load tracks for selected session
  async function fetchTracks(sessionId) {
    const res = await fetch(`/sessions/${sessionId}/tracks`);
    const tracks = await res.json();

    trackOptions.innerHTML = "";
    if (!tracks.length) {
      const li = document.createElement("li");
      li.textContent = "No tracks in session";
      li.className = "text-white/60 px-4 py-2 italic";
      trackOptions.appendChild(li);
      return;
    }

    tracks.forEach(track => {
      const li = document.createElement("li");
      li.className = "dropdown-option px-4 py-2 cursor-pointer transition";
      li.textContent = track.track_name || "Untitled Track";
      li.dataset.trackId = track.id;

      li.addEventListener("click", () => {
        trackInput.value = track.id;
        trackSelected.textContent = track.track_name;
        trackOptions.classList.add("hidden");
        loadTrackFeedback(track.id);
      });

      trackOptions.appendChild(li);
    });
  }

  // Load feedback and analysis
  async function loadTrackFeedback(trackId) {
    const feedbackBox = document.getElementById("history-feedback-output");
    const feedbackContainer = document.getElementById("history-feedback");

    try {
      const res = await fetch(`/tracks/${trackId}/messages`);
      const messages = await res.json();

      feedbackBox.innerHTML = "";
      if (messages.length === 0) {
        feedbackBox.innerHTML = "<p class='text-white/70'>No feedback found.</p>";
        return;
      }

      messages.forEach(msg => {
        const div = document.createElement("div");
        div.className = "mb-4";

        const heading = document.createElement("p");

        // Choose color based on track type
        const typeClass = msg.type?.toLowerCase() === "mixdown"
          ? "text-pink-400"
          : msg.type?.toLowerCase() === "master"
          ? "text-blue-400"
          : "text-white";

        heading.className = `font-semibold ${typeClass}`;
        heading.textContent = `Type: ${msg.type} | Profile: ${msg.feedback_profile || "Default"}`;
        div.appendChild(heading);

        const ul = document.createElement("ul");
        ul.className = "list-disc list-inside text-white/90 text-sm mt-2";

        const lines = msg.message
          .split("\n")
          .map(l => l.replace(/^[-•\s]+/, "").trim()) // ⬅️ Strip leading - or • or whitespace
          .filter(Boolean);

        lines.forEach(line => {
          const li = document.createElement("li");
          li.textContent = line;
          ul.appendChild(li);
        });

        div.appendChild(ul);
        feedbackBox.appendChild(div);
      });

      feedbackContainer.classList.remove("hidden");
    } catch (err) {
      console.error("Failed to load feedback:", err);
    }
  }

  // Initial fetch
  fetchSessions();
});

// ==========================================================
// 🔧 Manage Sessions & Tracks Logic (with live UI updates)
// ==========================================================

async function loadManageSection() {
  try {
    const res = await fetch("/sessions");
    const sessions = await res.json();

    const container = document.getElementById("manage-section");
    container.innerHTML = "";

    for (const session of sessions) {
      const sessionDiv = document.createElement("div");
      sessionDiv.className = "border-b border-white/20 pb-4";
      sessionDiv.setAttribute("data-session-wrapper", session.id); // ✅ for live delete

      const sessionHeader = document.createElement("div");
      sessionHeader.className = "flex items-center justify-between mb-2";

      // Collapsible title with arrow
      const sessionTitleWrap = document.createElement("button");
      sessionTitleWrap.className = "flex items-center justify-between w-full text-left";
      sessionTitleWrap.addEventListener("click", () => {
        trackList.classList.toggle("hidden");
        arrow.classList.toggle("rotate-90");
      });

      const sessionTitleText = document.createElement("span");
      sessionTitleText.className = "text-lg font-semibold";
      sessionTitleText.textContent = session.session_name;

      const arrow = document.createElement("svg");
      arrow.className = "w-4 h-4 text-white transform transition-transform";
      arrow.setAttribute("fill", "none");
      arrow.setAttribute("stroke", "currentColor");
      arrow.setAttribute("viewBox", "0 0 24 24");
      arrow.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />`;

      sessionTitleWrap.append(sessionTitleText, arrow);

      const sessionControls = document.createElement("div");
sessionControls.className = "flex items-center gap-2";

// DESKTOP BUTTONS
const renameBtn = document.createElement("button");
renameBtn.textContent = "Edit";
renameBtn.className =
  "hidden md:block px-3 py-1 text-sm rounded-full text-white bg-white/10 border border-white/20 " +
  "hover:border-green-400 hover:bg-green-400/10 hover:text-white transition-all duration-200";
renameBtn.addEventListener("mouseenter", () => sessionTitleText.classList.add("text-green-400"));
renameBtn.addEventListener("mouseleave", () => sessionTitleText.classList.remove("text-green-400"));
renameBtn.addEventListener("click", () => {
  const input = prompt("Rename session:", session.session_name);
  if (input) renameSession(session.id, input);
});

const deleteBtn = document.createElement("button");
deleteBtn.textContent = "−";
deleteBtn.className =
  "hidden md:flex w-8 h-8 items-center justify-center rounded-full text-white bg-white/10 border border-white/20 " +
  "hover:border-red-500 hover:bg-rose-500/10 hover:text-white transition-all duration-200";
deleteBtn.addEventListener("mouseenter", () => sessionTitleText.classList.add("text-red-500"));
deleteBtn.addEventListener("mouseleave", () => sessionTitleText.classList.remove("text-red-500"));
deleteBtn.addEventListener("click", () => {
  if (confirm("Delete session and all tracks?")) deleteSession(session.id);
});

// MOBILE "⋮" MENU
const dropdownWrapper = document.createElement("div");
dropdownWrapper.className = "relative md:hidden";

const menuButton = document.createElement("button");
menuButton.textContent = "⋮";
menuButton.className = "text-white text-xl px-2 py-1 rounded hover:bg-white/10";
menuButton.addEventListener("click", (e) => {
  e.stopPropagation();
  dropdownMenu.classList.toggle("hidden");
});

const dropdownMenu = document.createElement("div");
dropdownMenu.className = "absolute right-0 mt-2 w-32 rounded-md shadow-lg bg-black/90 border border-white/20 hidden z-20";

const mobileEdit = document.createElement("div");
mobileEdit.textContent = "Edit";
mobileEdit.className = "px-4 py-2 cursor-pointer hover:bg-green-400/20";
mobileEdit.addEventListener("click", () => {
  dropdownMenu.classList.add("hidden");
  const input = prompt("Rename session:", session.session_name);
  if (input) renameSession(session.id, input);
});

const mobileDelete = document.createElement("div");
mobileDelete.textContent = "Delete";
mobileDelete.className = "px-4 py-2 cursor-pointer hover:bg-red-500/20";
mobileDelete.addEventListener("click", () => {
  dropdownMenu.classList.add("hidden");
  if (confirm("Delete session and all tracks?")) deleteSession(session.id);
});

dropdownMenu.append(mobileEdit, mobileDelete);
dropdownWrapper.append(menuButton, dropdownMenu);

// Assemble controls
sessionControls.append(renameBtn, deleteBtn, dropdownWrapper);

      sessionHeader.append(sessionTitleWrap, sessionControls);
      sessionDiv.appendChild(sessionHeader);

      const trackList = document.createElement("ul");
      trackList.className = "ml-4 space-y-1 text-sm";

      const tracksRes = await fetch(`/sessions/${session.id}/tracks`);
      const tracks = await tracksRes.json();

      for (const track of tracks) {
        const trackItem = document.createElement("li");
        trackItem.className = "flex items-center justify-between";
        trackItem.setAttribute("data-track-item", track.id); // ✅ for live update/delete

        const trackName = document.createElement("span");
        trackName.textContent = track.track_name;

        const trackControls = document.createElement("div");
trackControls.className = "flex items-center gap-2";

// DESKTOP BUTTONS
const trackRenameBtn = document.createElement("button");
trackRenameBtn.textContent = "Edit";
trackRenameBtn.className =
  "hidden md:block px-2 py-0.5 text-xs rounded-full text-white bg-white/10 border border-white/20 " +
  "hover:border-green-400 hover:bg-green-400/10 hover:text-white transition-all duration-200";
trackRenameBtn.addEventListener("mouseenter", () => trackName.classList.add("text-green-400"));
trackRenameBtn.addEventListener("mouseleave", () => trackName.classList.remove("text-green-400"));
trackRenameBtn.addEventListener("click", () => {
  const newName = prompt("Rename track:", track.track_name);
  if (newName) renameTrack(track.id, newName, track.type);
});

const trackDeleteBtn = document.createElement("button");
trackDeleteBtn.textContent = "−";
trackDeleteBtn.className =
  "hidden md:flex w-6 h-6 items-center justify-center rounded-full text-white bg-white/10 border border-white/20 " +
  "hover:border-red-500 hover:bg-red-500/10 hover:text-white transition-all duration-200";
trackDeleteBtn.addEventListener("mouseenter", () => trackName.classList.add("text-red-500"));
trackDeleteBtn.addEventListener("mouseleave", () => trackName.classList.remove("text-red-500"));
trackDeleteBtn.addEventListener("click", () => {
  if (confirm("Delete this track?")) deleteTrack(track.id);
});

// MOBILE "⋮" MENU
const trackDropdownWrapper = document.createElement("div");
trackDropdownWrapper.className = "relative md:hidden";

const trackMenuBtn = document.createElement("button");
trackMenuBtn.textContent = "⋮";
trackMenuBtn.className = "text-white text-xl px-2 py-1 rounded hover:bg-white/10";
trackMenuBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  trackDropdown.classList.toggle("hidden");
});

const trackDropdown = document.createElement("div");
trackDropdown.className = "absolute right-0 mt-2 w-28 rounded-md shadow-lg bg-black/90 border border-white/20 hidden z-20";

const trackEditOption = document.createElement("div");
trackEditOption.textContent = "Edit";
trackEditOption.className = "px-4 py-2 cursor-pointer hover:bg-green-400/20";
trackEditOption.addEventListener("click", () => {
  trackDropdown.classList.add("hidden");
  const newName = prompt("Rename track:", track.track_name);
  if (newName) renameTrack(track.id, newName, track.type);
});

const trackDeleteOption = document.createElement("div");
trackDeleteOption.textContent = "Delete";
trackDeleteOption.className = "px-4 py-2 cursor-pointer hover:bg-red-500/20";
trackDeleteOption.addEventListener("click", () => {
  trackDropdown.classList.add("hidden");
  if (confirm("Delete this track?")) deleteTrack(track.id);
});

trackDropdown.append(trackEditOption, trackDeleteOption);
trackDropdownWrapper.append(trackMenuBtn, trackDropdown);

// Assemble controls
trackControls.append(trackRenameBtn, trackDeleteBtn, trackDropdownWrapper);

        trackItem.append(trackName, trackControls);
        trackList.appendChild(trackItem);
      }

      sessionDiv.appendChild(trackList);
      container.appendChild(sessionDiv);
    }
  } catch (err) {
    console.error("Failed to load manage section:", err);
  }
}

// ==========================================================
// 🔁 Live Update Helpers (no page refresh needed)
// ==========================================================

async function renameSession(id, newName) {
  await fetch(`/sessions/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ new_name: newName })
  });

  const titleEl = document.querySelector(`[data-session-wrapper="${id}"] span`);
  if (titleEl) titleEl.textContent = newName;
}

async function deleteSession(id) {
  await fetch(`/sessions/${id}`, { method: "DELETE" });
  const wrapper = document.querySelector(`[data-session-wrapper="${id}"]`);
  if (wrapper) wrapper.remove();
}

async function renameTrack(id, newName, type) {
  await fetch(`/tracks/${id}?track_name=${encodeURIComponent(newName)}&type=${encodeURIComponent(type)}`, {
    method: "PUT"
  });

  const nameEl = document.querySelector(`[data-track-item="${id}"] span`);
  if (nameEl) nameEl.textContent = newName;
}

async function deleteTrack(id) {
  await fetch(`/tracks/${id}`, { method: "DELETE" });
  const item = document.querySelector(`[data-track-item="${id}"]`);
  if (item) item.remove();
}

// 🚀 Run on page load
document.addEventListener("DOMContentLoaded", loadManageSection);
