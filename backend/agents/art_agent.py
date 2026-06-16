"""
DreamXV AI Studio — Art Agent
==============================
Generates cinematic image prompts and produces images using AIMLAPI.

Responsibilities:
1. Generate cinematic art prompts based on story/character/world context.
2. Generate images via ImageService (AIMLAPI).
3. Save generated images to outputs/images/.

Image types: character art, environment art, cover art.
Maximum: 3 images per project.
"""

from __future__ import annotations

from backend.models.output_models import ArtOutput
from backend.services.llm_service import LLMService
from backend.services.image_service import ImageService
from backend.services.band_service import BandRoom
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("art_agent")

AGENT_NAME = "Art Agent"


class ArtAgent:
    """
    Generates cinematic art prompts via LLM, then produces images
    using AIMLAPI image generation.
    """

    def __init__(self, llm: LLMService, image_service: ImageService) -> None:
        self._llm = llm
        self._image_service = image_service
        self._system_prompt = load_prompt("art_prompt")

    async def run(
        self,
        directive: str,
        room: BandRoom,
        *,
        project_id: str,
        genre: str = "",
        tone: str = "",
    ) -> ArtOutput:
        """
        Generate art prompts and produce images.

        Args:
            directive: Art-specific instructions from the Chief Agent.
            room: The Band room for context and communication.
            project_id: Project identifier for image file organization.
            genre: Identified genre.
            tone: Identified tone.

        Returns:
            ArtOutput with prompts, image paths, and style guide.
        """
        prompt = directive
        logger.info(f"Agent received: {prompt}")
        logger.info("ART_AGENT_START")
        logger.info("Art Agent starting visual production...")

        room.add_participant(AGENT_NAME)
        room.send_message(AGENT_NAME, "Creating visual direction and generating art...", msg_type="text")

        # Gather rich context from other agents
        context = room.get_context_summary(AGENT_NAME)

        user_message = f"ART DIRECTIVE:\n{directive}\n\n"
        if genre:
            user_message += f"GENRE: {genre}\n"
        if tone:
            user_message += f"TONE: {tone}\n"

        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=user_message,
            context=context if context else None,
        )

        # Step 1: Generate art prompts and style guide via LLM
        art_output = await self._llm.generate_structured(
            messages,
            ArtOutput,
            temperature=0.8,
        )

        logger.info(f"Art Agent generated {len(art_output.prompts)} art prompts")

        # Actual image generation is now handled asynchronously in the background.
        art_output.image_paths = []

        logger.info("Art Agent prompts generation complete.")

        # Clean up massive base64 strings before broadcasting to the room to protect other agents' context windows
        room_art_output = art_output.model_copy(deep=True)
        room_art_output.image_paths = [
            f"[Base64 Image Data - Length {len(p)}]" if p.startswith("data:") else p
            for p in room_art_output.image_paths
        ]

        room.send_message(
            AGENT_NAME,
            room_art_output.model_dump_json(),
            msg_type="result",
        )

        return art_output
