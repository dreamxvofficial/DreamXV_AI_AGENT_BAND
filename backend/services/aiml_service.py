"""
DreamXV AI Studio — AIMLAPI Service
====================================
Fallback LLM provider using the OpenAI-compatible API.
Endpoint: https://api.aimlapi.com/v1
"""

from __future__ import annotations

import json
from typing import Optional, Type, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger("aimlapi")
T = TypeVar("T", bound=BaseModel)


class AIMLService:
    """Async client for the AIMLAPI chat completions API (fallback provider)."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=settings.aiml_api_key,
            base_url=settings.aiml_base_url,
        )
        self._default_model = settings.aiml_model
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
        Send a chat completion request to AIMLAPI.

        Args:
            messages: OpenAI-compatible message list.
            model: Override model identifier.
            temperature: Override temperature.
            max_tokens: Override max tokens.

        Returns:
            The assistant's response text.
        """
        logger.info(f"AIMLAPI generate (fallback) -> model={model or self._default_model}")

        response = await self._client.chat.completions.create(
            model=model or self._default_model,
            messages=messages,
            temperature=temperature or self._default_temperature,
            max_tokens=max_tokens or self._default_max_tokens,
            timeout=30.0,
        )

        content = response.choices[0].message.content or ""
        logger.debug(f"AIMLAPI response length: {len(content)} chars")
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
        Generate a structured Pydantic model output via AIMLAPI.

        Same approach as FeatherlessService — injects JSON schema instruction,
        then parses the LLM response into the target model.
        """
        import typing
        from pydantic import BaseModel

        def generate_example_dict(model_cls) -> dict:
            example = {}
            for name, field in model_cls.model_fields.items():
                desc = field.description or ""
                annotation = field.annotation
                origin = typing.get_origin(annotation)
                args = typing.get_args(annotation)

                if origin is list:
                    item_type = args[0] if args else str
                    if isinstance(item_type, type) and issubclass(item_type, BaseModel):
                        example[name] = [generate_example_dict(item_type)]
                    else:
                        type_name = getattr(item_type, "__name__", str(item_type))
                        example[name] = [f"<{type_name}: {desc}>"]
                elif isinstance(annotation, type) and issubclass(annotation, BaseModel):
                    example[name] = generate_example_dict(annotation)
                else:
                    type_name = getattr(annotation, "__name__", str(annotation)) if annotation else "string"
                    example[name] = f"<{type_name}: {desc}>"
            return example

        example_dict = generate_example_dict(response_model)
        example_json = json.dumps(example_dict, indent=2)
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)

        # Inject structured output instruction into the last system message
        structured_instruction = (
            "\n\n[STRUCTURED OUTPUT REQUIREMENT]\n"
            "You MUST respond with ONLY a valid JSON object matching this example structure:\n"
            f"```json\n{example_json}\n```\n"
            "Here is the formal Pydantic schema for validation:\n"
            f"```json\n{schema_json}\n```\n"
            "Do NOT return the schema definition itself. Replace all placeholders (like <type: description>) with your actual, generated content.\n"
            "Do NOT include any text before or after the JSON. "
            "Do NOT wrap in markdown code fences."
        )

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
            temperature=temperature or 0.4,
            max_tokens=self._default_max_tokens,
        )

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
