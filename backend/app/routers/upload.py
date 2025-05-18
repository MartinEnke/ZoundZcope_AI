from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
import shutil, os
from app.database import SessionLocal
from app.models import Track, AnalysisResult, Session as UserSession
from app.audio_analysis import analyze_audio
from typing import Optional

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
    session_id: int = Form(...),
    track_name: Optional[str] = Form(None),
    type: str = Form(...),
    genre: str = Form(...),
    db: Session = Depends(get_db)
):
    file_location = f"{UPLOAD_FOLDER}/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    analysis = analyze_audio(file_location)

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

    return {
        "track_name": track_name,
        "genre": genre,
        "analysis": analysis,
        "feedback": "Feedback not yet generated – coming soon!"
    }