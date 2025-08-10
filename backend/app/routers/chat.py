from fastapi import APIRouter, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Track, AnalysisResult, ChatMessage
from app.gpt_utils import generate_feedback_prompt, generate_feedback_response, build_followup_prompt
from app.utils import normalize_type, normalize_genre, normalize_profile, sanitize_user_question
from app.gpt_utils import generate_comparison_feedback
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
from typing import List
import uuid


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/generate_feedback")
def get_feedback(
    track_id: str = Form(...),
    session_id: str = Form(...),
    genre: str = Form(...),
    type: str = Form(...),
    feedback_profile: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Handle a request to generate AI mixing/mastering feedback for a given audio track.

    This function normalizes user inputs, fetches audio analysis data, builds
    an AI prompt, sends it for feedback generation, saves the feedback in the
    database, and returns it to the client.

    Parameters:
        track_id (str): Unique identifier of the audio track.
        session_id (str): Current user session identifier.
        genre (str): Genre of the track, used to tailor feedback.
        type (str): Feedback type ('mixdown', 'mastering', 'master review').
        feedback_profile (str): Detail level ('simple', 'detailed', 'pro').
        db (Session): Database session for querying track data.

    Returns:
        dict: JSON response containing AI feedback text, or error message if analysis not found.
    """
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
    """
        Fetches the main track and optional reference track analysis from the database.
        Retrieves the previous follow-up summary if available to provide context for the AI prompt.

        Parameters:
            req (FollowUpRequest): The follow-up request containing session, track, and follow-up group info.
            db (Session): Database session for querying data.

        Returns:
            tuple: (main_track, ref_analysis, summary_text)
                main_track: The primary Track object or None if not found.
                ref_analysis: Dict of reference track analysis data or None.
                summary_text: Previous follow-up summary string or empty string.
        """

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

    # 3. Retrieve previous follow-up summary if applicable
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

    if user_msgs_count >= 4 and not existing_summary:
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

        print(f"Auto summary saved for followup_group {req.followup_group}")
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
    """
        Retrieve all chat messages associated with a specific track.

        This function fetches all chat messages related to a given track, ordered
        by their timestamp. The response includes details such as the sender,
        message content, feedback profile, and track name.

        Parameters:
            track_id (str): The unique identifier of the track whose messages are to be retrieved.
            db (Session): Database session for querying track and chat messages.

        Returns:
            list: A list of dictionaries, each containing details about a chat message (sender,
                  message content, feedback profile, track name).
            HTTPException: Raises a 404 error if the track is not found in the database.
        """
    track = db.query(Track).filter_by(id=track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.track_id == track_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )

    print(f"DEBUG: Found {len(messages)} messages for track_id={track_id}")
    for msg in messages:
        print(f"DEBUG: message id={msg.id} content={msg.message[:30]}")

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
    """
        Generate a summary of a follow-up conversation thread.

        Retrieves chat messages for a given session, track, and follow-up group,
        then uses AI to summarize the thread into a concise improvement strategy.

        Parameters:
            req (SummarizeRequest): Contains session_id, track_id, and followup_group.
            db (Session): Database session for querying chat messages.

        Returns:
            dict: A JSON response with the AI-generated summary or a message if
                  no follow-up messages are found.
        """
    print(f"Summarize request: session_id={req.session_id}, track_id={req.track_id}, group={req.followup_group}")
    messages = (
        db.query(ChatMessage)
        .filter_by(session_id=req.session_id, track_id=req.track_id, followup_group=req.followup_group)
        .order_by(ChatMessage.timestamp)
        .all()
    )
    print(f"Found {len(messages)} messages")
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



class CompareTracksRequest(BaseModel):
    track_ids: List[str]


@router.post("/compare-tracks")
def compare_tracks(data: CompareTracksRequest, db: Session = Depends(get_db)):
    """
        Compare multiple audio tracks by their analysis results and chat history.

        This function accepts a list of track IDs, retrieves their analysis and
        chat history, and generates a comparison of the tracks. The feedback is
        generated by AI and saved in the database as a new chat message.

        Parameters:
            data (CompareTracksRequest): Contains the list of track IDs to compare.
            db (Session): Database session for querying track and chat data.

        Returns:
            dict: JSON response with AI-generated comparison feedback, comparison group ID,
                  and track names.
        """
    track_ids = data.track_ids

    if not track_ids or len(track_ids) < 2:
        raise HTTPException(status_code=400, detail="At least two tracks must be selected.")

    comparison_data = []
    track_names = []

    for track_id in track_ids:
        track = db.query(Track).filter_by(id=track_id).first()
        if not track or not track.analysis:
            continue

        messages = db.query(ChatMessage).filter_by(track_id=track_id).order_by(ChatMessage.timestamp.asc()).all()
        chat_history = "\n".join(f"{m.sender}: {m.message}" for m in messages)

        comparison_data.append({
            "track_name": track.track_name,
            "analysis_summary": f"""
LUFS: {track.analysis.lufs}
Width: {track.analysis.stereo_width}
Key: {track.analysis.key}
Peak: {track.analysis.peak_db}
Issues: {track.analysis.issues or 'None'}
Spectral balance: {track.analysis.spectral_balance_description or 'n/a'}
""",
            "chat_history": chat_history or "No chat history."
        })

        track_names.append(track.track_name)

    if not comparison_data:
        raise HTTPException(status_code=404, detail="No analysis or chat data found.")

    # Get AI response using helper
    feedback = generate_comparison_feedback(comparison_data, max_tokens=500)

    # Save in chat history
    group_id = str(uuid.uuid4())
    db.add(ChatMessage(
        sender="ai",
        message=feedback,
        session_id=track.session_id if track else None,
        comparison_group_id=group_id,
        compared_track_ids=",".join(track_ids),
        compared_track_names=",".join(track_names)
    ))
    db.commit()

    return {
        "feedback": feedback,
        "comparison_group_id": group_id,
        "track_names": track_names
    }


@router.get("/comparisons")
def get_comparison_history(db: Session = Depends(get_db)):
    """
        Retrieve the history of track comparisons stored in the database.

        This function queries the database for all distinct comparison group IDs and
        returns the list of comparisons with their associated track names and IDs.

        Parameters:
            db (Session): Database session for querying comparison data.

        Returns:
            JSONResponse: A list of comparison history, including group ID, track IDs,
                          and track names.
        """
    results = db.query(ChatMessage.comparison_group_id)\
        .filter(ChatMessage.comparison_group_id.isnot(None))\
        .distinct().all()

    history = []
    for (group_id,) in results:
        messages = db.query(ChatMessage)\
            .filter(ChatMessage.comparison_group_id == group_id)\
            .order_by(ChatMessage.timestamp.asc()).all()

        if not messages:
            continue

        # Get the first message for this group (usually where compared_track_ids is filled)
        first_msg = next((m for m in messages if m.compared_track_ids), None)
        if not first_msg:
            continue

        # Parse comma-separated string of IDs
        raw_ids = first_msg.compared_track_ids.split(",")
        track_ids = [tid.strip() for tid in raw_ids if tid.strip()]

        tracks = db.query(Track).filter(Track.id.in_(track_ids)).all()
        track_names = [t.track_name for t in tracks]

        history.append({
            "group_id": group_id,
            "track_ids": track_ids,
            "track_names": track_names,
        })

    return JSONResponse(content=history)


@router.get("/comparisons/{group_id}")
def get_comparison_by_group(group_id: str, db: Session = Depends(get_db)):
    """
        Retrieve a specific track comparison by its group ID.

        This function fetches all messages related to a specific comparison group and
        returns the AI-generated feedback along with the compared track names.

        Parameters:
            group_id (str): The ID of the comparison group.
            db (Session): Database session for querying comparison messages.

        Returns:
            dict: JSON response containing feedback and track names for the specified group.
        """
    messages = db.query(ChatMessage) \
        .filter(ChatMessage.comparison_group_id == group_id) \
        .order_by(ChatMessage.timestamp.asc()).all()

    if not messages:
        return JSONResponse(content={"error": "No comparison found."}, status_code=404)

    first_msg = next((m for m in messages if m.message and m.message.startswith("###")), messages[0])

    return {
        "feedback": first_msg.message,
        "track_names": first_msg.compared_track_names.split(",") if first_msg.compared_track_names else []
    }


@router.delete("/comparisons/{group_id}")
def delete_comparison(group_id: str, db: Session = Depends(get_db)):
    """
        Delete a track comparison and all associated messages by group ID.

        This function deletes all chat messages that belong to a specified comparison group.

        Parameters:
            group_id (str): The ID of the comparison group to delete.
            db (Session): Database session for querying and deleting comparison data.

        Returns:
            dict: JSON response indicating the number of deleted messages in the specified group.
        """

    # Get all messages belonging to the comparison group
    messages = db.query(ChatMessage).filter(ChatMessage.comparison_group_id == group_id).all()

    if not messages:
        raise HTTPException(status_code=404, detail="Comparison group not found")

    # Delete all messages in that group
    for msg in messages:
        db.delete(msg)

    db.commit()

    return {"detail": f"Deleted {len(messages)} messages in group {group_id}"}


