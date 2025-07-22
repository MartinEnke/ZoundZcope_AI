from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sessions = relationship("Session", back_populates="user")

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    session_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")
    tracks = relationship("Track", back_populates="session")
    chats = relationship("ChatMessage", back_populates="session")

class Track(Base):
    __tablename__ = 'tracks'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey('sessions.id'))
    track_name = Column(String)
    file_path = Column(String)
    type = Column(String)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    upload_group_id = Column(String, nullable=False, default=lambda: str(uuid.uuid4()))

    session = relationship("Session", back_populates="tracks")
    analysis = relationship("AnalysisResult", back_populates="track", uselist=False)

class AnalysisResult(Base):
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
    __tablename__ = 'chat_history'
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey('sessions.id'))
    track_id = Column(String, ForeignKey('tracks.id'))
    sender = Column(String)
    message = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    feedback_profile = Column(String, nullable=True)
    followup_group = Column(Integer, nullable=True, default=0)

    session = relationship("Session", back_populates="chats")
