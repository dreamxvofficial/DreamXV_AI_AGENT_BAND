"""
DreamXV AI Studio — Project Planner Agent
==========================================
Generates sprint plans, milestones, dependencies, and Kanban tasks.
"""

from __future__ import annotations

from backend.models.output_models import ProjectPlannerOutput
from backend.services.llm_service import LLMService
from backend.services.band_service import BandRoom
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("project_planner_agent")
AGENT_NAME = "Project Planner Agent"


class ProjectPlannerAgent:
    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._system_prompt = load_prompt("project_planner_prompt")

    async def run(
        self,
        directive: str,
        room: BandRoom,
        *,
        genre: str = "",
        tone: str = "",
    ) -> ProjectPlannerOutput:
        logger.info("Project Planner Agent starting sprint layout...")
        room.add_participant(AGENT_NAME)
        room.send_message(AGENT_NAME, "Generating sprints and task dependencies...", msg_type="text")

        context = room.get_context_summary(AGENT_NAME)
        user_message = f"PLANNER DIRECTIVE:\n{directive}\n\n"
        if genre:
            user_message += f"GENRE: {genre}\n"
        if tone:
            user_message += f"TONE: {tone}\n"

        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=user_message,
            context=context if context else None,
        )

        planner = await self._llm.generate_structured(
            messages,
            ProjectPlannerOutput,
            temperature=0.7,
        )

        logger.info(f"Project Planner Agent complete: {len(planner.sprints)} sprints designed")
        room.send_message(AGENT_NAME, planner.model_dump_json(), msg_type="result")
        return planner
