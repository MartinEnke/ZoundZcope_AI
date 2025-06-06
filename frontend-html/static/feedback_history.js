let justClosedDropdown = false;
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
  opt.textContent = track.track_name || "Unnamed Track";
  opt.dataset.track = JSON.stringify(track); // ✅ required for chat display
  trackDropdown.appendChild(opt); // ✅ FIXED
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
  dropdown.appendChild(opt); // ✅ FIXED
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
    li.className = "dropdown-option";
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
    li.className = "dropdown-option";
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

// ✅ Enable session open/closed memory using localStorage

function getOpenSessions() {
  const raw = localStorage.getItem("openSessions");
  try {
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveOpenSessions(openSessionIds) {
  localStorage.setItem("openSessions", JSON.stringify(openSessionIds));
}

async function loadManageSection() {
  try {
    const res = await fetch("/sessions");
    const sessions = await res.json();

    const openSessionIds = getOpenSessions();

    const container = document.getElementById("manage-section");
    container.innerHTML = "";

    for (const session of sessions) {
      const sessionDiv = document.createElement("div");
      sessionDiv.className = "border-b border-white/20 pb-4";
      sessionDiv.setAttribute("data-session-wrapper", session.id);

      const sessionHeader = document.createElement("div");
      sessionHeader.className = "flex items-center justify-between mb-2";

      const sessionTitleWrap = document.createElement("button");
      sessionTitleWrap.className = "flex items-center justify-between w-full text-left";

      const sessionTitleText = document.createElement("span");
      sessionTitleText.className = "text-lg font-semibold";
      sessionTitleText.textContent = session.session_name;

      const arrow = document.createElement("svg");
      arrow.className = "w-4 h-4 text-white transform transition-transform";
      arrow.setAttribute("fill", "none");
      arrow.setAttribute("stroke", "currentColor");
      arrow.setAttribute("viewBox", "0 0 24 24");
      arrow.innerHTML = `<path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M9 5l7 7-7 7\" />`;

      sessionTitleWrap.append(sessionTitleText, arrow);

      const sessionControls = document.createElement("div");
      sessionControls.className = "flex items-center gap-2";

      const renameBtn = document.createElement("button");
      renameBtn.textContent = "Edit";
      renameBtn.className = "hidden md:block px-3 py-1 text-sm rounded-full text-white bg-white/10 border border-white/20 hover:border-green-400 hover:bg-green-400/10 hover:text-white transition-all duration-200";
      renameBtn.addEventListener("mouseenter", () => sessionTitleText.classList.add("text-green-400"));
      renameBtn.addEventListener("mouseleave", () => sessionTitleText.classList.remove("text-green-400"));
      renameBtn.addEventListener("click", () => {
        const input = prompt("Rename session:", session.session_name);
        if (input) renameSession(session.id, input);
      });

      const deleteBtn = document.createElement("button");
      deleteBtn.textContent = "−";
      deleteBtn.className = "hidden md:flex w-8 h-8 items-center justify-center rounded-full text-white bg-white/10 border border-white/20 hover:border-red-500 hover:bg-rose-500/10 hover:text-white transition-all duration-200";
      deleteBtn.addEventListener("mouseenter", () => sessionTitleText.classList.add("text-red-500"));
      deleteBtn.addEventListener("mouseleave", () => sessionTitleText.classList.remove("text-red-500"));
      deleteBtn.addEventListener("click", () => {
        if (confirm("Delete session and all tracks?")) deleteSession(session.id);
      });

      const dropdownWrapper = document.createElement("div");
      dropdownWrapper.className = "relative md:hidden";

      const menuButton = document.createElement("button");
      menuButton.textContent = "⋮";
      menuButton.className = "text-white text-xl px-2 py-1 rounded hover:bg-white/10";
      menuButton.setAttribute("type", "button");

      const dropdownMenu = document.createElement("div");
      dropdownMenu.className = "session-dropdown absolute right-0 mt-2 w-36 rounded-lg shadow-lg backdrop-blur-md bg-white/10 border border-white/10 text-sm text-white z-20 hidden p-2 space-y-1";

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

      menuButton.addEventListener("click", (e) => {
        e.stopPropagation();
        dropdownMenu.classList.toggle("hidden");
      });

      sessionControls.append(renameBtn, deleteBtn, dropdownWrapper);
      sessionHeader.append(sessionTitleWrap, sessionControls);
      sessionDiv.appendChild(sessionHeader);













      const trackList = document.createElement("ul");
  trackList.className = "ml-4 space-y-1 text-sm";

  const isOpen = openSessionIds.includes(String(session.id));
  if (isOpen) {
    trackList.classList.remove("hidden");
    arrow.classList.add("rotate-90");
  } else {
    trackList.classList.add("hidden");
    arrow.classList.remove("rotate-90");
  }

  // 🟡 Load tracks for this session
  let tracks = [];
  try {
    const trackRes = await fetch(`/sessions/${session.id}/tracks`);
    const raw = await trackRes.text();
    try {
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) throw new Error("Not an array");
      tracks = parsed;
    } catch (err) {
      console.error(`💥 Error parsing tracks for session ${session.id}:`, err, raw);
      continue; // Skip this session
    }
  } catch (fetchErr) {
    console.error(`❌ Network error fetching tracks for session ${session.id}:`, fetchErr);
    continue; // Skip this session
  }

  // ✅ Now tracks is a safe array
  for (const track of tracks) {
    const trackItem = document.createElement("li");
    trackItem.className = "track-hover-row flex items-center justify-between px-2 py-1 relative z-10 rounded-md";
    trackItem.setAttribute("data-track-item", track.id);

    const trackName = document.createElement("span");
    trackName.className = "track-name";
    trackName.textContent = track.track_name;

    // ✏️ Rename button
    const trackRenameBtn = document.createElement("button");
    trackRenameBtn.textContent = "Edit";
    trackRenameBtn.className = "track-edit-btn hidden md:block px-2 py-0.5 text-xs rounded-full text-white bg-white/10 border border-white/20 hover:border-green-400 hover:bg-green-400/10 hover:text-white transition-all duration-200";
    trackRenameBtn.addEventListener("mouseenter", () => trackName.classList.add("text-green-400"));
    trackRenameBtn.addEventListener("mouseleave", () => trackName.classList.remove("text-green-400"));
    trackRenameBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const newName = prompt("Rename track:", track.track_name);
      if (newName) renameTrack(track.id, newName, track.type);
    });

    // ❌ Delete button
    const trackDeleteBtn = document.createElement("button");
    trackDeleteBtn.textContent = "−";
    trackDeleteBtn.className = "flex w-6 h-6 items-center justify-center rounded-full text-white bg-white/10 border border-white/20 hover:border-red-500 hover:bg-red-500/10 hover:text-white transition-all duration-200";
    trackDeleteBtn.addEventListener("mouseenter", () => {
      trackName.classList.remove("text-green-400");
      trackName.classList.add("text-red-400", "red-hover");
      trackItem.classList.add("suppress-edit-hover");
    });
    trackDeleteBtn.addEventListener("mouseleave", () => {
      trackName.classList.remove("text-red-400", "red-hover");
      trackItem.classList.remove("suppress-edit-hover");
    });
    trackDeleteBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (confirm("Delete this track?")) deleteTrack(track.id);
    });

    const trackControls = document.createElement("div");
    trackControls.className = "flex items-center gap-2";
    trackControls.append(trackRenameBtn, trackDeleteBtn);

    trackItem.append(trackName, trackControls);
    trackList.appendChild(trackItem);

    trackItem.addEventListener("click", (e) => {
      const isDelete = e.target.closest("button")?.textContent.trim() === "−";
      const isMobileMenu = e.target.closest(".relative.md\\:hidden");
      if (isDelete || isMobileMenu) return;

      const newName = prompt("Rename track:", track.track_name);
      if (newName) renameTrack(track.id, newName, track.type);
    });
  }

  sessionDiv.appendChild(trackList);
  container.appendChild(sessionDiv);

  // After appending sessionDiv to container
