let justClosedDropdown = false;
// ==========================================================
// 🔸 Load Tracks When a Session Is Selected
// Fetch session list on page load,
// then populate tracks dropdown based on selected session
// ==========================================================
document.addEventListener("DOMContentLoaded", () => {
  // ✅ Attach the close button handler immediately on page load
  const closeBtn = document.getElementById("close-feedback-btn");
  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      document.getElementById("history-feedback").classList.add("hidden");
      document.getElementById("history-feedback-output").innerHTML = "";
    });
  }

  // 🔸 Fetch sessions and populate the dropdown
  fetchSessions();

  // 🔧 Load the Manage section
  loadManageSection();


  // 🔄 Handle session dropdown changes
  const sessionDropdown = document.getElementById("session-select");
  const trackDropdown = document.getElementById("track-select");

  sessionDropdown.addEventListener("change", async (e) => {
    const sessionId = e.target.value;

    // Reset track dropdown
    trackDropdown.innerHTML = '<option value="">-- Select a session first --</option>';
    trackDropdown.disabled = true;


    document.getElementById("close-feedback-btn").addEventListener("click", () => {
  document.getElementById("history-feedback").classList.add("hidden");
  document.getElementById("history-feedback-output").innerHTML = "";
});


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

if (track.type === "mixdown") {
  subheading.className = "text-pink-400 text-lg font-semibold";
  subheading.textContent = "Mixdown Suggestions:";
} else if (track.type === "master") {
  subheading.className = "text-blue-400 text-lg font-semibold";
  subheading.textContent = "Mastering Advice:";
} else if (track.type === "master review") {
  subheading.className = "text-blue-400 text-lg font-semibold";
  subheading.textContent = "Master Review:";
} else {
  subheading.className = "text-white/70 text-lg font-semibold";
  subheading.textContent = "AI Feedback:";
}
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

  // Force custom styles on dropdown containers (session + track)
[sessionOptions, trackOptions].forEach(dropdown => {
  if (dropdown) {
    dropdown.style.backgroundColor = "rgba(90, 90, 90, 0.05)";
    dropdown.style.backdropFilter = "blur(20px)";
    dropdown.style.webkitBackdropFilter = "blur(20px)";
    dropdown.style.border = "1px solid rgba(255,255,255,0.01)";
    dropdown.style.boxShadow = "0 8px 16px rgba(255, 255, 255, 0.0.1)";
    dropdown.style.color = "#f0f0f0"; // optional for legibility
  }
});

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
    const res = await fetch(`/chat/tracks/${trackId}/messages`);
    let messages = await res.json();

    // Filter only initial feedback messages
    messages = messages.filter(msg =>
      msg.followup_group === 0 || msg.followup_group === "0" || msg.followup_group == null
    );

    feedbackBox.innerHTML = "";
    if (messages.length === 0) {
      feedbackBox.innerHTML = "<p class='text-white/70'>No feedback found.</p>";
      return;
    }

    messages.forEach(msg => {
      if (!msg.message?.trim()) return;

      const pairs = msg.message.split(/\n\s*\n/);
      const hasValidPairs = pairs.some(pairText =>
        /-?\s*(INSIGHT|SUGGESTION):\s*/i.test(pairText)
      );
      if (!hasValidPairs) return;

      const wrapper = document.createElement("div");
      wrapper.className = "p-4 bg-white/5 rounded-xl backdrop-blur";

      // Capitalize helper
      function capitalize(word) {
        return word ? word.charAt(0).toUpperCase() + word.slice(1).toLowerCase() : "";
      }

      const meta = document.createElement("p");
      const type = msg.type?.toLowerCase();
      const typeClass =
        type === "mixdown" ? "text-pink-400"
        : type === "master" || type === "mastering" ? "text-blue-400"
        : "text-white";

      meta.className = `font-semibold ${typeClass} mb-4`;
      meta.textContent = `Type: ${capitalize(msg.type)} | Profile: ${msg.feedback_profile || "Default"}`;
      wrapper.appendChild(meta);

      pairs.forEach(pairText => {
        const insightMatch = pairText.match(/-?\s*INSIGHT:\s*(.*)/i);
        const suggestionMatch = pairText.match(/-?\s*SUGGESTION:\s*([\s\S]*)/i);

        if (insightMatch || suggestionMatch) {
          const pairDiv = document.createElement("div");
          pairDiv.className = "bg-white/10 p-4 rounded-md mb-3 text-white/90 text-sm";

          if (insightMatch) {
            const insightP = document.createElement("p");
            insightP.className = "font-semibold mb-1 text-purple-300";
            insightP.textContent = "INSIGHT: " + insightMatch[1].trim();
            pairDiv.appendChild(insightP);
          }

          if (suggestionMatch) {
            const suggestionP = document.createElement("p");
            suggestionP.className = "mb-0 text-white-300";
            suggestionP.textContent = "SUGGESTION: " + suggestionMatch[1].trim();
            pairDiv.appendChild(suggestionP);
          }

          wrapper.appendChild(pairDiv);
        }
      });

      feedbackBox.appendChild(wrapper);
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

      // 👇 ADD: Make session droppable for tracks
sessionDiv.addEventListener("dragover", (e) => {
  e.preventDefault();  // Necessary to allow drop
  sessionDiv.classList.add("bg-white/10");  // Optional: hover effect
});

sessionDiv.addEventListener("dragleave", () => {
  sessionDiv.classList.remove("bg-white/10");
});

sessionDiv.addEventListener("drop", async (e) => {
  e.preventDefault();
  sessionDiv.classList.remove("bg-white/10");

  const trackId = e.dataTransfer.getData("text/plain");
  const newSessionId = session.id;

  try {
    const formData = new FormData();
    formData.append("session_id", newSessionId);

    const res = await fetch(`/tracks/${trackId}`, {
      method: "PUT",
      body: formData,
    });

    if (!res.ok) throw new Error(await res.text());

    await loadManageSection();  // Refresh UI
  } catch (err) {
    alert("Error moving track: " + err.message);
    console.error("❌ Move track failed:", err);
  }
});

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

      const sessionCheckbox = document.createElement("input");
      sessionCheckbox.type = "checkbox";
      sessionCheckbox.className = "session-compare-checkbox w-4 h-4 mr-2";
      sessionCheckbox.setAttribute("data-session-id", session.id);

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

      sessionControls.append(sessionCheckbox, renameBtn, deleteBtn, dropdownWrapper);
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

      let tracks = [];
      try {
        const trackRes = await fetch(`/sessions/${session.id}/tracks`);
        const raw = await trackRes.text();
        const parsed = JSON.parse(raw);
        if (!Array.isArray(parsed)) throw new Error("Not an array");
        tracks = parsed;
      } catch (err) {
        console.error(`❌ Error fetching tracks for session ${session.id}:`, err);
        continue;
      }

      for (const track of tracks) {
        const trackItem = document.createElement("li");
trackItem.className = "track-hover-row flex items-center justify-between px-2 py-1 relative z-10 rounded-md";
trackItem.setAttribute("data-track-item", track.id);

// 👇 ADD: Make draggable
trackItem.setAttribute("draggable", "true");
trackItem.addEventListener("dragstart", (e) => {
  e.dataTransfer.setData("text/plain", track.id);
});
        trackItem.className = "track-hover-row flex items-center justify-between px-2 py-1 relative z-10 rounded-md";
        trackItem.setAttribute("data-track-item", track.id);

        const trackName = document.createElement("span");
        trackName.className = "track-name";
        trackName.textContent = track.track_name;

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.className = "track-compare-checkbox w-4 h-4 mr-2";
        checkbox.setAttribute("data-track-id", track.id);
        checkbox.setAttribute("data-track-name", track.track_name || "Unnamed Track");

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

        const trackLeft = document.createElement("div");
        trackLeft.className = "flex items-center gap-2";
        trackLeft.append(checkbox, trackName);

        trackItem.append(trackLeft, trackControls);
        trackList.appendChild(trackItem);
      }

      sessionCheckbox.addEventListener("change", () => {
        const allCheckboxes = trackList.querySelectorAll(".track-compare-checkbox");
        allCheckboxes.forEach(cb => cb.checked = sessionCheckbox.checked);
      });

      sessionDiv.appendChild(trackList);
      container.appendChild(sessionDiv);

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





document.addEventListener("DOMContentLoaded", () => {
  const compareBtn = document.getElementById("compare-tracks-btn");
  const outputBox = document.getElementById("comparison-feedback-output");
  const feedbackSection = document.getElementById("comparison-feedback");

  // ✅ Load comparison history on page load
  loadComparisonHistory();


  compareBtn.addEventListener("click", async () => {
    // Collect all selected track IDs
    const selectedTrackCheckboxes = document.querySelectorAll(".track-compare-checkbox:checked");
    const trackIds = Array.from(selectedTrackCheckboxes).map(cb => cb.dataset.trackId);

    if (trackIds.length < 2) {
      alert("Please select at least two tracks to compare.");
      return;
    }

    // Optional: disable button while loading
    compareBtn.disabled = true;
    compareBtn.textContent = "Comparing...";

    try {
      const res = await fetch("/chat/compare-tracks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ track_ids: trackIds }),
      });

      if (!res.ok) {
        const err = await res.text();
        throw new Error(err);
      }

      const data = await res.json();
      outputBox.textContent = data.feedback || "No feedback returned.";
      feedbackSection.classList.remove("hidden");
    } catch (err) {
      console.error("❌ Comparison error:", err);
      outputBox.textContent = "An error occurred during comparison.";
      feedbackSection.classList.remove("hidden");
    } finally {
      compareBtn.disabled = false;
      compareBtn.textContent = "Compare Selected Tracks";
    }
  });
});


document.getElementById("compare-button").addEventListener("click", async () => {
  const button = document.getElementById("compare-button");

  const checked = document.querySelectorAll('.track-compare-checkbox:checked');
  const selectedIds = Array.from(checked).map(cb => cb.dataset.trackId);
  const selectedNames = Array.from(checked).map(cb => cb.dataset.trackName);

  if (selectedIds.length < 2) {
    alert("Please select at least two tracks to compare.");
    return;
  }

  // ✨ Add swoosh effect
  button.classList.add("swoosh");

  try {
    const response = await fetch("/chat/compare-tracks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ track_ids: selectedIds })
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Comparison failed.");

    // ✅ Show formatted feedback
    const outputBox = document.getElementById("comparison-feedback-output");
    const feedbackSection = document.getElementById("comparison-feedback");
    const metaBox = document.getElementById("comparison-meta");
    const messageSpan = document.getElementById("comparison-session-message");

    outputBox.innerHTML = formatComparisonFeedback(data.feedback || "No feedback returned.");
    feedbackSection.classList.remove("hidden");
    metaBox.classList.remove("hidden");

    if (messageSpan && selectedNames.length > 0) {
      messageSpan.textContent = "✅ Compared: " + selectedNames.join(", ");
    }

    // 🔁 Reload history so export button appears right away
    await loadComparisonHistory();

    // ✅ Add success message
    const successNote = document.createElement("p");
    successNote.className = "text-green-400 text-sm mt-2";
    successNote.textContent = "✅ Comparison saved to history and available for export.";
    metaBox.appendChild(successNote);

  } catch (err) {
    console.error("❌ Comparison failed:", err);
    alert("An error occurred during comparison. Please try again.");
  } finally {
    // ❌ Remove swoosh effect
    button.classList.remove("swoosh");
  }
});



async function loadComparisonHistory() {
  const historyBox = document.getElementById("comparison-history-list");
  if (!historyBox) {
    console.warn("⚠️ #comparison-history-list not found");
    return;
  }

  historyBox.innerHTML = "";

  try {
    const res = await fetch("/chat/comparisons");
    const groups = await res.json();

    if (!groups.length) {
      historyBox.innerHTML = "<p class='text-white/60'>No comparisons found.</p>";
      return;
    }

    for (const group of groups) {
      const div = document.createElement("div");
      div.className = "flex justify-between items-start gap-4 p-4 rounded-lg bg-white/5 backdrop-blur-sm shadow-md";

      // 🟣 Left: Compared Tracks (with aligned rows)
const trackListBox = document.createElement("div");
trackListBox.className = "grid grid-cols-[auto,1fr] gap-x-2";

// Row 1
const label = document.createElement("span");
label.style.color = "rgba(180, 150, 222, 0.8)";  // slightly minty turquoise
label.className = "font-semibold mb-2";
label.textContent = "Compared Tracks:";

const firstTrack = document.createElement("span");
firstTrack.className = "text-white/90";
firstTrack.textContent = group.track_names[0];

trackListBox.append(label, firstTrack);

// Remaining rows (empty label cell + track name)
group.track_names.slice(1).forEach(name => {
  const empty = document.createElement("span"); // to keep alignment
  const track = document.createElement("span");
  track.className = "text-white/80";
  track.textContent = name;
  trackListBox.append(empty, track);
});

      // 🟢 Right: Stylish White Chip Buttons
const buttonCol = document.createElement("div");
buttonCol.className = "flex flex-col items-end gap-2";

// Shared chip style
const chipClass = "text-white border border-white px-3 py-1 rounded-full text-sm hover:bg-white hover:text-black transition duration-200";

// View Again
const viewBtn = document.createElement("button");
viewBtn.className = `${chipClass} comparison-view-btn`;
viewBtn.textContent = "View Again";
viewBtn.addEventListener("click", () => viewComparison(group.group_id, viewBtn));

// Export
const exportBtn = document.createElement("button");
exportBtn.className = chipClass;
exportBtn.textContent = "Export";

exportBtn.addEventListener("click", () => {
  exportBtn.disabled = true;
  exportBtn.textContent = "Exporting...";

  exportComparison(group.group_id);

  // Reset after export (adjust delay as needed)
  setTimeout(() => {
    exportBtn.disabled = false;
    exportBtn.textContent = "Export";
  }, 10000);
});

// Delete
const deleteBtn = document.createElement("button");
deleteBtn.className = chipClass;
deleteBtn.textContent = "Delete";
deleteBtn.addEventListener("click", async () => {
  if (confirm("Are you sure you want to delete this comparison?")) {
    try {
      const res = await fetch(`/chat/comparisons/${group.group_id}`, {
        method: "DELETE",
      });

      if (!res.ok) throw new Error("Failed to delete");
      await loadComparisonHistory();

      const messageSpan = document.getElementById("comparison-session-message");
      if (messageSpan && messageSpan.textContent.includes(group.track_names[0])) {
        document.getElementById("comparison-feedback").classList.add("hidden");
        document.getElementById("comparison-meta").classList.add("hidden");
        document.getElementById("comparison-feedback-output").innerHTML = "";
      }

    } catch (err) {
      console.error("❌ Failed to delete comparison:", err);
      alert("An error occurred while deleting.");
    }
  }
});

// Append buttons to column
buttonCol.append(viewBtn, exportBtn, deleteBtn);

// Append everything to row
div.append(trackListBox, buttonCol);
historyBox.appendChild(div);
}
  } catch (err) {
    console.error("❌ Error loading comparison history:", err);
    historyBox.innerHTML = "<p class='text-red-400'>Failed to load comparisons.</p>";
  }
}


function formatComparisonFeedback(feedbackText) {
  const lines = feedbackText.trim().split("\n");
  let html = "";
  let inUl = false;
  let inOl = false;

  const flushLists = () => {
    if (inUl) {
      html += "</ul>";
      inUl = false;
    }
    if (inOl) {
      html += "</ol>";
      inOl = false;
    }
  };

  for (let line of lines) {
    const trimmed = line.trim();

    if (!trimmed) {
      flushLists();
      html += "<br>";
      continue;
    }

    if (trimmed.startsWith("### ")) {
      flushLists();
      html += `<h3 class="text-lg font-semibold mt-10 mb-1 text-white/90">${trimmed.slice(4)}</h3>`;
    } else if (trimmed.startsWith("#### ")) {
      flushLists();
      html += `<h4 class="text-md font-semibold mt-2 mb-1">${trimmed.slice(5)}</h4>`;
    } else if (/^\d+\.\s/.test(trimmed)) {
      if (!inOl) {
        flushLists();
        html += "<ol class='list-decimal list-inside ml-4 mb-2'>";
        inOl = true;
      }
      const formatted = trimmed.replace(/^\d+\.\s/, "");
      html += `<li>${formatBold(formatted)}</li>`;
    } else if (trimmed.startsWith("- ")) {
      if (!inUl) {
        flushLists();
        html += "<ul class='list-disc list-inside ml-4 mb-2'>";
        inUl = true;
      }
      html += `<li>${formatBold(trimmed.slice(2))}</li>`;
    } else {
      flushLists();
      html += `<p class="mb-2">${formatBold(trimmed)}</p>`;
    }
  }

  flushLists();
  return html;
}

// Bold helper
function formatBold(text) {
  return text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
}



async function viewComparison(groupId, button) {
  const outputBox = document.getElementById("comparison-feedback-output");
  const feedbackSection = document.getElementById("comparison-feedback");
  const metaBox = document.getElementById("comparison-meta");
  const messageSpan = document.getElementById("comparison-session-message");

  const isVisible = !feedbackSection.classList.contains("hidden");

  if (isVisible && button.textContent === "Close") {
    // 🔁 Hide and reset
    feedbackSection.classList.add("hidden");
    metaBox.classList.add("hidden");
    outputBox.textContent = "";
    messageSpan.textContent = "";
    button.textContent = "View Again";
    return;
  }

  // 🧠 Load comparison feedback
  try {
    const res = await fetch(`/chat/comparisons/${groupId}`);
    if (!res.ok) throw new Error("Failed to load comparison");

    const data = await res.json();

    outputBox.innerHTML = formatComparisonFeedback(data.feedback || "No feedback found.");

    messageSpan.textContent = "Compared Tracks: " + (data.track_names || []).join(", ");

    feedbackSection.classList.remove("hidden");
    metaBox.classList.remove("hidden");
    // 🔁 Reset all other buttons
document.querySelectorAll(".comparison-view-btn").forEach(btn => {
  if (btn !== button) {
    btn.textContent = "View Again";
    btn.classList.remove("view-active");
  }
});

// 🔄 Update current button
button.textContent = "Close";
button.classList.add("view-active");

    // Optional: scroll into view
    document.getElementById("feedback-anchor").scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    console.error("❌ Error viewing comparison:", err);
    outputBox.textContent = "An error occurred while loading the comparison.";
    feedbackSection.classList.remove("hidden");
  }
}

function exportComparison(groupId) {
  const url = `/export/export-comparison?group_id=${encodeURIComponent(groupId)}`;

  const link = document.createElement("a");
  link.href = url;
  link.download = "";  // Let the server's Content-Disposition handle filename
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}