"""
DreamXV AI Studio — Band Manager
=================================
High-level orchestrator that manages the Band Room lifecycle
and coordinates the multi-agent pipeline.

Pipeline flow:
    User Prompt → Chief Agent → Band Room →
    [Story, Character, World, Gameplay, Art, QA] → Final Result
"""

from __future__ import annotations

import asyncio
from typing import Callable, Optional

from backend.agents.chief_agent import ChiefAgent
from backend.agents.story_agent import StoryAgent
from backend.agents.character_agent import CharacterAgent
from backend.agents.world_agent import WorldAgent
from backend.agents.gameplay_agent import GameplayAgent
from backend.agents.art_agent import ArtAgent
from backend.agents.qa_agent import QAAgent

from backend.models.output_models import ProjectOutput
from backend.models.schemas import AgentStatus

from backend.services.llm_service import LLMService
from backend.services.image_service import ImageService
from backend.services.band_service import BandService
from backend.services.memory_service import MemoryService, AGENT_NAMES
from backend.services.export_service import ExportService

from backend.utils.helpers import generate_project_id
from backend.utils.logger import get_logger

logger = get_logger("band_manager")

# Callback type for status updates (used by WebSocket)
StatusCallback = Callable[[str, str, AgentStatus, Optional[str]], None]


