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
from backend.agents.reviewer_agent import ReviewerAgent
from backend.agents.documentation_agent import DocumentationAgent

from backend.models.output_models import (
    ProjectOutput,
    DocumentationOutput,
    StoryOutput,
    CharacterRoster,
    WorldOutput,
    GameplayOutput,
    ArtOutput,
    QAOutput,
    ReviewerOutput
)
from backend.services.llm_service import generate_mock_data_for_model
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
        reviewer_agent = ReviewerAgent(self._llm)
        documentation_agent = DocumentationAgent(self._llm)

        # ── Phase 1: Chief Agent Breakdown ──────────────────────────────
        import time
        start = time.time()
        self._update_status(project_id, "Chief Agent", AgentStatus.RUNNING)
        breakdown = None
        _chief_retry_delays = [1.0, 3.0, 5.0]
        for _attempt in range(1, 4):
            try:
                logger.info(f"Chief Agent attempt {_attempt}/3...")
                breakdown = await asyncio.wait_for(chief.run(user_prompt, room), timeout=180.0)
                logger.info(f"Chief Agent completed in {time.time()-start:.2f}s (attempt {_attempt})")
                self._update_status(project_id, "Chief Agent", AgentStatus.COMPLETED)
                break
            except Exception as e:
                logger.warning(f"Chief Agent attempt {_attempt}/3 failed: {type(e).__name__}: {e}")
                if _attempt < 3:
                    wait_sec = _chief_retry_delays[_attempt - 1]
                    logger.info(f"Waiting {wait_sec}s before Chief Agent retry...")
                    await asyncio.sleep(wait_sec)
                else:
                    logger.error("Chief Agent failed after 3 attempts — using mock breakdown fallback")
                    self._update_status(project_id, "Chief Agent", AgentStatus.ERROR, f"Chief Agent failed: {e}")
                    # Fallback to mock breakdown so pipeline can continue
                    from backend.services.llm_service import generate_mock_data_for_model
                    from backend.models.output_models import ChiefTaskBreakdown
                    breakdown = generate_mock_data_for_model(ChiefTaskBreakdown, user_prompt)
                    self._update_status(project_id, "Chief Agent", AgentStatus.COMPLETED)

        # ── Phase 2: Parallel Specialist Agents ─────────────────────────
        async def run_story():
            self._update_status(project_id, "Story Agent", AgentStatus.RUNNING)
            start_story = time.time()
            try:
                result = await asyncio.wait_for(
                    story_agent.run(
                        breakdown.story_directive, room,
                        genre=breakdown.genre, tone=breakdown.tone,
                    ),
                    timeout=180.0
                )
                logger.info(f"Story Agent completed in {time.time()-start_story:.2f}s")
                self._update_status(project_id, "Story Agent", AgentStatus.COMPLETED)
                return result
            except Exception as e:
                logger.exception(e)
                logger.error(f"Story Agent failed or timed out: {e}")
                self._update_status(project_id, "Story Agent", AgentStatus.ERROR, str(e))
                return generate_mock_data_for_model(StoryOutput, user_prompt)

        async def run_characters():
            self._update_status(project_id, "Character Agent", AgentStatus.RUNNING)
            start_char = time.time()
            _char_delays = [1.0, 3.0, 5.0]
            for _cattempt in range(1, 4):
                try:
                    result = await asyncio.wait_for(
                        character_agent.run(
                            breakdown.character_directive, room,
                            genre=breakdown.genre, tone=breakdown.tone,
                        ),
                        timeout=120.0
                    )
                    logger.info(f"Character Agent completed in {time.time()-start_char:.2f}s (attempt {_cattempt})")
                    self._update_status(project_id, "Character Agent", AgentStatus.COMPLETED)
                    return result
                except Exception as e:
                    logger.warning(f"Character Agent attempt {_cattempt}/3 failed: {type(e).__name__}: {e}")
                    if _cattempt < 3:
                        wait_sec = _char_delays[_cattempt - 1]
                        logger.info(f"Waiting {wait_sec}s before Character Agent retry...")
                        await asyncio.sleep(wait_sec)
                    else:
                        logger.error(f"Character Agent failed after 3 attempts — using fallback characters from prompt")
                        self._update_status(project_id, "Character Agent", AgentStatus.ERROR, str(e))
                        # Generate fallback characters from prompt; never crash pipeline
                        try:
                            roster = generate_mock_data_for_model(CharacterRoster, user_prompt)
                            return roster.characters if roster and roster.characters else []
                        except Exception as fallback_err:
                            logger.error(f"Character fallback also failed: {fallback_err}")
                            return []

        async def run_world():
            self._update_status(project_id, "World Agent", AgentStatus.RUNNING)
            start_world = time.time()
            try:
                result = await asyncio.wait_for(
                    world_agent.run(
                        breakdown.world_directive, room,
                        genre=breakdown.genre, tone=breakdown.tone,
                    ),
                    timeout=180.0
                )
                logger.info(f"World Agent completed in {time.time()-start_world:.2f}s")
                self._update_status(project_id, "World Agent", AgentStatus.COMPLETED)
                return result
            except Exception as e:
                logger.exception(e)
                logger.error(f"World Agent failed or timed out: {e}")
                self._update_status(project_id, "World Agent", AgentStatus.ERROR, str(e))
                return generate_mock_data_for_model(WorldOutput, user_prompt)

        async def run_gameplay():
            self._update_status(project_id, "Gameplay Agent", AgentStatus.RUNNING)
            start_gameplay = time.time()
            try:
                result = await asyncio.wait_for(
                    gameplay_agent.run(
                        breakdown.gameplay_directive, room,
                        genre=breakdown.genre, tone=breakdown.tone,
                    ),
                    timeout=180.0
                )
                logger.info(f"Gameplay Agent completed in {time.time()-start_gameplay:.2f}s")
                self._update_status(project_id, "Gameplay Agent", AgentStatus.COMPLETED)
                return result
            except Exception as e:
                logger.exception(e)
                logger.error(f"Gameplay Agent failed or timed out: {e}")
                self._update_status(project_id, "Gameplay Agent", AgentStatus.ERROR, str(e))
                return generate_mock_data_for_model(GameplayOutput, user_prompt)

        # Run parallel specialists
        story, characters, world, gameplay = await asyncio.gather(
            run_story(),
            run_characters(),
            run_world(),
            run_gameplay(),
        )

        # ── Phase 3: Art Agent (needs context from prior agents) ────────
        self._update_status(project_id, "Art Agent", AgentStatus.RUNNING)
        start_art = time.time()
        try:
            art = await asyncio.wait_for(
                art_agent.run(
                    breakdown.art_directive, room,
                    project_id=project_id,
                    genre=breakdown.genre, tone=breakdown.tone,
                ),
                timeout=180.0
            )
            logger.info(f"Art Agent completed in {time.time()-start_art:.2f}s")
            self._update_status(project_id, "Art Agent", AgentStatus.COMPLETED)
        except Exception as e:
            logger.exception(e)
            logger.error(f"Art Agent failed or timed out: {e}")
            self._update_status(project_id, "Art Agent", AgentStatus.ERROR, str(e))
            art = generate_mock_data_for_model(ArtOutput, user_prompt)

        # ── Phase 4: QA Agent (reviews everything) ─────────────────────
        self._update_status(project_id, "QA Agent", AgentStatus.RUNNING)
        start_qa = time.time()
        try:
            qa = await asyncio.wait_for(qa_agent.run(breakdown.qa_directive, room), timeout=180.0)
            logger.info(f"QA Agent completed in {time.time()-start_qa:.2f}s")
            self._update_status(project_id, "QA Agent", AgentStatus.COMPLETED)
        except Exception as e:
            logger.exception(e)
            logger.error(f"QA Agent failed or timed out: {e}")
            self._update_status(project_id, "QA Agent", AgentStatus.ERROR, str(e))
            qa = generate_mock_data_for_model(QAOutput, user_prompt)

        # ── Phase 5: Reviewer Agent (cross-agent consistency) ──────────
        self._update_status(project_id, "Reviewer Agent", AgentStatus.RUNNING)
        start_reviewer = time.time()
        review = None
        try:
            review = await asyncio.wait_for(reviewer_agent.run(breakdown.reviewer_directive, room), timeout=180.0)
            logger.info(f"Reviewer Agent completed in {time.time()-start_reviewer:.2f}s")
            self._update_status(project_id, "Reviewer Agent", AgentStatus.COMPLETED)
        except Exception as e:
            logger.exception(e)
            logger.error(f"Reviewer Agent failed or timed out: {e}")
            self._update_status(project_id, "Reviewer Agent", AgentStatus.ERROR, str(e))
            review = generate_mock_data_for_model(ReviewerOutput, user_prompt)

        # ── Phase 6: Documentation Agent (generates docs) ─────────────
        logger.info("Starting Documentation Agent")
        self._update_status(project_id, "Documentation Agent", AgentStatus.RUNNING)
        start_docs = time.time()
        documentation = None
        try:
            project_title = story.title if story else "Untitled Project"
            documentation = await asyncio.wait_for(
                documentation_agent.run(
                    breakdown.documentation_directive,
                    room,
                    title=project_title,
                    genre=breakdown.genre,
                    tone=breakdown.tone,
                ),
                timeout=180.0
            )
            logger.info(f"Documentation Agent completed in {time.time()-start_docs:.2f}s")
            self._update_status(project_id, "Documentation Agent", AgentStatus.COMPLETED)
        except Exception as e:
            logger.exception(e)
            logger.error(f"Documentation Agent failed or timed out: {e}")
            self._update_status(project_id, "Documentation Agent", AgentStatus.ERROR, str(e))
            try:
                documentation = generate_mock_data_for_model(DocumentationOutput, user_prompt)
            except Exception as fallback_exc:
                logger.exception(fallback_exc)
                documentation = DocumentationOutput(
                    readme=f"# {story.title if story else 'Untitled Project'}\n\nFallback README content. Generation succeeded with partial documentation.",
                    gdd=f"# Game Design Document: {story.title if story else 'Untitled Project'}\n\nFallback Game Design Document. Generation succeeded with partial documentation."
                )

        logger.info("Documentation Agent complete")

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
            review=review,
            documentation=documentation,
        )

        # Persist and clean up
        logger.info("Saving project...")
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
        logger.info("Generation finished")
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
