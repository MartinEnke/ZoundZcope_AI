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
  toast.className = `
    fixed bottom-5 right-5 bg-blue-600 text-white px-4 py-2 rounded shadow-lg
    opacity-90 z-50 transition-opacity duration-500
  `;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => document.body.removeChild(toast), 500);
  }, 3000);
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
  const thinkingEl = document.createElement("p");
  thinkingEl.className = "mt-4 italic text-pink-400 text-opacity-80 animate-pulse";
  thinkingEl.textContent = "Thinking...";
  outputBox.appendChild(thinkingEl);

  const requestBody = {
    analysis_text: analysis,
    feedback_text: feedback,
    user_question: question,
    session_id: sessionId,
    track_id: trackId,
    feedback_profile: profile,
    followup_group: followupGroupIndex,
  };

  if (typeof refTrackAnalysisData !== "undefined" && refTrackAnalysisData !== null) {
    requestBody.ref_analysis_data = refTrackAnalysisData;
  }

  try {
    const res = await fetch("/chat/ask-followup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    const data = await res.json();
    const answer = data.answer;

    if (data.summary_created) showInfoToast("💡 Internal summary created to keep conversations concise.");

    thinkingEl.classList.remove("animate-pulse");
    thinkingEl.innerHTML = `<span class="text-blue-400 text-lg">➤</span>`;

    const questionP = document.createElement("p");
    const strongQ = document.createElement("strong");
    strongQ.textContent = "Q:";
    questionP.appendChild(strongQ);
    questionP.appendChild(document.createTextNode(" " + question));
    outputBox.appendChild(questionP);

    const answerDiv = document.createElement("div");
    answerDiv.innerHTML = marked.parse(answer);
    outputBox.appendChild(answerDiv);

    const manualSummarizeBtn = document.getElementById("manualSummarizeBtn");
    if (manualSummarizeBtn.style.display === "none") {
      manualSummarizeBtn.style.display = "inline-block";
    }

    followupThread.push({ question, answer });

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

      outputBox.appendChild(summaryEl);
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
