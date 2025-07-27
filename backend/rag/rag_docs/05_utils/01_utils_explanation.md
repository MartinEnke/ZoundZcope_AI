# Function Explanations: Utility Functions (utils.py)

---

## `sanitize_input(input_str: str) -> str`

- Trims whitespace, normalizes internal whitespace to single spaces.
- Limits output to 100 characters.
- Returns an empty string if input is not a string.
- Used to clean general user inputs before further processing.

---

## `sanitize_user_question(text: str) -> str`

- Cleans user question strings by removing unwanted characters,
  allowing common punctuation and symbols used in text queries.
- Limits length to 400 characters.
- Escapes HTML entities to prevent injection vulnerabilities.
- Ensures safe inclusion of user queries in prompts or displays.

---

## `normalize_session_name(name: str) -> str`

- Cleans session names by removing invalid characters,
  only allowing letters, digits, spaces, dashes, and underscores.
- Truncates to 60 characters.
- Escapes HTML for safe UI rendering and prompt usage.
- Returns empty string if input is invalid.

---

## `safe_track_name(name, fallback_filename)`

- Returns a sanitized track name if valid and meaningful.
- Falls back to filename without extension if the provided name is missing,
  empty, or a generic placeholder like "string".
- Strips whitespace from name input.

---

## `normalize_type(input_str: str) -> str`

- Sanitizes and validates track type inputs.
- Allowed types: "mixdown", "mastering", "master".
- Defaults to "mixdown" if input is invalid or unrecognized.

---

## `normalize_profile(input_str: str) -> str`

- Sanitizes and validates feedback profile inputs.
- Allowed profiles: "simple", "detailed", "pro".
- Defaults to "simple" if input is invalid or unrecognized.

---

## `normalize_genre(input_str: str) -> str`

- Sanitizes and validates genre inputs.
- Allowed genres include popular styles such as electronic, pop, rock, hiphop, etc.
- Defaults to "electronic" if input is invalid or unrecognized.

---

## `normalize_subgenre(sub: str) -> str`

- Cleans and normalizes user-provided subgenre strings.
- Allows ASCII letters, digits, spaces, dashes, ampersands, and apostrophes only.
- Truncates to 50 characters.
- Converts to title case (e.g., "neo-soul" → "Neo-Soul").
- Escapes HTML entities for safe prompt inclusion.
- Returns empty string if input is invalid.

---

*These utility functions form the basis for consistent and secure input handling across the application.*
