
## Function: `compute_windowed_rms_db(y_mono, sr, window_duration=0.5)`

Calculates average and peak RMS (root mean square) loudness in dB over sliding windows.

- Splits audio into overlapping windows.  
- Computes RMS per window, then averages and finds the loudest 10% peak.  
- Converts values to decibels (dB).

**Inputs:**  
- `y_mono`: Mono audio time series.  
- `sr`: Sampling rate.  
- `window_duration`: Duration of windows in seconds (default 0.5s).

**Output:**  
- Tuple of average RMS dB and peak RMS dB.

**Design Notes:**  
- Mimics perceptual loudness metrics.  
- Helps identify loudness dynamics over time.