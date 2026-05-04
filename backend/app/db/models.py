"""SQLAlchemy ORM models.

Schema rationale
----------------
Two tables:
  * sessions     - one row per ingest session (a webcam stream or uploaded video)
  * roi_records  - one row per detected face ROI on a given frame

Relational design fits because:
  - A session has many frames; each frame may have one ROI (problem assumes 1 face).
  - We want history queryable by session and by time.
  - Constraints (foreign key, indexes) enforce integrity at the DB layer.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    label = Column(String(120), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    frame_count = Column(Integer, nullable=False, default=0)

    rois = relationship(
        "RoiRecord",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class RoiRecord(Base):
    __tablename__ = "roi_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    frame_index = Column(Integer, nullable=False)
    # Pixel coordinates of axis-aligned minimal bounding box.
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=True)
    detected_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    session = relationship("Session", back_populates="rois")

    __table_args__ = (
        Index("ix_roi_session_frame", "session_id", "frame_index"),
        Index("ix_roi_session_time", "session_id", "detected_at"),
    )
