# Function: ask_followup 

## Part 3: Auto Summary and Response

```python
def create_summary_if_needed(req, db):
    """
    Checks if enough follow-up user messages exist to generate an automatic summary.
    If so, generates a concise summary via the AI, saves it, and marks it in the response.

    Parameters:
        req (FollowUpRequest): Follow-up request data.
        db (Session): Database session for querying and saving messages.

    Returns:
        dict: Contains AI answer and summary creation flag if applicable.
    """
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

    response_data = {}

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

        summary_text = generate_feedback_response(summary_prompt)

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
        response_data["summary_text"] = summary_text

    return response_data
```

Explanation:
This function monitors the number of follow-up user messages in the current thread and, 
when a threshold is reached, triggers the AI to produce a concise summary of the conversation. 
The summary is saved as a special chat message and flagged in the response, 
improving context management for future interactions.