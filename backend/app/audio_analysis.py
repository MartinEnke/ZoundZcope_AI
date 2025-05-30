import numpy as np

# Fix deprecated alias for compatibility with newer numpy
if not hasattr(np, 'complex'):
    np.complex = complex

import librosa
import json
import pyloudnorm as pyln
import math


def detect_key(y, sr):
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)

    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                              2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                              2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

    best_corr = -1
    best_key = ""
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F',
                  'F#', 'G', 'G#', 'A', 'A#', 'B']
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

    total_energy = np.sum(S)
    band_energies = {}

    for band, (low, high) in bands.items():
        mask = (freqs >= low) & (freqs < high)
        band_energy = np.sum(S[mask])
        band_energies[band] = round(float(band_energy / (total_energy + 1e-9)), 4)

    return band_energies


def describe_low_end_profile(ratio):
    if ratio < 0.05:
        return "Very light bass presence – the low-end might feel thin."
    elif ratio < 0.10:
        return "Light low-end – possibly lacking warmth or weight."
    elif ratio < 0.20:
        return "Balanced low-end – generally acceptable for most genres."
    elif ratio < 0.35:
        return "Bass-forward – might be powerful but risks mud in dense mixes."
    else:
        return "Very heavy low-end – could overwhelm mids/highs or translate poorly."


def describe_spectral_balance(band_energies: dict) -> str:
    # Simplify keys for easier math
    sub = band_energies.get("sub", 0)
    low = band_energies.get("low", 0)
    low_mid = band_energies.get("low-mid", 0)
    mid = band_energies.get("mid", 0)
    high_mid = band_energies.get("high-mid", 0)
    high = band_energies.get("high", 0)
    air = band_energies.get("air", 0)

    lows = sub + low
    highs = high + air
    mids = low_mid + mid + high_mid

    # Use ratios to describe balance
    if highs > 0.35 and highs > mids and highs > lows:
        return "High frequencies dominate. May sound bright or harsh."
    elif lows > 0.35 and lows > mids and lows > highs:
        return "Low frequencies dominate. May sound muddy or boomy."
    elif mids > 0.4 and mids > highs and mids > lows:
        return "Mid frequencies dominate. May sound boxy or honky."
    elif 0.25 < highs < 0.35 and 0.25 < lows < 0.35:
        return "Spectral balance appears fairly even across lows, mids, and highs."
    else:
        return "Unusual spectral balance. Further inspection may be needed."


def compute_windowed_rms_db(y_mono, sr, window_duration=0.5):
    window_size = int(sr * window_duration)
    hop_size = int(window_size / 2)

    rms_blocks = []
    for i in range(0, len(y_mono) - window_size, hop_size):
        block = y_mono[i:i + window_size]
        rms = np.sqrt(np.mean(block ** 2))
        rms_blocks.append(rms)

    # Now calculate:
    rms_blocks = np.array(rms_blocks)
    rms_db_avg = 20 * np.log10(np.mean(rms_blocks) + 1e-9)

    # Loudest 10%
    sorted_rms = np.sort(rms_blocks)
    top_10 = sorted_rms[int(len(sorted_rms) * 0.9):]
    rms_db_peak = 20 * np.log10(np.mean(top_10) + 1e-9)

    return round(rms_db_avg, 2), round(rms_db_peak, 2)


def detect_transient_strength(y, sr):
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    avg_transient_strength = float(np.mean(onset_env))
    max_transient_strength = float(np.max(onset_env))
    return round(avg_transient_strength, 4), round(max_transient_strength, 4)


def describe_transients(avg, max):
    if avg < 1.5:
        quality = "very soft or buried"
    elif avg < 3.5:
        quality = "balanced"
    elif avg < 7:
        quality = "punchy and defined"
    else:
        quality = "sharp or overly spiky"

    if max > 30:
        note = "The track has extremely spiky transients — possibly over-accentuated drums or uncompressed attacks."
    elif max > 15:
        note = "Transients are strong and pronounced — mix might feel punchy or aggressive."
    elif max < 5:
        note = "Transients appear soft throughout — the mix may lack snap or attack."
    else:
        note = "Transient range appears normal for most styles."

    return f"Transients are {quality}. {note}"


def generate_peak_issues_description(peak_db: float):
    issues = []
    explanation_parts = []

    if peak_db > 0.0:
        issues.append("Clipping risk")
        explanation_parts.append(
            "The track peaks above 0.0 dBFS, which can result in digital clipping. "
            "Even if your DAW meters show 0.0 dB, intersample peaks may exceed this in real-world playback. "
            "Consider using a true peak limiter set to -1.0 dBTP to avoid distortion."
        )
    elif -0.3 < peak_db <= 0.0:
        issues.append("Near-clipping warning")
        explanation_parts.append(
            "The track peaks very close to 0.0 dBFS. While it may not clip outright, "
            "there is a risk of intersample peaks causing distortion on some playback systems. "
            "A ceiling of -1.0 dBTP is generally safer."
        )
    elif peak_db < -5.0:
        issues.append("Low peak level")
        explanation_parts.append(
            "The track peaks well below typical full-scale levels. "
            "This might indicate improper gain staging and can affect metering or plugin behavior. "
            "Consider raising the level during export to reach closer to 0 dBFS without clipping."
        )

    return issues, " ".join(explanation_parts)


