"""Persistence-layer tests.

Verify that:
  - sessions and ROIs round-trip through the schema
  - cascade delete works (deleting a session removes its ROIs)
  - basic invariants (NOT NULL, FK) hold
"""
from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import RoiRecord, Session as SessionModel


def test_create_session_defaults(db):
    s = SessionModel(label="hello")
    db.add(s)
    db.commit()
    db.refresh(s)
    assert s.id is not None
    assert s.frame_count == 0
    assert s.started_at is not None
    assert s.ended_at is None


def test_roi_requires_session(db):
    bad = RoiRecord(
        session_id=None,
        frame_index=0,
        x=0, y=0, width=10, height=10, confidence=0.5,
    )
    db.add(bad)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_cascade_delete_removes_rois(db, sample_session_id):
    db.add(
        RoiRecord(
            session_id=sample_session_id,
            frame_index=0, x=0, y=0, width=10, height=10, confidence=0.5,
        )
    )
    db.commit()
    assert db.query(RoiRecord).count() == 1

    s = db.get(SessionModel, sample_session_id)
    db.delete(s)
    db.commit()

    assert db.query(RoiRecord).count() == 0


def test_query_by_session(db, sample_session_id):
    for i in range(3):
        db.add(
            RoiRecord(
                session_id=sample_session_id,
                frame_index=i, x=i, y=i, width=10, height=10, confidence=0.9,
            )
        )
    db.commit()

    rows = (
        db.query(RoiRecord)
        .filter(RoiRecord.session_id == sample_session_id)
        .order_by(RoiRecord.frame_index)
        .all()
    )
    assert [r.frame_index for r in rows] == [0, 1, 2]
