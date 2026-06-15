"""
DreamXV AI Studio — World Agent
================================
Designs immersive game worlds with regions, lore, and atmosphere.
"""

from __future__ import annotations

from backend.models.output_models import WorldOutput
from backend.services.llm_service import LLMService
from backend.services.band_service import BandRoom
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("world_agent")

AGENT_NAME = "World Agent"


class WorldAgent:
    """Builds detailed, immersive game worlds."""

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._system_prompt = load_prompt("world_prompt")

    async def run(
        self,
        directive: str,
        room: BandRoom,
        *,
        genre: str = "",
        tone: str = "",
    ) -> WorldOutput:
        """
        Generate world-building content based on the Chief Agent's directive.

        Args:
            directive: World-specific instructions from the Chief Agent.
            room: The Band room for context and communication.
            genre: Identified genre.
            tone: Identified tone.

        Returns:
            WorldOutput with name, description, regions, lore, and atmosphere.
        """
        prompt = directive
        logger.info(f"Agent received: {prompt}")
        logger.info("World Agent starting world creation...")

        room.add_participant(AGENT_NAME)
        room.send_message(AGENT_NAME, "Constructing world...", msg_type="text")

        context = room.get_context_summary(AGENT_NAME)

        user_message = f"WORLD DIRECTIVE:\n{directive}\n\n"
        if genre:
            user_message += f"GENRE: {genre}\n"
        if tone:
            user_message += f"TONE: {tone}\n"

        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=user_message,
            context=context if context else None,
        )

        world = await self._llm.generate_structured(
            messages,
            WorldOutput,
            temperature=0.75,
        )

        logger.info(f"World Agent complete: '{world.name}' — {len(world.regions)} regions")

        room.send_message(
            AGENT_NAME,
            world.model_dump_json(),
            msg_type="result",
        )

        return world
