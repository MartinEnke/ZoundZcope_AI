import librosa
import numpy as np
import json
from pathlib import Path

def compute_rms_chunks(file_path, chunk_duration=0.5, json_output_path=None):
    print("🔍 Writing RMS JSON to:", json_output_path)
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

    # ✅ Write JSON only if path is provided
    if json_output_path:
        json_path = Path(json_output_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w") as f:
            json.dump(rms_chunks, f)

    return rms_chunks


def process_reference_track(ref_track_path, rms_json_output_dir):
    # Define output JSON path (e.g., alongside ref track)
    json_output_path = Path(rms_json_output_dir) / (Path(ref_track_path).stem + "_rms.json")

    # Compute RMS chunks using your function
    rms_chunks = compute_rms_chunks(str(ref_track_path), chunk_duration=0.5, json_output_path=str(json_output_path))

    print(f"Reference track RMS JSON saved at: {json_output_path}")
    return json_output_path