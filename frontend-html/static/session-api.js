// session-api.js

export async function createSessionInBackend(sessionName) {
  const userId = 1;  // Optionally make this dynamic later

  try {
    const response = await fetch("/sessions/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_name: sessionName, user_id: userId }),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error("❌ Session creation failed:", error);
      return null;
    }

    const result = await response.json();
    console.log("✅ Created session:", result);
    return result;

  } catch (err) {
    console.error("❌ Session creation fetch error:", err);
    return null;
  }
}

export async function loadSessionTracks(sessionId) {
  try {
    const response = await fetch(`/sessions/${sessionId}/tracks`);
    if (!response.ok) throw new Error("Failed to fetch tracks");

    const tracks = await response.json();
    const latestTrack = tracks[0]; // Assumes latest uploaded is first

    // Update dropdown if present
    const trackSelect = document.getElementById("track-select");
    if (trackSelect) {
      trackSelect.innerHTML = '<option value="">Choose Track</option>';
      tracks.forEach(track => {
        const opt = document.createElement("option");
        opt.value = track.id;
        opt.textContent = track.track_name || "Untitled Track";
        trackSelect.appendChild(opt);
      });
      trackSelect.value = latestTrack?.id || "";
    }

    // Store latest track/session ID for export or follow-up use
    window.lastSessionId = sessionId;
    window.lastTrackId = latestTrack?.id || "";

    return tracks;
  } catch (err) {
    console.error("❌ Error loading session tracks:", err);
    return [];
  }
}
