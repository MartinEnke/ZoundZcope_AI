# app/routers/upload.py

"""
Audio upload and initial feedback generation endpoints for ZoundZcope.

This module handles uploading new tracks (and optional reference tracks),
performing audio analysis, saving results to the database, and generating
AI-based feedback. It also stores RMS chunk data for visual display in the
frontend.
"""

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional
from pathlib import Path
import os
import shutil
import time
import uuid
import traceback

from app.database import SessionLocal
from app.models import (
    Track,
    AnalysisResult as AnalysisResultModel,
    ChatMessage,
    Session as UserSession,
)
from app.audio_analysis import analyze_audio
from app.gpt_utils import generate_feedback_prompt, generate_feedback_response
from app.utils import (
    normalize_session_name,
    normalize_profile,
    normalize_genre,
    normalize_subgenre,
    safe_track_name,
)
from app.analysis_rms_chunks import compute_rms_chunks

router = APIRouter()

# Where uploaded audio files are stored (relative to /app/backend working dir)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Limits & debug
MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "15"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


def _filter_analysis_for_db(analysis: dict) -> dict:
    """Keep only fields that exist on AnalysisResult model."""
    if not analysis:
        return {}
    allowed = {c.name for c in AnalysisResultModel.__table__.columns} - {"id", "track_id"}
    filtered = {k: v for k, v in analysis.items() if k in allowed}
    dropped = set(analysis.keys()) - allowed
    if dropped:
        print("Analysis keys not in DB (dropped):", dropped)
    return filtered


def _file_too_big(path: str) -> bool:
    try:
        size_mb = os.path.getsize(path) / (1024 * 1024)
        return size_mb > MAX_FILE_MB
    except Exception as e:
        print("Size check error:", repr(e))
        return False


