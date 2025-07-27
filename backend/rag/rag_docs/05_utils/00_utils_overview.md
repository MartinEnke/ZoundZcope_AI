# Utility Functions Overview (utils.py)

This module provides helper functions for sanitizing, normalizing, and validating
user inputs related to session names, track types, genres, feedback profiles,
and user questions within the music AI feedback system.

These utilities ensure consistent, safe, and clean data handling across the application,
preventing injection attacks, input errors, and unexpected values.

Key features:

- Sanitization of arbitrary text inputs with length and character restrictions.
- Normalization of session names to safe, HTML-escaped strings.
- Safe generation of track names with fallback logic.
- Validation against allowed sets of types, profiles, and genres.
- Title casing and safe escaping of subgenre strings.

This module is foundational for maintaining data integrity and user experience.
