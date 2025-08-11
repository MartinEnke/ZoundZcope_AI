"""
Utility functions for ZoundZcope.

This module provides common helper functions for:
    - Sanitizing and normalizing user input.
    - Validating allowed types, profiles, and genres.
    - Safe naming for sessions and tracks.
    - Token counting for AI prompt cost estimation.

Dependencies:
    - re, html, os for text cleaning and formatting.
    - tiktoken for accurate OpenAI token counting.

Constants:
    ALLOWED_TYPES    : Permitted track types.
    ALLOWED_PROFILES : Permitted feedback profiles.
    ALLOWED_GENRES   : Permitted music genres.
"""
import re
import html
import os
import tiktoken

# from openai import OpenAI

# import os
# from dotenv import load_dotenv
# from google import genai
#
# load_dotenv()

# def get_gemini_client() -> genai.Client:
#     key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
#     if not key:
#         raise RuntimeError("Set GEMINI_API_KEY (or GOOGLE_API_KEY) first.")
#     return genai.Client(api_key=key)
#
# def count_tokens_gemini(text: str, model: str = "gemini-2.0-flash") -> int:
#     client = get_gemini_client()
#     r = client.models.count_tokens(model=model, contents=text)
#     return int(getattr(r, "total_tokens", 0))





# Allowed values (adjust as needed)
ALLOWED_TYPES = {"mixdown", "mastering", "master"}
ALLOWED_PROFILES = {"simple", "detailed", "pro"}
ALLOWED_GENRES = {
    "electronic", "pop", "rock", "hiphop", "indie", "punk", "metal", "jazz", "reggae", "funk",
    "rnb", "soul", "country", "folk", "classic"
}


def sanitize_input(input_str: str) -> str:
    """
    Sanitize a generic string input.

    - Strips leading/trailing whitespace.
    - Replaces multiple spaces with a single space.
    - Truncates to 100 characters.

    Args:
        input_str (str): Input to sanitize.

    Returns:
        str: Cleaned and truncated string, or empty string if invalid.
    """
    if not isinstance(input_str, str):
        return ""
    return re.sub(r"\s+", " ", input_str.strip())[:100]


def sanitize_user_question(text: str) -> str:
    """
        Clean and escape a user-provided question.

        - Removes disallowed characters, keeping common punctuation.
        - Limits length to 400 characters.
        - Escapes HTML entities to prevent injection.

        Args:
            text (str): User question.

        Returns:
            str: Sanitized and HTML-escaped string.
        """
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
    Sanitize and normalize a session name.

    - Trims whitespace.
    - Allows only letters, numbers, spaces, dashes, and underscores.
    - Truncates to 60 characters.
    - Escapes HTML for safe UI display.

    Args:
        name (str): User-provided session name.

    Returns:
        str: Sanitized and escaped session name.
    """
    if not isinstance(name, str):
        return ""
    name = name.strip()
    name = re.sub(r"[^\w\s\-]", "", name)  # Keep alphanumeric, space, dash, underscore
    name = name[:60]
    return html.escape(name)


def safe_track_name(name, fallback_filename):
    """
        Ensure a valid track name, falling back to filename if needed.

        Args:
            name (str): User-provided track name.
            fallback_filename (str): Filename to use if name is invalid.

        Returns:
            str: Safe track name.
        """
    name = name.strip() if name else ""
    return name if name and name.lower() != "string" else os.path.splitext(fallback_filename)[0]


def normalize_type(input_str: str) -> str:
    """
        Sanitize and validate track type.

        Falls back to 'mixdown' if type is not allowed.

        Args:
            input_str (str): Track type to validate.

        Returns:
            str: Validated track type.
        """
    """Sanitize and validate track type."""
    val = sanitize_input(input_str).lower()
    return val if val in ALLOWED_TYPES else "mixdown"


def normalize_profile(input_str: str) -> str:
    """
    Sanitize and validate feedback profile.

    Falls back to 'simple' if profile is not allowed.

    Args:
        input_str (str): Profile name to validate.

    Returns:
        str: Validated profile name.
    """
    val = sanitize_input(input_str).lower()
    return val if val in ALLOWED_PROFILES else "simple"


def normalize_genre(input_str: str) -> str:
    """
    Sanitize and validate genre.

    Falls back to 'electronic' if genre is not allowed.

    Args:
        input_str (str): Genre to validate.

    Returns:
        str: Validated genre.
    """
    val = sanitize_input(input_str).lower()
    return val if val in ALLOWED_GENRES else "electronic"


def normalize_subgenre(sub: str) -> str:
    """
    Sanitize and normalize a subgenre string.

    - Strips whitespace.
    - Allows only letters, digits, spaces, dashes, ampersands, and apostrophes.
    - Truncates to 50 characters.
    - Converts to title case.
    - Escapes HTML for safety.

    Args:
        sub (str): User-provided subgenre.

    Returns:
        str: Sanitized, formatted, and escaped subgenre.
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
    Count tokens in a string using tiktoken for a given model.

    Args:
        text (str): Input text to measure.
        model (str, optional): Model name for encoding rules.

    Returns:
        int: Number of tokens.
    """
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


