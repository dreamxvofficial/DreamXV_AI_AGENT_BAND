"""
DreamXV AI Studio — API Routes
================================
FastAPI router with REST endpoints:
    POST /generate-project
    GET  /agent-status
    GET  /projects
"""

from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.band_manager import BandManager
from backend.models.schemas import (
    GenerateProjectRequest,
    GenerateProjectResponse,
    AgentStatusResponse,
    AgentStatusItem,
    ProjectListResponse,
    ProjectSummary,
    ErrorResponse,
)
from backend.utils.validators import validate_prompt, validate_user_id
from backend.utils.logger import get_logger

logger = get_logger("routes")

router = APIRouter()

# Singleton BandManager instance — initialized in main.py
_band_manager: Optional[BandManager] = None


def init_band_manager(manager: BandManager) -> None:
    """Set the global BandManager instance (called from main.py startup)."""
    global _band_manager
    _band_manager = manager


def get_band_manager() -> BandManager:
    """Retrieve the BandManager, raising if not initialized."""
    if _band_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Service not ready. BandManager not initialized.",
        )
    return _band_manager


# ─── POST /generate-project ───────────────────────────────────────────────
@router.post(
    "/generate-project",
    response_model=GenerateProjectResponse,
    responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    summary="Generate a new game project",
    description="Initiates the multi-agent pipeline to generate a complete game project.",
)
async def generate_project(
    request: GenerateProjectRequest,
    background_tasks: BackgroundTasks,
):
    """
    Accept a user prompt and kick off the multi-agent pipeline.
    Returns immediately with a project ID; generation runs in the background.
    """
    manager = get_band_manager()

    # Validate inputs
    valid, error = validate_prompt(request.prompt)
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    valid, error = validate_user_id(request.user_id)
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    logger.info(f"Generate project request from user={request.user_id}")

    # Start generation in background
    async def _run_generation():
        try:
            await manager.generate_project(request.prompt, request.user_id)
        except Exception as exc:
            logger.error(f"Project generation failed: {exc}")

    background_tasks.add_task(_run_generation)

    # Return immediately — client polls /agent-status or uses WebSocket
    return GenerateProjectResponse(
        project_id="pending",  # Will be set once Chief Agent starts
        status="started",
        message="Project generation initiated. Monitor progress via /agent-status or WebSocket.",
    )


# ─── GET /agent-status ────────────────────────────────────────────────────
@router.get(
    "/agent-status",
    response_model=AgentStatusResponse,
    summary="Get agent statuses",
    description="Returns the current status of all agents for the active project.",
)
async def get_agent_status(project_id: Optional[str] = None):
    """
    Return the current lifecycle status of every agent.
    If project_id is not specified, returns the most recent active project.
    """
    manager = get_band_manager()
    statuses = manager.get_agent_statuses(project_id)

    return AgentStatusResponse(
        project_id=project_id,
        agents=statuses,
    )


# ─── GET /projects ────────────────────────────────────────────────────────
@router.get(
    "/projects",
    response_model=ProjectListResponse,
    summary="List projects",
    description="Returns a list of all completed projects.",
)
async def list_projects():
    """List all completed projects from memory and disk."""
    manager = get_band_manager()
    projects = manager.list_projects()

    summaries = [
        ProjectSummary(
            project_id=p["project_id"],
            title=p.get("title", "Untitled"),
            created_at=p.get("created_at", ""),
            status=p.get("status", "completed"),
        )
        for p in projects
    ]

    return ProjectListResponse(
        projects=summaries,
        total=len(summaries),
    )
