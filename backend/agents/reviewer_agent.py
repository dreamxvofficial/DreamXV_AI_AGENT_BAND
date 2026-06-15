"""
DreamXV AI Studio — Reviewer Agent
====================================
Cross-agent consistency reviewer that detects inconsistencies,
naming mismatches, and contradictions across all outputs.
Runs after QA Agent in the pipeline.
"""

from __future__ import annotations

from backend.models.output_models import ReviewerOutput
from backend.services.llm_service import LLMService
from backend.services.band_service import BandRoom
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("reviewer_agent")

AGENT_NAME = "Reviewer Agent"


class ReviewerAgent:
    """Detects cross-agent inconsistencies and naming mismatches."""

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._system_prompt = load_prompt("reviewer_prompt")

    async def run(
        self,
        directive: str,
        room: BandRoom,
    ) -> ReviewerOutput:
        """
        Review all agent outputs for cross-domain consistency.

        Args:
            directive: Reviewer-specific instructions from the Chief Agent.
            room: The Band room containing all agent outputs.

        Returns:
            ReviewerOutput with consistency score, issues, and summary.
        """
        logger.info("Reviewer Agent starting cross-agent consistency review...")

        room.add_participant(AGENT_NAME)
        room.send_message(
            AGENT_NAME,
            "Performing cross-agent consistency review...",
            msg_type="text",
        )

        # Gather ALL context — Reviewer needs to see everything
        all_results = room.get_messages(msg_type="result")
        context_parts = []
        for msg in all_results:
            context_parts.append(f"[{msg['sender']}] Output:\n{msg['content']}")
        full_context = "\n\n---\n\n".join(context_parts)

        user_message = (
            f"REVIEWER DIRECTIVE:\n{directive}\n\n"
            f"REVIEW THE FOLLOWING AGENT OUTPUTS FOR CONSISTENCY:\n\n{full_context}"
        )

        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=user_message,
        )

        review = await self._llm.generate_structured(
            messages,
            ReviewerOutput,
            temperature=0.3,  # Very low creativity for precise review
        )

        logger.info(
            f"Reviewer Agent complete: score={review.consistency_score}/10, "
            f"{len(review.issues)} issues detected"
        )

        room.send_message(
            AGENT_NAME,
            review.model_dump_json(),
            msg_type="result",
        )

        return review
