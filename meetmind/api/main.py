"""
FastAPI application entry point.

Starts the MeetMind API server with all routers and CORS middleware.
"""

import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env file FIRST before any module that reads env vars
load_dotenv()

from api.database import init_db
from api.routers import sessions, bot, audio, websocket
from api.routers import demo as demo_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup + shutdown events."""
    logger.info("Initialising database...")
    init_db()
    logger.info("MeetMind API ready")
    yield
    logger.info("Shutting down MeetMind API")


app = FastAPI(
    title="MeetMind API",
    description="AI-powered Google Meet bot that generates personalised Minutes of Meeting",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow dashboard frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to dashboard URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])
app.include_router(bot.router, prefix="/api", tags=["Bot"])
app.include_router(audio.router, prefix="/api", tags=["Audio"])
app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(demo_router.router, tags=["Demo"])


@app.get("/")
async def root():
    return {"app": "MeetMind", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
