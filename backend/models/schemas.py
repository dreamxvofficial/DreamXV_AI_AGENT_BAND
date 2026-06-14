"""
DreamXV AI Studio — API Request / Response Schemas
===================================================
Pydantic models for FastAPI endpoint validation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .output_models import ProjectOutput


# ─── Enums ─────────────────────────────────────────────────────────────────
class AgentStatus(str, Enum):
    """Lifecycle status of an agent within a Band room."""
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


# ─── Request Schemas ───────────────────────────────────────────────────────
class GenerateProjectRequest(BaseModel):
    """POST /generate-project request body."""
    prompt: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="User's creative prompt describing the desired game/project",
    )
    user_id: Optional[str] = Field(
        default="anonymous",
        description="Authenticated user identifier",
    )


# ─── Response Schemas ──────────────────────────────────────────────────────
class GenerateProjectResponse(BaseModel):
    """POST /generate-project response."""
    project_id: str
    status: str = "started"
    message: str = "Project generation initiated. Monitor progress via /agent-status or WebSocket."


class AgentStatusItem(BaseModel):
    """Status of a single agent."""
    agent_name: str
    status: AgentStatus = AgentStatus.READY
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AgentStatusResponse(BaseModel):
    """GET /agent-status response."""
    project_id: Optional[str] = None
    agents: list[AgentStatusItem] = Field(default_factory=list)


class ProjectSummary(BaseModel):
    """Lightweight project listing entry."""
    project_id: str
    title: str
    created_at: datetime
    status: str = "completed"


class ProjectListResponse(BaseModel):
    """GET /projects response."""
    projects: list[ProjectSummary] = Field(default_factory=list)
    total: int = 0


class ErrorResponse(BaseModel):
    """Standard error envelope."""
    error: str
    detail: Optional[str] = None
