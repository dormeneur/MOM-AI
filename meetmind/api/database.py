"""
Database models and setup — SQLAlchemy + SQLite.
"""

import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = "sqlite:///./meetmind.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Session(Base):
    """One row per Google Meet call."""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    meet_url = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending | active | processing | complete | error
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    host_email = Column(String, nullable=True)

    participants = relationship("Participant", back_populates="session", cascade="all, delete-orphan")
    segments = relationship("TranscriptSegment", back_populates="session", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="session", cascade="all, delete-orphan")


class Participant(Base):
    """One row per person in the meeting."""
    __tablename__ = "participants"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    display_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    speaker_label = Column(String, nullable=True)  # SPEAKER_00, SPEAKER_01, etc.

    session = relationship("Session", back_populates="participants")


class TranscriptSegment(Base):
    """One row per sentence/utterance."""
    __tablename__ = "transcript_segments"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    speaker_label = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)
    label = Column(String, nullable=True)  # action_item | decision | topic | deadline_mention | general
    label_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="segments")
    action_items = relationship("ActionItem", back_populates="segment", cascade="all, delete-orphan")


class ActionItem(Base):
    """One row per extracted task."""
    __tablename__ = "action_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    segment_id = Column(String, ForeignKey("transcript_segments.id"), nullable=True)
    assigned_to_name = Column(String, nullable=True)
    assigned_to_email = Column(String, nullable=True)
    assigned_by_name = Column(String, nullable=True)
    task_description = Column(Text, nullable=False)
    deadline = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="action_items")
    segment = relationship("TranscriptSegment", back_populates="action_items")


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
