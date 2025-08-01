// ✅ Cleaned version of your app.js with separate flat DOMContentLoaded blocks
let rmsChunks = [];  // 👈 declare it globally
const chunkDuration = 0.5;
let refWavesurfer = null;
let refWaveformReady = false; // "main" or "ref"
let focusedWaveform = "main";
let refTrackAnalysisData = null;
let lastManualSummaryGroup = -1;  // track last manual summary group




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
// 🔁 Ask AI Follow-Up Logic with Threading + Summarization
// ==========================================================
let followupThread = [];        // Stores current thread of 5 Q&As
let followupGroupIndex = 0;     // Tracks the group number per analysis

// ENTER TRIGGER
document.getElementById("customQuestion").addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    event.preventDefault();
    document.getElementById("askAIButton").click();
  }
});

document.getElementById("askAIButton").addEventListener("click", async () => {
  const questionInput = document.getElementById("customQuestion");
  const question = questionInput.value.trim();
  const outputBox = document.getElementById("aiFollowupResponse");

  if (!question) {
    alert("Please enter a question.");
    return;
  }

  // Use globally tracked latest IDs instead of dropdown
  const trackId = window.lastTrackId || "";
  if (!trackId) {
    alert("No analyzed track found. Please upload and analyze first.");
    return;
  }

  const sessionId = window.lastSessionId || "";
  if (!sessionId) {
    alert("No active session found. Please upload and analyze first.");
    return;
  }

  const profileInput = document.getElementById("profile-input");
  const profile = profileInput?.value || "";

  const analysis = document.getElementById("analysisOutput")?.innerText || "";
  const feedback = document.getElementById("gptResponse")?.innerText || "";

  outputBox.classList.remove("hidden");
  const thinkingEl = document.createElement("p");
  thinkingEl.className = "mt-4 italic text-pink-400 text-opacity-80 animate-pulse";
  thinkingEl.textContent = "Thinking...";
  outputBox.appendChild(thinkingEl);

  // Build request payload conditionally including ref_analysis_data only if defined
  const requestBody = {
    analysis_text: analysis,
    feedback_text: feedback,
    user_question: question,
    session_id: sessionId,
    track_id: trackId,
    feedback_profile: profile,
    followup_group: followupGroupIndex,
  };

  if (typeof refTrackAnalysisData !== "undefined" && refTrackAnalysisData !== null) {
    requestBody.ref_analysis_data = refTrackAnalysisData;
  }

  try {
    const res = await fetch("/chat/ask-followup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });

    if (!res.ok) {
      throw new Error(`Server error: ${res.status} ${res.statusText}`);
    }

    const data = await res.json();
const answer = data.answer;

if (data.summary_created) {
  showInfoToast("💡 Internal summary created to keep conversations concise.");
}

thinkingEl.classList.remove("animate-pulse");
thinkingEl.innerHTML = `<span class="text-blue-400 text-lg">➤</span>`;

// Create safe Q paragraph
    const questionP = document.createElement("p");
    const strongQ = document.createElement("strong");
    strongQ.textContent = "Q:";
    questionP.appendChild(strongQ);
    questionP.appendChild(document.createTextNode(" " + question));
    outputBox.appendChild(questionP);

    // Create div for formatted answer
    const answerDiv = document.createElement("div");
    answerDiv.innerHTML = marked.parse(answer);
    outputBox.appendChild(answerDiv);

    // *** SHOW THE MANUAL SUMMARIZE BUTTON HERE IF HIDDEN ***
const manualSummarizeBtn = document.getElementById("manualSummarizeBtn");
if (manualSummarizeBtn.style.display === "none") {
  manualSummarizeBtn.style.display = "inline-block";  // or "block"
}

    // Track current thread
    followupThread.push({ question, answer });

    // Save to localStorage history
    try {
      const raw = localStorage.getItem("zoundzcope_history") || "[]";
      const history = JSON.parse(raw);
      if (history.length > 0) {
        if (!Array.isArray(history[0].followup)) {
          history[0].followup = history[0].followup ? [history[0].followup] : [];
        }
        history[0].followup.push(`<p><strong>Q:</strong> ${question}<br><strong>A:</strong> ${answer}</p>`);
        localStorage.setItem("zoundzcope_history", JSON.stringify(history));
      }
    } catch (err) {
      console.error("❌ Failed to store follow-up in history:", err);
    }

    // Check if it's time to summarize
    if (followupThread.length >= 4) {
      followupGroupIndex++;
      followupThread = [];  // No auto-summarize, just reset
    }

    // Clear input
    questionInput.value = "";
    localStorage.setItem("zoundzcope_last_followup", outputBox.innerHTML);

    // ERST JETZT den Button zeigen:
    showSummarizeButton();

  } catch (err) {
    console.error("❌ Follow-up failed:", err);
    outputBox.innerHTML += `<p class='text-red-400'>Something went wrong: ${err.message}</p>`;
  }
});


// ==========================================================
// 🧠 Summarize Last 4 Follow-Ups
// ==========================================================
async function summarizeFollowupThread() {
  try {
    const sessionId = window.lastSessionId || "";
    const trackId = window.lastTrackId || "";

    if (!sessionId || !trackId) {
      alert("No analyzed session or track found. Please upload and analyze first.");
      return;
    }

    const groupToSummarize = followupThread.length === 0 ? Math.max(followupGroupIndex - 1, 0) : followupGroupIndex;

    console.log("Summarizing follow-up thread for session:", sessionId, "track:", trackId, "group:", groupToSummarize);

    const res = await fetch("/chat/summarize-thread", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        track_id: trackId,
        followup_group: groupToSummarize
      })
    });

    if (!res.ok) {
      throw new Error(`Server error: ${res.status} ${res.statusText}`);
    }

    const data = await res.json();
    const summary = data.summary;

    if (!summary) {
      console.warn("No summary returned from backend");
      return;
    }

    const htmlSummary = marked.parse(summary);

    const summaryEl = document.createElement("div");
    summaryEl.className = "bg-white/10 text-white/90 p-4 rounded-lg mt-4";
    summaryEl.innerHTML = `
      <p class="text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 font-bold text-lg mb-2">
        Thread Summary
      </p>
      <div class="text-white text-base leading-relaxed">
        ${htmlSummary}
      </div>
    `;

    document.getElementById("aiFollowupResponse").appendChild(summaryEl);

    // Optionally save summary in localStorage
    localStorage.setItem("zoundzcope_last_followup_summary", summaryEl.outerHTML);

  } catch (err) {
    console.error("❌ Failed to summarize follow-up thread:", err);
  }
}


