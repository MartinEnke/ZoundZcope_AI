# Database Models Overview (models.py)

This module defines the SQLAlchemy ORM models used for persistent storage of users, sessions, tracks, audio analysis results, and chat history.

It establishes relationships between entities, enforces schema constraints, and supports complex queries necessary for the music AI feedback system.

The models include:

- **User**: Stores authentication and profile information.  
- **Session**: Represents user sessions grouping tracks and chat messages.  
- **Track**: Represents uploaded audio tracks with metadata.  
- **AnalysisResult**: Stores detailed audio analysis data linked to tracks.  
- **ChatMessage**: Records conversational history between users and the AI assistant.

---