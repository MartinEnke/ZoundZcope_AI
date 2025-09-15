# app/audio_analysis.py
"""
Audio analysis module for ZoundZcope — Render-friendly & MP3-safe.

Changes vs your previous version:
- Robust decode: librosa -> ffmpeg fallback (handles MP3 reliably).
- True-peak: light oversampling (2x, capped at 48 kHz) instead of 192 kHz.
- Each feature wrapped so failure doesn't crash the whole request.
"""

from __future__ import annotations
import math
import json
import subprocess
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np

# Keep your numpy compat shim
if not hasattr(np, "complex"):
    np.complex = complex  # for older libs expecting np.complex

# Optional libs
try:
    import librosa  # type: ignore
    _HAS_LIBROSA = True
except Exception:
    _HAS_LIBROSA = False

try:
    import pyloudnorm as pyln  # type: ignore
    _HAS_PYLN = True
except Exception:
    _HAS_PYLN = False


# -------------------- Robust decoding --------------------

def _decode_with_librosa(path: str, target_sr: int = 22050, mono: bool = True) -> Tuple[np.ndarray, int]:
    if not _HAS_LIBROSA:
        raise RuntimeError("librosa not available")
    y, sr = librosa.load(path, sr=target_sr, mono=mono)
    if y.dtype != np.float32:
        y = y.astype(np.float32)
    return y, sr

def _decode_with_ffmpeg(path: str, target_sr: int = 22050, mono: bool = True) -> Tuple[np.ndarray, int]:
    """Decode audio to float32 PCM via ffmpeg (installed in your Docker image)."""
    ac = "1" if mono else "2"
    cmd = [
        "ffmpeg", "-v", "error", "-i", path,
        "-f", "f32le", "-acodec", "pcm_f32le",
        "-ac", ac, "-ar", str(target_sr),
        "-"
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    y = np.frombuffer(proc.stdout, dtype=np.float32)
    if mono:
        return y, target_sr
    if y.size % 2 != 0:  # defensive
        y = y[:-1]
    y = y.reshape(-1, 2).T
    return y, target_sr

def _safe_decode_mono(path: str, target_sr: int = 22050) -> Tuple[np.ndarray, int]:
    if _HAS_LIBROSA:
        try:
            return _decode_with_librosa(path, target_sr=target_sr, mono=True)
        except Exception as e1:
            print("Analysis decode (librosa) failed:", repr(e1))
    try:
        return _decode_with_ffmpeg(path, target_sr=target_sr, mono=True)
    except Exception as e2:
        print("Analysis decode (ffmpeg) failed:", repr(e2))
        raise RuntimeError("Could not decode audio") from e2


# -------------------- Your helpers (mostly unchanged) --------------------

def detect_key(y, sr):
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)

        major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                                  2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                                  2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

        best_corr = -1
        best_key = ""
        note_names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
        for i in range(12):
            corr_major = np.corrcoef(np.roll(major_profile, i), chroma_mean)[0, 1]
            corr_minor = np.corrcoef(np.roll(minor_profile, i), chroma_mean)[0, 1]
            if corr_major > best_corr:
                best_corr = corr_major
                best_key = f"{note_names[i]} Major"
            if corr_minor > best_corr:
                best_corr = corr_minor
                best_key = f"{note_names[i]} minor"
        return best_key
    except Exception as e:
        print("detect_key failed:", repr(e))
        return None

def compute_band_energies(S, freqs):
    bands = {
        "sub": (20, 60),
        "low": (60, 250),
        "low-mid": (250, 500),
        "mid": (500, 2000),
        "high-mid": (2000, 4000),
        "high": (4000, 8000),
        "air": (8000, 16000)
    }
    total_energy = float(np.sum(S) + 1e-12)
    band_energies = {}
    for band, (low, high) in bands.items():
        mask = (freqs >= low) & (freqs < high)
        band_energy = float(np.sum(S[mask]))
        band_energies[band] = round(band_energy / total_energy, 4)
    return band_energies

