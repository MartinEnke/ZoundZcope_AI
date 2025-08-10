"""
Audio analysis module for ZoundZcope.

This module extracts and interprets a range of technical and musical
features from uploaded audio tracks. It is used by the backend to
generate detailed analysis data for AI feedback, reporting, and
comparisons.

Main capabilities:
- **True Peak Detection** (with optional oversampling to catch intersample peaks)
- **Loudness Measurement** (LUFS, RMS, and crest factor)
- **Transient Analysis** (average/max strength with descriptive categorization)
- **Tempo & Key Detection** (via beat tracking and chroma correlation)
- **Stereo Width Measurement** (mid/side ratio and qualitative label)
- **Frequency Band Energy Analysis** (sub to air, normalized ratios)
- **Low-End Profile & Spectral Balance** descriptions (genre-aware)
- **Peak Issue Detection** (clipping risk, low level warnings)
- **Dynamic Range Calculation** (based on top-loudness segments)

Returned analysis is structured as a dictionary, with each key providing
either a numeric value or a descriptive string that can be used for
display in the UI, storage in the database, or inclusion in AI prompts.
"""
import numpy as np

# Fix deprecated alias for compatibility with newer numpy
if not hasattr(np, 'complex'):
    np.complex = complex

import librosa
import json
import pyloudnorm as pyln
import math


def detect_key(y, sr):
    """
        Detect the musical key of an audio signal.

        Parameters
        ----------
        y : np.ndarray
            Audio time series (mono or stereo), normalized or raw.
        sr : int
            Sampling rate of the audio signal.

        Returns
        -------
        str
            Estimated musical key in the format '<Note> Major' or '<Note> minor'.

        Notes
        -----
        Uses chroma features and correlation against
        the Krumhansl–Kessler key profiles.
        """
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
    """
        Compute normalized energy distribution across predefined frequency bands.

        Parameters
        ----------
        S : np.ndarray
            Spectrogram magnitude (power) values.
        freqs : np.ndarray
            Corresponding frequency bins for `S`.

        Returns
        -------
        dict
            Mapping of band names ('sub', 'low', 'low-mid', etc.) to
            normalized energy ratios (0.0–1.0).
        """
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


def describe_low_end_profile(ratio: float, genre: str = None) -> str:
    """
        Provide a genre-aware interpretation of low-end energy ratio.

        Parameters
        ----------
        ratio : float
            Fraction of total energy in the low-end region (≤150 Hz).
        genre : str, optional
            Musical genre to adjust thresholds and phrasing.

        Returns
        -------
        str
            Human-readable description of low-end presence and possible mix issues.
        """
    genre = (genre or "").lower()

    bass_driven = {"electronic", "hiphop", "rnb"}
    balanced = {"pop", "rock", "indie", "reggae", "funk", "soul", "classic"}
    less_bassy = {"punk", "metal", "jazz", "country", "folk"}

    if genre in bass_driven:
        if ratio < 0.08:
            return f"Low-end is light for {genre}. Consider boosting the bass or sub for fullness."
        elif ratio < 0.28:
            return f"Low-end feels balanced for bass-driven music."
        elif ratio < 0.45:
            return f"Low-end is elevated — still genre-typical. No changes needed unless masking is audible."
        else:
            return f"Low-end is very strong — double-check clarity in the sub region."

    elif genre in balanced:
        if ratio < 0.05:
            return f"Low-end is light — may sound thin or underpowered for {genre}."
        elif ratio < 0.20:
            return f"Low-end feels appropriate and balanced for this style."
        elif ratio < 0.35:
            return f"Low-end is strong — possibly a stylistic choice, but check for mud or masking."
        else:
            return f"Low-end is very heavy — could overwhelm mids or make the mix feel boomy."

    elif genre in less_bassy:
        if ratio < 0.03:
            return f"Low-end is very light — likely appropriate for {genre}."
        elif ratio < 0.12:
            return f"Low-end feels balanced and controlled for this genre."
        elif ratio < 0.25:
            return f"Low-end is on the heavier side — may still work, but ensure it doesn't obscure midrange clarity."
        else:
            return f"Low-end is unusually strong for {genre} — might overpower vocals or acoustic instruments."

    else:
        # Fallback for unknown genres
        if ratio < 0.05:
            return "Low-end is very light — might feel thin unless intentional."
        elif ratio < 0.15:
            return "Low-end is on the light side, but may be fine for minimal or acoustic styles."
        elif ratio < 0.30:
            return "Low-end appears balanced — acceptable for many genres."
        elif ratio < 0.45:
            return "Low-end is strong — stylistic, but check for muddiness."
        else:
            return "Low-end is very dominant — could overwhelm mids or cause translation issues."


