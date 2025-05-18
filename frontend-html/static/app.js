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

  try {
    const response = await fetch("/upload/", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (response.ok) {
      // Show analysis section
      document.getElementById("results").classList.remove("hidden");
      document.getElementById("feedback").classList.remove("hidden");

      // Display analysis results
      const output = document.getElementById("analysisOutput");
      output.innerHTML = `
        <p><strong>Track Name:</strong> ${result.track_name}</p>
        <p><strong>LUFS:</strong> ${result.analysis.lufs}</p>
        <p><strong>Key:</strong> ${result.analysis.key}</p>
        <p><strong>Stereo Width:</strong> ${result.analysis.stereo_width}</p>
        <p><strong>Dynamic Range:</strong> ${result.analysis.dynamic_range}</p>
        <p><strong>Genre:</strong> ${result.genre}</p>
      `;

      // GPT Feedback
      const feedback = document.getElementById("gptResponse");
      feedback.textContent = result.feedback || "No feedback received.";
    } else {
      alert("Upload failed: " + (result.detail || "Unknown error"));
    }
  } catch (err) {
    console.error(err);
    alert("An error occurred during upload.");
  }
});
