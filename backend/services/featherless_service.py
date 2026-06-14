"""
DreamXV AI Studio — Featherless AI Service
===========================================
Primary LLM provider using the OpenAI-compatible API.
Endpoint: https://api.featherless.ai/v1
"""

from __future__ import annotations

import json
from typing import Optional, Type, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger("featherless")
T = TypeVar("T", bound=BaseModel)


class FeatherlessService:
    """Async client for the Featherless AI chat completions API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=settings.featherless_api_key,
            base_url=settings.featherless_base_url,
        )
        self._default_model = settings.featherless_model
        self._default_temperature = settings.default_temperature
        self._default_max_tokens = settings.default_max_tokens

    async def generate(
        self,
        messages: list[dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send a chat completion request to Featherless AI.

        Args:
            messages: OpenAI-compatible message list.
            model: Override model identifier.
            temperature: Override temperature.
            max_tokens: Override max tokens.

        Returns:
            The assistant's response text.
        """
        logger.info(f"Featherless generate → model={model or self._default_model}")

        response = await self._client.chat.completions.create(
            model=model or self._default_model,
            messages=messages,
            temperature=temperature or self._default_temperature,
            max_tokens=max_tokens or self._default_max_tokens,
            timeout=5.0,
        )

        content = response.choices[0].message.content or ""
        logger.debug(f"Featherless response length: {len(content)} chars")
        return content

    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        response_model: Type[T],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        """
        Generate a structured Pydantic model output.

        Instructs the LLM to return JSON matching the model schema,
        then parses and validates the response.

        Args:
            messages: Chat messages.
            response_model: Pydantic model class to parse into.
            model: Override model identifier.
            temperature: Override temperature.

        Returns:
            Validated Pydantic model instance.
        """
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)

        # Inject structured output instruction into the last system message
        structured_instruction = (
            "\n\n[STRUCTURED OUTPUT REQUIREMENT]\n"
            "You MUST respond with ONLY valid JSON matching this schema:\n"
            f"```json\n{schema_json}\n```\n"
            "Do NOT include any text before or after the JSON. "
            "Do NOT wrap in markdown code fences."
        )

        # Append instruction to the system message
        enhanced_messages = list(messages)
        if enhanced_messages and enhanced_messages[0]["role"] == "system":
            enhanced_messages[0] = {
                "role": "system",
                "content": enhanced_messages[0]["content"] + structured_instruction,
            }
        else:
            enhanced_messages.insert(0, {
                "role": "system",
                "content": structured_instruction,
            })

        raw = await self.generate(
            enhanced_messages,
            model=model,
            temperature=temperature or 0.4,  # Lower temp for structured output
            max_tokens=self._default_max_tokens,
        )

        # Clean potential markdown fences from response
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        return response_model.model_validate_json(cleaned)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.close()
