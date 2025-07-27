## Function: `compute_band_energies(S, freqs)`

Calculates the relative energy distribution across predefined frequency bands from a spectral power matrix.

- Bands include sub-bass, low, low-mid, mid, high-mid, high, and air frequency ranges.
- Normalizes energy per band relative to total spectral energy.
- Returns a dictionary mapping band names to normalized energy values.

**Inputs:**  
- `S`: Power spectrogram (numpy array).  
- `freqs`: Array of corresponding frequencies (numpy array).

**Output:**  
- Dictionary of normalized band energy ratios.

**Design Notes:**  
- Useful for spectral balance assessment.  
- Designed for clear band separation in audio frequency spectrum.