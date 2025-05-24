from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Track, AnalysisResult, ChatMessage
from app.gpt_utils import generate_feedback_prompt, generate_feedback_response
import json

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/feedback_history.html")
def get_feedback(
    track_id: int = Form(...),
    session_id: int = Form(...),
    genre: str = Form(...),  # genre now passed from frontend
    db: Session = Depends(get_db)
):
    # Load track and related analysis
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track or not track.analysis:
        return {"error": "Track analysis not found"}

    # Convert analysis into a dict
    analysis = {
        "peak_db": track.analysis.peak_db,
        "rms_db": track.analysis.rms_db,
        "lufs": track.analysis.lufs,
        "dynamic_range": track.analysis.dynamic_range,
        "stereo_width": track.analysis.stereo_width,
        "key": track.analysis.key,
        "tempo": track.analysis.tempo,
        "low_end_energy_ratio": track.analysis.low_end_energy_ratio,
        "bass_profile": track.analysis.bass_profile,
        "band_energies": json.loads(track.analysis.band_energies),
        "issues": json.loads(track.analysis.issues),
    }

    # Generate prompt + send to OpenAI
    prompt = generate_feedback_prompt(genre, analysis)
    response = generate_feedback_response(prompt)

    # Save assistant message
    chat = ChatMessage(
        session_id=session_id,
        sender="assistant",
        message=response
    )
    db.add(chat)
    db.commit()

    return {"feedback": response}


@router.get("/tracks/{track_id}/messages")
def get_messages_for_track(track_id: str, db: Session = Depends(get_db)):
    track = db.query(Track).filter_by(id=track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.track_id == track_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )

    return [
        {
            "sender": msg.sender,
            "message": msg.message,
            "feedback_profile": msg.feedback_profile,
            "type": track.type,
            "track_name": track.track_name  # Include name from joined track
        }
        for msg in messages
    ]