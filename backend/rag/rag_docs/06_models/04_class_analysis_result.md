## Class: AnalysisResult

Stores detailed audio analysis results for a track.

### Fields

- `id` (Integer, Primary Key): Unique identifier.  
- `track_id` (String, Foreign Key): Reference to the associated `Track`.  
- `peak_db` (Float): Peak decibel level.  
- `rms_db_avg` (Float): Average RMS loudness.  
- `rms_db_peak` (Float): Peak RMS loudness.  
- `lufs` (Float): Loudness Units relative to Full Scale.  
- `dynamic_range` (Float): Difference between peak and RMS levels.  
- `stereo_width_ratio` (Float): Numeric stereo width metric.  
- `stereo_width` (String): Descriptive stereo width label (e.g., "narrow").  
- `key` (String): Detected musical key.  
- `tempo` (Float): Estimated tempo in BPM.  
- `low_end_energy_ratio` (Float): Ratio of low-frequency energy.  
- `low_end_description` (String): Textual description of low-end character.  
- `band_energies` (String): JSON string representing energy distribution by frequency bands.  
- `spectral_balance_description` (String): Description of spectral balance characteristics.  
- `issues` (Text): JSON array string describing detected issues (e.g., clipping).  
- `peak_issue` (Text): Text describing peak-related issues.  
- `peak_issue_explanation` (Text): Explanation for peak issues.  
- `avg_transient_strength` (Float): Average transient strength metric.  
- `max_transient_strength` (Float): Maximum transient strength metric.  
- `transient_description` (Text): Descriptive text about transient quality.

### Relationships

- `track`: One-to-one relationship to `Track`.