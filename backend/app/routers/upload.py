from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
import shutil, os
from app.database import SessionLocal
from app.models import Track, AnalysisResult, ChatMessage, Session as UserSession
from app.audio_analysis import analyze_audio
from typing import Optional
from fastapi.responses import JSONResponse
from app.gpt_utils import generate_feedback_prompt, generate_feedback_response

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
):
    try:
        print("Incoming upload:", {
            "session_id": session_id,
            "track_name": track_name,
            "type": type,
            "genre": genre
        })

        file_location = f"{UPLOAD_FOLDER}/{file.filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Analyze audio BEFORE DB
        analysis = analyze_audio(file_location)

        db = SessionLocal()

        # ✅ Make sure the session exists or create one
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
            type=type
        )
        db.add(track)
        db.commit()
        db.refresh(track)

        result = AnalysisResult(track_id=track.id, **analysis)
        db.add(result)
        db.commit()

        # ✅ Generate GPT feedback
        prompt = generate_feedback_prompt(genre, type, analysis)
        feedback = generate_feedback_response(prompt)

        # ✅ Save feedback in chat
        chat = ChatMessage(
            session_id=session_id,
            sender="assistant",
            message=feedback
        )
        db.add(chat)
        db.commit()

        db.close()

        return {
            "track_name": track_name,
            "genre": genre,
            "type": type,
            "analysis": analysis,
            "feedback": feedback
        }

    except Exception as e:
        print("UPLOAD ERROR:", e)
        return JSONResponse(status_code=500, content={"detail": str(e)})
