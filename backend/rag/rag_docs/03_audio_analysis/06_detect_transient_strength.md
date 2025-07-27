## Function: `detect_transient_strength(y, sr)`

Measures the average and maximum transient strength in an audio signal.

- Uses onset envelope estimation to quantify transient activity.  
- Returns rounded average and max transient strengths.

**Inputs:**  
- `y`: Audio signal.  
- `sr`: Sampling rate.

**Output:**  
- Tuple (average transient strength, max transient strength).

**Design Notes:**  
- Indicates punchiness or percussive energy in the mix.  
- Useful for feedback about mix dynamics.