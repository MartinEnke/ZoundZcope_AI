import re
import html
import os
import tiktoken


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


def sanitize_user_question(text: str) -> str:
    if not isinstance(text, str):
        return ""
    # Remove unwanted characters (allow common punctuation)
    cleaned = re.sub(r"[^\w\s.,!?@&$()\-+=:;\'\"/]", "", text.strip())
    # Limit length to 400 chars (adjust as needed)
    cleaned = cleaned[:400]
    # Escape HTML entities to prevent injection
    return html.escape(cleaned)

def normalize_session_name(name: str) -> str:
    """
    Sanitize user-provided session name:
    - Trim whitespace
    - Allow only letters, numbers, spaces, dashes, and underscores
    - Truncate to 60 characters
    - Escape HTML for safety in prompts/UI
    """
    if not isinstance(name, str):
        return ""
    name = name.strip()
    name = re.sub(r"[^\w\s\-]", "", name)  # Keep alphanumeric, space, dash, underscore
    name = name[:60]
    return html.escape(name)

def safe_track_name(name, fallback_filename):
    name = name.strip() if name else ""
    return name if name and name.lower() != "string" else os.path.splitext(fallback_filename)[0]

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


def count_tokens(text, model="gpt-4o"):
    """
    Count tokens for a given string using tiktoken.
    """
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def count_tokens_gemini(text, model="gemini"):
    """
    Approximate token count for a given string based on character count.
    """
    char_count = len(text)
    return int(char_count / 4)  # Approximate token count (1 token ≈ 4 characters)