def describe_spectral_balance(band_energies: dict, genre: str = "electronic") -> str:
    """
        Generate a qualitative description of the track's spectral balance.

        Parameters
        ----------
        band_energies : dict
            Mapping of frequency band names to normalized energy ratios
            (0.0–1.0). Expected keys include:
            - 'sub'
            - 'low'
            - 'low-mid'
            - 'mid'
            - 'high-mid'
            - 'high'

        Returns
        -------
        str
            Human-readable description summarizing the relative balance
            between low, mid, and high frequency regions.

        Notes
        -----
        The function groups bands into three regions:
        - Lows: 'sub', 'low'
        - Mids: 'low-mid', 'mid'
        - Highs: 'high-mid', 'high'

        It then compares their average energy to determine if the spectrum
        is balanced, low-heavy, mid-heavy, or high-heavy.
        """
    # Collapse to simple groups
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

    genre = genre.lower()

    if genre in {"electronic", "hiphop", "rnb"}:
        if lows > 0.75:
            return "Low-end is very strong — often genre-typical, but worth a clarity check."
        elif lows > 0.55:
            return "Low end is prominent, which is typical for this genre. No action needed unless masking is audible."
        elif mids > 0.5:
            return "Mid frequencies dominate — may sound boxy or congested for this genre."
        elif highs > 0.35:
            return "Highs are bright — ensure they don’t make the mix feel harsh or distract from the bass foundation."
        else:
            return "Spectral balance appears well suited for a bass-driven style."

    elif genre in {"pop", "rock", "indie", "reggae", "funk", "soul", "classic"}:
        if lows > 0.6:
            return "Low end is strong — may be stylistic, but check for any mud or masking."
        elif lows > 0.45:
            return "Low end is moderately elevated — still acceptable depending on artistic intent."
        elif mids > 0.5:
            return "Midrange is quite strong — might sound rich, or a bit crowded."
        elif highs > 0.45:
            return "Highs are crisp — could add brilliance, or cause sharpness if overdone."
        else:
            return "Spectral balance is fairly even and typical for a balanced genre."

    elif genre in {"punk", "metal", "jazz", "country", "folk"}:
        if lows > 0.50:
            return "Low end is elevated — uncommon in this genre, so check for rumble or mud."
        elif mids > 0.55:
            return "Midrange is dominant — can sound raw or aggressive, which fits this style."
        elif highs > 0.5:
            return "Highs are very pronounced — this can be typical but may fatigue the ear."
        else:
            return "Spectral balance looks appropriate for a mid/high-forward genre."

    return "Spectral balance analyzed, but genre could not be matched precisely."


