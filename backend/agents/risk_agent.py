"""
DreamXV AI Studio — Risk Agent
==============================
Detects scope creep, missing assets, unrealistic deadlines, and budget issues.
"""

from __future__ import annotations

from backend.models.output_models import RiskOutput
from backend.services.llm_service import LLMService
from backend.services.band_service import BandRoom
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("risk_agent")
AGENT_NAME = "Risk Agent"


class RiskAgent:
    def __init__(self, llm: LLMService) -> None:
        self._llm = llm
        self._system_prompt = load_prompt("risk_prompt")

    async def run(
        self,
        directive: str,
        room: BandRoom,
        *,
        genre: str = "",
        tone: str = "",
    ) -> RiskOutput:
        logger.info("Risk Agent starting risk analysis...")
        room.add_participant(AGENT_NAME)
        room.send_message(AGENT_NAME, "Analyzing delivery risks...", msg_type="text")

        context = room.get_context_summary(AGENT_NAME)
        user_message = f"RISK DIRECTIVE:\n{directive}\n\n"
        if genre:
            user_message += f"GENRE: {genre}\n"
        if tone:
            user_message += f"TONE: {tone}\n"

        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=user_message,
            context=context if context else None,
        )

        risk = await self._llm.generate_structured(
            messages,
            RiskOutput,
            temperature=0.6,
        )

        room.send_message(AGENT_NAME, risk.model_dump_json(), msg_type="result")
        return risk

