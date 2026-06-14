"""
DreamXV AI Studio — Chief Agent
================================
Orchestrator agent that decomposes user prompts into sub-tasks
for specialist agents within a Band room.
"""

from __future__ import annotations

from backend.models.output_models import ChiefTaskBreakdown
from backend.services.llm_service import LLMService
from backend.services.band_service import BandRoom
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("chief_agent")

AGENT_NAME = "Chief Agent"


class ChiefAgent:
    """
    Decomposes user prompts into structured directives for all specialist agents.
    This agent runs first and its output drives the entire pipeline.
    """

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._system_prompt = load_prompt("chief_prompt")

    async def run(
        self,
        user_prompt: str,
        room: BandRoom,
    ) -> ChiefTaskBreakdown:
        """
        Analyze the user prompt and produce a task breakdown.

        Args:
            user_prompt: The user's creative project prompt.
            room: The Band room for inter-agent communication.

        Returns:
            ChiefTaskBreakdown with directives for each specialist agent.
        """
        logger.info(f"Chief Agent analyzing prompt: {user_prompt[:100]}...")

        # Join the room and announce
        room.add_participant(AGENT_NAME)
        room.send_message(
            AGENT_NAME,
            f"Analyzing project prompt and creating task breakdown...",
            msg_type="text",
        )

        # Build messages for LLM
        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=(
                f"Analyze the following game/project concept and create detailed "
                f"directives for each specialist agent:\n\n"
                f"USER PROMPT:\n{user_prompt}"
            ),
        )

        # Generate structured breakdown
        breakdown = await self._llm.generate_structured(
            messages,
            ChiefTaskBreakdown,
            temperature=0.6,
        )

        logger.info(f"Chief Agent breakdown complete. Genre: {breakdown.genre}, Tone: {breakdown.tone}")

        # Broadcast breakdown to the room
        room.send_message(
            AGENT_NAME,
            breakdown.model_dump_json(),
            msg_type="directive",
        )

        return breakdown
