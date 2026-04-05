"""
Session CRUD endpoints + transcript, action items, participants, MOM, finalize.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from api.database import get_db, Session, Participant, TranscriptSegment, ActionItem, generate_uuid
from api.schemas import (
    SessionCreate, SessionResponse, SessionDetail,
    TranscriptSegmentResponse, ActionItemResponse,
    ParticipantResponse, ParticipantUpdate, ParticipantCreate,
    FinalizeResponse, MOMResponse,
)

router = APIRouter()


@router.post("/sessions", response_model=SessionResponse)
def create_session(data: SessionCreate, db: DBSession = Depends(get_db)):
    """Create a new meeting session."""
    session = Session(
        id=generate_uuid(),
        meet_url=data.meet_url,
        status="pending",
        host_email=data.host_email,
    )
    db.add(session)
    db.commit()
    return SessionResponse(session_id=session.id, status=session.status)


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    """Get session details."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions/{session_id}/transcript", response_model=list[TranscriptSegmentResponse])
def get_transcript(session_id: str, db: DBSession = Depends(get_db)):
    """Get all transcript segments for a session."""
    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.session_id == session_id)
        .order_by(TranscriptSegment.start_time)
        .all()
    )

    # Map speaker labels to display names
    participants = db.query(Participant).filter(Participant.session_id == session_id).all()
    label_to_name = {p.speaker_label: p.display_name for p in participants if p.speaker_label}

    return [
        TranscriptSegmentResponse(
            speaker_label=seg.speaker_label,
            display_name=label_to_name.get(seg.speaker_label, seg.speaker_label),
            text=seg.text,
            label=seg.label,
            label_confidence=seg.label_confidence,
            start_time=seg.start_time,
            end_time=seg.end_time,
        )
        for seg in segments
    ]


@router.get("/sessions/{session_id}/action_items", response_model=list[ActionItemResponse])
def get_action_items(session_id: str, db: DBSession = Depends(get_db)):
    """Get all action items for a session."""
    items = (
        db.query(ActionItem)
        .filter(ActionItem.session_id == session_id)
        .order_by(ActionItem.created_at)
        .all()
    )
    return [
        ActionItemResponse(
            id=item.id,
            task_description=item.task_description,
            assigned_to_name=item.assigned_to_name,
            assigned_to_email=item.assigned_to_email,
            assigned_by_name=item.assigned_by_name,
            deadline=item.deadline,
            confidence=item.confidence,
        )
        for item in items
    ]


@router.get("/sessions/{session_id}/participants", response_model=list[ParticipantResponse])
def get_participants(session_id: str, db: DBSession = Depends(get_db)):
    """Get all participants for a session."""
    participants = db.query(Participant).filter(Participant.session_id == session_id).all()
    return participants


@router.post("/sessions/{session_id}/participants", response_model=ParticipantResponse)
def add_participant(session_id: str, data: ParticipantCreate, db: DBSession = Depends(get_db)):
    """Add or update a participant (used by bot scraper)."""
    existing = (
        db.query(Participant)
        .filter(Participant.session_id == session_id, Participant.display_name == data.display_name)
        .first()
    )
    if existing:
        if data.email_guess and not existing.email:
            existing.email = data.email_guess
            db.commit()
        return existing

    participant = Participant(
        id=generate_uuid(),
        session_id=session_id,
        display_name=data.display_name,
        email=data.email_guess,
    )
    db.add(participant)
    db.commit()
    return participant


@router.put("/sessions/{session_id}/participants/{participant_id}")
def update_participant(session_id: str, participant_id: str, data: ParticipantUpdate, db: DBSession = Depends(get_db)):
    """Update participant email (host fills in manually via dashboard)."""
    participant = (
        db.query(Participant)
        .filter(Participant.id == participant_id, Participant.session_id == session_id)
        .first()
    )
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    participant.email = data.email
    db.commit()

    # Re-resolve action item assignments
    if participant.display_name:
        items = (
            db.query(ActionItem)
            .filter(
                ActionItem.session_id == session_id,
                ActionItem.assigned_to_name == participant.display_name,
            )
            .all()
        )
        for item in items:
            item.assigned_to_email = data.email
        db.commit()

    return {"updated": True}


@router.post("/sessions/{session_id}/finalize", response_model=FinalizeResponse)
async def finalize_session(session_id: str, db: DBSession = Depends(get_db)):
    """Post-meeting: summarise, generate MOMs, send emails."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    from api.services.finalize_service import finalize_session as do_finalize
    result = await do_finalize(session_id, db)
    return result


@router.get("/sessions/{session_id}/mom", response_model=MOMResponse)
def get_mom(session_id: str, db: DBSession = Depends(get_db)):
    """Get generated MOM (after finalization)."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Build MOM on-the-fly
    from mom.generator import MOMGenerator
    from api.services.finalize_service import _build_mom_data
    mom_data = _build_mom_data(session_id, db)
    gen = MOMGenerator()

    global_html = gen.generate_global(**mom_data)

    personalised_moms = {}
    participants = db.query(Participant).filter(
        Participant.session_id == session_id,
        Participant.email.isnot(None),
    ).all()

    for p in participants:
        p_tasks = [
            t for t in mom_data["action_items"]
            if t.get("assigned_to_email") == p.email or t.get("assigned_to_name") == p.display_name
        ]
        p_html = gen.generate_personalised(
            participant={"display_name": p.display_name, "email": p.email},
            summary=mom_data["summary"],
            decisions=mom_data["decisions"],
            topics=mom_data["topics"],
            tasks=p_tasks,
        )
        personalised_moms[p.email] = p_html

    return MOMResponse(global_mom_html=global_html, personalised_moms=personalised_moms)
