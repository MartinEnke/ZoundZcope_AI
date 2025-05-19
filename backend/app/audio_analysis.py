import librosa
import numpy as np
import json
import pyloudnorm as pyln
import math


def detect_key(y, sr):
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)

    # Define major and minor key profiles (Krumhansl-Schmuckler)
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                              2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                              2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

    # Compare to all 12 pitch classes
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


def analyze_audio(file_path):
    y, sr = librosa.load(file_path, mono=False)
    print(f"y shape: {y.shape}, ndim: {y.ndim}")

    # Create mono version for analysis functions that require it
    y_mono = librosa.to_mono(y)

    # Peak in dB
    peak_amp = np.max(np.abs(y_mono))
    peak_db = 20 * np.log10(peak_amp + 1e-9)  # Avoid log(0)

    # RMS in dB
    rms_linear = librosa.feature.rms(y=y_mono).mean()
    rms_db = 20 * np.log10(rms_linear + 1e-9)

    # Compute tempo
    tempo_arr, _ = librosa.beat.beat_track(y=y_mono, sr=sr)
    tempo = float(tempo_arr)

    # key detection
    key = detect_key(y_mono, sr)

    # lufs
    meter = pyln.Meter(sr) # sample rate
    loudness = meter.integrated_loudness(y_mono)

    # Dynamic range
    dynamic_range = peak_db - rms_db


    # Compute stereo-width
    # Stereo width from original stereo signal
    # Default fallback
    width_ratio = 0.0

    if y.ndim == 1:
        stereo_width_label = "narrow"
    else:
        mid = (y[0] + y[1]) / 2
        side = (y[0] - y[1]) / 2
        width_ratio = np.mean(np.abs(side)) / (np.mean(np.abs(mid)) + 1e-9)

        if not math.isfinite(width_ratio):
            width_ratio = 0.0  # prevent NaN or inf
            stereo_width_label = "narrow"
        elif width_ratio < 0.25:
            stereo_width_label = "narrow"
        elif width_ratio < 0.6:
            stereo_width_label = "medium"
        elif width_ratio < 1.2:
            stereo_width_label = "wide"
        else:
            stereo_width_label = "too wide"

    # Compute Short-Time Fourier Transform (power spectrogram)
    S = np.abs(librosa.stft(y_mono)) ** 2
    freqs = librosa.fft_frequencies(sr=sr)

    # Mask to keep only low frequencies (e.g., under 150 Hz)
    low_freq_mask = freqs <= 150
    low_energy = S[low_freq_mask, :]

    # Compute energy
    low_end_energy = np.sum(low_energy)
    total_energy = np.sum(S)
    normalized_low_end = low_end_energy / (total_energy + 1e-9)

    if normalized_low_end < 0.1:
        bass_profile = "light"
    elif normalized_low_end < 0.3:
        bass_profile = "balanced"
    else:
        bass_profile = "bass heavy"

    print(f"Low-End Raw: {low_end_energy:.3f} | Total: {total_energy:.3f} | Ratio: {normalized_low_end:.3f}")

    # ========== Basic Masking Detection ==========
    # Define frequency bands
    bands = {
        "sub": (20, 60),
        "low": (60, 250),
        "mid": (250, 2000),
        "high": (2000, 6000),
        "air": (6000, 16000)
    }

    band_energies = {}
    for band, (low, high) in bands.items():
        mask = (freqs >= low) & (freqs < high)
        band_energy = np.mean(S[mask])
        band_energies[band] = band_energy

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
        "band_energies": json.dumps({k: round(float(v), 2) for k, v in band_energies.items()}),
        "issues": json.dumps(["issues"])
    }


