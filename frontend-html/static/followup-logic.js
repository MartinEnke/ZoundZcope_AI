// ============================
// followup-logic.js
// Handles follow-up questions, threading, summarization, and smart suggestions
// ============================

let followupThread = [];
let followupGroupIndex = 0;
let lastManualSummaryGroup = -1;

function showInfoToast(message) {
  const toast = document.createElement("div");
  toast.textContent = message;

  Object.assign(toast.style, {
    position: "fixed",
    bottom: "30px",
    right: "30px",
    background: "rgba(255, 255, 255, 0.07)",
    color: "white",
    padding: "12px 20px",
    borderRadius: "16px",
    fontSize: "15px",
    fontWeight: "500",
    letterSpacing: "0.3px",
    zIndex: "9999",
    opacity: "0",
    transition: "opacity 0.4s ease, transform 0.4s ease",
    backdropFilter: "blur(12px)",
    WebkitBackdropFilter: "blur(12px)",
    boxShadow: "0 0 12px rgba(236, 72, 153, 0.35), 0 0 12px rgba(59, 130, 246, 0.35)",
    transform: "translateY(20px)",
    pointerEvents: "none",
  });

  document.body.appendChild(toast);

  // Animate in
  requestAnimationFrame(() => {
    toast.style.opacity = "0.95";
    toast.style.transform = "translateY(0)";
  });

  // Animate out after 3 seconds
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(20px)";
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 400);
  }, 6000);
}


// ============================
// Ask Follow-Up
// ============================

document.getElementById("customQuestion").addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    event.preventDefault();
    document.getElementById("askAIButton").click();
  }
});

document.getElementById("askAIButton").addEventListener("click", async () => {
  const questionInput = document.getElementById("customQuestion");
  const question = questionInput.value.trim();
  const outputBox = document.getElementById("aiFollowupResponse");

  if (!question) return alert("Please enter a question.");

  const trackId = window.lastTrackId || "";
  const sessionId = window.lastSessionId || "";
  const profile = document.getElementById("profile-input")?.value || "";
  const analysis = document.getElementById("analysisOutput")?.innerText || "";
  const feedback = document.getElementById("gptResponse")?.innerText || "";

  if (!trackId || !sessionId) return alert("Please upload and analyze first.");

  outputBox.classList.remove("hidden");

  // ⬅️ Show temporary "thinking..." inside a group wrapper
  const groupWrapper = document.createElement("div");
  groupWrapper.className = "followup-summary-group space-y-3 mt-4";

  const thinkingEl = document.createElement("p");
  thinkingEl.className = "italic text-pink-400 text-opacity-80 animate-pulse";
  thinkingEl.textContent = "Thinking...";
  groupWrapper.appendChild(thinkingEl);

  outputBox.appendChild(groupWrapper);

  try {
    const res = await fetch("/chat/ask-followup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        analysis_text: analysis,
        feedback_text: feedback,
        user_question: question,
        session_id: sessionId,
        track_id: trackId,
        feedback_profile: profile,
        followup_group: followupGroupIndex,
        ...(typeof refTrackAnalysisData !== "undefined" && refTrackAnalysisData !== null
          ? { ref_analysis_data: refTrackAnalysisData }
          : {})
      }),
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    const data = await res.json();
    const answer = data.answer;

    console.log("Summary created?", data.summary_created);

    if (data.summary_created) {
  showInfoToast("AI generated an auto-summary for this follow-up thread.");
}

    // Remove thinking...
    thinkingEl.remove();

    // ✅ Now add question and answer
    const questionP = document.createElement("p");
    const strongQ = document.createElement("strong");
    strongQ.textContent = "Q:";
    questionP.appendChild(strongQ);
    questionP.appendChild(document.createTextNode(" " + question));

    const answerDiv = document.createElement("div");
    answerDiv.innerHTML = marked.parse(answer);

    groupWrapper.appendChild(questionP);
    groupWrapper.appendChild(answerDiv);

    // ✅ Make summary button appear
    const manualSummarizeBtn = document.getElementById("manualSummarizeBtn");
    if (manualSummarizeBtn && manualSummarizeBtn.style.display === "none") {
      manualSummarizeBtn.style.display = "inline-block";
    }

    followupThread.push({ question, answer });

    // 🧠 Optional: Store in local history
    try {
      const raw = localStorage.getItem("zoundzcope_history") || "[]";
      const history = JSON.parse(raw);
      if (history.length > 0) {
        if (!Array.isArray(history[0].followup)) {
          history[0].followup = history[0].followup ? [history[0].followup] : [];
        }
        history[0].followup.push(`<p><strong>Q:</strong> ${question}<br><strong>A:</strong> ${answer}</p>`);
        localStorage.setItem("zoundzcope_history", JSON.stringify(history));
      }
    } catch (err) {
      console.error("❌ Failed to store follow-up in history:", err);
    }

    if (followupThread.length >= 4) {
      followupGroupIndex++;
      followupThread = [];
    }

    questionInput.value = "";
    localStorage.setItem("zoundzcope_last_followup", outputBox.innerHTML);
    showSummarizeButton();

  } catch (err) {
    console.error("❌ Follow-up failed:", err);
    outputBox.innerHTML += `<p class='text-red-400'>Something went wrong: ${err.message}</p>`;
  }
});


