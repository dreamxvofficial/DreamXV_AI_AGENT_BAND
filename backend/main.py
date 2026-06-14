"""
DreamXV AI Studio — Application Entry Point
============================================
FastAPI application with CORS, routes, WebSocket, and startup initialization.

Run with:
    uvicorn backend.main:app --reload --port 8000

Or:
    python -m uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.api.routes import router as api_router, init_band_manager
from backend.api.websocket import websocket_status_endpoint, ws_manager
from backend.band_manager import BandManager
from backend.utils.logger import get_logger

logger = get_logger("main")

# ─── Global BandManager ───────────────────────────────────────────────────
_band_manager: BandManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — startup and shutdown."""
    global _band_manager
    settings = get_settings()

    # ── Startup ────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("  DreamXV AI Studio — Starting Up")
    logger.info("  Born at 15. Built for Infinity.")
    logger.info("=" * 60)

    # Ensure output directories exist
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    settings.images_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {settings.outputs_dir}")
    logger.info(f"Images directory: {settings.images_dir}")

    # Initialize BandManager
    _band_manager = BandManager()

    # Wire up WebSocket status broadcasting
    status_callback = ws_manager.create_status_callback()
    _band_manager.set_status_callback(status_callback)

    # Register with routes module
    init_band_manager(_band_manager)

    logger.info("BandManager initialized with WebSocket status broadcasting")
    logger.info(f"Primary LLM: Featherless AI ({settings.featherless_model})")
    logger.info(f"Fallback LLM: AIMLAPI ({settings.aiml_model})")
    logger.info(f"Image Model: AIMLAPI ({settings.aiml_image_model})")
    logger.info("DreamXV AI Studio is ready.")
    logger.info("=" * 60)

    yield

    # ── Shutdown ───────────────────────────────────────────────────────
    logger.info("DreamXV AI Studio — Shutting down...")
    if _band_manager:
        await _band_manager.close()
    logger.info("Shutdown complete.")


# ─── FastAPI Application ──────────────────────────────────────────────────
app = FastAPI(
    title="DreamXV AI Studio",
    description=(
        "Multi-agent AI platform for game concept generation. "
        "Powered by Featherless AI, AIMLAPI, and Band SDK. "
        "Born at 15. Built for Infinity."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS Middleware ──────────────────────────────────────────────────────
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── REST Routes ──────────────────────────────────────────────────────────
app.include_router(api_router, tags=["Projects"])

# ─── WebSocket Route ──────────────────────────────────────────────────────
app.websocket("/ws/status")(websocket_status_endpoint)


# ─── Health Check ─────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": "DreamXV AI Studio",
        "status": "running",
        "tagline": "Born at 15. Built for Infinity.",
        "version": "1.0.0",
    }
