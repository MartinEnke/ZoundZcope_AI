from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Track, AnalysisResult, ChatMessage
from app.gpt_utils import generate_feedback_prompt, generate_feedback_response, build_followup_prompt
import json
from pydantic import BaseModel
from app.utils import normalize_type, normalize_genre, normalize_profile, sanitize_user_question
from typing import Optional, Dict, Any

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
    ref_analysis_data: Optional[Dict[str, Any]] = None


@router.post("/ask-followup")
def ask_followup(req: FollowUpRequest, db: Session = Depends(get_db)):
    profile = normalize_profile(req.feedback_profile)
    user_question = sanitize_user_question(req.user_question)

    # 1. Fetch main track
    main_track = db.query(Track).filter(Track.id == req.track_id).first()
    if not main_track:
        raise HTTPException(status_code=404, detail="Main track not found")

    # 2. Fetch reference track by upload_group_id
    ref_track = (
        db.query(Track)
        .filter(
            Track.upload_group_id == main_track.upload_group_id,
            Track.type == "reference"
        )
        .order_by(Track.uploaded_at.desc())
        .first()
    )

    ref_analysis = None
    if ref_track and ref_track.analysis:
        ref_analysis = {
            "peak_db": ref_track.analysis.peak_db,
            "rms_db_peak": ref_track.analysis.rms_db_peak,
            "lufs": ref_track.analysis.lufs,
            "transient_description": ref_track.analysis.transient_description,
            "spectral_balance_description": ref_track.analysis.spectral_balance_description,
            "dynamic_range": ref_track.analysis.dynamic_range,
            "stereo_width": ref_track.analysis.stereo_width,
            "low_end_description": ref_track.analysis.low_end_description,
            # add other needed fields...
        }

    # 🔍 Include summary from previous thread if applicable
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
        print(f"Previous summary message for group {req.followup_group - 1}: {summary_msg.message if summary_msg else 'None'}")
        if summary_msg:
            summary_text = summary_msg.message

    # 3. Build prompt including ref_analysis data and summary
    prompt = build_followup_prompt(
        analysis_text=req.analysis_text,
        feedback_text=req.feedback_text,
        user_question=user_question,
        thread_summary=summary_text,
        ref_analysis_data=req.ref_analysis_data
    )

    try:
        ai_response = generate_feedback_response(prompt)
        print("GPT response:", ai_response)
    except Exception as e:
        print("❌ GPT call failed:", e)
        raise HTTPException(status_code=500, detail="AI follow-up failed")

    # Save user message
    user_msg = ChatMessage(
        session_id=req.session_id,
        track_id=req.track_id,
        sender="user",
        message=user_question,
        feedback_profile=profile,
        followup_group=req.followup_group
    )
    db.add(user_msg)

    # Save AI assistant response
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

    # --- Automatic summary creation after 4 user follow-ups ---
    user_msgs_count = (
        db.query(ChatMessage)
        .filter_by(
            session_id=req.session_id,
            track_id=req.track_id,
            followup_group=req.followup_group,
            sender="user"
        )
        .count()
    )

    response_data = {"answer": ai_response}

    existing_summary = (
        db.query(ChatMessage)
        .filter_by(
            session_id=req.session_id,
            track_id=req.track_id,
            followup_group=req.followup_group,
            sender="assistant",
            feedback_profile="summary"
        )
        .first()
    )

    if user_msgs_count >= 2 and not existing_summary:
        # Fetch all messages in this group (user + assistant)
        msgs = (
            db.query(ChatMessage)
            .filter_by(
                session_id=req.session_id,
                track_id=req.track_id,
                followup_group=req.followup_group,
            )
            .order_by(ChatMessage.timestamp)
            .all()
        )

        conversation = "\n".join(
            f"{'User' if msg.sender == 'user' else 'Assistant'}: {msg.message}"
            for msg in msgs
        )

        summary_prompt = f"""
Summarize this follow-up thread (up to 4 user questions and assistant responses) into a concise overall improvement strategy:

{conversation}
"""

        print(f"Generating summary for followup_group {req.followup_group} with conversation:\n{conversation}")

        summary_text = generate_feedback_response(summary_prompt)

        print(f"✅ Auto summary saved for followup_group {req.followup_group}")
        print(f"Summary content:\n{summary_text}\n{'-'*40}")

        summary_msg = ChatMessage(
            session_id=req.session_id,
            track_id=req.track_id,
            sender="assistant",
            message=summary_text,
            feedback_profile="summary",
            followup_group=req.followup_group
        )
        db.add(summary_msg)
        db.commit()

        response_data["summary_created"] = True

    return response_data



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


@router.post("/summarize-thread")
def summarize_thread(req: SummarizeRequest, db: Session = Depends(get_db)):
    messages = (
        db.query(ChatMessage)
        .filter_by(session_id=req.session_id, track_id=req.track_id, followup_group=req.followup_group)
        .order_by(ChatMessage.timestamp)
        .all()
    )
    # Count only user messages as "follow-up" messages
    user_msgs = [msg for msg in messages if msg.sender == "user"]

    if not user_msgs:
        return {"summary": "No follow-up messages found for this thread to summarize."}

    thread = []
    for msg in messages:
        if msg.sender == "user":
            thread.append({"role": "user", "content": msg.message})
        else:
            thread.append({"role": "assistant", "content": msg.message})

    conversation = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in thread])
    print(f"Conversation for summarization:\n{conversation}")

    if not conversation.strip():
        return {"summary": "No follow-up messages found for this thread to summarize."}

    prompt = f"""
Summarize this follow-up thread (5 user questions with assistant responses) into a concise overall improvement strategy:

{conversation}
"""

    summary = generate_feedback_response(prompt)
    return {"summary": summary}


@router.get("/test")
def test():
    return {"message": "Chat router works"}