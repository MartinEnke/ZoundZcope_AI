# AI Response Generation Functions

This section covers functions responsible for sending prompts to the AI model and retrieving responses.

---

## `generate_feedback_response`

```python
def generate_feedback_response(prompt: str) -> str:
    """
    Sends a prompt string to the AI model and returns the generated feedback text.

    Parameters:
        prompt (str): The fully constructed prompt containing context, instructions, and analysis data.

    Returns:
        str: The AI-generated feedback text, stripped of leading/trailing whitespace.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()
```

Explanation:
Uses OpenAI's chat completion API with the specified model.
Assumes the prompt is already well-formed.
Returns the textual content from the first choice in the response.


---

## `generate_follow_response`


```python

def generate_followup_response(analysis_text: str, feedback_text: str, user_question: str, thread_summary: str = "") -> str:
    """
    Builds a follow-up prompt incorporating prior analysis, feedback, user question,
    and optionally a summary of the follow-up conversation thread, then sends it to the AI.

    Parameters:
        analysis_text (str): Text description of the audio analysis.
        feedback_text (str): Previous AI feedback given to the user.
        user_question (str): The user's follow-up question.
        thread_summary (str, optional): Summary of previous follow-up messages for context.

    Returns:
        str: AI-generated answer to the follow-up question.
    """
    
    prompt = build_followup_prompt(analysis_text, feedback_text, user_question, thread_summary)
    return generate_feedback_response(prompt)
```
Explanation:
Leverages build_followup_prompt to create a context-rich prompt.
Calls generate_feedback_response to get the AI's reply.
Designed for multi-turn conversations with context preservation.