"""In-memory pub/sub of processed frames per session.

Why in-memory: the *frames themselves* are ephemeral — only the ROI metadata
is durable (in PostgreSQL). Streaming consumers want low-latency access to the
latest frame, not historical playback. Keeping frames in RAM avoids hammering
the DB and keeps the design pragmatic.

For multi-worker / multi-instance deployments this would be swapped for a
shared bus (Redis pub/sub, NATS, etc.); the swap is local to this module.
"""
from __future__ import annotations

import asyncio
from typing import Dict, Optional, Set
from uuid import UUID


class FrameBus:
    """Per-session frame fan-out with bounded subscriber queues."""

    _QUEUE_SIZE = 4  # tiny — drop old frames rather than backlog

    def __init__(self) -> None:
        self._latest: Dict[UUID, bytes] = {}
        self._subs: Dict[UUID, Set[asyncio.Queue[bytes]]] = {}
        self._lock = asyncio.Lock()

    async def publish(self, session_id: UUID, jpeg_bytes: bytes) -> None:
        """Make jpeg_bytes available to all subscribers of session_id."""
        async with self._lock:
            self._latest[session_id] = jpeg_bytes
            subs = list(self._subs.get(session_id, ()))

        for queue in subs:
            # Drop the oldest frame if the consumer can't keep up — real-time
            # streams should prefer recency over completeness.
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(jpeg_bytes)
            except asyncio.QueueFull:
                pass

    async def subscribe(self, session_id: UUID) -> asyncio.Queue[bytes]:
        queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=self._QUEUE_SIZE)
        async with self._lock:
            self._subs.setdefault(session_id, set()).add(queue)
            # Seed with the latest frame so a new viewer sees something
            # immediately rather than waiting for the next ingest.
            latest = self._latest.get(session_id)
        if latest is not None:
            try:
                queue.put_nowait(latest)
            except asyncio.QueueFull:
                pass
        return queue

    async def unsubscribe(self, session_id: UUID, queue: asyncio.Queue[bytes]) -> None:
        async with self._lock:
            subs = self._subs.get(session_id)
            if subs:
                subs.discard(queue)
                if not subs:
                    self._subs.pop(session_id, None)

    def latest(self, session_id: UUID) -> Optional[bytes]:
        return self._latest.get(session_id)

    def drop(self, session_id: UUID) -> None:
        self._latest.pop(session_id, None)
        self._subs.pop(session_id, None)


# Process-wide singleton.
frame_bus = FrameBus()
