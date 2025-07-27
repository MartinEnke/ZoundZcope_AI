## Function: `describe_spectral_balance(band_energies: dict, genre: str = "electronic")`

Analyzes and summarizes the spectral energy distribution into broad frequency regions and interprets the balance relative to genre norms.

- Collapses bands into lows, mids, highs.  
- Applies genre-specific logic to describe tonal balance and highlight potential issues.

**Inputs:**  
- `band_energies`: Dictionary of frequency band energies.  
- `genre`: Genre string for contextual interpretation.

**Output:**  
- Descriptive string assessing spectral balance.

**Design Notes:**  
- Focuses on common production genres.  
- Alerts to mix characteristics like muddiness or harshness.