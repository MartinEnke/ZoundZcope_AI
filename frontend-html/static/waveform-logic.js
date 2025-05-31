// Inject metallic style dynamically
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


document.addEventListener("DOMContentLoaded", () => {
  const chunkDuration = 0.5;
  let rmsChunks = [];

  // Load RMS data
  fetch('/static/analysis/sample_rms.json')
    .then((res) => res.json())
    .then((data) => {
      rmsChunks = data;
      console.log("✅ RMS data loaded:", rmsChunks.length);
    })
    .catch((err) => {
      console.error("❌ Failed to load RMS data", err);
    });

  const trackPath = window.trackPath || "";
  if (!trackPath || trackPath.includes("{{")) {
    console.warn("⚠️ No valid trackPath found:", trackPath);
    return;
  }

  console.log("🎧 Loading track:", trackPath);

  // Create WaveSurfer instance
  window.wavesurfer = WaveSurfer.create({
    container: '#waveform',
    waveColor: '#a0a0a0',
    progressColor: '#2196f3',
    height: 100,
    responsive: true
  });

  window.wavesurfer.load(encodeURI(trackPath));

  window.wavesurfer.on("ready", () => {
    console.log("✅ WaveSurfer is ready and track is loaded");

  });

  // RMS display on waveform click
  window.wavesurfer.container.addEventListener("click", (e) => {
    const box = window.wavesurfer.container.getBoundingClientRect();
    const percent = (e.clientX - box.left) / box.width;
    const time = percent * window.wavesurfer.getDuration();
    const index = Math.floor(time / chunkDuration);
    const rms = rmsChunks[index];
    const display = document.getElementById("rms-display");

    if (display) {
      display.innerText = rms !== undefined
        ? `RMS at ${time.toFixed(2)}s: ${rms.toFixed(2)} dB`
        : `No RMS data at ${time.toFixed(2)}s`;
    }
  });
});

// Spacebar play/pause (unless typing in input/textarea)
document.addEventListener("keydown", (e) => {
  const tag = e.target.tagName;
  if ((e.code === "Space" || e.keyCode === 32) && !["INPUT", "TEXTAREA"].includes(tag)) {
    e.preventDefault();
    if (window.wavesurfer) {
      window.wavesurfer.playPause();
      const isPlaying = window.wavesurfer.isPlaying();
      const waveform = document.getElementById("waveform");
      if (waveform) {
        waveform.classList.toggle("waveform-playing", isPlaying);
      }
      console.log("🎹 Spacebar toggled playback:", isPlaying);
    }
  }
});

// Reset glow on finish
window.wavesurfer.on("finish", () => {
  const waveform = document.getElementById("waveform");
  if (waveform) waveform.classList.remove("waveform-playing");
});