function showSummarizeButton() {
  const manualSummarizeBtn = document.getElementById("manualSummarizeBtn");
  if (manualSummarizeBtn && manualSummarizeBtn.style.display === "none") {
    manualSummarizeBtn.style.display = "inline-block"; // or "block"
  }
}


// ============================
// Manual Summarizer Handler
// ============================
document.addEventListener("DOMContentLoaded", () => {
  const manualBtn = document.getElementById("manualSummarizeBtn");
  if (!manualBtn) return;

  manualBtn.addEventListener("click", async () => {
    if (followupGroupIndex === lastManualSummaryGroup) {
      alert("This group has already been manually summarized.");
      return;
    }

    manualBtn.classList.add("pulsing");

    try {
      const trackIdToUse = window.lastTrackId || document.getElementById("track-select")?.value;
      const sessionId = window.lastSessionId || document.getElementById("session_id")?.value;

      if (!trackIdToUse || !sessionId) {
        alert("Please select or analyze a track first.");
        manualBtn.classList.remove("pulsing");
        return;
      }

      const res = await fetch("/chat/summarize-thread", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          track_id: trackIdToUse,
          followup_group: followupGroupIndex
        })
      });

      if (!res.ok) throw new Error(`Server error: ${res.status} ${res.statusText}`);

      const data = await res.json();
      const summary = data.summary;

      const htmlSummary = marked.parse(summary);
      const outputBox = document.getElementById("aiFollowupResponse");

      const summaryEl = document.createElement("div");
      summaryEl.className = "summary-block bg-white/10 text-white/90 p-4 rounded-lg mt-4";
      summaryEl.innerHTML = `
        <p class="text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 font-bold text-lg mb-2">
          Thread Summary
        </p>
        <div class="text-white text-base leading-relaxed">
          ${htmlSummary}
        </div>
      `;

      const allGroups = outputBox.querySelectorAll(".followup-summary-group");
const lastGroup = allGroups[allGroups.length - 1];

if (lastGroup) {
  lastGroup.appendChild(summaryEl);
} else {
  outputBox.appendChild(summaryEl); // fallback
}
      localStorage.setItem("zoundzcope_last_followup_summary", summaryEl.outerHTML);

      lastManualSummaryGroup = followupGroupIndex;
      followupGroupIndex++;
      followupThread = [];

    } catch (err) {
      console.error("❌ Failed to summarize follow-up thread:", err);
    } finally {
      manualBtn.classList.remove("pulsing");
    }
  });
});


// ==========================================================
// 🌐 Global Exposure for External Access
// ----------------------------------------------------------
// This section attaches functions or data to a global namespace
// so they can be accessed from other scripts or inline HTML.
// ==========================================================

window.ZoundZcope = window.ZoundZcope || {};
window.ZoundZcope.showSummarizeButton = showSummarizeButton;
// window.ZoundZcope.summarizeFollowupThread = summarizeFollowupThread; //