// ==========================================================
// Manual Summarizer
// ==========================================================
document.getElementById("manualSummarizeBtn").addEventListener("click", async () => {
  const button = document.getElementById("manualSummarizeBtn");

  if (followupGroupIndex === lastManualSummaryGroup) {
    alert("This group has already been manually summarized.");
    return;
  }

  button.classList.add("pulsing");

  try {
    const trackIdToUse = window.lastTrackId || document.getElementById("track-select")?.value;
    if (!trackIdToUse) {
      alert("Please select or analyze a track first.");
      button.classList.remove("pulsing");
      return;
    }

    const res = await fetch("/chat/summarize-thread", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: document.getElementById("session_id").value,
        track_id: trackIdToUse,
        followup_group: followupGroupIndex
      })
    });

    if (!res.ok) {
      throw new Error(`Server error: ${res.status} ${res.statusText}`);
    }

    const data = await res.json();
    const summary = data.summary;

    const htmlSummary = marked.parse(summary);

    const outputBox = document.getElementById("aiFollowupResponse");

    // Append summary block in the main Q&A container
    const summaryEl = document.createElement("div");
    summaryEl.className = "summary-block bg-white/10 text-white/90 p-4 rounded-lg mt-4";
    summaryEl.innerHTML = `
      <p class="text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 font-bold text-lg mb-2">
        Thread Summary
      </p>
      <div class="text-white text-base leading-relaxed">
        ${htmlSummary}
      </div>
    `;
    outputBox.appendChild(summaryEl);

    // Optional: show a separate summary container if you want (or remove this part)
    /*
    const summaryContainer = document.getElementById("aiSummaryResponse");
    summaryContainer.classList.remove("hidden");
    summaryContainer.appendChild(summaryEl);
    */

    localStorage.setItem("zoundzcope_last_followup_summary", summaryEl.outerHTML);

    lastManualSummaryGroup = followupGroupIndex;

    // Optionally reset or advance thread state here:
    followupGroupIndex++;
    followupThread = [];

  } catch (err) {
    console.error("❌ Failed to summarize follow-up thread:", err);
  } finally {
    button.classList.remove("pulsing");
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
    "Should I apply multiband compression on the drum bus?",
    "Does this mix need subtractive EQ in the low-mids?"
  ],
  mastering: [
    "Is this mix ready for mastering or should I adjust it first?",
    "Which plugin chain works best for transparent mastering?",
    "Do I need to rebalance the stereo field before mastering?",
    "Would pre-EQ help tame the harshness before limiting?",
    "How should I handle low-end phase coherence in mastering?"
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
  pop: [
    "How can I make the vocal sound more polished?",
    "Should I layer backing vocals like in mainstream pop tracks?",
    "Which saturation plugin gives a warm pop sheen?",
    "Does this need parallel compression on the vocal bus?",
    "How do I keep the low end clean in a dense pop mix?"
  ],
  rock: [
    "How does the guitar layer compare to Foo Fighters’ mixes?",
    "Should I try an API-style EQ on the drums?",
    "How can I make the bass more audible without clashing with the kick?",
    "Does this need tape saturation on the mix bus?",
    "Is the vocal presence comparable to Green Day’s tracks?"
  ],
  hiphop: [
    "Are the vocals sitting right like in Kendrick Lamar’s mixes?",
    "What plugin is best to glue the drums?",
    "Should I try parallel compression on the rap vocal?",
    "How do I add analog warmth to the beat?",
    "Would a CLA plugin chain help here?"
  ],
  indie: [
    "Should I go for a lo-fi or hi-fi mix character here?",
    "Would subtle tape saturation improve the vibe?",
    "Are the vocals too forward for this genre?",
    "How can I preserve dynamics while still sounding modern?",
    "Is the reverb tail too long for this intimate sound?"
  ],
  punk: [
    "Does the energy match early Ramones or Sex Pistols?",
    "Is the guitar tone too clean for this style?",
    "Would a Neve-style preamp plugin improve grit?",
    "Should I push the vocal compression harder?",
    "Is the rawness authentic or too harsh?"
  ],
  metal: [
    "Are the guitars tight enough for this subgenre?",
    "Should I scoop the mids on the rhythm guitars?",
    "How do I control harsh cymbals without dulling the mix?",
    "What’s the best way to fatten kick and bass together?",
    "Would a bus compressor help unify the low end?"
  ],
  jazz: [
    "Is this mix transparent enough for acoustic instruments?",
    "How do I retain natural room tone?",
    "Would light compression help or hurt dynamic feel?",
    "Are the cymbals too forward in the mix?",
    "How can I position piano, bass, and drums for clarity?"
  ],
  raggae: [
    "Is the groove tight like classic dub mixes?",
    "Should I add tape echo to the skank guitar?",
    "Does the bass have the right weight for reggae?",
    "How can I keep vocals present without overpowering the rhythm?",
    "What reverb would give a deep roots feel?"
  ],
  funk: [
    "Does the rhythm section have enough groove?",
    "How can I emphasize syncopation without clutter?",
    "Should I layer claps or tambourine for drive?",
    "Would analog-style compression add funkiness?",
    "Is the bass too clean or just right?"
  ],
  rnb: [
    "Is the vocal chain smooth enough for modern R&B?",
    "Would saturation or drive help the keys cut through?",
    "Should I tame the sibilance more?",
    "How do I balance lushness and clarity?",
    "Is this mix comparable to The Weeknd’s production?"
  ],
  soul: [
    "Is there enough warmth in the low-mids?",
    "How can I enhance the vocal emotion in the mix?",
    "Would plate reverb suit this vocal tone?",
    "Are the horns sitting well in the mix?",
    "How do I get that vintage soul glue?"
  ],
  country: [
    "Should I boost the acoustic guitar for clarity?",
    "How do I keep the vocal front and center?",
    "Is the reverb space natural enough?",
    "Would subtle compression enhance the storytelling?",
    "Is the kick too modern for classic country?"
  ],
  folk: [
    "Is the acoustic guitar resonating too much?",
    "Should I double-track the vocal for thickness?",
    "How do I preserve warmth without muddiness?",
    "Would analog tape plugins help here?",
    "Are the harmonies balanced correctly?"
  ],
  classical: [
    "Would referencing a Deutsche Grammophon master help dynamics?",
    "How do I preserve orchestral space while enhancing clarity?",
    "Is this reverb tail appropriate for the room size?",
    "Should I avoid compression on classical recordings?",
    "Would linear-phase EQ benefit this arrangement?"
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
    "Are the transients crisp enough on the snare?",
    "What could improve stereo image on the chorus?"
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

  let title = container.querySelector("p");
  let btnWrapper = container.querySelector(".grid");

  // If structure is missing, inject it
  if (!title || !btnWrapper) {
    container.innerHTML = `
      <p class="text-white/70 text-sm mb-1">Quick Follow-Up Questions:</p>
      <div class="grid grid-cols-2 gap-3"></div>
    `;
    title = container.querySelector("p");
    btnWrapper = container.querySelector(".grid");
  }

  btnWrapper.innerHTML = "";

  const uniqueQuestions = new Set([
    ...(predefinedFollowupQuestions[type] || []),
    ...(predefinedFollowupQuestions[genre] || []),
    ...(predefinedFollowupQuestions[profile] || [])
  ]);

  Array.from(uniqueQuestions).slice(0, 15).forEach((q) => {
    const btn = document.createElement("button");
    btn.textContent = q;

    btn.className = `
      quick-followup-button
      w-full
      px-4 py-2
      rounded-md
      bg-white/5
      text-white
      text-sm
      font-medium
      shadow-sm
      border border-white/10
      backdrop-blur-md
      transition-all duration-200
      hover:bg-white/10
      hover:scale-[1.01]
    `.trim();

    btn.style.fontSize = "0.825rem";

    btn.addEventListener("click", () => {
      document.getElementById("customQuestion").value = q;
      document.getElementById("askAIButton").click();
    });

    btnWrapper.appendChild(btn);
  });

  container.classList.toggle("hidden", btnWrapper.children.length === 0);
}


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

  // 1) Verstecke den Summarize-Button gleich zu Beginn der neuen Analyse:
  hideSummarizeButton();
  resetRMSDisplay();
  resetExportButton()

  // Quick Followup Buttons sofort ausblenden / leeren
  clearQuickFollowupButtons();

  const feedbackBox = document.getElementById("gptResponse");
if (feedbackBox) feedbackBox.innerHTML = "";

const followupResponseBox = document.getElementById("aiFollowupResponse");
if (followupResponseBox) followupResponseBox.innerHTML = "";

  // 🔁 Immediately reset old waveform to avoid showing it during wait
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

  // Clear follow-up and manual summary areas in the DOM
const followupContainer = document.getElementById("followupSection"); // or your actual ID for follow-up area
const manualSummaryContainer = document.getElementById("manualSummarySection"); // adjust as needed

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
  // Set genre (always from dropdown)
const selectedGenre = document.getElementById("genre-input").value;
formData.set("genre", selectedGenre);

// Set subgenre: prefer custom if filled
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

  // **NEW: append reference track file if any**
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

    // If your backend also sends reference track analysis data as part of the result, e.g.:
    refTrackAnalysisData = result.ref_analysis || null;  // <-- set it here

    if (response.ok) {

      const tracks = await loadSessionTracks(sessionId);
      console.log("Tracks loaded after upload:", tracks);
console.log("Setting window.lastTrackId to:", tracks[0]?.id);

      window.lastSessionId = sessionId;
window.lastTrackId = tracks[0]?.id || "";

// Sync hidden session_id input to keep manual summarizer in sync
const sessionIdInput = document.getElementById("session_id");
if (sessionIdInput) {
  sessionIdInput.value = sessionId;
}

// Reset follow-up state to avoid stale data after new session
followupThread = [];
followupGroupIndex = 0;
lastManualSummaryGroup = -1;  // or null if you prefer

console.log("Session and track set:", window.lastSessionId, window.lastTrackId);
console.log("Follow-up state reset");



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
      // Reference Track Analysis Rendering
if (refTrackAnalysisData) {
  const refContainer = document.createElement("div");
  refContainer.className = "mt-8 space-y-2 text-sm border-t border-white/10 pt-4";

  const ra = refTrackAnalysisData;

  function r(v) {
    return Number(v).toFixed(2);
  }

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
console.log("🎯 Received trackType:", trackType);

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


// After all bullets are appended:
loadReferenceWaveform();
document.getElementById("custom-ai-section")?.classList.remove("hidden");

      const exportBtn = document.getElementById("exportFeedbackBtn");
if (exportBtn && !exportBtn.dataset.listenerAdded) {
  exportBtn.addEventListener("click", async () => {
    console.log("Export button clicked");

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
        headers: {
          "Accept": "application/pdf"
        }
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

  exportBtn.dataset.listenerAdded = "true"; // mark listener added so you don’t add again
}


      const type = document.getElementById("type-input")?.value;
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

// ==========================================================
//  🎵 WaveSurfer
// ==========================================================

// Create new WaveSurfer instance globally
window.wavesurfer = WaveSurfer.create({
  container: '#waveform',
  waveColor: '#a0a0a0',
  progressColor: '#2196f3',
  height: 100,
  responsive: true
});

// Add cache-busting timestamp to avoid browser cache issues
const trackUrl = result.track_path + `?t=${Date.now()}`;
window.wavesurfer.load(trackUrl);

focusedWaveform = "main";
console.log("Focused waveform set to main (upload handler)");

document.getElementById("waveform").addEventListener("click", () => {
  const time = window.wavesurfer.getCurrentTime();
  console.log("🖱️ Clicked! Current time:", time);
  updateRMSDisplayAtTime(time);
});

// 🔗 Load the corresponding RMS chunk file
console.log("🔗 Trying to load RMS file:", result.rms_path);
fetch(result.rms_path)
  .then(response => response.json())
  .then(data => {
    rmsChunks = data;
    console.log("✅ RMS chunks loaded:", rmsChunks.length);
    console.log("🧪 First few RMS values:", rmsChunks.slice(0, 5));

  })
  .catch(err => {
    console.error("❌ Failed to load RMS chunks", err);
  });

window.wavesurfer.on('ready', () => {
  console.log("✅ New track loaded into WaveSurfer");

  const rmsDisplay = document.getElementById("rms-display");

  // ✅ Now that waveform + RMS are ready, show initial RMS value
  if (rmsChunks.length > 0) {
    updateRMSDisplayAtTime(0); // Start at beginning
  }

  // ✅ Optional: show the RMS display if it's hidden
  if (rmsDisplay) {
    rmsDisplay.classList.remove("hidden");
  }
});


// ✅ Utility: Display RMS based on time
function updateRMSDisplayAtTime(time) {
  const index = Math.floor(time / chunkDuration);
  const rmsValue = rmsChunks[index];
  const display = document.getElementById("rms-display");

  console.log("🧠 Time:", time, "→ Chunk Index:", index, "→ RMS:", rmsValue); // ✅ DIAGNOSTIC

  if (display && rmsValue !== undefined) {
    display.innerText = `Current RMS: ${rmsValue.toFixed(2)} dB`;
  } else if (display) {
    display.innerText = `Current RMS: --`;
  }
}

// ✅ Playback listener — update live
window.wavesurfer.on("audioprocess", () => {
  if (rmsChunks.length === 0) return;
  const time = window.wavesurfer.getCurrentTime();
  updateRMSDisplayAtTime(time);
});

// ✅ Seek/click listener — update when user clicks/scrubs
window.wavesurfer.on("seek", (progress) => {
  if (rmsChunks.length === 0) return;
  const duration = window.wavesurfer.getDuration();
  const time = duration * progress;
  updateRMSDisplayAtTime(time);
});


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
// ✅ Add this block after the form handler
window.addEventListener("DOMContentLoaded", () => {
  window.wavesurfer?.on("interaction", (e) => {
    const waveformContainer = window.wavesurfer.container;
    if (!waveformContainer) return;

    const boundingBox = waveformContainer.getBoundingClientRect();
    const percent = (e.clientX - boundingBox.left) / boundingBox.width;
    const duration = window.wavesurfer.getDuration();
    const time = percent * duration;

    const index = Math.floor(time / chunkDuration);
    const rmsValue = rmsChunks[index];

    const display = document.getElementById("rms-display");
    console.log(`🖱️ Clicked time: ${time.toFixed(2)}s → chunk ${index} → RMS: ${rmsValue}`);
    console.log("📊 rmsChunks length:", rmsChunks.length);

    if (display && rmsValue !== undefined) {
      display.innerText = `RMS at ${time.toFixed(2)}s: ${rmsValue.toFixed(2)} dB`;
    } else if (display) {
      display.innerText = `No RMS data at ${time.toFixed(2)}s`;
    }
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const mainWaveformContainer = document.getElementById("waveform");
  const refWaveformContainer = document.getElementById("ref-waveform");

  async function toggleWaveformPlayPause(wavesurferToToggle, otherWavesurfer, name) {
  if (!wavesurferToToggle) {
    console.warn(`${name} wavesurfer instance not ready`);
    return;
  }
  if (wavesurferToToggle.isPlaying()) {
    wavesurferToToggle.pause();
    console.log(`${name} waveform paused`);
  } else {
    if (otherWavesurfer && otherWavesurfer.isPlaying()) {
      otherWavesurfer.pause();
      console.log(`Other waveform paused before playing ${name}`);
    }
    try {
      await wavesurferToToggle.play();
      console.log(`${name} waveform playing`);
    } catch (e) {
      console.warn(`${name} play() interrupted:`, e);
    }
  }
}

  if (mainWaveformContainer) {
    mainWaveformContainer.addEventListener("click", () => {
      focusedWaveform = "main";
      toggleWaveformPlayPause(window.wavesurfer, refWavesurfer, "Main");
    });
  }

  if (refWaveformContainer) {
    refWaveformContainer.addEventListener("click", () => {
  focusedWaveform = "ref";
  console.log("Ref waveform clicked — focusedWaveform set to:", focusedWaveform);
  if (refClickCooldown) {
    console.log("Ignoring click - cooldown active");
    return;
  }
  refClickCooldown = true;
  setTimeout(() => {
    refClickCooldown = false;
  }, 300); // 300ms cooldown - adjust if needed

      focusedWaveform = "ref";
      if (!refWaveformReady) {
        console.warn("Reference waveform not ready yet");
        return;
      }
      toggleWaveformPlayPause(refWavesurfer, window.wavesurfer, "Reference");
    });
  }
});


// Your existing loadReferenceWaveform function here
function loadReferenceWaveform() {
  const refFileInput = document.getElementById("ref-file-upload");
  const refWaveformContainer = document.getElementById("ref-waveform");
  const refWrapper = document.getElementById("ref-waveform-wrapper");

  if (!refFileInput || !refWaveformContainer || !refWrapper) return;

  if (refFileInput.files.length === 0) {
    if (refWavesurfer) {
      refWavesurfer.destroy();
      refWavesurfer = null;
    }
    // Hide the entire wrapper when no ref file
    refWrapper.style.display = "none";
    refWaveformContainer.innerHTML = "";
    return;
  }

  // Show the wrapper when loading a ref track
  refWrapper.style.display = "inline-block"; // or "block"

  const file = refFileInput.files[0];
  const fileURL = URL.createObjectURL(file);

  if (refWavesurfer) refWavesurfer.destroy();

  refWavesurfer = WaveSurfer.create({
    container: "#ref-waveform",
    waveColor: "#888",
    progressColor: "#6b46c1",
    height: 100,
    responsive: true,
  });

  refWaveformReady = false;

  refWavesurfer.load(fileURL);

  refWavesurfer.on("ready", () => {
    console.log("✅ Reference track waveform loaded");
    refWaveformReady = true;
    focusedWaveform = "ref";
  });

  // Pause main waveform if playing when ref starts playing
  refWavesurfer.on("play", () => {
    if (window.wavesurfer && window.wavesurfer.isPlaying()) {
      window.wavesurfer.pause();
    }
    if (refWaveformContainer) {
      refWaveformContainer.classList.add("waveform-playing");
    }
  });

  refWavesurfer.on("pause", () => {
    if (refWaveformContainer) {
      refWaveformContainer.classList.remove("waveform-playing");
    }
  });

  refWavesurfer.on("finish", () => {
    if (refWaveformContainer) {
      refWaveformContainer.classList.remove("waveform-playing");
    }
  });
}



document.addEventListener("keydown", (e) => {
  if (e.code === "Space" && !e.repeat) {
    const active = document.activeElement;
    const isTyping =
      active &&
      (
        active.tagName === "INPUT" ||
        active.tagName === "TEXTAREA" ||
        active.isContentEditable
      );

    if (isTyping) {
      // User is typing — do NOT trigger play/pause or prevent default
      return;  // <--- return immediately here!
    }

    console.log("Spacebar pressed — focusedWaveform is:", focusedWaveform);

    if (focusedWaveform === "ref" && refWavesurfer) {
      console.log("Attempting to toggle ref waveform");
      if (refWavesurfer.isPlaying()) {
        refWavesurfer.pause();
        console.log("Ref waveform paused");
      } else {
        refWavesurfer.play();
        console.log("Ref waveform playing");
      }
    }
    // Only prevent default and toggle playback if NOT typing
    e.preventDefault();

    if (focusedWaveform === "main" && window.wavesurfer) {
      if (window.wavesurfer.isPlaying()) {
        window.wavesurfer.pause();
      } else {
        if (refWavesurfer && refWavesurfer.isPlaying()) {
          refWavesurfer.pause();
        }
        window.wavesurfer.play();
      }
    } else if (focusedWaveform === "ref" && refWavesurfer) {
      if (refWavesurfer.isPlaying()) {
        refWavesurfer.pause();
      } else {
        if (window.wavesurfer && window.wavesurfer.isPlaying()) {
          window.wavesurfer.pause();
        }
        refWavesurfer.play();
      }
    }
  }
});


// 1) Click listeners to update focusedWaveform:
document.addEventListener("DOMContentLoaded", () => {
  const mainWaveformContainer = document.getElementById("waveform");
  const refWaveformContainer = document.getElementById("ref-waveform");

  if (mainWaveformContainer) {
    mainWaveformContainer.addEventListener("click", () => {
      focusedWaveform = "main";
      console.log("Focused waveform set to main");
    });
  }

  if (refWaveformContainer) {
    refWaveformContainer.addEventListener("click", () => {
      focusedWaveform = "ref";
      console.log("Focused waveform set to reference (clicked)");

      if (refWavesurfer) {
        if (refWavesurfer.isPlaying()) {
          refWavesurfer.pause();
          console.log("Reference waveform paused");
        } else {
          refWavesurfer.play();
          console.log("Reference waveform playing");
        }
      } else {
        console.warn("refWavesurfer is not initialized yet");
      }
    });
  }
});


// 2) Global spacebar listener to toggle play/pause on focused waveform:
document.addEventListener("keydown", (e) => {
  if (e.code === "Space" && !e.repeat) {
    const active = document.activeElement;
    const isTyping =
      active &&
      (
        active.tagName === "INPUT" ||
        active.tagName === "TEXTAREA" ||
        active.isContentEditable
      );

    if (isTyping) {
      // Allow spacebar to work normally in text inputs
      return;
    }

    e.preventDefault();

    let wavesurferToControl = null;

    if (focusedWaveform === "main") {
      wavesurferToControl = window.wavesurfer;
      if (refWavesurfer && refWavesurfer.isPlaying()) refWavesurfer.pause();
    } else if (focusedWaveform === "ref") {
      wavesurferToControl = refWavesurfer;
      if (window.wavesurfer && window.wavesurfer.isPlaying()) window.wavesurfer.pause();
    }

    if (!wavesurferToControl) {
      console.warn("No wavesurfer to control!");
      return;
    }

    if (wavesurferToControl.isPlaying()) {
      wavesurferToControl.pause();
      console.log(`${focusedWaveform} paused`);
    } else {
      wavesurferToControl.play();
      console.log(`${focusedWaveform} playing`);

      setTimeout(() => {
        console.log(`${focusedWaveform} isPlaying after play():`, wavesurferToControl.isPlaying());
      }, 100);
    }
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


function toggleFollowup(id) {
  const el = document.getElementById(id);
  const btn = el?.previousElementSibling;
  const parentBox = el?.closest(".feedback-box");

  if (!el || !btn || !parentBox || parentBox.dataset.expanded !== "true") return;

  const isHidden = el.classList.contains("hidden");

  // Toggle visibility
  el.classList.toggle("hidden");
  btn.textContent = isHidden ? "Hide Follow-up" : "Show Follow-up";

  // Recalculate height correctly:
  // Step 1: Temporarily clear the height so browser can reflow the real scrollHeight
  parentBox.style.height = "auto";

  // Step 2: Wait a tick, then measure and apply new scrollHeight
  requestAnimationFrame(() => {
    const newHeight = parentBox.scrollHeight;
    parentBox.style.height = newHeight + "px";
  });
}


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
box.className = "feedback-box relative bg-white/5 p-4 rounded-lg shadow-md space-y-2 border border-white/10";




// Start in collapsed state
box.style.height = "108px";
box.classList.add("collapsed");
box.dataset.expanded = "false"; // custom flag

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
        <p class="${subheadingText.toLowerCase().includes('master') ? 'text-blue-400' : 'text-pink-400'} text-lg font-bold">
          ${subheadingText}
        </p>
        <span class="text-white font-semibold text-sm">${trackName}</span>
      </div>
      <span class="text-white/50 text-xs">${dateStr}</span>
    </div>
  `;

  // Build the toggle and follow-up sections
  const toggleAreaHTML = `
  <div class="fold-toggle-area text-white/90 text-sm space-y-2 cursor-pointer">
    ${headingHTML}
    ${feedbackHTML}
  </div>
`;

const followupSectionHTML = `
  <div class="pt-2">
    ${followupToggleHTML}
    ${followupHTML}
  </div>
`;

box.innerHTML = toggleAreaHTML + followupSectionHTML;


  // Attach the toggle only to the upper area
  // Attach toggle
const toggleArea = box.querySelector(".fold-toggle-area");

toggleArea.addEventListener("click", () => {
  const expanded = box.dataset.expanded === "true";

  if (expanded) {
    box.style.height = "108px";
    box.dataset.expanded = "false";
    box.classList.remove("expanded");
    box.classList.add("collapsed"); // ✅ re-apply collapsed class
  } else {
    box.style.height = box.scrollHeight + "px";
    box.dataset.expanded = "true";
    box.classList.remove("collapsed"); // ✅ remove it when open
    box.classList.add("expanded");
  }
});

  container.appendChild(box);
});


  panel.classList.remove("hidden");
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





function showInfoToast(message) {
  const toast = document.createElement("div");
  toast.textContent = message;
  toast.className = `
    fixed bottom-5 right-5 bg-blue-600 text-white px-4 py-2 rounded shadow-lg
    opacity-90 z-50 transition-opacity duration-500
  `;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => document.body.removeChild(toast), 500);
  }, 3000);
}


// RAG Tabs logic
const tabDocs = document.getElementById('tab-docs');
const tabTut = document.getElementById('tab-tut');
const docsContainer = document.getElementById('docs-chat-container');
const tutContainer = document.getElementById('tut-chat-container');

function activateTab(tabToActivate) {
  if (tabToActivate === 'docs') {
    tabDocs.classList.add('border-pink-500', 'font-semibold');
    tabDocs.classList.remove('border-transparent');
    tabTut.classList.remove('border-pink-500', 'font-semibold');
    tabTut.classList.add('border-transparent');
    docsContainer.classList.remove('hidden');
    tutContainer.classList.add('hidden');
  } else {
    tabTut.classList.add('border-pink-500', 'font-semibold');
    tabTut.classList.remove('border-transparent');
    tabDocs.classList.remove('border-pink-500', 'font-semibold');
    tabDocs.classList.add('border-transparent');
    tutContainer.classList.remove('hidden');
    docsContainer.classList.add('hidden');
  }
}

tabDocs.addEventListener('click', () => activateTab('docs'));
tabTut.addEventListener('click', () => activateTab('tut'));

// Helper to append messages to chat windows
function appendMessage(container, sender, text) {
  const div = document.createElement('div');
  div.className = `rag-message ${sender === 'user' ? 'text-pink-400 text-right' : 'text-blue-400 text-left'}`;
  if (sender === 'ai') {
    div.innerHTML = marked.parse(text);
  } else {
    div.textContent = text;
  }
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

// Query backend RAG API
async function queryRagAPI(endpoint, question, history) {
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ question, history })
    });
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    const data = await response.json();
    return data.answer;
  } catch (err) {
    return `Error: ${err.message}`;
  }
}

// Docs Assistant elements
const docsForm = document.getElementById('docs-chat-form');
const docsInput = document.getElementById('docs-chat-input');
const docsChat = document.getElementById('docs-chat');

// Tutorial Assistant elements
const tutForm = document.getElementById('tut-chat-form');
const tutInput = document.getElementById('tut-chat-input');
const tutChat = document.getElementById('tut-chat');


// Docs Assistant form handling
docsForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const question = docsInput.value.trim();
  if (!question) return;

  appendMessage(docsChat, 'user', `You: ${question}`);
  docsInput.value = '';

  appendMessage(docsChat, 'ai', 'AI is thinking...');

  const history = getChatHistory(docsChat);
  const answer = await queryRagAPI('/chat/rag_docs', question, history);

  // Replace placeholder
  const thinkingMsg = [...docsChat.querySelectorAll('.rag-message')]
    .reverse()
    .find(msg => msg.textContent.includes('AI is thinking'));

  if (thinkingMsg) {
    thinkingMsg.textContent = 'AI response:';
    const answerDiv = document.createElement('div');
    answerDiv.className = 'rag-message text-blue-400 text-left';
    answerDiv.innerHTML = marked.parse(answer);
    docsChat.appendChild(answerDiv);
  } else {
    appendMessage(docsChat, 'ai', answer);
  }

  adjustChatHeight(docsChat);
});

// Tutorial Assistant form handling
tutForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const question = tutInput.value.trim();
  if (!question) return;

  appendMessage(tutChat, 'user', `You: ${question}`);
  tutInput.value = '';

  appendMessage(tutChat, 'ai', 'AI is thinking...');

  // 🧠 Extract chat history from previous messages
  const history = getChatHistory(tutChat);

  // 📡 Send current question + history
  const answer = await queryRagAPI('/chat/rag_tut', question, history);

  // Replace the "AI is thinking..." message with the real response
  const thinkingMsg = [...tutChat.querySelectorAll('.rag-message')]
    .reverse()
    .find(msg => msg.textContent.includes('AI is thinking'));

  if (thinkingMsg) {
    thinkingMsg.textContent = 'AI response:';
    const answerDiv = document.createElement('div');
    answerDiv.className = 'rag-message text-blue-400 text-left';
    answerDiv.innerHTML = marked.parse(answer);
    tutChat.appendChild(answerDiv);
  } else {
    appendMessage(tutChat, 'ai', answer);
  }

  adjustChatHeight(tutChat);
});




function adjustChatHeight(chatDiv) {
  const minHeight = 240; // px (15rem)
  const maxHeight = 480; // px

  // Reset height to auto to get scrollHeight
  chatDiv.style.height = 'auto';

  const contentHeight = chatDiv.scrollHeight;

  const newHeight = Math.min(Math.max(contentHeight, minHeight), maxHeight);

  chatDiv.style.height = newHeight + 'px';

  chatDiv.style.overflowY = contentHeight > maxHeight ? 'auto' : 'hidden';
}

const toggleRagBtn = document.getElementById('toggle-rag-btn');
const ragContainer = document.getElementById('rag-container');

toggleRagBtn.addEventListener('click', () => {
  if (ragContainer.classList.contains('hidden')) {
    ragContainer.classList.remove('hidden');
    toggleRagBtn.innerHTML = 'Close Assistant';

    // Smooth scroll to the RAG section when opened
    document.getElementById('rag-assistants').scrollIntoView({ behavior: 'smooth', block: 'start' });
  } else {
    ragContainer.classList.add('hidden');
    toggleRagBtn.innerHTML = 'AI-powered<br>Docs & Tutorials';

    // Smooth scroll to top of page when closed
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
});

function getChatHistory(container) {
  const messages = [...container.querySelectorAll('.rag-message')];
  const history = [];

  for (let i = 0; i < messages.length - 1; i++) {
    const userMsg = messages[i];
    const aiMsg = messages[i + 1];

    if (userMsg.classList.contains('text-pink-400') && aiMsg.classList.contains('text-blue-400')) {
      history.push({
        question: userMsg.textContent.replace(/^You:\s*/, ''),
        answer: aiMsg.innerText
      });
      i++; // skip next since it's paired
    }
  }

  return history;
}
