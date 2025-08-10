"""
RMS chunk analysis utilities for ZoundZcope.

This module provides functions to:
    - Estimate BPM from audio files.
    - Determine adaptive RMS chunk durations based on BPM.
    - Compute RMS values for audio segments.
    - Smooth RMS values over time.
    - Process reference tracks for waveform visualization.

The computed RMS chunks are typically stored as JSON for use in the
frontend's waveform displays.

Dependencies:
    - librosa: Audio loading and beat tracking.
    - numpy: RMS and decibel calculations.
    - json, pathlib: Data storage.
"""
import librosa
import numpy as np
import json
from pathlib import Path


def estimate_bpm(file_path):
    """
        Estimate the beats per minute (BPM) of an audio file.

        Args:
            file_path (str or Path): Path to the audio file.

        Returns:
            int: Estimated BPM, rounded to the nearest integer.
        """
    y, sr = librosa.load(file_path, mono=True)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return round(tempo)


def get_chunk_duration_from_bpm(bpm, fraction=0.5, min_chunk=0.2, max_chunk=0.6):
    """
        Calculate RMS chunk duration based on BPM.

        Args:
            bpm (int): Estimated beats per minute.
            fraction (float, optional): Fraction of a beat per RMS chunk.
            min_chunk (float, optional): Minimum chunk duration in seconds.
            max_chunk (float, optional): Maximum chunk duration in seconds.

        Returns:
            float: Chunk duration in seconds, constrained between min_chunk and max_chunk.
        """
    beat_duration = 60 / bpm
    chunk = beat_duration * fraction
    return max(min(chunk, max_chunk), min_chunk)


def compute_rms_chunks(file_path, chunk_duration=0.5, json_output_path=None, smoothing_factor=0.95):
    """
        Compute RMS values for fixed-duration chunks of an audio file.

        Args:
            file_path (str or Path): Path to the audio file.
            chunk_duration (float, optional): Length of each chunk in seconds.
            json_output_path (str or Path, optional): File path to save RMS values as JSON.
            smoothing_factor (float, optional): Factor for smoothing RMS values.

        Returns:
            list[float]: Smoothed RMS values (in dB) for each chunk.
        """
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
    """
        Smooth RMS values using exponential smoothing.

        Args:
            rms_values (list[float]): List of RMS values in dB.
            smoothing_factor (float, optional): Weight for previous value in smoothing.

        Returns:
            list[float]: Smoothed RMS values.
        """
    if not rms_values:
        return []
    smoothed = [rms_values[0]]
    for val in rms_values[1:]:
        prev = smoothed[-1]
        smoothed_val = (smoothing_factor * prev) + ((1 - smoothing_factor) * val)
        smoothed.append(round(smoothed_val, 2))
    return smoothed


def process_reference_track(ref_track_path, rms_json_output_dir):
    """
        Process a reference track for adaptive RMS chunk analysis.

        This function:
          - Estimates BPM from the reference track.
          - Calculates an adaptive chunk duration from BPM.
          - Computes RMS values for the track.
          - Saves RMS values to a JSON file in the given directory.

        Args:
            ref_track_path (str or Path): Path to the reference audio file.
            rms_json_output_dir (str or Path): Directory where RMS JSON will be saved.

        Returns:
            Path: Path to the saved RMS JSON file.
        """
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
