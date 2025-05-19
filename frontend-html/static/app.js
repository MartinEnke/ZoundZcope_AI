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

const form = document.getElementById("uploadForm");
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData(form);
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
        // Show sections
        document.getElementById("results").classList.remove("hidden");
        document.getElementById("feedback").classList.remove("hidden");

        // Analysis Results
        const output = document.getElementById("analysisOutput");
        output.innerHTML = `
          <p><strong>Track Name:</strong> ${result.track_name}</p>
          <p><strong>LUFS:</strong> ${result.analysis.lufs}</p>
          <p><strong>Key:</strong> ${result.analysis.key}</p>
          <p><strong>Stereo Width:</strong> ${result.analysis.stereo_width}</p>
          <p><strong>Dynamic Range:</strong> ${result.analysis.dynamic_range}</p>
          <p><strong>Genre:</strong> ${result.genre}</p>
        `;

        // AI Feedback
        const feedbackSection = document.getElementById("gptResponse");
        const trackType = result.type?.toLowerCase();

        if (trackType === "mixdown") {
          feedbackSection.innerHTML = `
            <p class="text-pink-400 font-semibold">Mixdown Suggestions:</p>
            <ul class="list-disc list-inside mt-2 text-white/80">
              ${result.feedback
                .split("\n")
                .map(line => line.trim())
                .filter(line => line)
                .map(line => `<li>${line}</li>`)
                .join("")}
            </ul>
          `;
        } else if (trackType === "master") {
          feedbackSection.innerHTML = `
            <p class="text-blue-400 font-semibold">Mastering Advice:</p>
            <ul class="list-disc list-inside mt-2 text-white/80">
              ${result.feedback
                .split("\n")
                .map(line => line.trim())
                .filter(line => line)
                .map(line => `<li>${line}</li>`)
                .join("")}
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
