// /static/demo-autoload.js
(function () {
  const DEMO_URL = "/static/demo/zz_demo_main.mp3";
  const DEMO_REF_URL = "/static/demo/zz_demo_ref.mp3";
  const DEMO_MAIN_NAME = "ZoundZcope_Demo.mp3";
  const DEMO_REF_NAME  = "ZoundZcope_Demo_Ref.mp3";

  const MAIN_LABEL_TEXT = "Upload Track (Demo)";
  const REF_LABEL_TEXT  = "Reference Track (Demo)";

  function esc(s) {
    return String(s).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  }

  function setLabel(labelEl, baseText, selectedName = "") {
    if (!labelEl) return;
    labelEl.dataset.base = baseText;
    labelEl.innerHTML = selectedName
      ? `${baseText} <span class="zz-demo-badge">Selected: ${esc(selectedName)}</span>`
      : baseText;
  }

  async function attachDemoFile(inputEl, labelEl, url, fileName, baseText) {
    if (!inputEl || !url) return;
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const demoFile = new File([blob], fileName, { type: blob.type });

      const dt = new DataTransfer();
      dt.items.add(demoFile);
      inputEl.files = dt.files;
      inputEl.dispatchEvent(new Event("change", { bubbles: true }));

      setTimeout(() => setLabel(labelEl, baseText, demoFile.name), 0);

      inputEl.addEventListener("change", () => {
        const f = inputEl.files?.[0];
        setLabel(labelEl, baseText, f ? f.name : "");
      }, { once: true });
    } catch (e) {
      console.warn("Demo attach failed:", e);
      setLabel(labelEl, baseText);
    }
  }

  async function init() {
    const mainInput = document.getElementById("file-upload");
    const mainLabel = document.getElementById("file-name");
    const refInput  = document.getElementById("ref-file-upload");
    const refLabel  = document.getElementById("ref-file-name");

    // Always set the new button names
    if (mainLabel) setLabel(mainLabel, MAIN_LABEL_TEXT);
    if (refLabel)  setLabel(refLabel,  REF_LABEL_TEXT);

    // Auto-prefill demos only if empty
    if (mainInput && (!mainInput.files || mainInput.files.length === 0)) {
      await attachDemoFile(mainInput, mainLabel, DEMO_URL, DEMO_MAIN_NAME, MAIN_LABEL_TEXT);
    }
    if (DEMO_REF_URL && refInput && (!refInput.files || refInput.files.length === 0)) {
      await attachDemoFile(refInput, refLabel, DEMO_REF_URL, DEMO_REF_NAME, REF_LABEL_TEXT);
    }

    // Keep labels stable but show selection when user changes files later
    if (mainInput) {
      mainInput.addEventListener("change", () => {
        const f = mainInput.files?.[0];
        setLabel(mainLabel, MAIN_LABEL_TEXT, f ? f.name : "");
      });
    }
    if (refInput) {
      refInput.addEventListener("change", () => {
        const f = refInput.files?.[0];
        setLabel(refLabel, REF_LABEL_TEXT, f ? f.name : "");
      });
    }
  }

  // Run after disclaimer accept, or fall back on page load
  window.addEventListener("zz:disclaimerAccepted", init);
  if (document.readyState !== "loading") {
    setTimeout(init, 600);
  } else {
    window.addEventListener("DOMContentLoaded", () => setTimeout(init, 600));
  }
})();
