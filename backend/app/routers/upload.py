"""
Audio upload and initial feedback generation endpoints for ZoundZcope.

This module handles uploading new tracks (and optional reference tracks),
performing audio analysis, saving results to the database, and generating
AI-based feedback. It also stores RMS chunk data for visual display in the
frontend.

Workflow:
    1) Accept and validate uploaded files and form metadata.
    2) Normalize session and track data (name, type, genre, profile).
    3) Save uploaded files to disk.
    4) Compute RMS chunks for visualization.
    5) Run audio analysis on the uploaded files.
    6) Store analysis results, track records, and related chat messages in the DB.
    7) Optionally handle and analyze a reference track in the same upload group.
    8) Generate GPT feedback incorporating analysis results (and reference track
       comparison if provided).
    9) Return structured JSON containing paths and analysis/feedback data.

Endpoint:
    POST /upload/
        Upload a main track (and optional reference track) with metadata,
        perform analysis, and return analysis results and AI feedback.

Dependencies:
    - Models: Track, AnalysisResult, ChatMessage, Session
    - Audio analysis: analyze_audio()
    - Feedback: generate_feedback_prompt(), generate_feedback_response()
    - RMS computation: compute_rms_chunks()
    - Normalization utils: normalize_session_name(), normalize_profile(),
      normalize_genre(), normalize_subgenre(), safe_track_name()
    - Filesystem: os, shutil, Pathlib for saving/deleting files
"""
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from app.database import SessionLocal
from app.models import Track, AnalysisResult, ChatMessage, Session as UserSession
from app.audio_analysis import analyze_audio
from app.gpt_utils import generate_feedback_prompt, generate_feedback_response
from app.utils import normalize_session_name, normalize_profile, normalize_genre, normalize_subgenre, safe_track_name
from app.analysis_rms_chunks import compute_rms_chunks
import time
from pathlib import Path
import shutil, os
import uuid
from typing import Optional

