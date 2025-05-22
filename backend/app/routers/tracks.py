from fastapi import APIRouter, HTTPException, Depends
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

@router.get("/{id}")
def get_track(id: int, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return {
        "track": track,
        "analysis": track.analysis
    }

@router.put("/{id}")
def update_track(id: int, track_name: str, type: str, db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    track.track_name = track_name
    track.type = type
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