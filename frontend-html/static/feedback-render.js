// feedback-render.js
import { initMainWaveform, loadReferenceWaveform } from "./waveform-logic.js";


export function renderFeedbackAnalysis(result, refTrackAnalysisData = null) {
  const resultsEl = document.getElementById("results");
  const feedbackEl = document.getElementById("feedback");
  const feedbackBox = document.getElementById("gptResponse");
  const output = document.getElementById("analysisOutput");

  resultsEl.classList.remove("hidden");
  feedbackEl.classList.remove("hidden");

  // ✨ Animate
  feedbackEl.classList.remove("fade-in-up");
  void feedbackEl.offsetWidth;
  feedbackEl.classList.add("fade-in-up");

  // 🔢 Helper for rounding
  function r(v) {
    return Number(v).toFixed(2);
  }

  const a = result.analysis;
  output.innerHTML = `
    <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2 text-sm">
      <p><strong>Tempo:</strong> ${a.tempo} BPM</p>
      <p><strong>Key:</strong> ${a.key}</p>
      <p><strong>Peak Level:</strong> ${r(a.peak_db)} dB</p>
      <p><strong>Peak Issue:</strong> ${a.peak_issue}</p>
      <p><strong>RMS Peak:</strong> ${r(a.rms_db_peak)} dB</p>
      <p><strong>LUFS:</strong> ${r(a.lufs)} LUFS</p>
      <p><strong>Dynamic Range:</strong> ${r(a.dynamic_range)} dB</p>
      <p><strong>Stereo Width:</strong> ${a.stereo_width}</p>
      <p class="md:col-span-2"><strong>Low-End:</strong> ${a.low_end_description}</p>
      <p class="md:col-span-2"><strong>Spectral Balance:</strong> ${a.spectral_balance_description}</p>
      <div class="md:col-span-2">
        <strong>Band Energies:</strong>
        <pre class="whitespace-pre-wrap">${JSON.stringify(a.band_energies, null, 2)}</pre>
      </div>
    </div>
  `;

  // Optional Reference Track Section
  if (refTrackAnalysisData) {
    const ra = refTrackAnalysisData;
    const refContainer = document.createElement("div");
    refContainer.className = "mt-8 space-y-2 text-sm border-t border-white/10 pt-4";

    refContainer.innerHTML = `
      <h2 class="text-lg font-semibold text-white mt-8 mb-4">Reference Track Analysis</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2 text-sm">
        <p><strong>Tempo:</strong> ${ra.tempo} BPM</p>
        <p><strong>Key:</strong> ${ra.key}</p>
        <p><strong>Peak Level:</strong> ${r(ra.peak_db)} dB</p>
        <p><strong>Peak Issue:</strong> ${ra.peak_issue}</p>
        <p><strong>RMS Peak:</strong> ${r(ra.rms_db_peak)} dB</p>
        <p><strong>LUFS:</strong> ${r(ra.lufs)} LUFS</p>
        <p><strong>Dynamic Range:</strong> ${r(ra.dynamic_range)} dB</p>
        <p><strong>Stereo Width:</strong> ${ra.stereo_width}</p>
        <p class="md:col-span-2"><strong>Low-End:</strong> ${ra.low_end_description}</p>
        <p class="md:col-span-2"><strong>Spectral Balance:</strong> ${ra.spectral_balance_description}</p>
        <div class="md:col-span-2">
          <strong>Band Energies:</strong>
          <pre class="whitespace-pre-wrap">${JSON.stringify(ra.band_energies, null, 2)}</pre>
        </div>
      </div>
    `;
    output.appendChild(refContainer);
  }

  // Feedback Text
  feedbackBox.innerHTML = "";
  feedbackBox.classList.add("pulsing-feedback");

  const type = (result.type || "").trim().toLowerCase();
  const subheading = document.createElement("p");
  subheading.className = "text-lg font-semibold";

  if (type === "mixdown") {
    subheading.classList.add("text-pink-400");
    subheading.classList.add("mixdown-review");
    subheading.textContent = "Mixdown Review:";
  } else if (type === "mastering") {
    subheading.classList.add("text-blue-400");
    subheading.textContent = "Mastering Guidance:";
  } else if (type === "master") {
    subheading.classList.add("text-blue-400");
    subheading.textContent = "Master Review:";
  } else {
    subheading.classList.add("text-white/70");
    subheading.textContent = "AI Feedback:";
  }

  feedbackBox.appendChild(subheading);

  const ul = document.createElement("ul");
ul.className = "list-disc list-inside mt-2 text-white/90 space-y-1";
feedbackBox.appendChild(ul);

const lines = result.feedback
  .split("\n")
  .map(line => line.replace(/^[-•\s]+/, "").trim())
  .filter(Boolean);

for (const [index, line] of lines.entries()) {
  const li = document.createElement("li");
  li.style.display = "list-item";
  if (index > 0) li.style.marginTop = "0.75rem";

  // Match "INSIGHT:" followed by optional "SUGGESTION:"
  const insightMatch = line.match(/INSIGHT:\s*([\s\S]*?)(?:SUGGESTION:\s*([\s\S]*))?$/i);

  if (insightMatch) {
    const insightText = insightMatch[1].trim();
    const suggestionText = insightMatch[2]
      ? insightMatch[2].replace(/^SUGGESTION:\s*/i, "").trim()
      : "";

    const metallicViolet = "#D8B4FE"; // silver-violet tone

    li.innerHTML = `
      <strong class="insight-label" style="color:${metallicViolet};">INSIGHT:</strong>
      <span class="insight-text">${insightText}</span>
      ${
        suggestionText
          ? `<br><strong class="suggestion-label" style="color:${metallicViolet};">SUGGESTION:</strong> <span class="suggestion-text">${suggestionText}</span>`
          : ""
      }
    `;
  } else {
    li.textContent = line;
  }

  ul.appendChild(li);
}


  const exportBtn = document.getElementById("exportFeedbackBtn");
if (exportBtn) {
  exportBtn.disabled = false;
  exportBtn.textContent = "Export Feedback & Presets";
}


  initMainWaveform(result);
  loadReferenceWaveform();

  document.getElementById("custom-ai-section")?.classList.remove("hidden");

  feedbackBox.classList.remove("pulsing-feedback");

  // Save to localStorage
  localStorage.setItem("zoundzcope_last_analysis", output.innerHTML);
  localStorage.setItem("zoundzcope_last_feedback", ul.outerHTML);
  localStorage.setItem("zoundzcope_last_subheading", subheading?.outerHTML || "");
  localStorage.setItem("zoundzcope_last_followup", "");

  const current = {
  analysis: output.innerHTML,
  feedback: feedbackBox.innerHTML,
  subheading: subheading?.outerHTML || "",
  followup: "",
  track_name: result.track_name || "Untitled Track",
  timestamp: Date.now()
};

try {
    const rawHistory = localStorage.getItem("zoundzcope_history") || "[]";
    const history = JSON.parse(rawHistory);
    const duplicate = history.find(h => JSON.stringify(h) === JSON.stringify(current));
    if (!duplicate) {
      history.unshift(current);
      if (history.length > 3) history.length = 3;
      localStorage.setItem("zoundzcope_history", JSON.stringify(history));
    }
  } catch (err) {
    console.error("❌ Failed to store history:", err);
  }

  const genre = document.getElementById("genre-input")?.value;
  const profile = document.getElementById("profile-input")?.value?.toLowerCase();
  loadQuickFollowupButtons(type, genre, profile);
}