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



def analyze_audio(file_path):
    y, sr = librosa.load(file_path, mono=False)
    print(f"y shape: {y.shape}, ndim: {y.ndim}")

    y_mono = librosa.to_mono(y)

    peak_amp = np.max(np.abs(y_mono))
    peak_db = 20 * np.log10(peak_amp + 1e-9)

    rms_linear = librosa.feature.rms(y=y_mono).mean()
    rms_db = 20 * np.log10(rms_linear + 1e-9)

    tempo_arr, _ = librosa.beat.beat_track(y=y_mono, sr=sr)
    tempo = float(tempo_arr)

    key = detect_key(y_mono, sr)

    meter = pyln.Meter(sr)
    loudness = meter.integrated_loudness(y_mono)

    dynamic_range = peak_db - rms_db

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

    S = np.abs(librosa.stft(y_mono, n_fft=2048, hop_length=512)) ** 2
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
        "rms_db": f"{rms_db:.2f}",
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
        "issues": json.dumps(["issues"])
    }
