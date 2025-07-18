from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
import shutil, os
from app.database import SessionLocal
from app.models import Track, AnalysisResult, ChatMessage, Session as UserSession
from app.audio_analysis import analyze_audio
from typing import Optional
from fastapi.responses import JSONResponse
from app.gpt_utils import generate_feedback_prompt, generate_feedback_response
from app.utils import normalize_session_name, normalize_profile, normalize_genre, normalize_subgenre, safe_track_name
from app.analysis_rms_chunks import compute_rms_chunks
import time
from pathlib import Path

router = APIRouter()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
    # 🧼 Normalize user input
    session_id = normalize_session_name(session_id)
    session_name = normalize_session_name(session_name)
    type = type.strip().lower()
    genre = normalize_genre(genre)
    subgenre = normalize_subgenre(subgenre) if subgenre else ""
    feedback_profile = normalize_profile(feedback_profile)

    try:
        print("Incoming upload:", {
            "session_id": session_id,
            "track_name": track_name,
            "type": type,
            "genre": genre,
            "subgenre": subgenre,
            "feedback_profile": feedback_profile
        })

        ext = os.path.splitext(file.filename)[1]
        timestamped_name = f"{int(time.time())}_{file.filename}"
        file_location = os.path.join(UPLOAD_FOLDER, timestamped_name)

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

            # Save reference track file if uploaded
            ref_file_location = None
            if ref_file:
                ref_ext = os.path.splitext(ref_file.filename)[1]
                ref_timestamped_name = f"{int(time.time())}_ref_{ref_file.filename}"
                ref_file_location = os.path.join(UPLOAD_FOLDER, ref_timestamped_name)
                with open(ref_file_location, "wb") as buffer:
                    shutil.copyfileobj(ref_file.file, buffer)

        BASE_DIR = Path(__file__).resolve().parents[3]
        rms_filename = f"{timestamped_name}_rms.json"
        rms_output_path = BASE_DIR / "frontend-html" / "static" / "analysis" / rms_filename
        compute_rms_chunks(file_location, json_output_path=str(rms_output_path))
        print("✅ RMS saved to:", rms_output_path)

        analysis = analyze_audio(file_location, genre=genre)


        db = SessionLocal()

        existing_session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if not existing_session:
            new_session = UserSession(id=session_id, user_id=1, session_name=session_name)
            db.add(new_session)
            db.commit()

        filename_without_ext = os.path.splitext(file.filename)[0]
        track_name = safe_track_name(filename_without_ext, file.filename)

        track = Track(
            session_id=session_id,
            track_name=track_name,
            file_path=file_location,
            type=type.lower()
        )
        db.add(track)
        db.commit()
        db.refresh(track)

        result = AnalysisResult(track_id=track.id, **analysis)
        db.add(result)
        db.commit()

        # Generate GPT feedback with full genre context
        prompt = generate_feedback_prompt(
            genre=genre,
            subgenre=subgenre,
            type=type,
            analysis_data=analysis,
            feedback_profile=feedback_profile
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
            "feedback": feedback,
            "track_path": f"/uploads/{timestamped_name}",
            "ref_track_path": f"/uploads/{ref_timestamped_name}" if ref_file else None,
            "rms_path": f"/static/analysis/{rms_filename}"
        }

    except Exception as e:
        print("UPLOAD ERROR:", e)
        return JSONResponse(status_code=500, content={"detail": str(e)})
