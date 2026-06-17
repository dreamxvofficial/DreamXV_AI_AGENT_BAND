"""
DreamXV AI Studio — Feasibility Agent
======================================
Estimates success probability, team size, days, and risk level.
"""

from __future__ import annotations

from backend.models.output_models import FeasibilityOutput
from backend.services.llm_service import LLMService
from backend.services.band_service import BandRoom
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("feasibility_agent")
AGENT_NAME = "Feasibility Agent"


class FeasibilityAgent:
    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._system_prompt = load_prompt("feasibility_prompt")

    async def run(
        self,
        directive: str,
        room: BandRoom,
        *,
        genre: str = "",
        tone: str = "",
    ) -> FeasibilityOutput:
        logger.info("Feasibility Agent starting audit...")
        room.add_participant(AGENT_NAME)
        room.send_message(AGENT_NAME, "Auditing project feasibility...", msg_type="text")

        context = room.get_context_summary(AGENT_NAME)
        user_message = f"FEASIBILITY DIRECTIVE:\n{directive}\n\n"
        if genre:
            user_message += f"GENRE: {genre}\n"
        if tone:
            user_message += f"TONE: {tone}\n"

        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=user_message,
            context=context if context else None,
        )

        feasibility = await self._llm.generate_structured(
            messages,
            FeasibilityOutput,
            temperature=0.6,
        )

        logger.info(f"Feasibility Agent complete: {feasibility.success_probability}% success chance")
        room.send_message(AGENT_NAME, feasibility.model_dump_json(), msg_type="result")
        return feasibility
