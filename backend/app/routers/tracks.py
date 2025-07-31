from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Track, AnalysisResult, ChatMessage
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
    id: str,
    track_name: str = Form(None),
    session_id: str = Form(None),
    db: Session = Depends(get_db)
):
    track = db.query(Track).filter(Track.id == id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    if track_name is not None:
        track.track_name = track_name
    if session_id is not None:
        track.session_id = session_id

    db.commit()
    return {"message": "Track updated", "track": track}



@router.delete("/{id}")
def delete_track(id: str, db: Session = Depends(get_db)):
    print("Deleting track:", id)
    track = db.query(Track).filter(Track.id == id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    # Delete associated analysis result if any
    if track.analysis:
        db.delete(track.analysis)

    # Delete related chat messages
    deleted_chats = db.query(ChatMessage).filter(ChatMessage.track_id == track.id).delete()
    print(f"Deleted {deleted_chats} chat messages for track {track.id}")

    # Safely delete file if file_path is set and file exists
    if track.file_path:
        try:
            if os.path.exists(track.file_path):
                os.remove(track.file_path)
                print(f"Deleted file: {track.file_path}")
            else:
                print(f"File path does not exist: {track.file_path}")
        except Exception as e:
            print(f"Warning: Failed to delete file {track.file_path}: {e}")

    # Delete track from DB
    db.delete(track)
    db.commit()

    return {"message": "Track, analysis, and chat messages deleted"}
