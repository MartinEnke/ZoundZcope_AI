# ask_followup - Part 2: Build Prompt, Generate Response, Save Messages

```python
def process_followup_and_save(req, main_track, ref_analysis, summary_text, db):
    """
    Constructs the AI prompt for the follow-up question, sends it to the AI,
    and saves both the user's question and AI assistant's response in the database.

    Parameters:
        req (FollowUpRequest): The follow-up request containing user question and metadata.
        main_track (Track): The main track object retrieved from the database.
        ref_analysis (dict or None): Reference track analysis data for comparative feedback.
        summary_text (str): Summary of previous follow-up conversation.
        db (Session): Database session for saving chat messages.

    Returns:
        str: The AI-generated response text.
    """
    profile = normalize_profile(req.feedback_profile)
    user_question = sanitize_user_question(req.user_question)

    prompt = build_followup_prompt(
        analysis_text=req.analysis_text,
        feedback_text=req.feedback_text,
        user_question=user_question,
        thread_summary=summary_text,
        ref_analysis_data=ref_analysis or req.ref_analysis_data
    )

    ai_response = generate_feedback_response(prompt)

    # Save user message
    user_msg = ChatMessage(
        session_id=req.session_id,
        track_id=main_track.id,
        sender="user",
        message=user_question,
        feedback_profile=profile,
        followup_group=req.followup_group
    )
    db.add(user_msg)

    # Save AI assistant response
    assistant_msg = ChatMessage(
        session_id=req.session_id,
        track_id=main_track.id,
        sender="assistant",
        message=ai_response,
        feedback_profile=profile,
        followup_group=req.followup_group
    )
    db.add(assistant_msg)
    db.commit()

    return ai_response




Explanation:
This step prepares the AI prompt using the user’s question, previous feedback, audio analysis, 
and optional reference track data. It then calls the AI to generate a contextual answer 
and records both sides of the conversation in the database for session continuity and history.
