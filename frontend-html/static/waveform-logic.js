// waveform-logic.js

// ========== 🔧 Style ========== //
const style = document.createElement("style");
style.textContent = `
  .metal-round-button {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: linear-gradient(to bottom, #5a5a5a, #2c2c2c);
    color: white;
    font-size: 20px;
    font-weight: bold;
    border: 1px solid #666;
    box-shadow: inset 0 1px 0 #888, 0 3px 6px rgba(255,255,255,0.3);
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    padding: 0;
  }
  .metal-round-button:hover {
    background: linear-gradient(to bottom, #777, #333);
    transform: translateY(-1px);
    box-shadow: inset 0 1px 1px #aaa, 0 4px 8px rgba(255,255,255,0.4);
  }
  .metal-round-button:active {
    background: #111;
    box-shadow: inset 0 2px 4px rgba(255,255,255,0.7);
    transform: translateY(1px);
  }
`;
document.head.appendChild(style);

// ========== 🎧 Global ========== //
let rmsChunks = [];
const chunkDuration = 0.5;
let refWavesurfer = null;
let refWaveformReady = false;
let focusedWaveform = "main";
let refClickCooldown = false;

// ========== 🧠 Helpers ========== //
function updateRMSDisplayAtTime(time) {
  const index = Math.floor(time / chunkDuration);
  const rmsValue = rmsChunks[index];
  const display = document.getElementById("rms-display");

  if (display && rmsValue !== undefined) {
    display.innerText = `Current RMS: ${rmsValue.toFixed(2)} dB`;
  } else if (display) {
    display.innerText = `Current RMS: --`;
  }
}

// ========== 🎵 Init Main Waveform ========== //
function initMainWaveform(result) {
  const container = document.getElementById("waveform");
  if (!container || !result?.track_path) {
    console.warn("⛔ No waveform container or track path found.");
    return;
  }

  console.log("🎧 Initializing waveform with:", result.track_path);

  container.innerHTML = "";
  container.classList.remove("waveform-playing");

  if (window.wavesurfer) {
    window.wavesurfer.destroy();
  }

  window.wavesurfer = WaveSurfer.create({
    container: '#waveform',
    waveColor: '#a0a0a0',
    progressColor: '#2196f3',
    height: 100,
    responsive: true
  });

  const url = result.track_path + `?t=${Date.now()}`;
  window.wavesurfer.load(url);

  focusedWaveform = "main";

  fetch(result.rms_path)
    .then((res) => res.json())
    .then((data) => {
      rmsChunks = data;
      updateRMSDisplayAtTime(0);
      const rmsDisplay = document.getElementById("rms-display");
      if (rmsDisplay) rmsDisplay.classList.remove("hidden");
    })
    .catch((err) => {
      console.error("❌ Failed to load RMS:", err);
    });

  window.wavesurfer.on("audioprocess", () => {
    updateRMSDisplayAtTime(window.wavesurfer.getCurrentTime());
  });

  window.wavesurfer.on("seek", (progress) => {
    const duration = window.wavesurfer.getDuration();
    updateRMSDisplayAtTime(progress * duration);
  });

  window.wavesurfer.on("finish", () => {
    container.classList.remove("waveform-playing");
  });
}

// ========== 🎵 Init Ref Waveform ========== //
function loadReferenceWaveform() {
  const refInput = document.getElementById("ref-file-upload");
  const refContainer = document.getElementById("ref-waveform");
  const wrapper = document.getElementById("ref-waveform-wrapper");

  if (!refInput || !refContainer || !wrapper) return;

  if (refInput.files.length === 0) {
    if (refWavesurfer) refWavesurfer.destroy();
    refContainer.innerHTML = "";
    refWavesurfer = null;
    wrapper.style.display = "none";
    return;
  }

  wrapper.style.display = "inline-block";
  const fileURL = URL.createObjectURL(refInput.files[0]);

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
    refWaveformReady = true;
    focusedWaveform = "ref";
  });

  refWavesurfer.on("play", () => {
    if (window.wavesurfer?.isPlaying()) window.wavesurfer.pause();
    refContainer.classList.add("waveform-playing");
  });

  refWavesurfer.on("pause", () => refContainer.classList.remove("waveform-playing"));
  refWavesurfer.on("finish", () => refContainer.classList.remove("waveform-playing"));
}

// ========== 🖱️ Click Handling ========== //
document.addEventListener("DOMContentLoaded", () => {
  const main = document.getElementById("waveform");
  const ref = document.getElementById("ref-waveform");

  async function togglePlayPause(target, other, label) {
    if (!target) return;
    if (target.isPlaying()) {
      target.pause();
    } else {
      if (other?.isPlaying()) other.pause();
      await target.play();
    }
    console.log(`${label} waveform toggled`);
  }

  if (main) {
    main.addEventListener("click", () => {
      focusedWaveform = "main";
      if (!window.wavesurfer.isPlaying()) {
        window.wavesurfer.play();
        if (refWavesurfer?.isPlaying()) refWavesurfer.pause();
        console.log("▶️ Main waveform started after click");
      }
    });
  }

  if (ref) {
    ref.addEventListener("click", () => {
      if (refClickCooldown) return;
      refClickCooldown = true;
      setTimeout(() => (refClickCooldown = false), 300);

      focusedWaveform = "ref";
      if (!refWaveformReady) return;

      if (!refWavesurfer.isPlaying()) {
        refWavesurfer.play();
        if (window.wavesurfer?.isPlaying()) window.wavesurfer.pause();
        console.log("▶️ Ref waveform started after click");
      }
    });
  }
});

// ========== ⌨️ Spacebar Handling ========== //
document.addEventListener("keydown", (e) => {
  if (e.code !== "Space" || e.repeat) return;

  const tag = e.target.tagName;
  if (["INPUT", "TEXTAREA"].includes(tag) || e.target.isContentEditable) return;

  e.preventDefault();
  const active = focusedWaveform === "main" ? window.wavesurfer : refWavesurfer;
  const other = focusedWaveform === "main" ? refWavesurfer : window.wavesurfer;

  if (!active) return;

  if (active.isPlaying()) {
    active.pause();
  } else {
    if (other?.isPlaying()) other.pause();
    active.play();
  }
});

export { initMainWaveform, loadReferenceWaveform };
