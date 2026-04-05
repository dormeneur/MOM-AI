"""
Pipeline Service — Orchestrates the full ML pipeline per audio chunk.

Called for every audio chunk the bot uploads:
1. STT (Whisper) — transcribe audio
2. Diarize (pyannote) — assign speakers
3. Classify (MLP) — label each sentence
4. NER (BERT) — extract tasks from action_items/deadlines
5. Store in DB
6. Push to WebSocket
"""

import os
import logging
import numpy as np
import joblib

from sqlalchemy.orm import Session as DBSession
from api.database import TranscriptSegment, ActionItem, Participant, generate_uuid

logger = logging.getLogger(__name__)

# Lazy-loaded ML models
_mlp_model = None
_tfidf_vectorizer = None
_transcriber = None
_diarizer = None
_task_extractor = None

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'ml', 'classifier', 'models')


def _load_classifier():
    global _mlp_model
    if _mlp_model is None:
        path = os.environ.get(
            "CLASSIFIER_MODEL_PATH",
            os.path.join(MODEL_DIR, "mlp_classifier.pkl"),
        )
        _mlp_model = joblib.load(path)
        logger.info("Loaded MLP classifier")
    return _mlp_model


def _get_transcriber():
    global _transcriber
    if _transcriber is None:
        from ml.stt.transcriber import WhisperTranscriber
        _transcriber = WhisperTranscriber()
    return _transcriber


def _get_diarizer():
    global _diarizer
    if _diarizer is None:
        from ml.diarization.diarizer import SpeakerDiarizer
        _diarizer = SpeakerDiarizer()
    return _diarizer


def _get_task_extractor():
    global _task_extractor
    if _task_extractor is None:
        from ml.ner.task_extractor import TaskExtractor
        _task_extractor = TaskExtractor()
    return _task_extractor


async def process_audio_chunk(session_id: str, audio_path: str, db: DBSession):
    """
    Full pipeline for one 5-second audio chunk:

    1. transcriber.transcribe(audio_path) → raw segments
    2. diarizer.diarize(audio_path) → speaker labels
    3. diarizer.align(transcript, diarization) → speaker-attributed segments
    4. For each segment:
        a. features = feature_extractor.extract([segment.text])
        b. label = mlp_classifier.predict(features)[0]
        c. confidence = mlp_classifier.predict_proba(features).max()
        d. Save TranscriptSegment to DB
        e. If label in ['action_item', 'deadline_mention']:
              extract task → save ActionItem → push WebSocket
        f. push WebSocket segment message
    """
    from ml.classifier.features import extract_features
    from ml.classifier.mlp_model import INT_TO_LABEL

    # Step 1: Transcribe
    logger.info(f"Processing chunk: {audio_path}")
    transcriber = _get_transcriber()
    transcript_segments = transcriber.transcribe(audio_path)

    if not transcript_segments:
        logger.info("No speech detected in chunk")
        return

    # Step 2: Diarize
    try:
        diarizer = _get_diarizer()
        diarization_segments = diarizer.diarize(audio_path)
        aligned_segments = diarizer.align(transcript_segments, diarization_segments)
    except Exception as e:
        logger.warning(f"Diarization failed, using segments without speaker labels: {e}")
        aligned_segments = [
            {**seg, "speaker": "SPEAKER_UNKNOWN"} for seg in transcript_segments
        ]

    # Step 3-4: Classify and extract
    classifier = _load_classifier()
    task_extractor = _get_task_extractor()

    # Map speaker labels to display names
    participants = db.query(Participant).filter(Participant.session_id == session_id).all()
    label_to_name = {p.speaker_label: p.display_name for p in participants if p.speaker_label}

    for seg in aligned_segments:
        text = seg["text"]
        if not text.strip():
            continue

        # Feature extraction + classification
        features = extract_features([text], training=False)
        pred_int = classifier.model.predict(features)[0]
        label = INT_TO_LABEL[pred_int]
        proba = classifier.model.predict_proba(features).max()

        # Save transcript segment
        display_name = label_to_name.get(seg["speaker"], seg["speaker"])
        ts = TranscriptSegment(
            id=generate_uuid(),
            session_id=session_id,
            speaker_label=seg["speaker"],
            text=text,
            start_time=seg.get("start"),
            end_time=seg.get("end"),
            label=label,
            label_confidence=float(proba),
        )
        db.add(ts)
        db.flush()

        # Push segment to WebSocket
        from api.routers.websocket import broadcast
        import asyncio
        await broadcast(session_id, {
            "type": "segment",
            "data": {
                "speaker_label": seg["speaker"],
                "display_name": display_name,
                "text": text,
                "label": label,
                "confidence": float(proba),
            },
        })

        # Extract action items/deadlines
        if label in ("action_item", "deadline_mention"):
            try:
                extraction = task_extractor.extract(text, speaker_name=display_name)

                # Resolve assignee email
                assignee_email = None
                if extraction["assignee"]:
                    for p in participants:
                        if p.display_name and extraction["assignee"].lower() in p.display_name.lower():
                            assignee_email = p.email
                            break

                ai = ActionItem(
                    id=generate_uuid(),
                    session_id=session_id,
                    segment_id=ts.id,
                    assigned_to_name=extraction["assignee"],
                    assigned_to_email=assignee_email,
                    assigned_by_name=display_name,
                    task_description=extraction["task_description"],
                    deadline=extraction["deadline"],
                    confidence=extraction["confidence"],
                )
                db.add(ai)

                await broadcast(session_id, {
                    "type": "action_item",
                    "data": {
                        "task_description": extraction["task_description"],
                        "assigned_to_name": extraction["assignee"],
                        "deadline": extraction["deadline"],
                        "confidence": extraction["confidence"],
                    },
                })

            except Exception as e:
                logger.error(f"Task extraction failed: {e}")

    db.commit()
    logger.info(f"Processed {len(aligned_segments)} segments for session {session_id}")
