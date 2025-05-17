import librosa
import numpy as np
import json

def analyze_audio(file_path):
    y, sr = librosa.load(file_path)

    # Compute tempo
    tempo_arr, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo_arr)

    # Peak in dB
    peak_amp = np.max(np.abs(y))
    peak_db = 20 * np.log10(peak_amp + 1e-9)  # Avoid log(0)

    # RMS in dB
    rms_linear = librosa.feature.rms(y=y).mean()
    rms_db = 20 * np.log10(rms_linear + 1e-9)

    # Dynamic range
    dynamic_range = peak_db - rms_db

    # Placeholder for later features
    return {
        "peak_db": round(peak_db, 2),
        "rms_db": round(rms_db, 2),
        "tempo": round(tempo, 2),
        "key": "A minor",         # still placeholder
        "lufs": -9.1,             # placeholder for now
        "dynamic_range": round(dynamic_range, 2),
        "stereo_width": "medium",  # placeholder
        "low_end_energy": 0.8,    # semi-placeholder
        "masking_detected": False, # placeholder
        "issues": json.dumps(["issues"]) # json can take more than one issue
    }