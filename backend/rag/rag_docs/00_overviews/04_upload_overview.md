# Audio Upload and Analysis Endpoint Overview

This module defines the FastAPI endpoint responsible for handling audio file uploads,
performing comprehensive audio analysis, saving data to the database,
and generating AI-driven feedback based on the analysis.

---

Key features:

- Supports uploading both a main audio track and an optional reference track.
- Normalizes and validates input parameters such as session ID, track name, genre, and feedback profile.
- Saves uploaded files with timestamped unique filenames to avoid collisions.
- Computes RMS chunks for frontend waveform visualization and saves as JSON.
- Analyzes audio tracks for loudness, key, spectral balance, transient strength, and more.
- Stores analysis results and metadata in the database, maintaining session and track records.
- Generates AI feedback prompts using both main and reference track analyses.
- Returns detailed JSON response including analysis data, AI feedback, and file paths.

---

Error handling includes logging exceptions and returning HTTP 500 responses with error details.

This endpoint is central to the project’s workflow, linking user uploads, audio analysis, and AI feedback generation.
