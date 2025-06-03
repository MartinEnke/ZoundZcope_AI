import re
import html

# Allowed values (adjust as needed)
ALLOWED_TYPES = {"mixdown", "mastering", "master"}
ALLOWED_PROFILES = {"simple", "detailed", "pro"}
ALLOWED_GENRES = {
    "electronic", "pop", "rock", "hiphop", "indie", "punk", "metal", "jazz", "reggae", "funk",
    "rnb", "soul", "country", "folk", "classic"
}

def sanitize_input(input_str: str) -> str:
    """Sanitize string: trim, normalize whitespace, limit length."""
    if not isinstance(input_str, str):
        return ""
    return re.sub(r"\s+", " ", input_str.strip())[:100]

def normalize_type(input_str: str) -> str:
    """Sanitize and validate track type."""
    val = sanitize_input(input_str).lower()
    return val if val in ALLOWED_TYPES else "mixdown"

def normalize_profile(input_str: str) -> str:
    """Sanitize and validate feedback profile."""
    val = sanitize_input(input_str).lower()
    return val if val in ALLOWED_PROFILES else "simple"

def normalize_genre(input_str: str) -> str:
    """Sanitize and validate genre."""
    val = sanitize_input(input_str).lower()
    return val if val in ALLOWED_GENRES else "electronic"

def normalize_subgenre(sub: str) -> str:
    """
    Sanitize and normalize a user-provided subgenre string.

    - Strips leading/trailing whitespace
    - Limits to ASCII letters, digits, spaces, dashes, ampersands, and apostrophes
    - Truncates to 50 characters
    - Escapes HTML for safe injection into prompts
    - Converts to title case (e.g., 'neo-soul' → 'Neo-Soul')
    """
    if not isinstance(sub, str):
        return ""

    # Basic cleanup
    sub = sub.strip()

    # Remove unwanted characters (but allow dashes, ampersands, apostrophes)
    sub = re.sub(r"[^a-zA-Z0-9 &\-']", "", sub)

    # Truncate to prevent abuse or overflow
    sub = sub[:50]

    # Convert to title case
    sub = sub.title()

    # Escape for prompt safety
    return html.escape(sub)
