# Function Explanation: `upload_audio` (upload endpoint)

This API endpoint handles the full process triggered when a user uploads an audio file.

**Workflow:**

1. **Input Normalization:**  
   Normalizes `session_id`, `session_name`, `genre`, `subgenre`, `type`, and `feedback_profile` to standardized forms.

2. **File Saving:**  
   Saves the uploaded main audio file and optionally a reference audio file with unique timestamped filenames in the designated upload folder.

3. **RMS Chunk Computation:**  
   Computes RMS values over time windows for waveform visualization and saves the results as a JSON file accessible by the frontend.

4. **Audio Analysis:**  
   Uses the `analyze_audio` function to extract loudness, key, transient strength, spectral balance, and other audio features from the main and reference tracks.

5. **Database Operations:**  
   - Cleans up old tracks linked to the session to avoid stale files.  
   - Creates or updates session records.  
   - Saves new track metadata and analysis results, including linking reference tracks by a shared group ID.

6. **AI Feedback Generation:**  
   Constructs a detailed prompt with audio analysis data (and optional reference analysis) using `generate_feedback_prompt`.  
   Sends the prompt to the AI model and stores the assistant's response as chat history.

7. **Response Construction:**  
   Returns a comprehensive JSON payload containing track details, analyses, AI feedback, and URLs to uploaded files and RMS data.

---

**Error Handling:**  
Captures exceptions during upload or processing, logs full stack traces, and returns HTTP 500 JSON error responses.

---

**Design Notes:**  
- Timestamped filenames prevent file overwrites and maintain upload history.  
- Reference tracks are optional but enable comparative feedback for users.  
- Database cleanup ensures disk space is managed by removing outdated session tracks.  
- Tight integration with AI prompt generation provides contextual and personalized feedback.  
- Modular helper functions keep the endpoint code readable and maintainable.

---

*This explanation focuses on the overall logic and flow rather than low-level code details, which are documented separately.*
