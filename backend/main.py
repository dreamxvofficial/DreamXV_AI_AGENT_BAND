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

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

    # Ensure output directories exist (skip or handle gracefully on Vercel)
    if not os.getenv("VERCEL"):
        try:
            settings.outputs_dir.mkdir(parents=True, exist_ok=True)
            settings.images_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory: {settings.outputs_dir}")
            logger.info(f"Images directory: {settings.images_dir}")
        except Exception as e:
            logger.warning(f"Could not create output directories: {e}")
    else:
        logger.info("Running on Vercel: skipped output directories creation.")

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

# ─── Request/Response Logging Middleware ──────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code} for {request.method} {request.url.path}")
        return response
    except Exception as exc:
        logger.error(f"Request failed: {request.method} {request.url.path} - {exc}")
        raise exc

# ─── Custom 404 Exception Handler ─────────────────────────────────────────
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    detail = f"Endpoint '{request.url.path}' not found. Please ensure the backend is running and your routes match."
    logger.warning(f"404 Error: {detail}")
    return JSONResponse(
        status_code=404,
        content={"detail": detail}
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
