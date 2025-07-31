# 🎧 ZoundZcope

ZoundZcope is a modular audio analysis and feedback tool that gives automated mixing and mastering suggestions based on extracted audio features. It's built with FastAPI, SQLAlchemy, and OpenAI-compatible models (e.g. Together.ai).

![License: Contact Author](https://img.shields.io/badge/license-contact--author-orange)


## 🔍 What It Does

- Analyze uploaded audio files for:
  - Peak, RMS, LUFS, Dynamic Range
  - Tempo & Musical Key
  - Stereo Width
  - Low-End Energy Ratio & Bass Profile
  - Frequency Band Energies
  - Estimated Masking Score & Bands
- Store track and analysis data in a SQLite database
- Generate human-like feedback from an AI assistant
  - Feedback is customized by genre and user expertise level
- View and manage sessions and track history

## 🛠 Tech Stack

- **Backend:** FastAPI, SQLAlchemy, Uvicorn
- **Audio Analysis:** Librosa, PyLoudNorm, NumPy
- **AI Feedback:** Together.ai / OpenAI API
- **Database:** SQLite (ORM via SQLAlchemy)
- **Frontend:** Swagger UI (built-in) + optional JS client

## 📁 Folder Structure

