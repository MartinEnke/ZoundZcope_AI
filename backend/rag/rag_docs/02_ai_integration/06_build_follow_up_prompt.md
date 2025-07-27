# Follow-Up Prompt Construction (gpt_utils.py)

This section describes the function responsible for assembling a detailed, context-aware prompt
to guide the AI assistant in providing precise and relevant answers to user follow-up questions.

---

## Function: `build_followup_prompt`

- Integrates multiple sources of context into a single prompt string:  
  - Prior audio analysis text describing the submitted track’s attributes.  
  - Previous AI feedback given to the user.  
  - The user’s current follow-up question, sanitized and escaped for safety.  
  - An optional summary of the previous conversation to maintain continuity and reduce prompt length.  
  - Optional reference track analysis data for comparative feedback.

- Sanitizes and truncates the user’s question to remove unwanted characters and limit length.  
- Dynamically includes a reference track analysis section if such data is provided and valid.  
- Structures the prompt with clear labeled sections to ensure the AI understands the context and stays focused.  
- Provides explicit instructions to the AI to avoid repeating full prior text and to answer clearly and technically.

---

**Inputs:**

- `analysis_text` (str): Description of the track’s audio analysis.  
- `feedback_text` (str): The last AI-generated feedback text.  
- `user_question` (str): The follow-up question from the user.  
- `thread_summary` (str, optional): Summary of earlier follow-up conversation for context.  
- `ref_analysis_data` (dict, optional): Reference track analysis for comparison.

---

**Output:**

- A formatted prompt string, ready to be submitted to the AI model for generating the follow-up response.

---

**Design Notes:**

- Ensures the prompt is concise and well-structured to optimize AI understanding and response quality.  
- Handles missing or invalid reference data gracefully with warnings.  
- Emphasizes professional, helpful, and focused assistant behavior.

---

*The complete source code for this function is stored separately for exact retrieval.*
