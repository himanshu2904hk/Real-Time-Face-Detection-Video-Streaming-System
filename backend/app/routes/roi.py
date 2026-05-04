"""Endpoint #3: serve ROI data."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as OrmSession

from app.db.database import get_db
from app.db.models import RoiRecord, Session as SessionModel
from app.schemas import RoiOut, RoiPage

router = APIRouter(prefix="/api/sessions", tags=["roi"])


@router.get("/{session_id}/roi", response_model=RoiPage)
def list_rois(
    session_id: UUID,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: OrmSession = Depends(get_db),
) -> RoiPage:
    """Paginated ROI history for a session, newest first."""
    if db.get(SessionModel, session_id) is None:
        raise HTTPException(status_code=404, detail="session not found")

    q = (
        db.query(RoiRecord)
        .filter(RoiRecord.session_id == session_id)
        .order_by(RoiRecord.detected_at.desc())
    )
    total = q.count()
    rows = q.offset(offset).limit(limit).all()
    return RoiPage(
        session_id=session_id,
        total=total,
        items=[RoiOut.model_validate(r) for r in rows],
    )


@router.get("/{session_id}/roi/latest", response_model=RoiOut)
def latest_roi(session_id: UUID, db: OrmSession = Depends(get_db)) -> RoiOut:
    if db.get(SessionModel, session_id) is None:
        raise HTTPException(status_code=404, detail="session not found")

    row = (
        db.query(RoiRecord)
        .filter(RoiRecord.session_id == session_id)
        .order_by(RoiRecord.detected_at.desc())
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="no ROIs recorded yet")
    return RoiOut.model_validate(row)
