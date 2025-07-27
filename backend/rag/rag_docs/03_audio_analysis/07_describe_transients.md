## Function: `describe_transients(avg, max)`

Generates a qualitative description of transient characteristics based on average and maximum strengths.

- Categorizes transients as soft, balanced, punchy, or sharp.  
- Adds notes on mix impact depending on transient range.

**Inputs:**  
- `avg`: Average transient strength (float).  
- `max`: Maximum transient strength (float).

**Output:**  
- Human-readable description string.

**Design Notes:**  
- Helps users understand transient clarity and mix attack.