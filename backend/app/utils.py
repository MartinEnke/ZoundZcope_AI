import re

# Allowed values (adjust as needed)
ALLOWED_TYPES = {"mixdown", "master"}
ALLOWED_PROFILES = {"simple", "detailed", "pro"}
ALLOWED_GENRES = {
    "electronic", "hiphop", "rock", "ambient", "classic", "punk"
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
