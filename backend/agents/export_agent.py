"""
DreamXV AI Studio — Export Agent
=================================
Prepares markdown documents, JSON, PDF summaries, and ZIP design kits.
"""

from __future__ import annotations

from backend.models.output_models import ExportOutput
from backend.services.llm_service import LLMService
from backend.services.band_service import BandRoom
from backend.utils.helpers import load_prompt, build_chat_messages
from backend.utils.logger import get_logger

logger = get_logger("export_agent")
AGENT_NAME = "Export Agent"


class ExportAgent:
    def __init__(self, llm: LLMService, export_service=None) -> None:
        self._llm = llm
        self._export_service = export_service
        self._system_prompt = load_prompt("export_prompt")

    async def run(
        self,
        directive: str,
        room: BandRoom,
        *,
        genre: str = "",
        tone: str = "",
    ) -> ExportOutput:
        logger.info("Export Agent starting report package preparation...")
        room.add_participant(AGENT_NAME)
        room.send_message(AGENT_NAME, "Assembling exportable files...", msg_type="text")

        context = room.get_context_summary(AGENT_NAME)
        user_message = f"EXPORT DIRECTIVE:\n{directive}\n\n"
        if genre:
            user_message += f"GENRE: {genre}\n"
        if tone:
            user_message += f"TONE: {tone}\n"

        messages = build_chat_messages(
            system_prompt=self._system_prompt,
            user_message=user_message,
            context=context if context else None,
        )

        export_out = await self._llm.generate_structured(
            messages,
            ExportOutput,
            temperature=0.5,
        )

        logger.info("Export Agent complete")
        room.send_message(AGENT_NAME, export_out.model_dump_json(), msg_type="result")
        return export_out
