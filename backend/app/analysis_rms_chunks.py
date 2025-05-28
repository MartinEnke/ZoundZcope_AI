import librosa
import numpy as np
import json
from pathlib import Path

def compute_rms_chunks(file_path, chunk_duration=0.5):
    y, sr = librosa.load(file_path, mono=True)
    samples_per_chunk = int(sr * chunk_duration)
    total_chunks = len(y) // samples_per_chunk

    rms_chunks = []
    for i in range(total_chunks):
        start = i * samples_per_chunk
        end = start + samples_per_chunk
        chunk = y[start:end]
        if len(chunk) == 0:
            continue
        rms = np.sqrt(np.mean(chunk ** 2))
        rms_db = 20 * np.log10(rms + 1e-9)
        rms_chunks.append(float(np.round(rms_db, 2)))


    base_dir = Path(__file__).resolve().parents[2]
    output_path = base_dir / "frontend-html" / "static" / "analysis" / "sample_rms.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(rms_chunks, f)

    return rms_chunks


# if __name__ == "__main__":
#     # ✅ Safe absolute path to audio file inside backend/uploads
#     base_dir = Path(__file__).resolve().parents[2]
#     audio_path = base_dir / "backend" / "uploads" / "01 - Llewellyn - Total Fantasy.mp3"
#
#     compute_rms_chunks(str(audio_path))
#     print("✅ sample_rms.json created at", audio_path)