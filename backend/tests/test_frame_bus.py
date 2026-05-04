"""Unit tests for the in-memory frame pub/sub."""
from __future__ import annotations

import asyncio
import uuid

import pytest

from app.services.frame_store import FrameBus


@pytest.mark.asyncio
async def test_subscriber_gets_published_frames():
    bus = FrameBus()
    sid = uuid.uuid4()
    q = await bus.subscribe(sid)
    await bus.publish(sid, b"frame-1")
    await bus.publish(sid, b"frame-2")

    f1 = await asyncio.wait_for(q.get(), timeout=1)
    f2 = await asyncio.wait_for(q.get(), timeout=1)
    assert (f1, f2) == (b"frame-1", b"frame-2")


@pytest.mark.asyncio
async def test_late_subscriber_gets_latest():
    bus = FrameBus()
    sid = uuid.uuid4()
    await bus.publish(sid, b"first")
    q = await bus.subscribe(sid)
    seeded = await asyncio.wait_for(q.get(), timeout=1)
    assert seeded == b"first"


@pytest.mark.asyncio
async def test_unsubscribe_stops_delivery():
    bus = FrameBus()
    sid = uuid.uuid4()
    q = await bus.subscribe(sid)
    await bus.unsubscribe(sid, q)
    await bus.publish(sid, b"after-unsub")
    assert q.empty()


@pytest.mark.asyncio
async def test_slow_subscriber_drops_old_frames():
    bus = FrameBus()
    sid = uuid.uuid4()
    q = await bus.subscribe(sid)
    # Push more than the queue can hold without anyone draining.
    for i in range(20):
        await bus.publish(sid, str(i).encode())
    # Queue should have at most _QUEUE_SIZE items.
    assert q.qsize() <= bus._QUEUE_SIZE