class BandManager:
    """
    Orchestrates the complete multi-agent pipeline within a Band Room.

    Creates a room, registers all agents, runs them in sequence,
    tracks statuses, and assembles the final ProjectOutput.
    """

    def __init__(self) -> None:
        self._llm = LLMService()
        self._image_service = ImageService()
        self._band_service = BandService()
        self._memory = MemoryService()
        self._export = ExportService()

        # Status change callback (set by WebSocket handler)
        self._status_callback: Optional[StatusCallback] = None

    def set_status_callback(self, callback: StatusCallback) -> None:
        """Register a callback for real-time status updates."""
        self._status_callback = callback

    def _update_status(
        self,
        project_id: str,
        agent_name: str,
        status: AgentStatus,
        message: Optional[str] = None,
    ) -> None:
        """Update agent status in memory and fire callback if set."""
        self._memory.update_agent_status(project_id, agent_name, status, message)

        if self._status_callback:
            try:
                self._status_callback(project_id, agent_name, status, message)
            except Exception as exc:
                logger.warning(f"Status callback error: {exc}")

    async def generate_project(
        self,
        user_prompt: str,
        user_id: str,
    ) -> ProjectOutput:
        """
        Execute the full multi-agent pipeline for a project.

        Args:
            user_prompt: The user's creative project prompt.
            user_id: Authenticated user identifier.

        Returns:
            Complete ProjectOutput with all agent results.
        """
        project_id = generate_project_id()
        logger.info(f"Starting project: {project_id}")

        # Initialize tracking
        self._memory.init_project(project_id, user_prompt, user_id)

        # Create Band Room
        room = self._band_service.create_room(project_id)
        self._band_service.register_agents(room, AGENT_NAMES)

        # Initialize agents
        chief = ChiefAgent(self._llm)
        story_agent = StoryAgent(self._llm)
        character_agent = CharacterAgent(self._llm)
        world_agent = WorldAgent(self._llm)
        gameplay_agent = GameplayAgent(self._llm)
        art_agent = ArtAgent(self._llm, self._image_service)
        qa_agent = QAAgent(self._llm)

        # ── Phase 1: Chief Agent Breakdown ──────────────────────────────
        self._update_status(project_id, "Chief Agent", AgentStatus.RUNNING)
        breakdown = None
        try:
            breakdown = await chief.run(user_prompt, room)
            self._update_status(project_id, "Chief Agent", AgentStatus.COMPLETED)
        except Exception as e:
            status = "Error"
            error_message = str(e)
            logger.error(f"Chief Agent failed: {error_message}")
            self._update_status(project_id, "Chief Agent", AgentStatus.ERROR, error_message)
            # Create a default fallback breakdown structure so specialists can run
            from backend.models.output_models import ChiefTaskBreakdown
            breakdown = ChiefTaskBreakdown(
                story_directive=f"Create a game story based on: {user_prompt}",
                character_directive=f"Generate characters for: {user_prompt}",
                world_directive=f"Build the world setting for: {user_prompt}",
                gameplay_directive=f"Design gameplay mechanics for: {user_prompt}",
                art_directive=f"Define visual direction and style for: {user_prompt}",
                qa_directive=f"Assess consistency and quality for: {user_prompt}",
                genre="Role-Playing Game",
                tone="Epic"
            )

        # ── Phase 2: Parallel Specialist Agents ─────────────────────────
        # Story, Character, World, and Gameplay can run in parallel
        async def run_story():
            self._update_status(project_id, "Story Agent", AgentStatus.RUNNING)
            try:
                result = await story_agent.run(
                    breakdown.story_directive, room,
                    genre=breakdown.genre, tone=breakdown.tone,
                )
                self._update_status(project_id, "Story Agent", AgentStatus.COMPLETED)
                return result
            except Exception as e:
                status = "Error"
                error_message = str(e)
                logger.error(f"Story Agent failed: {error_message}")
                self._update_status(project_id, "Story Agent", AgentStatus.ERROR, error_message)
                return None

        async def run_characters():
            self._update_status(project_id, "Character Agent", AgentStatus.RUNNING)
            try:
                result = await character_agent.run(
                    breakdown.character_directive, room,
                    genre=breakdown.genre, tone=breakdown.tone,
                )
                self._update_status(project_id, "Character Agent", AgentStatus.COMPLETED)
                return result
            except Exception as e:
                status = "Error"
                error_message = str(e)
                logger.error(f"Character Agent failed: {error_message}")
                self._update_status(project_id, "Character Agent", AgentStatus.ERROR, error_message)
                return []

        async def run_world():
            self._update_status(project_id, "World Agent", AgentStatus.RUNNING)
            try:
                result = await world_agent.run(
                    breakdown.world_directive, room,
                    genre=breakdown.genre, tone=breakdown.tone,
                )
                self._update_status(project_id, "World Agent", AgentStatus.COMPLETED)
                return result
            except Exception as e:
                status = "Error"
                error_message = str(e)
                logger.error(f"World Agent failed: {error_message}")
                self._update_status(project_id, "World Agent", AgentStatus.ERROR, error_message)
                return None

        async def run_gameplay():
            self._update_status(project_id, "Gameplay Agent", AgentStatus.RUNNING)
            try:
                result = await gameplay_agent.run(
                    breakdown.gameplay_directive, room,
                    genre=breakdown.genre, tone=breakdown.tone,
                )
                self._update_status(project_id, "Gameplay Agent", AgentStatus.COMPLETED)
                return result
            except Exception as e:
                status = "Error"
                error_message = str(e)
                logger.error(f"Gameplay Agent failed: {error_message}")
                self._update_status(project_id, "Gameplay Agent", AgentStatus.ERROR, error_message)
                return None

        # Run story, character, world, gameplay in parallel
        story, characters, world, gameplay = await asyncio.gather(
            run_story(),
            run_characters(),
            run_world(),
            run_gameplay(),
        )

        # ── Phase 3: Art Agent (needs context from prior agents) ────────
        self._update_status(project_id, "Art Agent", AgentStatus.RUNNING)
        try:
            art = await art_agent.run(
                breakdown.art_directive, room,
                project_id=project_id,
                genre=breakdown.genre, tone=breakdown.tone,
            )
            self._update_status(project_id, "Art Agent", AgentStatus.COMPLETED)
        except Exception as e:
            error_message = str(e)
            logger.error(f"Art Agent failed: {error_message}")
            self._update_status(
                project_id,
                "Art Agent",
                AgentStatus.COMPLETED,
                f"Completed with warning: {error_message}"
            )
            from backend.models.output_models import ArtOutput
            art = ArtOutput(
                prompts=[],
                image_paths=[],
                style_guide=f"Warning: {error_message}"
            )

        # ── Phase 4: QA Agent (reviews everything) ─────────────────────
        self._update_status(project_id, "QA Agent", AgentStatus.RUNNING)
        try:
            qa = await qa_agent.run(breakdown.qa_directive, room)
            self._update_status(project_id, "QA Agent", AgentStatus.COMPLETED)
        except Exception as e:
            status = "Error"
            error_message = str(e)
            logger.error(f"QA Agent failed: {error_message}")
            self._update_status(project_id, "QA Agent", AgentStatus.ERROR, error_message)
            qa = None

        # ── Assemble Final Output ──────────────────────────────────────
        project = ProjectOutput(
            project_id=project_id,
            title=story.title if story else "Untitled Project",
            story=story,
            characters=characters or [],
            world=world,
            gameplay=gameplay,
            art=art,
            qa=qa,
        )

        # Persist and clean up
        try:
            self._export.save_project(project)
        except Exception as e:
            logger.warning(f"Failed to save project export: {e}")

        try:
            self._memory.store_completed_project(project)
        except Exception as e:
            logger.warning(f"Failed to store project in memory: {e}")

        try:
            self._band_service.close_room(project_id)
        except Exception as e:
            logger.warning(f"Failed to close band room: {e}")

        logger.info(f"Project completed: {project_id} — '{project.title}'")
        return project

    def get_agent_statuses(self, project_id: Optional[str] = None):
        """Get agent statuses for a project (or the active project)."""
        if project_id is None:
            project_id = self._memory.get_active_project_id()
        if project_id is None:
            return []
        return self._memory.get_agent_statuses(project_id)

    def list_projects(self) -> list[dict]:
        """List all completed projects."""
        # Combine in-memory and disk-persisted projects
        memory_projects = self._memory.list_completed_projects()
        disk_projects = self._export.list_projects()

        # Merge, preferring memory (more recent)
        seen_ids = {p["project_id"] for p in memory_projects}
        all_projects = list(memory_projects)
        for p in disk_projects:
            if p["project_id"] not in seen_ids:
                all_projects.append(p)

        return all_projects

    async def close(self) -> None:
        """Shut down all services."""
        await self._llm.close()
