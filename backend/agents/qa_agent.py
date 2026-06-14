"""
DreamXV AI Studio — QA Agent
==============================
Reviews all agent outputs for consistency, quality, and coherence.
Runs last in the pipeline to validate the complete project.
"""

from __future__ import annotations

from backend.models.output_models import QAOutput
from backend.services.llm_service import LLMService
from backend.services.band_service import BandRoom
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("qa_agent")

AGENT_NAME = "QA Agent"


class QAAgent:
    """Reviews all project outputs for quality and consistency."""

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._system_prompt = load_prompt("qa_prompt")

    async def run(
        self,
        directive: str,
        room: BandRoom,
    ) -> QAOutput:
        """
        Review all agent outputs and produce a quality assessment.

        Args:
            directive: QA-specific instructions from the Chief Agent.
            room: The Band room containing all agent outputs.

        Returns:
            QAOutput with consistency score, issues, suggestions, and assessment.
        """
        logger.info("QA Agent starting quality review...")

        room.add_participant(AGENT_NAME)
        room.send_message(AGENT_NAME, "Reviewing all outputs for quality and consistency...", msg_type="text")

        # Gather ALL context — QA needs to see everything
        all_results = room.get_messages(msg_type="result")
        context_parts = []
        for msg in all_results:
            context_parts.append(f"[{msg['sender']}] Output:\n{msg['content']}")
        full_context = "\n\n---\n\n".join(context_parts)

        user_message = (
            f"QA DIRECTIVE:\n{directive}\n\n"
            f"REVIEW THE FOLLOWING AGENT OUTPUTS:\n\n{full_context}"
        )

        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=user_message,
        )

        qa = await self._llm.generate_structured(
            messages,
            QAOutput,
            temperature=0.4,  # Low creativity, high precision for QA
        )

        logger.info(
            f"QA Agent complete: score={qa.consistency_score}/10, "
            f"{len(qa.issues)} issues, {len(qa.suggestions)} suggestions"
        )

        room.send_message(
            AGENT_NAME,
            qa.model_dump_json(),
            msg_type="result",
        )

        return qa
