from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Track, AnalysisResult
import os

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{track_id}")
def get_single_track(track_id: str, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    return {
        "id": track.id,
        "track_name": track.track_name,
        "type": track.type,
        "session_id": track.session_id,
        "file_path": track.file_path
    }

@router.put("/{id}")
def update_track(
    id: int,
    track_name: str = Form(...),
    db: Session = Depends(get_db)
):
    track = db.query(Track).filter(Track.id == id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    track.track_name = track_name
    db.commit()
    return {"message": "Track updated", "track": track}

@router.delete("/{id}")
def delete_track(id: int, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    # Delete associated analysis result
    if track.analysis:
        db.delete(track.analysis)

    # Optionally delete file
    if os.path.exists(track.file_path):
        os.remove(track.file_path)

    db.delete(track)
    db.commit()
    return {"message": "Track and analysis deleted"}