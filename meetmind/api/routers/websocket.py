"""
WebSocket endpoint for live transcript push.

Server pushes JSON messages on each new transcript segment:
- { type: "segment", data: { speaker_label, display_name, text, label } }
- { type: "action_item", data: { task_description, assigned_to_name, deadline } }
- { type: "finalized", data: { mom_url } }
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger(__name__)

# Store active WebSocket connections per session
_connections: dict[str, list[WebSocket]] = {}


def get_connections(session_id: str) -> list[WebSocket]:
    """Get all active WebSocket connections for a session."""
    return _connections.get(session_id, [])


async def broadcast(session_id: str, message: dict):
    """Send a message to all connected clients for a session."""
    import json
    connections = _connections.get(session_id, [])
    dead = []
    for ws in connections:
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            dead.append(ws)

    for ws in dead:
        connections.remove(ws)


@router.websocket("/ws/sessions/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket connection for live meeting updates."""
    await websocket.accept()
    logger.info(f"WebSocket connected for session {session_id}")

    if session_id not in _connections:
        _connections[session_id] = []
    _connections[session_id].append(websocket)

    try:
        while True:
            # Keep connection alive; client can also send messages
            data = await websocket.receive_text()
            # Echo back for ping/pong or handle client messages
            if data == "ping":
                await websocket.send_text('{"type": "pong"}')
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        if websocket in _connections.get(session_id, []):
            _connections[session_id].remove(websocket)
