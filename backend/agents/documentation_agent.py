"""
DreamXV AI Studio — Documentation Agent
=========================================
Generates comprehensive project documentation including README,
Game Design Document, feature lists, and more.
"""

from __future__ import annotations

from backend.models.output_models import DocumentationOutput
from backend.services.llm_service import LLMService
from backend.services.band_service import BandRoom
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("documentation_agent")

AGENT_NAME = "Documentation Agent"


class DocumentationAgent:
    """Generates comprehensive project documentation from all agent outputs."""

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._system_prompt = load_prompt("documentation_prompt")

    async def run(
        self,
        directive: str,
        room: BandRoom,
        *,
        title: str = "",
        genre: str = "",
        tone: str = "",
    ) -> DocumentationOutput:
        """
        Generate comprehensive project documentation.

        Args:
            directive: Documentation-specific instructions from the Chief Agent.
            room: The Band room containing all agent outputs.
            title: Project title for documentation headers.
            genre: Identified genre from Chief Agent.
            tone: Identified tone from Chief Agent.

        Returns:
            DocumentationOutput with all documentation sections.
        """
        prompt = directive
        logger.info(f"Agent received: {prompt}")
        logger.info("Documentation Agent starting documentation generation...")

        room.add_participant(AGENT_NAME)
        room.send_message(
            AGENT_NAME,
            "Generating comprehensive project documentation...",
            msg_type="text",
        )

        # Gather ALL context — Documentation needs to see everything
        all_results = room.get_messages(msg_type="result")
        context_parts = []
        for msg in all_results:
            context_parts.append(f"[{msg['sender']}] Output:\n{msg['content']}")
        full_context = "\n\n---\n\n".join(context_parts)

        user_message = (
            f"DOCUMENTATION DIRECTIVE:\n{directive}\n\n"
            f"PROJECT TITLE: {title}\n"
            f"GENRE: {genre}\n"
            f"TONE: {tone}\n\n"
            f"GENERATE DOCUMENTATION FROM THE FOLLOWING AGENT OUTPUTS:\n\n{full_context}"
        )

        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=user_message,
        )

        docs = await self._llm.generate_structured(
            messages,
            DocumentationOutput,
            temperature=0.5,
        )

        logger.info(
            f"Documentation Agent complete: "
            f"{len(docs.feature_list)} features, "
            f"{len(docs.core_mechanics)} mechanics listed"
        )

        room.send_message(
            AGENT_NAME,
            docs.model_dump_json(),
            msg_type="result",
        )

        return docs
