from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

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
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    session_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")
    tracks = relationship("Track", back_populates="session")
    chats = relationship("ChatMessage", back_populates="session")

class Track(Base):
    __tablename__ = 'tracks'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    track_name = Column(String)
    file_path = Column(String)
    type = Column(String)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="tracks")
    analysis = relationship("AnalysisResult", back_populates="track", uselist=False)

class AnalysisResult(Base):
    __tablename__ = 'analysis_results'
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey('tracks.id'))
    peak_db = Column(Float)
    rms_db = Column(Float)
    lufs = Column(Float)
    dynamic_range = Column(Float)
    stereo_width_ratio = Column(Float)
    stereo_width = Column(String)
    key = Column(String)
    tempo = Column(Float)
    low_end_energy_ratio = Column(Float)
    bass_profile = Column(String)
    masking_detected = Column(Boolean)
    issues = Column(Text) # Store as JSON string (e.g. '["clipping", "bass masking"]')

    track = relationship("Track", back_populates="analysis")

class ChatMessage(Base):
    __tablename__ = 'chat_history'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    sender = Column(String)
    message = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    session = relationship("Session", back_populates="chats")
