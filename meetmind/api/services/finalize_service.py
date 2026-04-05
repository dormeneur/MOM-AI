"""
Finalize Service — Post-meeting processing.

Called once when the meeting ends:
1. Load all transcript segments
2. Run BART summarisation
3. Generate global + personalised MOMs
4. Send emails
5. Update session status
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session as DBSession

from api.database import Session, Participant, TranscriptSegment, ActionItem
from api.schemas import FinalizeResponse

logger = logging.getLogger(__name__)


def _build_mom_data(session_id: str, db: DBSession) -> dict:
    """Build all data needed for MOM generation."""
    # Load all segments
    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.session_id == session_id)
        .order_by(TranscriptSegment.start_time)
        .all()
    )

    # Map speaker labels to names
    participants = db.query(Participant).filter(Participant.session_id == session_id).all()
    label_to_name = {p.speaker_label: p.display_name for p in participants if p.speaker_label}

    # Build full transcript
    transcript_lines = []
    for seg in segments:
        name = label_to_name.get(seg.speaker_label, seg.speaker_label or "Unknown")
        transcript_lines.append(f"{name}: {seg.text}")
    full_transcript = "\n".join(transcript_lines)

    # Summarise
    summary = "Meeting summary not available."
    if full_transcript.strip():
        try:
            from ml.summariser.summariser import MeetingSummariser
            summariser = MeetingSummariser()
            summary = summariser.summarise(full_transcript)
        except Exception as e:
            logger.error(f"Summarisation failed: {e}")
            # Fallback: first 3 sentences
            sentences = full_transcript.split(".")[:3]
            summary = ". ".join(sentences).strip() + "."

    # Collect decisions, topics, action items
    decisions = [
        {"speaker": label_to_name.get(s.speaker_label, s.speaker_label), "text": s.text}
        for s in segments if s.label == "decision"
    ]
    topics = [
        {"speaker": label_to_name.get(s.speaker_label, s.speaker_label), "text": s.text}
        for s in segments if s.label == "topic"
    ]

    action_items_db = (
        db.query(ActionItem)
        .filter(ActionItem.session_id == session_id)
        .all()
    )
    action_items = [
        {
            "task_description": ai.task_description,
            "assigned_to_name": ai.assigned_to_name,
            "assigned_to_email": ai.assigned_to_email,
            "assigned_by_name": ai.assigned_by_name,
            "deadline": ai.deadline,
            "confidence": ai.confidence,
        }
        for ai in action_items_db
    ]

    # Session info
    session = db.query(Session).filter(Session.id == session_id).first()
    participant_list = [
        {"display_name": p.display_name, "email": p.email}
        for p in participants
    ]

    return {
        "summary": summary,
        "decisions": decisions,
        "topics": topics,
        "action_items": action_items,
        "participants": participant_list,
        "session": {
            "meet_url": session.meet_url if session else "",
            "created_at": session.created_at.isoformat() if session and session.created_at else "",
            "host_email": session.host_email if session else "",
        },
    }


async def finalize_session(session_id: str, db: DBSession) -> FinalizeResponse:
    """
    Post-meeting finalization:
    1. Summarise transcript
    2. Generate MOMs
    3. Send emails
    4. Update session status
    """
    logger.info(f"Finalising session {session_id}")

    mom_data = _build_mom_data(session_id, db)

    from mom.generator import MOMGenerator
    gen = MOMGenerator()

    # Generate global MOM
    global_html = gen.generate_global(**mom_data)

    # Send personalised MOMs
    emails_sent = 0
    try:
        from mom.mailer import Mailer
        mailer = Mailer()

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
            try:
                mailer.send(p.email, "[MeetMind] Your action items from today's meeting", p_html)
                emails_sent += 1
            except Exception as e:
                logger.error(f"Failed to email {p.email}: {e}")

        # Send global MOM to host
        session = db.query(Session).filter(Session.id == session_id).first()
        if session and session.host_email:
            try:
                today = datetime.now().strftime("%Y-%m-%d")
                mailer.send(
                    session.host_email,
                    f"[MeetMind] Full MOM — {today} meeting",
                    global_html,
                )
                emails_sent += 1
            except Exception as e:
                logger.error(f"Failed to email host {session.host_email}: {e}")

    except Exception as e:
        logger.error(f"Email sending failed: {e}")

    # Update session status
    session = db.query(Session).filter(Session.id == session_id).first()
    if session:
        session.status = "complete"
        session.ended_at = datetime.utcnow()
        db.commit()

    # Push finalised event to WebSocket
    try:
        from api.routers.websocket import broadcast
        await broadcast(session_id, {
            "type": "finalized",
            "data": {"mom_url": f"/api/sessions/{session_id}/mom"},
        })
    except Exception:
        pass

    logger.info(f"Session {session_id} finalised: {emails_sent} emails sent")
    return FinalizeResponse(mom_generated=True, emails_sent=emails_sent)
