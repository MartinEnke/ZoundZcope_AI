# app/analysis_rms_chunks.py
"""
RMS chunk analysis utilities for ZoundZcope.

- Robust decoding (librosa -> ffmpeg fallback) so MP3s work on slim containers.
- Keeps the original JSON format: a simple list of smoothed dB RMS values.
"""

from __future__ import annotations
import json
from pathlib import Path
import subprocess
from typing import Tuple

import numpy as np

# Prefer librosa/audioread if available
try:
    import librosa  # type: ignore
    _HAS_LIBROSA = True
except Exception:
    _HAS_LIBROSA = False


# ---------- Decoding helpers ----------

def _decode_with_librosa(path: str, target_sr: int = 22050) -> Tuple[np.ndarray, int]:
    if not _HAS_LIBROSA:
        raise RuntimeError("librosa not available")
    # match your prior behavior: resample to 22050 and mono
    y, sr = librosa.load(path, sr=target_sr, mono=True)
    if y.dtype != np.float32:
        y = y.astype(np.float32)
    return y, sr


def _decode_with_ffmpeg(path: str, target_sr: int = 22050) -> Tuple[np.ndarray, int]:
    """Decode with ffmpeg to mono float32 at target_sr."""
    cmd = [
        "ffmpeg", "-v", "error", "-i", path,
        "-f", "f32le", "-acodec", "pcm_f32le",
        "-ac", "1", "-ar", str(target_sr),
        "-"
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    y = np.frombuffer(proc.stdout, dtype=np.float32)
    return y, target_sr


def _safe_decode(path: str, target_sr: int = 22050) -> Tuple[np.ndarray, int]:
    # Try librosa first (uses audioread->ffmpeg when present)
    if _HAS_LIBROSA:
        try:
            return _decode_with_librosa(path, target_sr)
        except Exception as e1:
            print("RMS decode error (librosa):", repr(e1))
    # Fallback to direct ffmpeg pipe
    try:
        return _decode_with_ffmpeg(path, target_sr)
    except Exception as e2:
        print("RMS decode error (ffmpeg):", repr(e2))
        raise RuntimeError("Could not decode audio for RMS") from e2


# ---------- Public API (keeps your original signatures/output) ----------

def estimate_bpm(file_path):
    """Estimate BPM (rounded int). More robust decode; uses librosa beat tracking if available."""
    y, sr = _safe_decode(str(file_path), target_sr=22050)
    if not _HAS_LIBROSA:
        # Basic fallback if librosa missing
        return 120
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return int(round(float(tempo)))


def get_chunk_duration_from_bpm(bpm, fraction=0.5, min_chunk=0.2, max_chunk=0.6):
    beat_duration = 60.0 / max(float(bpm), 1.0)
    chunk = beat_duration * float(fraction)
    return max(min(chunk, float(max_chunk)), float(min_chunk))


def smooth_rms_values(rms_values, smoothing_factor=0.9):
    if not rms_values:
        return []
    smoothed = [rms_values[0]]
    for val in rms_values[1:]:
        prev = smoothed[-1]
        smoothed_val = (smoothing_factor * prev) + ((1 - smoothing_factor) * val)
        smoothed.append(round(smoothed_val, 2))
    return smoothed


def compute_rms_chunks(file_path, chunk_duration=0.5, json_output_path=None, smoothing_factor=0.95):
    """
    Compute RMS for fixed-duration chunks (in seconds) and optionally write JSON.
    Returns: list[float] of smoothed RMS in dB (same format as before).
    """
    print(f"🔍 Using RMS chunk duration: {float(chunk_duration):.3f} sec")

    # Decode robustly, match librosa default behavior with sr=22050 mono
    y, sr = _safe_decode(str(file_path), target_sr=22050)

    if y is None or y.size == 0 or not np.isfinite(y).any():
        raise RuntimeError("Empty or invalid audio buffer")

    samples_per_chunk = int(sr * float(chunk_duration))
    if samples_per_chunk <= 0:
        samples_per_chunk = max(1, int(sr * 0.5))

    total_chunks = len(y) // samples_per_chunk
    raw_rms = []

    for i in range(total_chunks):
        start = i * samples_per_chunk
        end = start + samples_per_chunk
        chunk = y[start:end]
        if chunk.size == 0:
            continue
        rms = float(np.sqrt(np.mean(chunk * chunk) + 1e-12))
        rms_db = 20.0 * np.log10(rms)
        # keep your original +0.82 tweak & rounding
        raw_rms.append(float(np.round(rms_db + 0.82, 2)))

    smoothed_rms = smooth_rms_values(raw_rms, smoothing_factor=smoothing_factor)

    if json_output_path:
        json_path = Path(json_output_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(smoothed_rms, f)

    return smoothed_rms


def process_reference_track(ref_track_path, rms_json_output_dir):
    """
    Same as before but with robust decode via compute_rms_chunks().
    """
    bpm = estimate_bpm(ref_track_path)
    chunk_duration = get_chunk_duration_from_bpm(bpm)
    print(f"🎵 Estimated BPM: {bpm}, Adaptive RMS Chunk: {chunk_duration:.3f} sec")

    out_dir = Path(rms_json_output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_output_path = out_dir / (Path(ref_track_path).stem + "_rms.json")

    _ = compute_rms_chunks(
        str(ref_track_path),
        chunk_duration=chunk_duration,
        json_output_path=str(json_output_path),
    )

    print(f"✅ RMS JSON saved at: {json_output_path}")
    return json_output_path
