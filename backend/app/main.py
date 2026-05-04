"""FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import engine
from app.db.models import Base
from app.routes import ingest, roi, sessions, stream

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables on startup. For real deployments this would be Alembic;
    # for a take-home project the simple path is more pragmatic.
    Base.metadata.create_all(bind=engine)
    logger.info("startup complete")
    yield
    logger.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Real-Time Face Detection API",
        version="1.0.0",
        description=(
            "Three core endpoints:\n"
            "  - WebSocket /ws/ingest/{session_id}  (receive video feed)\n"
            "  - WebSocket /ws/stream/{session_id}  (serve processed feed)\n"
            "  - GET       /api/sessions/{id}/roi   (serve ROI data)"
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(sessions.router)
    app.include_router(ingest.router)
    app.include_router(stream.router)
    app.include_router(roi.router)
    return app


app = create_app()
