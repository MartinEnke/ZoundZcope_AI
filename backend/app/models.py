"""
Database models for ZoundZcope.

This module defines SQLAlchemy ORM models for users, sessions, tracks,
analysis results, and chat messages. These models form the core database
schema for authentication, project organization, audio analysis storage,
and AI-driven feedback history.

Tables:
    - users            : Stores registered user accounts.
    - sessions         : Groups tracks under a named analysis/project context.
    - tracks           : Represents individual uploaded audio files with metadata.
    - analysis_results : Stores technical analysis metrics for a single track.
    - chat_history     : Holds AI feedback messages, follow-up Q&A, and comparison results.

Relationships:
    - User → Session (one-to-many)
    - Session → Track (one-to-many)
    - Session → ChatMessage (one-to-many)
    - Track → AnalysisResult (one-to-one)
    - Track → Session (many-to-one)
    - ChatMessage → Session (many-to-one)
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class User(Base):
    """
        Represents a registered application user.

        Fields:
            id (int): Primary key.
            username (str): Unique display/username.
            email (str): Unique email address for login/notifications.
            hashed_password (str): Securely hashed password.
            created_at (datetime): Timestamp of account creation.

        Relationships:
            sessions (list[Session]): All sessions created by the user.
        """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sessions = relationship("Session", back_populates="user")


class Session(Base):
    """
        Represents a collection of tracks grouped under a named project/session.

        Fields:
            id (str): Primary key (UUID string).
            user_id (int): Foreign key referencing User.id.
            session_name (str): User-defined session/project name.
            created_at (datetime): Timestamp of session creation.

        Relationships:
            user (User): The owning user.
            tracks (list[Track]): Tracks associated with this session.
            chats (list[ChatMessage]): Chat messages linked to this session.
        """
    __tablename__ = 'sessions'
    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    session_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")
    tracks = relationship("Track", back_populates="session")
    chats = relationship("ChatMessage", back_populates="session")


class Track(Base):
    """
        Represents an uploaded audio track.

        Fields:
            id (str): Primary key (UUID string).
            session_id (str): Foreign key referencing Session.id.
            track_name (str): User-provided track name.
            file_path (str): Filesystem path to the uploaded audio.
            type (str): Track type (e.g., 'mixdown', 'master').
            genre (str, optional): Genre classification.
            uploaded_at (datetime): Timestamp of upload.
            upload_group_id (str): Group identifier for related uploads.

        Relationships:
            session (Session): The parent session.
            analysis (AnalysisResult): The technical analysis result (one-to-one).
        """
    __tablename__ = 'tracks'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey('sessions.id'))
    track_name = Column(String)
    file_path = Column(String)
    type = Column(String)
    genre = Column(String, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    upload_group_id = Column(String, nullable=False, default=lambda: str(uuid.uuid4()))

    session = relationship("Session", back_populates="tracks")
    analysis = relationship("AnalysisResult", back_populates="track", uselist=False)


class AnalysisResult(Base):
    """
        Stores detailed audio analysis metrics for a single track.

        Fields:
            id (int): Primary key.
            track_id (str): Foreign key referencing Track.id.

            peak_db (float): Peak amplitude in dBFS.
            rms_db_avg (float): Average RMS level.
            rms_db_peak (float): Peak RMS level.
            lufs (float): Integrated loudness in LUFS.
            dynamic_range (float): Calculated dynamic range in dB.

            stereo_width_ratio (float): Stereo spread ratio (0–1).
            stereo_width (str): Qualitative stereo width descriptor.

            key (str): Musical key.
            tempo (float): Detected tempo in BPM.

            low_end_energy_ratio (float): Low-end energy proportion.
            low_end_description (str): Qualitative low-end description.

            band_energies (str): JSON string of frequency band energy values.
            spectral_balance_description (str): Qualitative tonal balance notes.
            issues (str): JSON string list of detected mix/master issues.
            peak_issue (str): Peak-related issue description.
            peak_issue_explanation (str): Detailed explanation of peak issue.

            avg_transient_strength (float): Average transient energy.
            max_transient_strength (float): Maximum transient energy.
            transient_description (str): Qualitative transient performance.

        Relationships:
            track (Track): The analyzed track.
        """
    __tablename__ = 'analysis_results'
    id = Column(Integer, primary_key=True)
    track_id = Column(String, ForeignKey('tracks.id'))

    peak_db = Column(Float)
    rms_db_avg = Column(Float)  # average RMS
    rms_db_peak = Column(Float)
    lufs = Column(Float)
    dynamic_range = Column(Float)

    stereo_width_ratio = Column(Float)
    stereo_width = Column(String)

    key = Column(String)
    tempo = Column(Float)

    low_end_energy_ratio = Column(Float)
    low_end_description = Column(String)

    band_energies = Column(String)  # JSON string like '{"low": 10.1, ...}'
    spectral_balance_description = Column(String)
    issues = Column(Text)  # JSON string like '["clipping", "bass masking"]'
    peak_issue = Column(Text)
    peak_issue_explanation = Column(Text)
    avg_transient_strength = Column(Float)
    max_transient_strength = Column(Float)
    transient_description = Column(Text)

    track = relationship("Track", back_populates="analysis")


class ChatMessage(Base):
    """
        Represents a chat message in the AI feedback history.

        Fields:
            id (int): Primary key.
            session_id (str): Foreign key referencing Session.id.
            track_id (str, optional): Foreign key referencing Track.id.
            sender (str): Message sender ('user' or 'AI').
            message (str): Message text content.
            timestamp (datetime): Timestamp of message creation.
            feedback_profile (str, optional): Profile used for AI feedback ('simple', 'detailed', 'pro').
            followup_group (int, optional): Group index for related follow-ups.

            comparison_group_id (str, optional): ID for comparison feedback grouping.
            compared_track_ids (str, optional): JSON/text list of compared track IDs.
            compared_track_names (str, optional): JSON/text list of compared track names.

        Relationships:
            session (Session): The parent session for this message.
        """
    __tablename__ = 'chat_history'
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey('sessions.id'))
    track_id = Column(String, ForeignKey('tracks.id'), nullable=True)
    sender = Column(String)
    message = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    feedback_profile = Column(String, nullable=True)
    followup_group = Column(Integer, nullable=True, default=0)

    comparison_group_id = Column(String, nullable=True)
    compared_track_ids = Column(Text, nullable=True)
    compared_track_names = Column(Text, nullable=True)

    session = relationship("Session", back_populates="chats")
