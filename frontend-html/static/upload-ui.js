// upload-ui.js

/**
 * Initializes UI behaviors for upload inputs:
 * - Original track file name display
 * - Reference track file name display
 * - Fake placeholder for track name input
 */
export function initUploadUI() {
  setupOriginalTrackInput();
  setupReferenceTrackInput();
}

function setupOriginalTrackInput() {
  const fileInput = document.getElementById("file-upload");
  const fileNameSpan = document.getElementById("file-name");

  if (fileInput && fileNameSpan) {
    fileInput.addEventListener("change", () => {
      if (fileInput.files.length > 0) {
        fileNameSpan.textContent = fileInput.files[0].name;
        fileNameSpan.style.color = "#2196f3"; // blue
      } else {
        fileNameSpan.textContent = "Choose a file";
        fileNameSpan.style.color = "";
      }
    });
  }
}

function setupReferenceTrackInput() {
  const refInput = document.getElementById("ref-file-upload");
  const refNameSpan = document.getElementById("ref-file-name");

  if (refInput && refNameSpan) {
    refInput.addEventListener("change", () => {
      if (refInput.files.length > 0) {
        refNameSpan.textContent = refInput.files[0].name;
        refNameSpan.style.color = "#8b5cf6"; // violet
      } else {
        refNameSpan.textContent = "Choose Reference Track";
        refNameSpan.style.color = "";
      }
    });
  }
}
