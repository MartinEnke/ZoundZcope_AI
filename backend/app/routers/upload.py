from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
import shutil, os
from app.database import SessionLocal
from app.models import Track, AnalysisResult, ChatMessage, Session as UserSession
from app.audio_analysis import analyze_audio
from typing import Optional
from fastapi.responses import JSONResponse
from app.gpt_utils import generate_feedback_prompt, generate_feedback_response
from app.utils import normalize_type, normalize_profile, normalize_genre
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
    session_id: str = Form(...),
    track_name: Optional[str] = Form(default=None, description="Leave blank to use filename"),
    type: str = Form(...),
    genre: str = Form(...),
    subgenre: Optional[str] = Form(default=None),
    feedback_profile: str = Form(...),
):
    # 🧼 Normalize user input
    genre = normalize_genre(genre)
    subgenre = subgenre.strip() if subgenre else ""
    type = normalize_type(type)
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

        BASE_DIR = Path(__file__).resolve().parents[3]
        rms_filename = f"{timestamped_name}_rms.json"
        rms_output_path = BASE_DIR / "frontend-html" / "static" / "analysis" / rms_filename
        compute_rms_chunks(file_location, json_output_path=str(rms_output_path))
        print("✅ RMS saved to:", rms_output_path)

        analysis = analyze_audio(file_location)

        db = SessionLocal()

        existing_session = db.query(UserSession).filter(UserSession.id == session_id).first()
        if not existing_session:
            new_session = UserSession(id=session_id, user_id=1, session_name="Untitled Session")
            db.add(new_session)
            db.commit()

        track_name = track_name.strip() if track_name else None
        if not track_name or track_name.lower() == "string":
            track_name = os.path.splitext(file.filename)[0]

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
            "rms_path": f"/static/analysis/{rms_filename}"
        }

    except Exception as e:
        print("UPLOAD ERROR:", e)
        return JSONResponse(status_code=500, content={"detail": str(e)})