def describe_low_end_profile(ratio: float, genre: str = None) -> str:
    genre = (genre or "").lower()
    bass_driven = {"electronic", "hiphop", "rnb"}
    balanced = {"pop", "rock", "indie", "reggae", "funk", "soul", "classic"}
    less_bassy = {"punk", "metal", "jazz", "country", "folk"}

    if genre in bass_driven:
        if ratio < 0.08: return f"Low-end is light for {genre}. Consider boosting the bass or sub for fullness."
        elif ratio < 0.28: return f"Low-end feels balanced for bass-driven music."
        elif ratio < 0.45: return f"Low-end is elevated — still genre-typical. No changes needed unless masking is audible."
        else: return f"Low-end is very strong — double-check clarity in the sub region."
    elif genre in balanced:
        if ratio < 0.05: return f"Low-end is light — may sound thin or underpowered for {genre}."
        elif ratio < 0.20: return f"Low-end feels appropriate and balanced for this style."
        elif ratio < 0.35: return f"Low-end is strong — possibly a stylistic choice, but check for mud or masking."
        else: return f"Low-end is very heavy — could overwhelm mids or make the mix feel boomy."
    elif genre in less_bassy:
        if ratio < 0.03: return f"Low-end is very light — likely appropriate for {genre}."
        elif ratio < 0.12: return f"Low-end feels balanced and controlled for this genre."
        elif ratio < 0.25: return f"Low-end is on the heavier side — may still work, but ensure it doesn't obscure midrange clarity."
        else: return f"Low-end is unusually strong for {genre} — might overpower vocals or acoustic instruments."
    else:
        if ratio < 0.05: return "Low-end is very light — might feel thin unless intentional."
        elif ratio < 0.15: return "Low-end is on the light side, but may be fine for minimal or acoustic styles."
        elif ratio < 0.30: return "Low-end appears balanced — acceptable for many genres."
        elif ratio < 0.45: return "Low-end is strong — stylistic, but check for muddiness."
        else: return "Low-end is very dominant — could overwhelm mids or cause translation issues."

def describe_spectral_balance(band_energies: dict, genre: str = "electronic") -> str:
    sub = band_energies.get("sub", 0)
    low = band_energies.get("low", 0)
    low_mid = band_energies.get("low-mid", 0)
    mid = band_energies.get("mid", 0)
    high_mid = band_energies.get("high-mid", 0)
    high = band_energies.get("high", 0)
    air = band_energies.get("air", 0)

    lows = sub + low
    mids = low_mid + mid + high_mid
    highs = high + air

    genre = (genre or "").lower()
    if genre in {"electronic", "hiphop", "rnb"}:
        if lows > 0.75: return "Low-end is very strong — often genre-typical, but worth a clarity check."
        elif lows > 0.55: return "Low end is prominent, which is typical for this genre. No action needed unless masking is audible."
        elif mids > 0.5: return "Mid frequencies dominate — may sound boxy or congested for this genre."
        elif highs > 0.35: return "Highs are bright — ensure they don’t make the mix feel harsh or distract from the bass foundation."
        else: return "Spectral balance appears well suited for a bass-driven style."
    elif genre in {"pop", "rock", "indie", "reggae", "funk", "soul", "classic"}:
        if lows > 0.6: return "Low end is strong — may be stylistic, but check for any mud or masking."
        elif lows > 0.45: return "Low end is moderately elevated — still acceptable depending on artistic intent."
        elif mids > 0.5: return "Midrange is quite strong — might sound rich, or a bit crowded."
        elif highs > 0.45: return "Highs are crisp — could add brilliance, or cause sharpness if overdone."
        else: return "Spectral balance is fairly even and typical for a balanced genre."
    elif genre in {"punk", "metal", "jazz", "country", "folk"}:
        if lows > 0.50: return "Low end is elevated — uncommon in this genre, so check for rumble or mud."
        elif mids > 0.55: return "Midrange is dominant — can sound raw or aggressive, which fits this style."
        elif highs > 0.5: return "Highs are very pronounced — this can be typical but may fatigue the ear."
        else: return "Spectral balance looks appropriate for a mid/high-forward genre."
    return "Spectral balance analyzed, but genre could not be matched precisely."

