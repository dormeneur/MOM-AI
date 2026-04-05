"""
Bot launch/stop endpoints.
"""

import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session as DBSession

from api.database import get_db, Session
from api.schemas import BotLaunchResponse, BotStopResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory store for active bot instances (single session at a time)
_active_bots = {}


@router.post("/sessions/{session_id}/bot/launch", response_model=BotLaunchResponse)
async def launch_bot(session_id: str, background_tasks: BackgroundTasks, db: DBSession = Depends(get_db)):
    """Start the Playwright bot as a background task."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session_id in _active_bots:
        return BotLaunchResponse(bot_status="already_running", meet_url=session.meet_url)

    session.status = "active"
    db.commit()

    async def run_bot():
        try:
            from bot.meet_bot import MeetBot
            bot = MeetBot(
                meet_url=session.meet_url,
                session_id=session_id,
            )
            _active_bots[session_id] = bot
            await bot.start()
        except Exception as e:
            logger.error(f"Bot failed for session {session_id}: {e}")
            _active_bots.pop(session_id, None)

    background_tasks.add_task(lambda: asyncio.create_task(run_bot()))

    return BotLaunchResponse(bot_status="joining", meet_url=session.meet_url)


@router.post("/sessions/{session_id}/bot/stop", response_model=BotStopResponse)
async def stop_bot(session_id: str, db: DBSession = Depends(get_db)):
    """Gracefully stop the bot and trigger finalization."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    bot = _active_bots.pop(session_id, None)
    if bot:
        await bot.stop()

    session.status = "processing"
    db.commit()

    return BotStopResponse(status="processing")
