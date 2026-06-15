"""
DreamXV AI Studio — Character Agent
====================================
Generates detailed character profiles with backstories, abilities, and visual descriptions.
"""

from __future__ import annotations

from backend.models.output_models import CharacterOutput, CharacterRoster
from backend.services.llm_service import LLMService
from backend.services.band_service import BandRoom
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("character_agent")

AGENT_NAME = "Character Agent"


class CharacterAgent:
    """Creates memorable character profiles for game projects."""

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._system_prompt = load_prompt("character_prompt")

    async def run(
        self,
        directive: str,
        room: BandRoom,
        *,
        genre: str = "",
        tone: str = "",
    ) -> list[CharacterOutput]:
        """
        Generate characters based on the Chief Agent's directive.

        Args:
            directive: Character-specific instructions from the Chief Agent.
            room: The Band room for context and communication.
            genre: Identified genre.
            tone: Identified tone.

        Returns:
            List of CharacterOutput instances.
        """
        prompt = directive
        logger.info(f"Agent received: {prompt}")
        logger.info("Character Agent starting character creation...")

        room.add_participant(AGENT_NAME)
        room.send_message(AGENT_NAME, "Designing characters...", msg_type="text")

        context = room.get_context_summary(AGENT_NAME)

        user_message = f"CHARACTER DIRECTIVE:\n{directive}\n\n"
        if genre:
            user_message += f"GENRE: {genre}\n"
        if tone:
            user_message += f"TONE: {tone}\n"

        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=user_message,
            context=context if context else None,
        )

        # Generate structured roster
        roster = await self._llm.generate_structured(
            messages,
            CharacterRoster,
            temperature=0.75,
        )

        characters = roster.characters
        logger.info(f"Character Agent complete: {len(characters)} characters created")

        # Post result to room
        room.send_message(
            AGENT_NAME,
            roster.model_dump_json(),
            msg_type="result",
        )

        return characters
