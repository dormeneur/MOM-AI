"""
Demo router — loads synthetic meeting data from demo_config.json.
Runs ML pipeline and pushes results to dashboard via WebSocket.
"""

import os
import json
import logging
import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from api.database import get_db, Session, Participant, TranscriptSegment, ActionItem, generate_uuid
from api.routers.websocket import broadcast

router = APIRouter()
logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'demo_config.json')


def _load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post("/api/demo/start")
async def start_demo(db: DBSession = Depends(get_db)):
    """
    Create a demo session from demo_config.json.
    Classifies each sentence, extracts tasks, pushes to WebSocket.
    """
    config = _load_config()
    meeting = config["meeting"]
    participants_cfg = config["participants"]
    transcript_cfg = config["transcript"]

    # Create session
    session = Session(
        id=generate_uuid(),
        meet_url="https://meet.google.com/demo-meeting",
        status="active",
        host_email=participants_cfg[0]["email"],
    )
    db.add(session)
    db.flush()

    # Add participants
    for p in participants_cfg:
        db.add(Participant(
            id=generate_uuid(),
            session_id=session.id,
            display_name=p["display_name"],
            email=p["email"],
            speaker_label=p["speaker_label"],
        ))
    db.flush()

    # Classify
    import joblib
    from ml.classifier.features import extract_features
    from ml.classifier.mlp_model import INT_TO_LABEL

    mlp = joblib.load("ml/classifier/models/mlp_classifier.pkl")

    sentences = [s["text"] for s in transcript_cfg]
    features = extract_features(sentences, training=False)
    predictions = mlp.model.predict(features)
    probas = mlp.model.predict_proba(features)

    # NER
    try:
        from ml.ner.task_extractor import TaskExtractor
        extractor = TaskExtractor()
        ner_ok = True
    except Exception:
        extractor = None
        ner_ok = False

    # Name-to-display mapping
    name_to_label = {p["display_name"]: p["speaker_label"] for p in participants_cfg}

    segments_out = []
    actions_out = []

    for i, s in enumerate(transcript_cfg):
        label = INT_TO_LABEL[predictions[i]]
        confidence = float(probas[i].max())
        speaker_label = name_to_label.get(s["speaker"], "SPEAKER_UNKNOWN")

        seg = TranscriptSegment(
            id=generate_uuid(),
            session_id=session.id,
            speaker_label=speaker_label,
            text=s["text"],
            start_time=float(i * 4),
            end_time=float(i * 4 + 3.5),
            label=label,
            label_confidence=confidence,
        )
        db.add(seg)
        db.flush()

        segments_out.append({
            "speaker_label": speaker_label,
            "display_name": s["speaker"],
            "text": s["text"],
            "label": label,
            "confidence": confidence,
        })

        if label in ("action_item", "deadline_mention") and extractor:
            try:
                extraction = extractor.extract(s["text"], speaker_name=s["speaker"])
                assignee_email = None
                for p in participants_cfg:
                    if extraction["assignee"] and extraction["assignee"] in p["display_name"]:
                        assignee_email = p["email"]
                        break

                ai = ActionItem(
                    id=generate_uuid(),
                    session_id=session.id,
                    segment_id=seg.id,
                    assigned_to_name=extraction["assignee"],
                    assigned_to_email=assignee_email,
                    assigned_by_name=s["speaker"],
                    task_description=extraction["task_description"],
                    deadline=extraction["deadline"],
                    confidence=extraction["confidence"],
                )
                db.add(ai)
                actions_out.append({
                    "task_description": extraction["task_description"],
                    "assigned_to_name": extraction["assignee"],
                    "deadline": extraction["deadline"],
                    "confidence": extraction["confidence"],
                })
            except Exception as e:
                logger.warning(f"NER failed for sentence {i}: {e}")

    db.commit()

    # Push to WebSocket with delay for live effect
    async def push():
        for seg in segments_out:
            await broadcast(session.id, {"type": "segment", "data": seg})
            await asyncio.sleep(0.3)
        for action in actions_out:
            await broadcast(session.id, {"type": "action_item", "data": action})
            await asyncio.sleep(0.2)

    asyncio.create_task(push())

    return {
        "session_id": session.id,
        "status": "active",
        "sentences_classified": len(sentences),
        "action_items_found": len(actions_out),
        "participants": [p["display_name"] for p in participants_cfg],
    }
