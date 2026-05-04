"""Endpoint #2: serve the processed video feed.

Exposes both:
  - WebSocket /ws/stream/{session_id} — pushes processed JPEG frames as they arrive
  - GET /api/stream/{session_id}/frame.jpg — single latest snapshot (handy for tests / debugging)

The WebSocket is the primary real-time channel. The HTTP fallback exists so
operators can poke at a session with curl.
"""
from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, WebSocket, WebSocketDisconnect, status

from app.db.database import db_session
from app.db.models import Session as SessionModel
from app.services.frame_store import frame_bus

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stream"])


@router.websocket("/ws/stream/{session_id}")
async def stream_ws(websocket: WebSocket, session_id: UUID) -> None:
    await websocket.accept()
    with db_session() as db:
        if db.get(SessionModel, session_id) is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="unknown session")
            return
    queue = await frame_bus.subscribe(session_id)
    try:
        while True:
            jpeg_bytes = await queue.get()
            try:
                await websocket.send_bytes(jpeg_bytes)
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    finally:
        await frame_bus.unsubscribe(session_id, queue)


@router.get(
    "/api/stream/{session_id}/frame.jpg",
    responses={
        200: {"content": {"image/jpeg": {}}},
        404: {"description": "no frames yet for this session"},
    },
)
def latest_frame(session_id: UUID) -> Response:
    jpeg_bytes = frame_bus.latest(session_id)
    if jpeg_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no frames available for this session",
        )
    return Response(
        content=jpeg_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-store"},
    )
