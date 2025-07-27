## Function: build_followup_prompt

```python
def build_followup_prompt(
    analysis_text: str,
    feedback_text: str,
    user_question: str,
    thread_summary: str = "",
    ref_analysis_data: dict = None,
) -> str:
    """
    Constructs a detailed prompt for AI follow-up feedback based on prior analysis,
    previous feedback, the user’s follow-up question, optional conversation summary,
    and optionally reference track analysis data.

    Parameters:
        analysis_text (str): Text description of the audio analysis.
        feedback_text (str): Previous AI feedback text.
        user_question (str): User’s follow-up question.
        thread_summary (str, optional): Summary of prior follow-up conversation for context.
        ref_analysis_data (dict, optional): Reference track analysis for comparison.

    Returns:
        str: A formatted prompt string ready for submission to the AI model.
    """
    
    # Clean and escape user question
    user_question = re.sub(r"[^\w\s.,!?@&$()\-+=:;\'\"/]", "", user_question.strip())[:400]
    user_question = html.escape(user_question)

    ref_section = ""
    if ref_analysis_data and isinstance(ref_analysis_data, dict):
        ref_section = f"""
        ### Reference Track Analysis (for comparison)
        - Peak: {ref_analysis_data.get('peak_db', 'N/A')} dB
        - RMS Peak: {ref_analysis_data.get('rms_db_peak', 'N/A')} dB
        - LUFS: {ref_analysis_data.get('lufs', 'N/A')}
        - Transients: {ref_analysis_data.get('transient_description', 'N/A')}
        - Spectral balance note: {ref_analysis_data.get('spectral_balance_description', 'N/A')}
        - Dynamic range: {ref_analysis_data.get('dynamic_range', 'N/A')}
        - Stereo width: {ref_analysis_data.get('stereo_width', 'N/A')}
        - Bass profile: {ref_analysis_data.get('low_end_description', '')}
        """
    else:
        print("Warning: ref_analysis_data missing or invalid:", ref_analysis_data)

    return f"""
You are a helpful and professional **audio engineer assistant**.

{"### Summary of Previous Conversation\n" + thread_summary + "\n" if thread_summary else ""}

### Track Analysis
{analysis_text}

{ref_section}

### Prior Feedback
{feedback_text}

### User's Follow-Up Question
"{user_question}"

### Instructions
- Use the analysis, feedback, and summary above as context.
- Do **not** repeat the full analysis or feedback.
- Answer the follow-up clearly and concisely.
- Stay on topic and be technically helpful.
- If the question is vague, use the existing context to infer intent.

Respond below:
"""
```

Explanation:
This function builds a context-rich prompt that guides the AI assistant when answering user follow-up questions. It includes the original audio analysis, prior AI feedback, the sanitized user question, an optional conversation summary to keep context concise, and optionally reference track analysis for comparative feedback. The prompt instructs the AI to be concise, focused, and technically helpful, ensuring relevant and precise answers.

