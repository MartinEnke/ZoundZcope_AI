// recent-feedback.js

export function toggleFollowup(id) {
  const el = document.getElementById(id);
  const btn = el?.previousElementSibling;
  const parentBox = el?.closest(".feedback-box");

  if (!el || !btn || !parentBox || parentBox.dataset.expanded !== "true") return;

  const isHidden = el.classList.contains("hidden");
  el.classList.toggle("hidden");
  btn.textContent = isHidden ? "Hide Follow-up" : "Show Follow-up";

  parentBox.style.height = "auto";
  requestAnimationFrame(() => {
    const newHeight = parentBox.scrollHeight;
    parentBox.style.height = newHeight + "px";
  });
}

export function renderRecentFeedbackPanel() {
  console.log("✅ renderRecentFeedbackPanel() called");

  const container = document.getElementById("recent-feedback-container");
  const panel = document.getElementById("recentFeedbackPanel");
  if (!container || !panel) return;

  let history = [];
  try {
    history = JSON.parse(localStorage.getItem("zoundzcope_history")) || [];
    console.log("🧠 Loaded history:", history);
  } catch (err) {
    console.error("🧠 Failed to parse feedback history:", err);
  }

  container.innerHTML = "";

  if (!history || history.length === 0) {
    console.warn("⚠️ No feedback history found.");
    panel.classList.add("hidden");
    return;
  }

  const recent = history.slice(0, 5);
  recent.forEach((entry, i) => {
    const box = document.createElement("div");
    box.className = "feedback-box relative bg-white/5 p-4 rounded-lg shadow-md space-y-2 border border-white/10";
    box.style.height = "108px";
    box.classList.add("collapsed");
    box.dataset.expanded = "false";

    const subheadingText = entry.subheading?.replace(/<[^>]+>/g, "").trim() || "Previous Feedback";
    const trackName = entry.track_name || "Untitled Track";
    const dateStr = entry.timestamp ? new Date(entry.timestamp).toLocaleDateString() : "";

    let feedbackHTML = entry.feedback || "<div class='text-white/60'>No feedback content.</div>";
    const headingRegex = new RegExp(`<p[^>]*>${subheadingText}</p>`, "i");
    feedbackHTML = feedbackHTML.replace(headingRegex, "").trim();

    const followupId = `followup-${i}`;
    const hasFollowup = entry.followup && Array.isArray(entry.followup) && entry.followup.length > 0;

    const followupToggleHTML = hasFollowup
  ? `<button class="text-xs text-purple-300 underline followup-btn" data-target="${followupId}">Show Follow-up</button>`
  : "";


    const followupHTML = hasFollowup
      ? `<div id="${followupId}" class="mt-2 text-sm text-white/70 border-t border-white/10 pt-2 hidden">
          ${entry.followup.map(f => `<p>${f}</p>`).join("")}
        </div>`
      : "";

    const headingHTML = `
      <div class="flex justify-between items-center mb-1">
        <div class="flex items-baseline gap-2">
          <p class="${subheadingText.toLowerCase().includes('master') ? 'text-blue-400' : 'text-pink-400'} text-lg font-bold">
            ${subheadingText}
          </p>
          <span class="text-white font-semibold text-sm">${trackName}</span>
        </div>
        <span class="text-white/50 text-xs">${dateStr}</span>
      </div>
    `;

    const toggleAreaHTML = `
      <div class="fold-toggle-area text-white/90 text-sm space-y-2 cursor-pointer">
        ${headingHTML}
        ${feedbackHTML}
      </div>
    `;

    const followupSectionHTML = `
      <div class="pt-2">
        ${followupToggleHTML}
        ${followupHTML}
      </div>
    `;

    box.innerHTML = toggleAreaHTML + followupSectionHTML;

    // Attach follow-up toggle handler
const followupBtn = box.querySelector(".followup-btn");
if (followupBtn) {
  followupBtn.addEventListener("click", (e) => {
    e.stopPropagation(); // prevent folding the main box
    const id = followupBtn.dataset.target;
    toggleFollowup(id);
  });
}


    const toggleArea = box.querySelector(".fold-toggle-area");
    toggleArea.addEventListener("click", () => {
      const expanded = box.dataset.expanded === "true";
      box.style.height = expanded ? "108px" : box.scrollHeight + "px";
      box.dataset.expanded = expanded ? "false" : "true";
      box.classList.toggle("collapsed", expanded);
      box.classList.toggle("expanded", !expanded);
    });

    container.appendChild(box);
  });

  panel.classList.remove("hidden");
}