def compute_dynamic_range_and_rms(y, sr, window_duration=0.4, top_percent=0.1):
    """
        Compute the dynamic range (crest factor) and RMS level of the loudest
        sections in an audio signal.

        Parameters
        ----------
        y : np.ndarray
            Audio time series (mono or stereo). If stereo, should already be
            mixed down to mono before calling this function.
        sr : int
            Sampling rate of the audio in Hz.
        window_duration : float, optional
            Length of analysis window in seconds (default is 0.4s).
        top_percent : float, optional
            Fraction of the loudest windows (by RMS) to include in the calculation.
            Must be between 0.0 and 1.0. Default is 0.1 (top 10%).

        Returns
        -------
        rms_db : float
            Average RMS level of the selected loudest sections, in decibels (dBFS).
        crest_factor : float
            Difference between peak and RMS levels (crest factor) in dB.

        Notes
        -----
        - The crest factor is a common measure of dynamic range, with higher
          values indicating more transient-rich material.
        - The function uses overlapping windows with 50% hop size.
        """
    window_size = int(sr * window_duration)
    hop_size = int(window_size // 2)

    rms_blocks = []
    peak_blocks = []

    for i in range(0, len(y) - window_size, hop_size):
        block = y[i:i + window_size]
        rms = np.sqrt(np.mean(block ** 2))
        peak = np.max(np.abs(block))
        rms_blocks.append(rms)
        peak_blocks.append(peak)

    rms_blocks = np.array(rms_blocks)
    peak_blocks = np.array(peak_blocks)

    # Focus on top X% loudest blocks
    top_n = max(1, int(len(rms_blocks) * top_percent))
    top_indices = np.argsort(rms_blocks)[-top_n:]

    top_rms = rms_blocks[top_indices]
    top_peaks = peak_blocks[top_indices]

    avg_rms = np.mean(top_rms)
    avg_peak = np.mean(top_peaks)

    # Convert to dB
    rms_db = 20 * np.log10(avg_rms + 1e-9)
    peak_db = 20 * np.log10(avg_peak + 1e-9)
    crest = peak_db - rms_db

    return round(rms_db, 2), round(crest, 2)


def compute_loudest_section_lufs(y, sr, meter=None, window_duration=1.0, top_percent=0.1):
    """
        Compute the integrated LUFS (Loudness Units Full Scale) of the loudest
        sections in an audio signal.

        Parameters
        ----------
        y : np.ndarray
            Audio time series (mono or stereo). If stereo, should be mixed down
            to mono before calling for consistent results.
        sr : int
            Sampling rate of the audio in Hz.
        window_duration : float, optional
            Length of each loudness analysis window in seconds.
            Default is 3.0s.
        top_percent : float, optional
            Fraction of the loudest windows (by LUFS) to include in the calculation.
            Must be between 0.0 and 1.0. Default is 0.1 (top 10%).

        Returns
        -------
        float
            Integrated LUFS of the selected loudest sections, in LUFS (negative dB).

        Notes
        -----
        - LUFS is measured using the ITU-R BS.1770 algorithm via the
          `pyloudnorm` library.
        - This function focuses on the loudest moments of the track,
          making it useful for mastering-level loudness checks.
        - More negative LUFS values indicate quieter audio.
        """
    if meter is None:
        meter = pyln.Meter(sr)

    window_size = int(sr * window_duration)
    hop_size = window_size // 2
    scores = []
    segments = []

    for i in range(0, len(y) - window_size, hop_size):
        segment = y[i:i + window_size]
        loudness = meter.integrated_loudness(segment)
        scores.append(loudness)
        segments.append(segment)

    # Sort by loudness, keep top X%
    top_n = max(1, int(len(scores) * top_percent))
    top_segments = [segments[i] for i in np.argsort(scores)[-top_n:]]
    combined = np.concatenate(top_segments)

    return meter.integrated_loudness(combined)


def compute_true_peak(y, sr, target_sr=192000):
    """
        Compute the true peak level of an audio signal.

        Parameters
        ----------
        y : np.ndarray
            Audio time series (mono or stereo).
        sr : int
            Sampling rate of the audio in Hz.
        oversample_factor : int, optional
            Factor by which to oversample the audio before peak detection.
            Higher values improve accuracy but increase computation time.
            Default is 4.

        Returns
        -------
        float
            True peak level in decibels full scale (dBFS).

        Notes
        -----
        - True peak measures the maximum instantaneous signal level
          after reconstruction, accounting for inter-sample peaks.
        - Oversampling helps detect peaks that may exceed 0 dBFS even if
          the discrete samples are below 0.
        - A true peak close to 0 dBFS can indicate risk of clipping during
          playback or conversion.
        """
    if sr >= target_sr:
        upsampled = y
    else:
        upsampled = librosa.resample(y, orig_sr=sr, target_sr=target_sr)

    true_peak_amp = np.max(np.abs(upsampled))
    true_peak_db = 20 * np.log10(true_peak_amp + 1e-9)

    return round(true_peak_db, 2)


def detect_transient_strength(y, sr):
    """
        Measure the transient strength of an audio signal.

        Parameters
        ----------
        y : np.ndarray
            Audio time series (mono or stereo).
        sr : int
            Sampling rate of the audio in Hz.

        Returns
        -------
        avg_transient_strength : float
            Average onset strength across the entire track.
        max_transient_strength : float
            Maximum onset strength observed in the track.

        Notes
        -----
        - Transients represent sudden increases in amplitude, typically from
          percussive sounds like drum hits or plucked strings.
        - Onset strength is calculated using `librosa.onset.onset_strength`.
        - Average strength gives an overall measure of track punchiness,
          while the maximum indicates the most prominent transient.
        - These values are useful for detecting whether a mix is punchy,
          balanced, or lacking attack.
        """
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    avg_transient_strength = float(np.mean(onset_env))
    max_transient_strength = float(np.max(onset_env))
    return round(avg_transient_strength, 4), round(max_transient_strength, 4)


def describe_transients(avg, max):
    """
        Generate a qualitative description of a track's transients based on
        average and maximum transient strength.

        Parameters
        ----------
        avg : float
            Average transient strength value, typically from `detect_transient_strength`.
        max : float
            Maximum transient strength value, typically from `detect_transient_strength`.

        Returns
        -------
        description : str
            A descriptive sentence summarizing the transient quality, including
            both overall punchiness and peak transient characteristics.

        Notes
        -----
        - The function uses threshold-based classification to label transients
          as "soft", "balanced", "punchy", or "sharp".
        - It also provides an additional note based on the maximum transient
          strength to indicate whether transients are excessively spiky or
          unusually soft.
        - This qualitative feedback can help identify potential mixing issues
          such as over-compression, excessive transient shaping, or insufficient
          attack on percussion.
        """
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
    """
        Analyze the peak level of an audio track and return a list of
        potential issues along with explanatory text.

        Parameters
        ----------
        peak_db : float
            Peak amplitude of the track in decibels relative to full scale (dBFS).
            Positive values indicate peaks above 0 dBFS, while negative values
            indicate headroom below full scale.

        Returns
        -------
        issues : list of str
            Short labels describing potential problems, e.g.
            ["Clipping risk", "Low peak level"].
        explanation : str
            A longer descriptive explanation providing context for the issues
            and suggesting corrective actions.

        Notes
        -----
        - If `peak_db` > 0.0, the track is considered at risk of digital clipping.
        - If -0.3 < `peak_db` <= 0.0, it is considered near-clipping and may
          cause intersample peaks.
        - If `peak_db` < -5.0, the track's peak level is unusually low, which
          could indicate poor gain staging.
        - The returned explanation is intended for display in analysis reports
          or user-facing feedback.
        """
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


def analyze_audio(file_path, genre=None):
    """
        Perform a full technical analysis of an audio file.

        Parameters
        ----------
        file_path : str
            Path to the audio file to analyze.
        genre : str, optional
            Musical genre for context-aware analysis.

        Returns
        -------
        dict
            Dictionary containing extracted audio features and descriptive labels:
            - peak_db, rms_db_peak, lufs, dynamic_range
            - tempo, key, stereo_width_ratio, stereo_width
            - low_end_energy_ratio, low_end_description
            - band_energies (JSON string), spectral_balance_description
            - peak_issue, peak_issue_explanation
            - avg_transient_strength, max_transient_strength, transient_description
        """
    y, sr = librosa.load(file_path, mono=True)

    # ----- TRUE PEAK (oversampled) -----
    true_peak_db = compute_true_peak(y, sr)

    # ----- NORMALIZE to 0 dBFS -----
    y_norm = y / (np.max(np.abs(y)) + 1e-9)

    # ----- LOUDNESS METRICS -----
    lufs = compute_loudest_section_lufs(y_norm, sr)
    rms_db_peak, crest_factor = compute_dynamic_range_and_rms(y_norm, sr)

    # ----- TRANSIENTS -----
    avg_transients, max_transients = detect_transient_strength(y_norm, sr)

    # ----- TEMPO + KEY -----
    tempo_arr, _ = librosa.beat.beat_track(y=y_norm, sr=sr)
    tempo = float(tempo_arr)
    key = detect_key(y_norm, sr)

    # ----- STEREO WIDTH -----
    if y.ndim == 1:
        stereo_width_label = "narrow"
        width_ratio = 0.0
    else:
        mid = (y[0] + y[1]) / 2
        side = (y[0] - y[1]) / 2
        width_ratio = np.mean(np.abs(side)) / (np.mean(np.abs(mid)) + 1e-9)

        if not math.isfinite(width_ratio):
            stereo_width_label = "narrow"
            width_ratio = 0.0
        elif width_ratio < 0.25:
            stereo_width_label = "narrow"
        elif width_ratio < 0.6:
            stereo_width_label = "medium"
        elif width_ratio < 1.2:
            stereo_width_label = "wide"
        else:
            stereo_width_label = "too wide"

    # ----- FREQUENCY ANALYSIS -----
    S = np.abs(librosa.stft(y_norm, n_fft=2048, hop_length=512)) ** 2
    freqs = librosa.fft_frequencies(sr=sr)
    total_energy = np.sum(S)

    low_end_mask = freqs <= 150
    low_end_energy = np.sum(S[low_end_mask])
    normalized_low_end = low_end_energy / (total_energy + 1e-9)

    low_end_description = describe_low_end_profile(normalized_low_end, genre=genre)
    band_energies = compute_band_energies(S, freqs)
    spectral_description = describe_spectral_balance(band_energies, genre=genre)

    # ----- PEAK ISSUES -----
    peak_amp = np.max(np.abs(y))
    peak_db = 20 * np.log10(peak_amp + 1e-9)
    peak_issues, peak_explanation_parts = generate_peak_issues_description(peak_db)

    if peak_db < -3.0 and rms_db_peak > -15.0:
        peak_issues.append("Low peak level without dynamic benefit")
        peak_explanation_parts.append(
            "The track peaks well below 0 dBFS, but the average loudness remains high. "
            "This suggests the level was lowered without gaining extra dynamic range. "
            "Consider exporting at full scale unless you're preparing for mastering."
        )

    return {
        "peak_db": f"{true_peak_db:.2f}",
        "rms_db_peak": float(round(rms_db_peak + 1.0, 2)),
        "lufs": float(round(lufs + 4.5, 2)),
        "dynamic_range": float(round(crest_factor + 0.8, 2)),
        "tempo": f"{tempo:.2f}",
        "key": key,
        "stereo_width_ratio": f"{width_ratio:.2f}",
        "stereo_width": stereo_width_label,
        "low_end_energy_ratio": f"{normalized_low_end:.2f}",
        "low_end_description": low_end_description,
        "band_energies": json.dumps(band_energies),
        "spectral_balance_description": spectral_description,
        "peak_issue": ", ".join(peak_issues) if peak_issues else None,
        "peak_issue_explanation": " ".join(peak_explanation_parts),
        "avg_transient_strength": avg_transients,
        "max_transient_strength": max_transients,
        "transient_description": describe_transients(avg_transients, max_transients)
    }
