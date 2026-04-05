"""
Pydantic request/response schemas for all API endpoints.
"""

from pydantic import BaseModel
from datetime import datetime


# --- Session ---
class SessionCreate(BaseModel):
    meet_url: str
    host_email: str | None = None


class SessionResponse(BaseModel):
    session_id: str
    status: str


class SessionDetail(BaseModel):
    id: str
    meet_url: str
    status: str
    created_at: datetime
    ended_at: datetime | None = None
    host_email: str | None = None

    class Config:
        from_attributes = True


# --- Bot ---
class BotLaunchResponse(BaseModel):
    bot_status: str
    meet_url: str


class BotStopResponse(BaseModel):
    status: str


# --- Audio ---
class AudioAccepted(BaseModel):
    accepted: bool
    chunk_id: str | None = None


# --- Transcript ---
class TranscriptSegmentResponse(BaseModel):
    speaker_label: str | None = None
    display_name: str | None = None
    text: str
    label: str | None = None
    label_confidence: float | None = None
    start_time: float | None = None
    end_time: float | None = None


# --- Action Item ---
class ActionItemResponse(BaseModel):
    id: str
    task_description: str
    assigned_to_name: str | None = None
    assigned_to_email: str | None = None
    assigned_by_name: str | None = None
    deadline: str | None = None
    confidence: float | None = None


# --- Participant ---
class ParticipantResponse(BaseModel):
    id: str
    display_name: str
    email: str | None = None
    speaker_label: str | None = None

    class Config:
        from_attributes = True


class ParticipantUpdate(BaseModel):
    email: str


class ParticipantCreate(BaseModel):
    display_name: str
    email_guess: str | None = None


# --- Finalize ---
class FinalizeResponse(BaseModel):
    mom_generated: bool
    emails_sent: int


# --- MOM ---
class MOMResponse(BaseModel):
    global_mom_html: str
    personalised_moms: dict[str, str] = {}
