# AI Integration Overview

This section explains how AI feedback and interactive chat features are integrated into the music mixing and mastering assistant backend.

---

## Key Components

### 1. Feedback Generation

- Receives user inputs such as track ID, session ID, genre, feedback type (mixdown, mastering, master review), and feedback profile (simple, detailed, pro).
- Fetches the stored audio analysis data for the selected track from the database.
- Normalizes user inputs like genre, type, and profile to ensure consistent processing.
- Calls the feedback prompt generator to build a detailed AI prompt, embedding audio metrics, genre context, and communication style guidance.
- Sends the prompt to the AI model to generate tailored feedback.
- Stores the AI feedback as a chat message in the database for session persistence.
- The generated feedback is displayed on the main user interface (e.g., `index.html`).

---

### 2. Follow-Up Question Handling (`/ask-followup` endpoint)

- Supports multi-turn conversations by accepting follow-up user questions referencing prior analysis and feedback.
- Retrieves the main track and optionally a reference track’s analysis data to provide context-aware comparison feedback.
- Includes a conversation summary from prior follow-up messages to keep context concise.
- Constructs a comprehensive follow-up prompt combining analysis, previous feedback, user question, and summary.
- Generates AI response and stores both user question and AI answer as chat messages linked by session and follow-up group.
- Implements automatic summarization of follow-up threads after several interactions to maintain concise context and improve response relevance.

---

### 3. Prompt Construction & AI Calls

- Prompts contain multiple structured sections including:  
  - Role-specific context describing the AI as a professional mixing or mastering engineer with genre expertise.  
  - Communication style instructions matching user-selected feedback profile (simple, detailed, pro).  
  - Embedded audio analysis data with loudness, dynamic range, transients, spectral balance, stereo width, and bass profile.  
  - Conditional inclusion of reference track analysis for comparative feedback.  
  - Format rules and example bullet point outputs guiding the AI’s response style.

- AI calls use OpenAI’s GPT models (`gpt-4o-mini` currently) with messages formatted as user prompts.

---

### 4. Data Persistence & Session Management

- Chat messages (user and assistant) are stored in a database table linked by session, track, and follow-up group identifiers.
- Enables resuming conversations, retrieving message history, and supporting multi-turn dialogue.
- Summaries generated after a set number of follow-ups optimize prompt length and AI context window usage.

---

## Summary

This AI integration combines precise audio analysis data with dynamic, role- and style-aware prompt construction to generate meaningful, user-tailored mixing and mastering feedback. It supports an interactive chat interface with follow-up questions and conversation summarization, creating a natural, continuous feedback experience for users.
