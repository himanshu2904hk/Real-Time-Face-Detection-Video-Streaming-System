"""Shared pytest fixtures.

We swap PostgreSQL for SQLite in-memory during tests. The schema is small
and our SQL is portable (SQLAlchemy 2.0). For UUID columns we register a
type-compat shim with SQLite.
"""
from __future__ import annotations

import os
import uuid

import pytest

# Force test config BEFORE importing the app modules.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ALLOWED_ORIGINS", "http://test")


@pytest.fixture(scope="session")
def _engine():
    from sqlalchemy import create_engine, event
    from sqlalchemy.pool import StaticPool

    # Use a single shared in-memory connection so all sessions see the same DB.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite ignores FOREIGN KEY constraints unless explicitly enabled per
    # connection — turn it on so the schema enforces the same invariants
    # (notably ON DELETE CASCADE) that PostgreSQL would in production.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_fks(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.close()

    return engine


@pytest.fixture
def db(_engine):
    """Fresh schema per test."""
    from app.db.database import SessionLocal
    from app.db import database as db_mod
    from app.db.models import Base

    # Patch the engine + sessionmaker to use our test engine.
    db_mod.engine = _engine
    db_mod.SessionLocal.configure(bind=_engine)

    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_session_id(db):
    from app.db.models import Session as SessionModel

    s = SessionModel(label="test")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s.id
