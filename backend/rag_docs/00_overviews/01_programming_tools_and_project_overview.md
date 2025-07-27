# Programming Tools, Libraries, and Project Overview

This project uses a variety of programming languages, tools, and Python libraries chosen for their functionality, performance, and ease of integration to build a powerful AI-powered music mixing and mastering assistant.

---

## Programming Languages & Tools

### Python  
The core language used to build the backend API, audio analysis, and AI integration.

### PyCharm  
The primary Integrated Development Environment (IDE) used for writing, debugging, and managing the Python backend code.

### HTML  
The foundational markup language used to structure the frontend web interface.

### CSS  
Styles the HTML, providing layout, colors, fonts, and responsive design.

### JavaScript  
Adds interactivity to the frontend, handles user events, and communicates asynchronously with the backend API.

---

## Key Libraries and Their Roles

### FastAPI  
Provides the web framework for building a high-performance, asynchronous backend API handling uploads, analysis, chat interactions, and export functions.

### SQLAlchemy  
Manages database models, sessions, and queries, allowing structured storage of sessions, tracks, audio analyses, and AI feedback.

### Librosa  
A widely used audio analysis library for feature extraction, including key detection, tempo analysis, transient detection, spectral features, and more.

### NumPy  
Core numerical computing library used throughout for array operations, signal processing, and mathematical calculations.

### pyloudnorm  
Implements loudness measurement compliant with the LUFS standard, crucial for accurate perceived loudness estimation in audio.

### OpenAI SDK (`openai`)  
Handles interaction with GPT models to generate AI feedback, prompts, and follow-up responses.

### ReportLab  
Used to generate PDF exports of AI feedback and presets, enabling users to save or print their mixing/mastering guidance.

### Dotenv  
Loads environment variables securely from `.env` files, including API keys and configuration.

### Tailwind CSS (frontend)  
Provides utility-first CSS styling to build a responsive and modern user interface.

---

## Special Notes

- A compatibility fix for NumPy deprecated aliases (like `np.complex`) ensures smooth operation across different NumPy versions.

---

This comprehensive set of languages, tools, and libraries provides the foundation for the project’s architecture, enabling efficient audio processing, AI integration, and smooth user experience.


---

## Project Overview

This AI-powered music assistant helps users improve their mixes and masters by combining detailed audio analysis with intelligent, context-aware AI feedback.

### Main Features and Workflow

1. **User Upload**  
   - Users upload an audio track, optionally with a reference track.  
   - They specify metadata: type of feedback desired (mixdown tips, mastering guidance, master review), genre/subgenre, and feedback detail level (simple, detailed, pro).

2. **Audio Analysis**  
   - The backend performs in-depth audio analysis extracting metrics such as loudness (LUFS), dynamic range, transient strength, spectral balance, stereo width, tempo, and key.  
   - These metrics provide objective data describing the track’s sonic characteristics.

3. **AI Feedback Generation**  
   - Using OpenAI’s GPT models, the system generates tailored feedback prompts combining the audio analysis results and user metadata.  
   - Users can ask follow-up questions, which the system answers using conversation context and summarization techniques to keep interactions concise.

4. **Export and Presets**  
   - Users can export the AI feedback as PDFs for offline reference.  
   - The system can also generate plugin preset recommendations related to identified feedback issues.

### Technology Stack

- **Backend**: Python 3.x, FastAPI framework, SQLAlchemy ORM for database interaction, OpenAI API for AI feedback.  
- **Frontend**: HTML, CSS, JavaScript, styled with Tailwind CSS, and using local storage for user session data.

### High-Level Architecture

- The user interacts with a frontend web app styled via Tailwind CSS.  
- The backend API handles audio file uploads, runs analysis functions (using `librosa`, `pyloudnorm`, and others), stores data in a relational database, and orchestrates AI feedback generation via the OpenAI API.  
- AI chat interactions are maintained via session and chat message records in the database.  
- Export features use ReportLab to generate PDFs dynamically.

---

This overview and tooling information provides foundational knowledge about how the project is built and functions, supporting deeper explanations via the RAG system.