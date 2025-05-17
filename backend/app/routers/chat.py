from fastapi import APIRouter, Form, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Track, AnalysisResult, ChatMessage
from app.gpt_utils import generate_feedback

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def get_feedback(track_id: int = Form(...), session_id: int = Form(...), db: Session = Depends(get_db)):
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track or not track.analysis:
        return {"error": "Track analysis not found"}

    feedback = generate_feedback(track.analysis.__dict__)

    chat = ChatMessage(
        session_id=session_id,
        sender="assistant",
        message=feedback
    )
    db.add(chat)
    db.commit()

    return {"feedback": feedback}