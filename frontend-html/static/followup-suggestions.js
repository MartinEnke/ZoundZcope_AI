// followup-suggestions.js

// ==========================================================
// 💡 Smart Predefined Follow-Up Buttons (Based on Context)
// ==========================================================
const predefinedFollowupQuestions = {
  mixdown: [
    "Which frequency range feels too dominant or lacking overall?",
    "Does the stereo width feel balanced across the spectrum?",
    "How can I improve dynamic range without losing energy?",
    "Is my loudness appropriate for a mastering-ready track?",
    "Does the low end feel too heavy, muddy, or underpowered?"
  ],
  mastering: [
    "Is this mix ready for mastering or should I adjust it first?",
    "Which plugin chain works best for transparent mastering?",
    "Do I need to rebalance the stereo field before mastering?",
    "Would pre-EQ help tame the harshness before limiting?",
    "How should I handle low-end phase coherence in mastering?"
  ],
  master: [
    "Would this track match the loudness of Daft Punk",
    "Which limiter plugin gives transparent results for this style?",
    "Is a dynamic EQ needed to tame harshness here?",
    "Could widening the stereo field improve spatial depth?",
    "Does this master need a low-shelf boost below 80Hz?"
  ],
  electronic: [
    "How can I add more movement or modulation in the midrange?",
    "Is the sidechain compression reacting musically and not over-pumping?",
    "Do the transients feel snappy and well-shaped for this genre?",
    "Is the sub-bass well-controlled and sitting cleanly in the mix?",
    "Does the dynamic range support both energy and impact?",
    "Are the highs crisp and present without becoming harsh?",
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

  let questions = Array.from(uniqueQuestions);
if (questions.length % 2 !== 0) {
  questions = questions.slice(0, questions.length - 1);
}

questions.forEach((q) => {
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


// ==========================================================
// 🌐 Global Exposure for External Access
// ----------------------------------------------------------
// This section attaches functions to a global namespace
// so they can be accessed from other scripts or HTML.
// This avoids polluting the global scope directly.
// ==========================================================

window.ZoundZcope = window.ZoundZcope || {};  // Create namespace if not already defined
window.ZoundZcope.loadQuickFollowupButtons = loadQuickFollowupButtons;