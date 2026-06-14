"""
DreamXV AI Studio — Story Agent
================================
Generates narrative content: title, lore, summary, acts, and themes.
"""

from __future__ import annotations

from backend.models.output_models import StoryOutput
from backend.services.llm_service import LLMService
from backend.services.band_service import BandRoom
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("story_agent")

AGENT_NAME = "Story Agent"


class StoryAgent:
    """Generates rich narrative content for game projects."""

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._system_prompt = load_prompt("story_prompt")

    async def run(
        self,
        directive: str,
        room: BandRoom,
        *,
        genre: str = "",
        tone: str = "",
    ) -> StoryOutput:
        """
        Generate story content based on the Chief Agent's directive.

        Args:
            directive: Story-specific instructions from the Chief Agent.
            room: The Band room for context and communication.
            genre: Identified genre from Chief Agent.
            tone: Identified tone from Chief Agent.

        Returns:
            StoryOutput with title, lore, summary, acts, and themes.
        """
        logger.info("Story Agent starting narrative generation...")

        room.add_participant(AGENT_NAME)
        room.send_message(AGENT_NAME, "Beginning narrative generation...", msg_type="text")

        # Gather any prior context from the room
        context = room.get_context_summary(AGENT_NAME)

        # Build the user message with directive and context
        user_message = f"STORY DIRECTIVE:\n{directive}\n\n"
        if genre:
            user_message += f"GENRE: {genre}\n"
        if tone:
            user_message += f"TONE: {tone}\n"

        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=user_message,
            context=context if context else None,
        )

        # Generate structured output
        story = await self._llm.generate_structured(
            messages,
            StoryOutput,
            temperature=0.8,  # Higher creativity for narrative
        )

        logger.info(f"Story Agent complete: '{story.title}' — {len(story.acts)} acts")

        # Post result to room
        room.send_message(
            AGENT_NAME,
            story.model_dump_json(),
            msg_type="result",
        )

        return story
