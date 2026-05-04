"""Endpoint #1: receive the video feed.

WebSocket protocol:
    Client connects to:  /ws/ingest/{session_id}
    Client sends:        binary JPEG frames (one frame per WS message)
    Server replies:      JSON ROI metadata for that frame, or empty object

The client also opens /ws/stream/{session_id} (endpoint #2) to view its own
processed feed if desired — typical for the React frontend so the user sees
the bounding-box overlay.
"""
from __future__ import annotations

import json
import logging
import time
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.config import get_settings
from app.db.database import db_session
from app.db.models import RoiRecord, Session as SessionModel
from app.services.face_detector import FaceDetector
from app.services.frame_processor import process_frame
from app.services.frame_store import frame_bus

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ingest"])

_settings = get_settings()


@router.websocket("/ws/ingest/{session_id}")
async def ingest_ws(websocket: WebSocket, session_id: UUID) -> None:
    await websocket.accept()

    # Confirm the session exists before doing real work.
    with db_session() as db:
        session = db.get(SessionModel, session_id)
        if session is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="unknown session")
            return

    detector = FaceDetector(min_confidence=0.5)
    frame_index = 0
    min_interval = 1.0 / _settings.max_ingest_fps if _settings.max_ingest_fps > 0 else 0.0
    last_ts = 0.0

    try:
        while True:
            try:
                jpeg_bytes = await websocket.receive_bytes()
            except WebSocketDisconnect:
                break

            # Bound input size to avoid OOM / DoS via giant frames.
            if len(jpeg_bytes) > _settings.max_frame_bytes:
                await websocket.send_text(json.dumps({"error": "frame too large"}))
                continue

            # Drop frames that arrive faster than the configured ceiling.
            now = time.monotonic()
            if min_interval and (now - last_ts) < min_interval:
                await websocket.send_text(json.dumps({"error": "rate limit", "frame_index": frame_index}))
                continue
            last_ts = now

            try:
                processed = process_frame(jpeg_bytes, detector)
            except ValueError as exc:
                # Malformed image — keep the connection open, let the client recover.
                await websocket.send_text(json.dumps({"error": str(exc)}))
                continue
            except Exception:
                logger.exception("unexpected error processing frame")
                await websocket.send_text(json.dumps({"error": "processing failed"}))
                continue

            await frame_bus.publish(session_id, processed.jpeg_bytes)

            roi_payload: dict = {"frame_index": frame_index, "detection": None}
            if processed.detection is not None:
                roi_payload["detection"] = processed.detection.as_dict()

                with db_session() as db:
                    db.add(
                        RoiRecord(
                            session_id=session_id,
                            frame_index=frame_index,
                            x=processed.detection.x,
                            y=processed.detection.y,
                            width=processed.detection.width,
                            height=processed.detection.height,
                            confidence=processed.detection.confidence,
                        )
                    )
                    s = db.get(SessionModel, session_id)
                    if s is not None:
                        s.frame_count = (s.frame_count or 0) + 1

            await websocket.send_text(json.dumps(roi_payload))
            frame_index += 1
    finally:
        detector.close()
