"""
Utility functions for ZoundZcope.

This module provides common helper functions for:
    - Sanitizing and normalizing user input.
    - Validating allowed types, profiles, and genres.
    - Safe naming for sessions and tracks.
    - Token counting for Gemini prompt cost estimation.

Dependencies:
    - re, html, os for text cleaning and formatting.
    - google-genai for Gemini token counting.
"""

import re
import html
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Allowed values
ALLOWED_TYPES = {"mixdown", "mastering", "master"}
ALLOWED_PROFILES = {"simple", "detailed", "pro"}
ALLOWED_GENRES = {
    "electronic", "pop", "rock", "hiphop", "indie", "punk", "metal", "jazz", "reggae", "funk",
    "rnb", "soul", "country", "folk", "classic"
}


def get_gemini_client() -> genai.Client:
    """
    Create and return a Gemini client using GEMINI_API_KEY.

    Returns:
        genai.Client: Configured Gemini client.

    Raises:
        RuntimeError: If GEMINI_API_KEY is missing.
    """
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=key)


def count_tokens(text: str, model: str = "gemini-2.5-flash") -> int:
    """
    Count tokens in a string using Gemini's token counting API.

    Args:
        text (str): Input text to measure.
        model (str, optional): Gemini model name.

    Returns:
        int: Number of tokens. Returns 0 if text is empty or counting fails.
    """
    if not text:
        return 0

    try:
        client = get_gemini_client()
        response = client.models.count_tokens(
            model=model,
            contents=text
        )
        return int(getattr(response, "total_tokens", 0) or 0)
    except Exception as e:
        print(f"⚠️ Token counting failed: {e}")
        return 0


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

    cleaned = re.sub(r"[^\w\s.,!?@&$()\-+=:;\'\"/]", "", text.strip())
    cleaned = cleaned[:400]
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
    name = re.sub(r"[^\w\s\-]", "", name)
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
    name = name.strip() if isinstance(name, str) else ""
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

    sub = sub.strip()
    sub = re.sub(r"[^a-zA-Z0-9 &\-']", "", sub)
    sub = sub[:50]
    sub = sub.title()
    return html.escape(sub)