sessionTitleWrap.addEventListener("click", () => {
  const isOpen = !trackList.classList.contains("hidden");
  const openSessionIds = getOpenSessions();

  if (isOpen) {
    trackList.classList.add("hidden");
    arrow.classList.remove("rotate-90");
    saveOpenSessions(openSessionIds.filter(id => id !== String(session.id)));
  } else {
    trackList.classList.remove("hidden");
    arrow.classList.add("rotate-90");
    if (!openSessionIds.includes(String(session.id))) {
      openSessionIds.push(String(session.id));
    }
    saveOpenSessions(openSessionIds);
  }
});

}
  } catch (err) {
    console.error("Failed to load manage section:", err);
  }
}

// ==========================================================
// 🔁 Live Update Helpers (no page refresh needed)
// ==========================================================

async function renameSession(id, newName) {
  const formData = new FormData();
  formData.append("new_name", newName);

  const res = await fetch(`/sessions/${id}`, {
    method: "PUT",
    body: formData,
  });

  if (!res.ok) {
    console.error("❌ Failed to rename session:", await res.text());
    alert("Failed to rename session.");
  }

  loadManageSection();
}


async function deleteSession(id) {
  await fetch(`/sessions/${id}`, { method: "DELETE" });
  const wrapper = document.querySelector(`[data-session-wrapper="${id}"]`);
  if (wrapper) wrapper.remove();
}

async function renameTrack(id, newName) {
  const formData = new FormData();
  formData.append("track_name", newName);

  const res = await fetch(`/tracks/${id}`, {
    method: "PUT",
    body: formData,
  });

  if (!res.ok) {
    console.error("❌ Failed to rename track:", await res.text());
    alert("Failed to rename track.");
    return;
  }

  loadManageSection();
}

async function deleteTrack(id) {
  await fetch(`/tracks/${id}`, { method: "DELETE" });
  const item = document.querySelector(`[data-track-item="${id}"]`);
  if (item) item.remove();
}

// 🚀 Run on page load
document.addEventListener("DOMContentLoaded", loadManageSection);
