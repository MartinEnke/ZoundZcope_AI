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