const chunkDuration = 0.5;
let rmsChunks = [];

fetch('/static/analysis/sample_rms.json')
  .then(response => response.json())
  .then(data => {
    rmsChunks = data;
    console.log("✅ RMS data loaded", rmsChunks.length, "chunks");
  })
  .catch(error => {
    console.error("❌ Failed to load RMS data", error);
  });

const wavesurfer = WaveSurfer.create({
  container: '#waveform',
  waveColor: '#a0a0a0',
  progressColor: '#2196f3',
  height: 100,
  responsive: true
});

// If trackPath is templated server-side
const trackPath = "{{ track_path }}";
if (trackPath) {
  wavesurfer.load(encodeURI(trackPath));
}

wavesurfer.on('ready', () => {
  console.log("✅ WaveSurfer loaded successfully");

  // Click listener
window.wavesurfer.on('click', (e) => {
  const boundingBox = window.wavesurfer.container.getBoundingClientRect();
  const percent = (e.clientX - boundingBox.left) / boundingBox.width;
  const duration = window.wavesurfer.getDuration();
  const time = percent * duration;

  const index = Math.floor(time / chunkDuration);
  const rmsValue = rmsChunks[index];

  const display = document.getElementById("rms-display");
  if (rmsValue !== undefined) {
    display.innerText = `RMS at ${time.toFixed(2)}s: ${rmsValue.toFixed(2)} dB`;
  } else {
    display.innerText = `No RMS data at ${time.toFixed(2)}s`;
  }
});
