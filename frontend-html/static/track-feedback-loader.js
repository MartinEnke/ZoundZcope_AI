// track-feedback-loader.js

export function setupTrackSelectHandler() {
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
          const msgEl = buildMessageElement(track, msg);
          feedbackBox.appendChild(msgEl);
        });
      }

      document.getElementById("feedback").classList.remove("hidden");
    } catch (err) {
      console.error("❌ Error displaying chat feedback:", err);
    }
  });
}

function buildMessageElement(track, msg) {
  const trackName = track?.track_name || "Unnamed Track";
  const type = track?.type
    ? capitalize(track.type)
    : "Unknown";
  const profile = msg.feedback_profile
    ? msg.feedback_profile.replace(/[_-]/g, " ").replace(/\b\w/g, l => l.toUpperCase())
    : "Default";

  const msgEl = document.createElement("div");
  msgEl.className = "mb-4";

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
  return msgEl;
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}