@router.post("/")
def upload_audio(
    file: UploadFile = File(...),
    ref_file: Optional[UploadFile] = File(None),
    session_id: str = Form(...),
    session_name: Optional[str] = Form(default="Untitled Session"),
    track_name: Optional[str] = Form(default=None),
    type: str = Form(...),
    genre: str = Form(...),
    subgenre: Optional[str] = Form(default=None),
    feedback_profile: str = Form(...),
):
    """
    Upload a main track and optional reference track, analyze them, and generate feedback.
    """

    # ---- Normalize inputs
    session_id = normalize_session_name(session_id)
    session_name = normalize_session_name(session_name)
    type = (type or "").strip().lower()
    genre = normalize_genre(genre)
    subgenre = normalize_subgenre(subgenre) if subgenre else ""
    feedback_profile = normalize_profile(feedback_profile)
    group_id = str(uuid.uuid4())

    print("Incoming upload:", {
        "session_id": session_id,
        "track_name": track_name,
        "type": type,
        "genre": genre,
        "subgenre": subgenre,
        "feedback_profile": feedback_profile,
    })

    # ---- Save original track to disk
    try:
        timestamp = int(time.time())
        timestamped_name = f"{timestamp}_{file.filename}"
        file_location = os.path.join(UPLOAD_FOLDER, timestamped_name)

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if _file_too_big(file_location):
            try:
                os.remove(file_location)
            except Exception:
                pass
            return JSONResponse(
                status_code=400,
                content={"detail": f"File too large. Limit is {MAX_FILE_MB} MB."},
            )

    except Exception as e:
        print("Save main file error:", repr(e))
        if DEBUG:
            traceback.print_exc()
        return JSONResponse(status_code=400, content={"detail": "Failed to save file."})

    # ---- Compute RMS chunks (ensure output dir exists first)
    try:
        # project root (/app)
        BASE_DIR = Path(__file__).resolve().parents[3]
        rms_filename = f"{timestamped_name}_rms.json"
        rms_output_path = BASE_DIR / "frontend-html" / "static" / "analysis" / rms_filename
        rms_output_path.parent.mkdir(parents=True, exist_ok=True)

        compute_rms_chunks(file_location, json_output_path=str(rms_output_path))
        print("✅ RMS saved to:", rms_output_path)
    except Exception as e:
        print("RMS error:", repr(e))
        if DEBUG:
            traceback.print_exc()
        return JSONResponse(status_code=400, content={"detail": "Failed to compute RMS."})

    # ---- Analyze original track
    try:
        analysis = analyze_audio(file_location, genre=genre)
    except Exception as e:
        print("Analysis error (main):", repr(e))
        if DEBUG:
            traceback.print_exc()
        return JSONResponse(status_code=400, content={"detail": "Audio analysis failed."})

    # ---- Optional reference track: save + analyze
    ref_file_location = None
    ref_timestamped_name = None
    ref_analysis = None

    if ref_file and ref_file.filename:
        try:
            ref_timestamped_name = f"{int(time.time())}_ref_{ref_file.filename}"
            ref_file_location = os.path.join(UPLOAD_FOLDER, ref_timestamped_name)
            with open(ref_file_location, "wb") as buffer:
                shutil.copyfileobj(ref_file.file, buffer)

            if _file_too_big(ref_file_location):
                try:
                    os.remove(ref_file_location)
                except Exception:
                    pass
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"The reference file is too large. Limit is {MAX_FILE_MB} MB."},
                )

            ref_analysis = analyze_audio(ref_file_location, genre=genre)
        except Exception as e:
            print("Reference file error:", repr(e))
            if DEBUG:
                traceback.print_exc()
            return JSONResponse(
                status_code=400,
                content={"detail": "The reference file is wrong, corrupted, or too big."},
            )

    # ---- Database operations
    db = SessionLocal()
    try:
        # Remove old main track files for the same session
        old_tracks = db.query(Track).filter(Track.session_id == session_id).all()
        for old_track in old_tracks:
            try:
                if old_track.file_path and os.path.exists(old_track.file_path):
                    os.remove(old_track.file_path)
                    print(f"Deleted old main track file: {old_track.file_path}")
            except Exception as e:
                print(f"Error deleting old main track file {old_track.file_path}: {repr(e)}")

        # Ensure session exists
        existing_session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if not existing_session:
            new_session = UserSession(id=session_id, user_id=1, session_name=session_name)
            db.add(new_session)
            db.commit()

        # Determine track name
        filename_without_ext = os.path.splitext(file.filename)[0]
        safe_name = safe_track_name(filename_without_ext, file.filename)
        track_name = track_name or safe_name

        # Create main track
        track = Track(
            session_id=session_id,
            track_name=track_name,
            file_path=file_location,
            type=type,
            upload_group_id=group_id,
        )
        db.add(track)
        db.commit()
        db.refresh(track)

        # Save analysis result for main track (filtered)
        filtered_analysis = _filter_analysis_for_db(analysis)
        result = AnalysisResultModel(track_id=track.id, **filtered_analysis)
        db.add(result)
        db.commit()

        # If reference provided: create ref track + ref analysis result
        if ref_file_location:
            ref_track_name = f"{track_name} (Reference)"
            ref_track = Track(
                session_id=session_id,
                track_name=ref_track_name,
                file_path=ref_file_location,
                type="reference",
                upload_group_id=group_id,
            )
            db.add(ref_track)
            db.commit()
            db.refresh(ref_track)

            ref_filtered = _filter_analysis_for_db(ref_analysis or {})
            ref_result = AnalysisResultModel(track_id=ref_track.id, **ref_filtered)
            db.add(ref_result)
            db.commit()

        print("Analysis data for main track (filtered keys):", list(filtered_analysis.keys()))
        print("Passing ref_analysis to prompt:", ref_analysis is not None)

        # ---- Generate GPT feedback
        prompt = generate_feedback_prompt(
            genre=genre,
            subgenre=subgenre,
            type=type,
            analysis_data=analysis,
            feedback_profile=feedback_profile,
            ref_analysis_data=ref_analysis,
        )
        feedback = generate_feedback_response(prompt)

        chat = ChatMessage(
            session_id=session_id,
            track_id=track.id,
            sender="assistant",
            message=feedback,
            feedback_profile=feedback_profile,
        )
        db.add(chat)
        db.commit()

        # ---- Response payload
        return {
            "track_name": track_name,
            "genre": genre,
            "subgenre": subgenre,
            "type": type,
            "analysis": analysis,
            "ref_analysis": ref_analysis,
            "feedback": feedback,
            "track_path": f"/uploads/{timestamped_name}",
            "ref_track_path": f"/uploads/{ref_timestamped_name}" if ref_timestamped_name else None,
            "rms_path": f"/static/analysis/{rms_filename}",
        }

    except Exception as e:
        # Catch-all for anything above; keep 400 to match your frontend expectations
        print("UPLOAD ERROR:", repr(e))
        if DEBUG:
            traceback.print_exc()
        msg = str(e) if DEBUG else "The file is wrong, corrupted, or too big."
        return JSONResponse(status_code=400, content={"detail": msg})
    finally:
        db.close()
