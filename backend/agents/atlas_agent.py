"""
DreamXV AI Studio — Atlas Agent
================================
Generates AI-powered development roadmaps, project structures, and production workflows.
"""

from __future__ import annotations

import re

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

        duration_days = self._duration_days(duration)
        available_hours = round(team_size * hours_per_day * duration_days, 2)

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
            f"CALENDAR DAYS: {duration_days}\n"
            f"AVAILABLE PRODUCTION HOURS: {team_size} * {hours_per_day} * {duration_days} = {available_hours}\n"
            f"TARGET: Playable MVP Prototype\n\n"
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
        self._validate_plan(atlas_output, available_hours)

        logger.info(
            f"Atlas Agent completed roadmap generation with "
            f"{len(atlas_output.roadmap)} phases and "
            f"{len(atlas_output.project_structure)} file/folder paths."
        )

        return atlas_output

    @staticmethod
    def _duration_days(duration: str) -> int:
        match = re.search(r"(\d+)\s*(day|week|month|year)s?", duration.lower())
        if not match:
            return 1
        value, unit = int(match.group(1)), match.group(2)
        return value * {"day": 1, "week": 7, "month": 30, "year": 365}[unit]

    @staticmethod
    def _validate_plan(output: AtlasOutput, available_hours: float) -> None:
        """Normalize model arithmetic and reject dangling/forward dependencies."""
        tasks = output.task_breakdown.detailed_tasks
        seen: set[str] = set()
        for index, task in enumerate(tasks, 1):
            task.id = f"TSK-{index:03d}"
            task.dependencies = [dep for dep in task.dependencies if dep in seen]
            seen.add(task.id)

        planned = round(sum(task.hours for task in tasks), 2)
        if planned > available_hours and planned:
            scale = available_hours / planned
            for task in tasks:
                task.hours = max(0.1, round(task.hours * scale, 2))
            # Rounding can drift above capacity; take it from the largest task.
            planned = round(sum(task.hours for task in tasks), 2)
            if planned > available_hours:
                largest = max(tasks, key=lambda item: item.hours)
                largest.hours = round(largest.hours - (planned - available_hours), 2)
        planned = round(sum(task.hours for task in tasks), 2)

        if output.roadmap_simulator is not None:
            output.roadmap_simulator.available_hours = available_hours
            output.roadmap_simulator.planned_hours = planned
            output.roadmap_simulator.status = "ON TRACK" if planned <= available_hours else "AT RISK"
            buffer = round(available_hours - planned, 2)
            output.roadmap_simulator.explanation = (
                f"Plan uses {planned} of {available_hours} available hours; "
                f"{abs(buffer)} hours {'remain as buffer' if buffer >= 0 else 'exceed capacity'}."
            )
