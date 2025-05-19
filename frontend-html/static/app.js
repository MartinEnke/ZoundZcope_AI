// Generate UUID for session
function generateSessionId() {
  return 'xxxxxxxxyxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

const sessionId = generateSessionId();
document.getElementById("session_id").value = sessionId;

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

const form = document.getElementById("uploadForm");
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const formData = new FormData(form);

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