"""
Audio chunk ingestion endpoint.

Receives WAV files from the bot and triggers the ML pipeline.
"""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session as DBSession

from api.database import get_db, Session, generate_uuid

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = "audio_uploads"


@router.post("/sessions/{session_id}/audio")
async def upload_audio(
    session_id: str,
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    db: DBSession = Depends(get_db),
):
    """
    Receive an audio chunk (WAV) and run the full ML pipeline asynchronously.
    STT → Diarize → Classify → NER → Store → Push to WebSocket
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save the uploaded file
    chunk_id = generate_uuid()
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    file_path = os.path.join(session_dir, f"{chunk_id}.wav")

    content = await audio_file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"Received audio chunk {chunk_id} for session {session_id} ({len(content)} bytes)")

    # Run pipeline in background
    background_tasks.add_task(run_pipeline_bg, session_id, file_path, chunk_id)

    return {"accepted": True, "chunk_id": chunk_id}


def run_pipeline_bg(session_id: str, audio_path: str, chunk_id: str):
    """Background task wrapper for the ML pipeline."""
    import asyncio
    from api.database import SessionLocal

    async def _run():
        db = SessionLocal()
        try:
            from api.services.pipeline_service import process_audio_chunk
            await process_audio_chunk(session_id, audio_path, db)
        except Exception as e:
            logger.error(f"Pipeline failed for chunk {chunk_id}: {e}")
        finally:
            db.close()

    # Run in a new event loop if needed
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_run())
        else:
            asyncio.run(_run())
    except RuntimeError:
        asyncio.run(_run())
