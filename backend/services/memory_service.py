"""
DreamXV AI Studio — Memory Service
===================================
Session-level memory for tracking active projects and agent states.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from backend.models.schemas import AgentStatus, AgentStatusItem
from backend.models.output_models import ProjectOutput
from backend.utils.logger import get_logger

logger = get_logger("memory")

# ─── Agent names in pipeline order ─────────────────────────────────────────
AGENT_NAMES: list[str] = [
    "Chief Agent",
    "Story Agent",
    "Character Agent",
    "World Agent",
    "Gameplay Agent",
    "Art Agent",
    "QA Agent",
    "Reviewer Agent",
    "Documentation Agent",
    "Timeline Agent",
    "Risk Agent",
    "Feasibility Agent",
    "Project Planner Agent",
    "Analytics Agent",
    "Export Agent",
]


class MemoryService:
    """
    In-memory state manager for active projects and agent statuses.

    Stores:
    - Active project metadata and states
    - Agent lifecycle statuses per project
    - Completed project outputs
    """

    def __init__(self) -> None:
        # project_id → { metadata }
        self._active_projects: dict[str, dict[str, Any]] = {}
        # project_id → { agent_name → AgentStatusItem }
        self._agent_statuses: dict[str, dict[str, AgentStatusItem]] = {}
        # project_id → ProjectOutput
        self._completed_projects: dict[str, ProjectOutput] = {}

    def init_project(self, project_id: str, user_prompt: str, user_id: str) -> None:
        """Initialize tracking for a new project."""
        self._active_projects[project_id] = {
            "user_prompt": user_prompt,
            "user_id": user_id,
            "started_at": datetime.now(timezone.utc),
        }

        # Initialize all agents as READY
        self._agent_statuses[project_id] = {
            name: AgentStatusItem(
                agent_name=name,
                status=AgentStatus.READY,
            )
            for name in AGENT_NAMES
        }

        logger.info(f"Project initialized in memory: {project_id}")

    def update_agent_status(
        self,
        project_id: str,
        agent_name: str,
        status: AgentStatus,
        message: Optional[str] = None,
    ) -> AgentStatusItem:
        """
        Update an agent's status for a project.

        Returns:
            The updated AgentStatusItem.
        """
        if project_id not in self._agent_statuses:
            logger.warning(f"Project {project_id} not found in memory")
            return AgentStatusItem(agent_name=agent_name, status=status)

        item = self._agent_statuses[project_id].get(
            agent_name,
            AgentStatusItem(agent_name=agent_name),
        )

        item.status = status
        item.message = message

        now = datetime.now(timezone.utc)
        if status == AgentStatus.RUNNING:
            item.started_at = now
        elif status in (AgentStatus.COMPLETED, AgentStatus.ERROR):
            item.completed_at = now

        self._agent_statuses[project_id][agent_name] = item
        logger.debug(f"[{project_id}] {agent_name} -> {status.value}")
        return item

    def get_agent_statuses(self, project_id: str) -> list[AgentStatusItem]:
        """Get all agent statuses for a project in pipeline order."""
        if project_id not in self._agent_statuses:
            return []
        return [
            self._agent_statuses[project_id][name]
            for name in AGENT_NAMES
            if name in self._agent_statuses[project_id]
        ]

    def get_active_project_id(self) -> Optional[str]:
        """Return the most recently started active project ID, if any."""
        if not self._active_projects:
            return None
        # Return the project with the latest start time
        return max(
            self._active_projects.keys(),
            key=lambda pid: self._active_projects[pid]["started_at"],
        )

    def store_completed_project(self, project: ProjectOutput) -> None:
        """Store a completed project output and remove from active."""
        self._completed_projects[project.project_id] = project
        self._active_projects.pop(project.project_id, None)
        logger.info(f"Project completed and stored: {project.project_id}")

    def get_completed_project(self, project_id: str) -> Optional[ProjectOutput]:
        """Retrieve a completed project by ID."""
        return self._completed_projects.get(project_id)

    def list_completed_projects(self) -> list[dict[str, Any]]:
        """List all completed projects as summary dicts."""
        return [
            {
                "project_id": p.project_id,
                "title": p.title,
                "created_at": p.created_at.isoformat(),
                "status": "completed",
            }
            for p in self._completed_projects.values()
        ]
