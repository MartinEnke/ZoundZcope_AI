## Function: `detect_key(y, sr)`

Determines the musical key of an audio signal by analyzing its chroma features.

- Computes the chromagram using Constant-Q Transform (CQT).
- Compares the chroma profile against predefined major and minor key templates using correlation.
- Returns the best matching key as a string (e.g., "C Major", "A minor").

**Inputs:**  
- `y`: Audio time series (numpy array).  
- `sr`: Sampling rate (int).

**Output:**  
- Detected musical key (str).

**Design Notes:**  
- Uses statistical correlation to identify key signature.  
- Considers both major and minor possibilities for each root note.