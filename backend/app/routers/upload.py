# 6. app/routers/upload.py
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
import shutil, os
from app.database import SessionLocal
from app.models import Track, AnalysisResult, Session as UserSession
from app.audio_analysis import analyze_audio

router = APIRouter()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def upload_audio(
    file: UploadFile = File(...),
    session_id: int = Form(...),
    track_name: str = Form(...),
    db: Session = Depends(get_db)
):
    file_location = f"{UPLOAD_FOLDER}/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    analysis = analyze_audio(file_location)

    track = Track(
        session_id=session_id,
        track_name=track_name,
        file_path=file_location,
        type="mix"
    )
    db.add(track)
    db.commit()
    db.refresh(track)

    result = AnalysisResult(track_id=track.id, **analysis)
    db.add(result)
    db.commit()

    return {"message": "File uploaded and analyzed successfully", "track_id": track.id}