def analyze_audio(file_path):
    y, sr = librosa.load(file_path, mono=False)
    print(f"y shape: {y.shape}, ndim: {y.ndim}")

    y_mono = librosa.to_mono(y)

    # 🎯 True peak measurement (preserved)
    peak_amp = np.max(np.abs(y_mono))
    peak_db = 20 * np.log10(peak_amp + 1e-9)

    # ✅ Normalize to 0 dBFS for consistent analysis
    y_norm = y_mono / (peak_amp + 1e-9)

    # ✅ Compute loudness + RMS on normalized audio
    rms_db_avg, rms_db_peak = compute_windowed_rms_db(y_norm, sr)
    meter = pyln.Meter(sr)
    loudness = meter.integrated_loudness(y_norm)

    # 🧠 Get peak issue info from unnormalized peak
    peak_issues, peak_explanation_parts = generate_peak_issues_description(peak_db)
    peak_explanation_parts = [peak_explanation_parts] if isinstance(peak_explanation_parts,
                                                                    str) else peak_explanation_parts
    issues = []
    pass

    # ✅ warn user if peak is low *and* RMS is still high
    if peak_db < -3.0 and rms_db_avg > -15.0:
        peak_issues.append("Low peak level without dynamic benefit")
        peak_explanation_parts.append(
            "The track peaks well below 0 dBFS, but the average loudness remains high. "
            "This suggests the level was lowered without gaining extra dynamic range. "
            "Consider exporting at full scale unless you're preparing for mastering."
        )

    # ✅ Transient strength (on normalized signal)
    avg_transients, max_transients = detect_transient_strength(y_norm, sr)

    # ✅ Tempo and key detection on normalized audio
    tempo_arr, _ = librosa.beat.beat_track(y=y_norm, sr=sr)
    tempo = float(tempo_arr)
    key = detect_key(y_norm, sr)

    # 🧮 Dynamic range (still meaningful with normalized signal)
    dynamic_range = peak_db - rms_db_avg  # This reflects actual range even after norm

    # ✅ Stereo width (must use original y to retain L/R difference)
    width_ratio = 0.0
    if y.ndim == 1:
        stereo_width_label = "narrow"
    else:
        mid = (y[0] + y[1]) / 2
        side = (y[0] - y[1]) / 2
        width_ratio = np.mean(np.abs(side)) / (np.mean(np.abs(mid)) + 1e-9)

        if not math.isfinite(width_ratio):
            width_ratio = 0.0
            stereo_width_label = "narrow"
        elif width_ratio < 0.25:
            stereo_width_label = "narrow"
        elif width_ratio < 0.6:
            stereo_width_label = "medium"
        elif width_ratio < 1.2:
            stereo_width_label = "wide"
        else:
            stereo_width_label = "too wide"

    # ✅ Spectral analysis (on normalized signal)
    S = np.abs(librosa.stft(y_norm, n_fft=2048, hop_length=512)) ** 2
    freqs = librosa.fft_frequencies(sr=sr)
    total_energy = np.sum(S)

    low_end_mask = freqs <= 150
    low_end_energy = np.sum(S[low_end_mask])
    normalized_low_end = low_end_energy / (total_energy + 1e-9)
    low_end_description = describe_low_end_profile(normalized_low_end)

    if normalized_low_end < 0.1:
        bass_profile = "light"
    elif normalized_low_end < 0.3:
        bass_profile = "balanced"
    else:
        bass_profile = "bass heavy"

    band_energies = compute_band_energies(S, freqs)
    spectral_description = describe_spectral_balance(band_energies)

    return {
        "peak_db": f"{peak_db:.2f}",
        "rms_db_avg": round(float(rms_db_avg), 2),
        "rms_db_peak": round(float(rms_db_peak), 2),
        "tempo": f"{tempo:.2f}",
        "key": key,
        "lufs": f"{loudness:.2f}",
        "dynamic_range": f"{dynamic_range:.2f}",
        "stereo_width_ratio": f"{width_ratio:.2f}",
        "stereo_width": stereo_width_label,
        "low_end_energy_ratio": f"{normalized_low_end:.2f}",
        "bass_profile": bass_profile,
        "low_end_description": low_end_description,
        "band_energies": json.dumps(band_energies),
        "spectral_balance_description": spectral_description,
        "peak_issue": ", ".join(peak_issues) if peak_issues else None,
        "peak_issue_explanation": " ".join(peak_explanation_parts),
        "avg_transient_strength": avg_transients,
        "max_transient_strength": max_transients,
        "transient_description": describe_transients(avg_transients, max_transients),
        "issues": json.dumps(issues)
    }
