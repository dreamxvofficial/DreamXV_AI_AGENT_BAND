"""
DreamXV AI Studio — Analytics Agent
===================================
Tracks agent runtimes, token counts, and cost/productivity metrics.
"""

from __future__ import annotations

from backend.models.output_models import AnalyticsOutput
from backend.services.llm_service import LLMService
from backend.services.band_service import BandRoom
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("analytics_agent")
AGENT_NAME = "Analytics Agent"


class AnalyticsAgent:
    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._system_prompt = load_prompt("analytics_prompt")

    async def run(
        self,
        directive: str,
        room: BandRoom,
        *,
        genre: str = "",
        tone: str = "",
        agent_runtimes: dict[str, float] = None,
    ) -> AnalyticsOutput:
        logger.info("Analytics Agent starting computation...")
        room.add_participant(AGENT_NAME)
        room.send_message(AGENT_NAME, "Calculating resource and runtime metrics...", msg_type="text")

        context = room.get_context_summary(AGENT_NAME)
        user_message = f"ANALYTICS DIRECTIVE:\n{directive}\n\n"
        if agent_runtimes:
            user_message += f"ACTUAL AGENT RUNTIMES (SECONDS):\n"
            for k, v in agent_runtimes.items():
                user_message += f"- {k}: {v:.2f}s\n"
        if genre:
            user_message += f"GENRE: {genre}\n"
        if tone:
            user_message += f"TONE: {tone}\n"

        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=user_message,
            context=context if context else None,
        )

        analytics = await self._llm.generate_structured(
            messages,
            AnalyticsOutput,
            temperature=0.5,
        )

        if agent_runtimes:
            # Overwrite mock runtime seconds with actual runtimes
            analytics.agent_runtime_seconds = agent_runtimes

        logger.info(f"Analytics Agent complete: Productivity Score: {analytics.productivity_score}%")
        room.send_message(AGENT_NAME, analytics.model_dump_json(), msg_type="result")
        return analytics
