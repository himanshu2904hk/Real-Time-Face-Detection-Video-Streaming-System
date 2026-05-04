"""Session lifecycle endpoints.

A *session* groups one ingest stream's frames and ROIs. Clients create one
before opening the ingest WebSocket. This is bookkeeping; the three core
endpoints (ingest / stream / roi) are defined elsewhere.
"""
from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as OrmSession

from app.db.database import get_db
from app.db.models import Session as SessionModel
from app.schemas import SessionCreate, SessionOut

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate, db: OrmSession = Depends(get_db)) -> SessionOut:
    session = SessionModel(label=payload.label)
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionOut.model_validate(session)


@router.get("", response_model=List[SessionOut])
def list_sessions(db: OrmSession = Depends(get_db)) -> List[SessionOut]:
    rows = db.query(SessionModel).order_by(SessionModel.started_at.desc()).limit(50).all()
    return [SessionOut.model_validate(r) for r in rows]


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: UUID, db: OrmSession = Depends(get_db)) -> SessionOut:
    session = db.get(SessionModel, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return SessionOut.model_validate(session)
