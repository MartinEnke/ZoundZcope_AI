from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Track, AnalysisResult, ChatMessage
from app.gpt_utils import generate_feedback_prompt, generate_feedback_response, generate_followup_response
import json
from pydantic import BaseModel
from app.utils import normalize_type, normalize_genre, normalize_profile

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/feedback_history.html")
def get_feedback(
    track_id: str = Form(...),
    session_id: str = Form(...),
    genre: str = Form(...),
    type: str = Form(...),
    feedback_profile: str = Form(...),
    db: Session = Depends(get_db)
):

    genre = normalize_genre(genre)
    type = normalize_type(type)
    feedback_profile = normalize_profile(feedback_profile)

    # Fetch track and analysis
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track or not track.analysis:
        return {"error": "Track analysis not found"}

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

    prompt = generate_feedback_prompt(genre, type, analysis, feedback_profile)
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

    return {"feedback": feedback}


class FollowUpRequest(BaseModel):
    analysis_text: str
    feedback_text: str
    user_question: str
    session_id: str
    track_id: str
    feedback_profile: str
    followup_group: int = 0

@router.post("/ask-followup")
def ask_followup(req: FollowUpRequest, db: Session = Depends(get_db)):
    profile = normalize_profile(req.feedback_profile)
    user_question = req.user_question.strip()

    # 🔍 Include previous thread summary if this is not the first group
    summary_text = ""
    if req.followup_group > 0:
        summary_msg = (
            db.query(ChatMessage)
            .filter_by(
                session_id=req.session_id,
                track_id=req.track_id,
                followup_group=req.followup_group - 1,
                sender="assistant",
                feedback_profile="summary"
            )
            .order_by(ChatMessage.timestamp.desc())
            .first()
        )
        if summary_msg:
            summary_text = summary_msg.message

    # 🧠 Build AI prompt with summary + original analysis + feedback + user question
    combined_prompt = f"""
You are an intelligent audio assistant helping a mastering engineer.

{"Here is a summary of the previous conversation:\n" + summary_text + "\n\n" if summary_text else ""}
This is the original track analysis:
{req.analysis_text}

This was the first feedback:
{req.feedback_text}

User's follow-up question:
"{user_question}"

Please respond concisely and helpfully, based on the previous context.
"""

    try:
        ai_response = generate_followup_response(
            analysis_text=req.analysis_text,
            feedback_text=req.feedback_text,
            user_question=user_question,
            thread_summary=summary_text  # <- now context-aware
        )
    except Exception as e:
        print("❌ GPT call failed:", e)
        raise HTTPException(status_code=500, detail="AI follow-up failed")

    # Save user question
    user_msg = ChatMessage(
        session_id=req.session_id,
        track_id=req.track_id,
        sender="user",
        message=req.user_question,
        feedback_profile=profile,
        followup_group=req.followup_group
    )
    db.add(user_msg)

    # Save assistant answer
    assistant_msg = ChatMessage(
        session_id=req.session_id,
        track_id=req.track_id,
        sender="assistant",
        message=ai_response,
        feedback_profile=profile,
        followup_group=req.followup_group
    )
    db.add(assistant_msg)
    db.commit()

    return {"answer": ai_response}


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
            "track_name": track.track_name
        }
        for msg in messages
    ]


class SummarizeRequest(BaseModel):
    session_id: str
    track_id: str
    followup_group: int

@router.post("/chat/summarize-thread")
def summarize_thread(req: SummarizeRequest, db: Session = Depends(get_db)):
    messages = (
        db.query(ChatMessage)
        .filter_by(session_id=req.session_id, track_id=req.track_id, followup_group=req.followup_group)
        .order_by(ChatMessage.timestamp)
        .all()
    )

    thread = []
    for msg in messages:
        if msg.sender == "user":
            thread.append({"role": "user", "content": msg.message})
        else:
            thread.append({"role": "assistant", "content": msg.message})

    conversation = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in thread])

    prompt = f"""
Summarize this follow-up thread (5 user questions with assistant responses) into a concise overall improvement strategy:

{conversation}
"""

    summary = generate_feedback_response(prompt)
    return {"summary": summary}
