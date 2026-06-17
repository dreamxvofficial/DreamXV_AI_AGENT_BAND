"""
DreamXV AI Studio — Timeline Agent
==================================
Generates week-by-week and month-by-month roadmaps.
"""

from __future__ import annotations

from backend.models.output_models import TimelineOutput
from backend.services.llm_service import LLMService
from backend.services.band_service import BandRoom
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("timeline_agent")
AGENT_NAME = "Timeline Agent"


class TimelineAgent:
    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._system_prompt = load_prompt("timeline_prompt")

    async def run(
        self,
        directive: str,
        room: BandRoom,
        *,
        genre: str = "",
        tone: str = "",
    ) -> TimelineOutput:
        logger.info("Timeline Agent starting timeline generation...")
        room.add_participant(AGENT_NAME)
        room.send_message(AGENT_NAME, "Generating week-by-week roadmap...", msg_type="text")

        context = room.get_context_summary(AGENT_NAME)
        user_message = f"TIMELINE DIRECTIVE:\n{directive}\n\n"
        if genre:
            user_message += f"GENRE: {genre}\n"
        if tone:
            user_message += f"TONE: {tone}\n"

        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=user_message,
            context=context if context else None,
        )

        timeline = await self._llm.generate_structured(
            messages,
            TimelineOutput,
            temperature=0.7,
        )

        logger.info(f"Timeline Agent complete: generated {len(timeline.roadmap_weekly)} weeks")
        room.send_message(AGENT_NAME, timeline.model_dump_json(), msg_type="result")
        return timeline