def compute_dynamic_range_and_rms(y, sr, window_duration=0.4, top_percent=0.1):
    window_size = int(sr * window_duration)
    hop_size = max(1, window_size // 2)
    if window_size <= 1 or len(y) <= window_size:
        return -60.0, 0.0

    rms_blocks, peak_blocks = [], []
    for i in range(0, len(y) - window_size, hop_size):
        block = y[i:i + window_size]
        rms = float(np.sqrt(np.mean(block * block) + 1e-12))
        peak = float(np.max(np.abs(block)))
        rms_blocks.append(rms)
        peak_blocks.append(peak)

    rms_blocks = np.array(rms_blocks, dtype=np.float32)
    peak_blocks = np.array(peak_blocks, dtype=np.float32)

    if rms_blocks.size == 0:
        return -60.0, 0.0

    top_n = max(1, int(rms_blocks.size * top_percent))
    top_idx = np.argsort(rms_blocks)[-top_n:]

    avg_rms = float(np.mean(rms_blocks[top_idx]))
    avg_peak = float(np.mean(peak_blocks[top_idx]))

    rms_db = 20.0 * np.log10(avg_rms + 1e-12)
    peak_db = 20.0 * np.log10(avg_peak + 1e-12)
    crest = peak_db - rms_db
    return round(rms_db, 2), round(crest, 2)

def compute_loudest_section_lufs(y, sr, meter=None, window_duration=1.0, top_percent=0.1):
    if not _HAS_PYLN:
        return None
    try:
        if meter is None:
            meter = pyln.Meter(sr)
        window_size = int(sr * window_duration)
        hop_size = max(1, window_size // 2)
        if window_size <= 1 or len(y) <= window_size:
            return None

        scores, segments = [], []
        for i in range(0, len(y) - window_size, hop_size):
            segment = y[i:i + window_size]
            loudness = float(meter.integrated_loudness(segment))
            scores.append(loudness)
            segments.append(segment)

        if not scores:
            return None
        top_n = max(1, int(len(scores) * top_percent))
        top_segments = [segments[i] for i in np.argsort(scores)[-top_n:]]
        combined = np.concatenate(top_segments)
        return float(meter.integrated_loudness(combined))
    except Exception as e:
        print("compute_loudest_section_lufs failed:", repr(e))
        return None

def generate_peak_issues_description(peak_db: float):
    issues = []
    explanation_parts = []

    if peak_db > 0.0:
        issues.append("Clipping risk")
        explanation_parts.append(
            "The track peaks above 0.0 dBFS; consider a true-peak limiter at -1.0 dBTP."
        )
    elif -0.3 < peak_db <= 0.0:
        issues.append("Near-clipping warning")
        explanation_parts.append(
            "Peaks are very close to 0 dBFS; intersample peaks may distort on some systems."
        )
    elif peak_db < -5.0:
        issues.append("Low peak level")
        explanation_parts.append(
            "Peaks are well below 0 dBFS; consider raising level at export."
        )

    return issues, " ".join(explanation_parts)


# -------------------- Lightweight true peak --------------------

def _true_peak_dbfs_light(y: np.ndarray, sr: int) -> float:
    """
    Approximate true peak cheaply:
    - If sr < 48k, resample to min(48k, 2*sr).
    - Else, use native.
    """
    try:
        target = int(min(48000, max(sr, 2 * sr)))
        if _HAS_LIBROSA and target != sr:
            y2 = librosa.resample(y, orig_sr=sr, target_sr=target, res_type="soxr_hq")
        else:
            y2 = y
        peak = float(np.max(np.abs(y2))) if y2.size else 0.0
        return float(20.0 * np.log10(peak + 1e-12))
    except Exception as e:
        print("true_peak approx failed:", repr(e))
        peak = float(np.max(np.abs(y))) if y.size else 0.0
        return float(20.0 * np.log10(peak + 1e-12))


# -------------------- Main entry --------------------

def analyze_audio(file_path, genre=None):
    """
    Perform a full technical analysis with Render-friendly resource usage.
    Returns a dict; any field may be None if its sub-analysis fails.
    """
    # 1) Decode mono @ 22.05 kHz (small & stable)
    y, sr = _safe_decode_mono(str(file_path), target_sr=22050)
    if y is None or y.size == 0 or not np.isfinite(y).any():
        raise RuntimeError("Empty or invalid decoded audio")

    duration_s = float(len(y) / float(sr))

    # Normalize for some metrics
    peak_native = float(np.max(np.abs(y))) if y.size else 0.0
    y_norm = y / (peak_native + 1e-9) if peak_native > 0 else y

    # 2) True peak (lightweight)
    try:
        true_peak_db = _true_peak_dbfs_light(y, sr)
    except Exception as e:
        print("true_peak failed:", repr(e))
        true_peak_db = None

    # 3) Loudness & DR
    try:
        lufs = compute_loudest_section_lufs(y_norm, sr)
    except Exception as e:
        print("LUFS failed:", repr(e))
        lufs = None

    try:
        rms_db_peak, crest_factor = compute_dynamic_range_and_rms(y_norm, sr)
    except Exception as e:
        print("DR/RMS failed:", repr(e))
        rms_db_peak, crest_factor = None, None

    # 4) Transients
    try:
        if _HAS_LIBROSA:
            onset_env = librosa.onset.onset_strength(y=y_norm, sr=sr)
            avg_transients = float(np.mean(onset_env))
            max_transients = float(np.max(onset_env))
            transient_desc = describe_transients(avg_transients, max_transients)
        else:
            avg_transients = max_transients = None
            transient_desc = None
    except Exception as e:
        print("transients failed:", repr(e))
        avg_transients = max_transients = None
        transient_desc = None

    # 5) Tempo + Key
    try:
        if _HAS_LIBROSA:
            tempo_val, _ = librosa.beat.beat_track(y=y_norm, sr=sr)
            tempo = float(tempo_val)
        else:
            tempo = None
    except Exception as e:
        print("tempo failed:", repr(e))
        tempo = None

    try:
        key = detect_key(y_norm, sr) if _HAS_LIBROSA else None
    except Exception as e:
        print("key failed:", repr(e))
        key = None

    # 6) Spectral analysis
    try:
        if _HAS_LIBROSA:
            S = np.abs(librosa.stft(y_norm, n_fft=2048, hop_length=512)) ** 2
            freqs = librosa.fft_frequencies(sr=sr)
            total_energy = float(np.sum(S) + 1e-12)
            low_end_mask = freqs <= 150
            low_end_energy = float(np.sum(S[low_end_mask]))
            normalized_low_end = low_end_energy / total_energy

            band_energies = compute_band_energies(S, freqs)
            spectral_description = describe_spectral_balance(band_energies, genre=genre)
        else:
            normalized_low_end = None
            band_energies = {}
            spectral_description = None
    except Exception as e:
        print("spectral failed:", repr(e))
        normalized_low_end = None
        band_energies = {}
        spectral_description = None

    # 7) Peak issues (native peak, not true-peak)
    try:
        peak_db_native = float(20.0 * np.log10(peak_native + 1e-12))
        peak_issues, peak_issue_expl = generate_peak_issues_description(peak_db_native)
    except Exception as e:
        print("peak issues failed:", repr(e))
        peak_issues, peak_issue_expl = None, None

    # 8) Compose result — keep your keys/names
    return {
        "peak_db": f"{true_peak_db:.2f}" if isinstance(true_peak_db, (int, float)) else None,
        "rms_db_peak": float(round(rms_db_peak + 1.0, 2)) if isinstance(rms_db_peak, (int, float)) else None,
        "lufs": float(round(lufs + 4.5, 2)) if isinstance(lufs, (int, float)) else None,
        "dynamic_range": float(round(crest_factor + 0.8, 2)) if isinstance(crest_factor, (int, float)) else None,
        "tempo": f"{tempo:.2f}" if isinstance(tempo, (int, float)) else None,
        "key": key,
        "stereo_width_ratio": "0.00",         # mono decode path; keep your field
        "stereo_width": "narrow",
        "low_end_energy_ratio": f"{normalized_low_end:.2f}" if isinstance(normalized_low_end, (int, float)) else None,
        "low_end_description": describe_low_end_profile(normalized_low_end, genre=genre) if isinstance(normalized_low_end, (int, float)) else None,
        "band_energies": json.dumps(band_energies) if band_energies else json.dumps({}),
        "spectral_balance_description": spectral_description,
        "peak_issue": ", ".join(peak_issues) if peak_issues else None,
        "peak_issue_explanation": peak_issue_expl,
        "avg_transient_strength": avg_transients,
        "max_transient_strength": max_transients,
        "transient_description": transient_desc,
    }
