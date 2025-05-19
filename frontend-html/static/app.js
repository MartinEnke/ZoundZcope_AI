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

// ✅ Attach file input change listener immediately
const fileInput = document.getElementById('file-upload');
const fileNameSpan = document.getElementById('file-name');

fileInput.addEventListener('change', () => {
  if (fileInput.files.length > 0) {
    fileNameSpan.textContent = fileInput.files[0].name;
  } else {
    fileNameSpan.textContent = 'Click to upload your track';
  }
});

// ✅ Submit handler
const form = document.getElementById("uploadForm");
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData(form);

  // Clean up track_name if empty or placeholder
  const trackName = formData.get("track_name");
  if (!trackName || trackName.trim() === "" || trackName.trim().toLowerCase() === "string") {
    formData.set("track_name", "string");
  }

  console.log("Sending to /upload/ with FormData:");
  for (let [key, value] of formData.entries()) {
    console.log(`${key}:`, value);
  }

  try {
    const response = await fetch("/upload/", {
      method: "POST",
      body: formData,
    });

    const raw = await response.text();
    console.log("Raw response text:", raw);

    try {
      const result = JSON.parse(raw);

      if (response.ok) {
        document.getElementById("results").classList.remove("hidden");
        document.getElementById("feedback").classList.remove("hidden");

        const output = document.getElementById("analysisOutput");
        output.innerHTML = `
  <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2 text-sm">
    <p><strong>Tempo:</strong> ${result.analysis.tempo} BPM</p>
    <p><strong>Key:</strong> ${result.analysis.key}</p>
    <p><strong>Peak db:</strong> ${result.analysis.peak_db}</p>
    <p><strong>RMS db:</strong> ${result.analysis.rms_db}</p>
    <p><strong>LUFS:</strong> ${result.analysis.lufs}</p>
    <p><strong>Dynamic Range:</strong> ${result.analysis.dynamic_range}</p>
    <p><strong>Stereo Width Ratio:</strong> ${result.analysis.stereo_width_ratio}</p>
    <p><strong>Stereo Width:</strong> ${result.analysis.stereo_width}</p>
    <p><strong>Low End Energy Ratio:</strong> ${result.analysis.low_end_energy_ratio}</p>
    <p><strong>Bass Profile:</strong> ${result.analysis.bass_profile}</p>
    <div class="md:col-span-2"><strong>Band Energies:</strong><pre class="whitespace-pre-wrap">${JSON.stringify(result.analysis.band_energies, null, 2)}</pre></div>
  </div>
`;

        const feedbackSection = document.getElementById("gptResponse");
        const trackType = result.type?.toLowerCase();

        if (trackType === "mixdown") {
          feedbackSection.innerHTML = `
            <p class="text-pink-400 font-semibold">Mixdown Suggestions:</p>
            <ul class="list-disc list-inside mt-2 text-white/80">
              ${result.feedback.split("\n").map(line => line.trim()).filter(Boolean).map(line => `<li>${line}</li>`).join("")}
            </ul>
          `;
        } else if (trackType === "master") {
          feedbackSection.innerHTML = `
            <p class="text-blue-400 font-semibold">Mastering Advice:</p>
            <ul class="list-disc list-inside mt-2 text-white/80">
              ${result.feedback.split("\n").map(line => line.trim()).filter(Boolean).map(line => `<li>${line}</li>`).join("")}
            </ul>
          `;
        } else {
          feedbackSection.textContent = result.feedback || "No feedback received.";
        }
      } else {
        console.error("Upload failed response:", result);
        alert("Upload failed: " + JSON.stringify(result));
      }
    } catch (parseError) {
      console.error("Failed to parse JSON response:", parseError);
      alert("Upload failed: Response was not valid JSON.");
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

  // 💜 Add purple highlight to the main field
  button.classList.add("selected-field");
});
  });

  // Close dropdown if clicked outside
  document.addEventListener("click", (e) => {
    if (!button.contains(e.target) && !options.contains(e.target)) {
      options.classList.add("hidden");
    }
  });
});

// Genre dropdown behavior
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

  // 💜 Add purple highlight to the main field
  genreButton.classList.add("selected-field");
});

  });

  // Close if clicked outside
  document.addEventListener("click", (e) => {
    if (!genreButton.contains(e.target) && !genreOptions.contains(e.target)) {
      genreOptions.classList.add("hidden");
    }
  });
});