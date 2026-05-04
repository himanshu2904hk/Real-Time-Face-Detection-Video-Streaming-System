"""HTTP-level integration tests for the REST endpoints.

We exercise the real FastAPI app against an in-memory SQLite DB. The
WebSocket endpoints are covered by unit tests on their underlying services
(processor, detector, frame_bus) — running a real WS client in tests adds
flakiness without proportional value.
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.db import database as db_mod
from app.db.models import Base
from app.main import create_app


@pytest.fixture
def client(_engine):
    db_mod.engine = _engine
    db_mod.SessionLocal.configure(bind=_engine)
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)

    app = create_app()
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_and_get_session(client):
    r = client.post("/api/sessions", json={"label": "demo"})
    assert r.status_code == 201
    body = r.json()
    assert body["label"] == "demo"
    sid = body["id"]

    r = client.get(f"/api/sessions/{sid}")
    assert r.status_code == 200
    assert r.json()["id"] == sid


def test_get_unknown_session_404(client):
    r = client.get(f"/api/sessions/{uuid.uuid4()}")
    assert r.status_code == 404


def test_roi_for_unknown_session_404(client):
    r = client.get(f"/api/sessions/{uuid.uuid4()}/roi")
    assert r.status_code == 404


def test_roi_empty_for_new_session(client):
    sid = client.post("/api/sessions", json={}).json()["id"]
    r = client.get(f"/api/sessions/{sid}/roi")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["items"] == []


def test_session_label_max_length(client):
    # Pydantic should reject labels longer than 120 chars.
    r = client.post("/api/sessions", json={"label": "x" * 200})
    assert r.status_code == 422


def test_latest_frame_404_when_no_frames(client):
    sid = client.post("/api/sessions", json={}).json()["id"]
    r = client.get(f"/api/stream/{sid}/frame.jpg")
    assert r.status_code == 404
