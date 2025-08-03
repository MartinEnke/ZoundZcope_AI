import librosa
import numpy as np
import json
from pathlib import Path


def estimate_bpm(file_path):
    y, sr = librosa.load(file_path, mono=True)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return round(tempo)


def get_chunk_duration_from_bpm(bpm, fraction=0.5, min_chunk=0.2, max_chunk=0.6):
    beat_duration = 60 / bpm
    chunk = beat_duration * fraction
    return max(min(chunk, max_chunk), min_chunk)


def compute_rms_chunks(file_path, chunk_duration=0.5, json_output_path=None, smoothing_factor=0.95):
    print(f"🔍 Using RMS chunk duration: {chunk_duration:.3f} sec")
    y, sr = librosa.load(file_path, mono=True)
    samples_per_chunk = int(sr * chunk_duration)
    total_chunks = len(y) // samples_per_chunk

    raw_rms = []
    for i in range(total_chunks):
        start = i * samples_per_chunk
        end = start + samples_per_chunk
        chunk = y[start:end]
        if len(chunk) == 0:
            continue
        rms = np.sqrt(np.mean(chunk ** 2))
        rms_db = 20 * np.log10(rms + 1e-9)
        raw_rms.append(float(np.round(rms_db + 0.82, 2)))

    smoothed_rms = smooth_rms_values(raw_rms, smoothing_factor=smoothing_factor)

    if json_output_path:
        json_path = Path(json_output_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w") as f:
            json.dump(smoothed_rms, f)

    return smoothed_rms


def smooth_rms_values(rms_values, smoothing_factor=0.9):
    if not rms_values:
        return []
    smoothed = [rms_values[0]]
    for val in rms_values[1:]:
        prev = smoothed[-1]
        smoothed_val = (smoothing_factor * prev) + ((1 - smoothing_factor) * val)
        smoothed.append(round(smoothed_val, 2))
    return smoothed


def process_reference_track(ref_track_path, rms_json_output_dir):
    bpm = estimate_bpm(ref_track_path)
    chunk_duration = get_chunk_duration_from_bpm(bpm)

    print(f"🎵 Estimated BPM: {bpm}, Adaptive RMS Chunk: {chunk_duration:.3f} sec")

    json_output_path = Path(rms_json_output_dir) / (Path(ref_track_path).stem + "_rms.json")

    rms_chunks = compute_rms_chunks(
        str(ref_track_path),
        chunk_duration=chunk_duration,
        json_output_path=str(json_output_path)
    )

    print(f"✅ RMS JSON saved at: {json_output_path}")
    return json_output_path
