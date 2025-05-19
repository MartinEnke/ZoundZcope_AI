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
    track_name: Optional[str] = Form(None),
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

        # Do audio analysis BEFORE opening DB session
        analysis = analyze_audio(file_location)

        from app.database import SessionLocal
        db = SessionLocal()

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
        db.close()

        # Generate GPT feedback
        prompt = generate_feedback_prompt(genre, type, analysis)
        feedback = generate_feedback_response(prompt)

        # Optionally save it to ChatMessage
        chat = ChatMessage(
            session_id=session_id,
            sender="assistant",
            message=feedback
        )
        db.add(chat)
        db.commit()

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
