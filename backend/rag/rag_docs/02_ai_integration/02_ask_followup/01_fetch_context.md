# Function: ask_followup (chat.py)

## Part 1: Fetch Tracks and Prepare Context

```python
class FollowUpRequest(BaseModel):
    analysis_text: str
    feedback_text: str
    user_question: str
    session_id: str
    track_id: str
    feedback_profile: str
    followup_group: int = 0
    ref_analysis_data: Optional[Dict[str, Any]] = None
```
    
This Pydantic model defines the expected structure of the follow-up request payload:

- **analysis_text**: Text of the original audio analysis.  
- **feedback_text**: Previous AI feedback text.  
- **user_question**: The follow-up question from the user.  
- **session_id**, **track_id**: Identify the session and track context.  
- **feedback_profile**: Detail level of feedback expected.  
- **followup_group**: Index of the follow-up conversation thread.  
- **ref_analysis_data**: Optional reference track analysis for comparative feedback.
    
```python
def fetch_tracks_and_context(req, db):
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
    # 1. Fetch main track
    main_track = db.query(Track).filter(Track.id == req.track_id).first()
    if not main_track:
        return None, None, None

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
        if summary_msg:
            summary_text = summary_msg.message

    return main_track, ref_analysis, summary_text
```

Explanation:
This part handles database interactions for the follow-up process. 
It retrieves the main track and optionally a reference track's analysis to provide comparative context. 
It also fetches a summary of the previous follow-up thread (if any) to keep the AI prompt concise 
and informed about past conversations.