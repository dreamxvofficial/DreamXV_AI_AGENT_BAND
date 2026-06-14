"""
DreamXV AI Studio — Gameplay Agent
===================================
Designs core gameplay mechanics, progression systems, and difficulty curves.
"""

from __future__ import annotations

from backend.models.output_models import GameplayOutput
from backend.services.llm_service import LLMService
from backend.services.band_service import BandRoom
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("gameplay_agent")

AGENT_NAME = "Gameplay Agent"


class GameplayAgent:
    """Designs engaging gameplay systems for game projects."""

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._system_prompt = load_prompt("gameplay_prompt")

    async def run(
        self,
        directive: str,
        room: BandRoom,
        *,
        genre: str = "",
        tone: str = "",
    ) -> GameplayOutput:
        """
        Generate gameplay systems based on the Chief Agent's directive.

        Args:
            directive: Gameplay-specific instructions from the Chief Agent.
            room: The Band room for context and communication.
            genre: Identified genre.
            tone: Identified tone.

        Returns:
            GameplayOutput with core loop, mechanics, progression, and difficulty.
        """
        logger.info("Gameplay Agent starting systems design...")

        room.add_participant(AGENT_NAME)
        room.send_message(AGENT_NAME, "Designing gameplay systems...", msg_type="text")

        context = room.get_context_summary(AGENT_NAME)

        user_message = f"GAMEPLAY DIRECTIVE:\n{directive}\n\n"
        if genre:
            user_message += f"GENRE: {genre}\n"
        if tone:
            user_message += f"TONE: {tone}\n"

        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=user_message,
            context=context if context else None,
        )

        gameplay = await self._llm.generate_structured(
            messages,
            GameplayOutput,
            temperature=0.65,
        )

        logger.info(f"Gameplay Agent complete: {len(gameplay.mechanics)} mechanics designed")

        room.send_message(
            AGENT_NAME,
            gameplay.model_dump_json(),
            msg_type="result",
        )

        return gameplay
