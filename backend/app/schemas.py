"""Pydantic schemas for the public API."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    label: Optional[str] = Field(default=None, max_length=120)


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    label: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    frame_count: int


class RoiOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    frame_index: int
    x: int
    y: int
    width: int
    height: int
    confidence: Optional[float]
    detected_at: datetime


class RoiPage(BaseModel):
    session_id: UUID
    total: int
    items: List[RoiOut]
