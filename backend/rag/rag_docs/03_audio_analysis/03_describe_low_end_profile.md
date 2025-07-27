## Function: `describe_low_end_profile(ratio: float, genre: str = None)`

Interprets the low-end energy ratio relative to genre-specific expectations and returns a descriptive string.

- Uses genre-specific thresholds to classify bass presence as light, balanced, elevated, or strong.
- Provides tailored feedback on bass level appropriateness per genre category.

**Inputs:**  
- `ratio`: Proportion of low-end energy to total energy (float).  
- `genre`: Optional genre string to guide interpretation.

**Output:**  
- Human-readable description of low-end profile.

**Design Notes:**  
- Supports genres grouped by bass emphasis.  
- Provides actionable suggestions like boosting or checking clarity.