router = APIRouter()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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

        This endpoint:
          - Saves uploaded audio files to disk.
          - Optionally analyzes a reference track for comparison.
          - Computes RMS chunk data for waveform visualization.
          - Performs audio analysis on the uploaded track(s).
          - Stores analysis results and track records in the database.
          - Generates GPT feedback using the provided profile and analysis results.
          - Saves the feedback as a ChatMessage linked to the track.

        Args:
            file (UploadFile): The primary track file to upload.
            ref_file (Optional[UploadFile]): An optional reference track for comparison.
            session_id (str): The ID of the session this track belongs to.
            session_name (Optional[str]): The name of the session (created if missing).
            track_name (Optional[str]): A display name for the track; defaults to safe file name.
            type (str): The type of track (e.g., 'mixdown', 'master').
            genre (str): The genre of the track.
            subgenre (Optional[str]): The subgenre of the track.
            feedback_profile (str): The AI feedback profile to use.

        Returns:
            dict: Metadata about the track(s), analysis results, feedback, and file paths.

        Raises:
            JSONResponse: With status 500 if an unexpected error occurs during processing.
        """
    # Normalize inputs
    session_id = normalize_session_name(session_id)
    session_name = normalize_session_name(session_name)
    type = type.strip().lower()
    genre = normalize_genre(genre)
    subgenre = normalize_subgenre(subgenre) if subgenre else ""
    feedback_profile = normalize_profile(feedback_profile)
    group_id = str(uuid.uuid4())

    try:
        print("Incoming upload:", {
            "session_id": session_id,
            "track_name": track_name,
            "type": type,
            "genre": genre,
            "subgenre": subgenre,
            "feedback_profile": feedback_profile
        })

        # Save original track
        ext = os.path.splitext(file.filename)[1]
        timestamped_name = f"{int(time.time())}_{file.filename}"
        file_location = os.path.join(UPLOAD_FOLDER, timestamped_name)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Save reference track if uploaded
        ref_file_location = None
        ref_analysis = None
        ref_timestamped_name = None

        try:
            if ref_file and ref_file.filename:
                ref_ext = os.path.splitext(ref_file.filename)[1]
                ref_timestamped_name = f"{int(time.time())}_ref_{ref_file.filename}"
                ref_file_location = os.path.join(UPLOAD_FOLDER, ref_timestamped_name)
                with open(ref_file_location, "wb") as buffer:
                    shutil.copyfileobj(ref_file.file, buffer)
                ref_analysis = analyze_audio(ref_file_location, genre=genre)
        except Exception:
            return JSONResponse(
                status_code=400,
                content={"detail": "The reference file is wrong, corrupted, or too big."}
            )
        else:
            ref_file_location = None
            ref_analysis = None

        print("Passing ref_analysis to prompt:", ref_analysis is not None)

            # Optional: delete reference file after analysis if you don't want to keep it on disk
            # os.remove(ref_file_location)

        BASE_DIR = Path(__file__).resolve().parents[3]
        rms_filename = f"{timestamped_name}_rms.json"
        rms_output_path = BASE_DIR / "frontend-html" / "static" / "analysis" / rms_filename
        compute_rms_chunks(file_location, json_output_path=str(rms_output_path))
        print("✅ RMS saved to:", rms_output_path)

        # Analyze original track
        analysis = analyze_audio(file_location, genre=genre)

        # Database operations
        db = SessionLocal()

        # Cleanup old main track files for the same session before saving new upload
        old_tracks = db.query(Track).filter(Track.session_id == session_id).all()
        for old_track in old_tracks:
            # Delete audio file
            try:
                if old_track.file_path and os.path.exists(old_track.file_path):
                    os.remove(old_track.file_path)
                    print(f"Deleted old main track file: {old_track.file_path}")
            except Exception as e:
                print(f"Error deleting old main track file {old_track.file_path}: {e}")

        existing_session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if not existing_session:
            new_session = UserSession(id=session_id, user_id=1, session_name=session_name)
            db.add(new_session)
            db.commit()

        filename_without_ext = os.path.splitext(file.filename)[0]
        safe_name = safe_track_name(filename_without_ext, file.filename)
        track_name = track_name or safe_name

        track = Track(
            session_id=session_id,
            track_name=track_name,
            file_path=file_location,
            type=type.lower(),
            upload_group_id = group_id
        )
        db.add(track)
        db.commit()
        db.refresh(track)

        result = AnalysisResult(track_id=track.id, **analysis)
        db.add(result)
        db.commit()

        print("Analysis data for main track:", analysis)
        if ref_file_location:
            # Analyze reference track first
            ref_analysis = analyze_audio(ref_file_location, genre=genre)
            print("Reference track analysis data:", ref_analysis)

            # Create the reference track in DB with same upload_group_id
            ref_track_name = f"{track_name} (Reference)"
            ref_track = Track(
                session_id=session_id,
                track_name=ref_track_name,
                file_path=ref_file_location,
                type="reference",
                upload_group_id=group_id  # assign the same group id here!
            )
            db.add(ref_track)
            db.commit()
            db.refresh(ref_track)

            # Save analysis result for reference track
            ref_result = AnalysisResult(track_id=ref_track.id, **ref_analysis)
            db.add(ref_result)
            db.commit()
        else:
            ref_analysis = None

        print("Passing ref_analysis to prompt:", ref_analysis is not None)

        # Generate GPT feedback with both original and ref analysis
        prompt = generate_feedback_prompt(
            genre=genre,
            subgenre=subgenre,
            type=type,
            analysis_data=analysis,
            feedback_profile=feedback_profile,
            ref_analysis_data=ref_analysis  # pass ref analysis here
        )

        feedback = generate_feedback_response(prompt)

        chat = ChatMessage(
            session_id=session_id,
            track_id=track.id,
            sender="assistant",
            message=feedback,
            feedback_profile=feedback_profile
        )
        db.add(chat)
        db.commit()
        db.close()

        return {
            "track_name": track_name,
            "genre": genre,
            "subgenre": subgenre,
            "type": type,
            "analysis": analysis,
            "ref_analysis": ref_analysis,  # included in response
            "feedback": feedback,
            "track_path": f"/uploads/{timestamped_name}",
            "ref_track_path": f"/uploads/{ref_timestamped_name}" if ref_timestamped_name else None,
            "rms_path": f"/static/analysis/{rms_filename}"
        }



    except Exception as e:

        import traceback

        traceback.print_exc()  # still log full error server-side

        print("UPLOAD ERROR:", e)

        return JSONResponse(

            status_code=400,  # use 400 instead of 500 for "bad upload"

            content={"detail": "The file is wrong, corrupted, or too big."}

        )
