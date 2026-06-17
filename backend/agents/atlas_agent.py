"""
DreamXV AI Studio — Atlas Agent
================================
Generates AI-powered development roadmaps, project structures, and production workflows.
"""

from __future__ import annotations

from backend.models.output_models import AtlasOutput
from backend.services.llm_service import LLMService
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("atlas_agent")

AGENT_NAME = "Atlas Agent"


class AtlasAgent:
    """Generates development roadmaps, folder structures, flow maps, and task breakdowns."""

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._system_prompt = load_prompt("atlas_prompt")

    async def run(
        self,
        project_data: dict,
        duration: str,
        tools: str,
        team_size: int = 1,
        hours_per_day: float = 8.0,
    ) -> AtlasOutput:
        """
        Generate development planning outputs.

        Args:
            project_data: Dictionary of full project data.
            duration: User specified project duration.
            tools: User specified tools & technologies.
            team_size: Number of team members.
            hours_per_day: Working hours per person per day.

        Returns:
            AtlasOutput.
        """
        logger.info("Atlas Agent starting production plan generation...")

        # Build context from project data
        story = project_data.get("story") or {}
        world = project_data.get("world") or {}
        characters = project_data.get("characters") or []
        gameplay = project_data.get("gameplay") or {}
        qa = project_data.get("qa") or {}
        documentation = project_data.get("documentation") or {}

        char_desc = "\n".join([f"- {c.get('name')} ({c.get('role')}): {c.get('backstory')}" for c in characters])
        
        context = (
            f"TITLE: {project_data.get('title', 'Untitled')}\n\n"
            f"STORY SUMMARY: {story.get('summary', 'N/A')}\n"
            f"STORY LORE: {story.get('lore', 'N/A')}\n\n"
            f"WORLD SETTING: {world.get('description', 'N/A')}\n"
            f"WORLD ATMOSPHERE: {world.get('atmosphere', 'N/A')}\n\n"
            f"CHARACTERS:\n{char_desc}\n\n"
            f"GAMEPLAY CORE LOOP: {gameplay.get('core_loop', 'N/A')}\n"
            f"GAMEPLAY MECHANICS: {', '.join(gameplay.get('mechanics', []))}\n\n"
            f"QA ASSESSMENT: {qa.get('overall_assessment', 'N/A')}\n\n"
            f"ELEVATOR PITCH: {documentation.get('elevator_pitch', 'N/A')}\n"
            f"TECHNICAL SUMMARY: {documentation.get('technical_summary', 'N/A')}\n"
        )

        user_message = (
            f"USER SPECIFIED DURATION: {duration}\n"
            f"USER SPECIFIED TOOLS & TECHNOLOGIES: {tools}\n"
            f"TEAM SIZE: {team_size} person(s)\n"
            f"HOURS PER DAY PER PERSON: {hours_per_day} hours\n\n"
            f"PROJECT SOURCE DETAILS:\n{context}\n"
        )

        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=user_message,
        )

        atlas_output = await self._llm.generate_structured(
            messages,
            AtlasOutput,
            temperature=0.5,
        )

        # Ensure project_id is set
        atlas_output.project_id = project_data.get("project_id", "")

        logger.info(
            f"Atlas Agent completed roadmap generation with "
            f"{len(atlas_output.roadmap)} phases and "
            f"{len(atlas_output.project_structure)} file/folder paths."
        )

        return atlas_output
