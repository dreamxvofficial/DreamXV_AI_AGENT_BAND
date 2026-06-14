"""
DreamXV AI Studio — Helper Utilities
====================================
Common utility functions used across the backend.
"""

from __future__ import annotations

import uuid
import re
from pathlib import Path
from typing import Optional


def load_prompt(prompt_name: str, prompts_dir: Optional[Path] = None) -> str:
    """
    Load a system prompt from the prompts/ directory.

    Args:
        prompt_name: Filename without extension (e.g. "chief_prompt")
        prompts_dir: Override path to prompts directory

    Returns:
        The prompt text content.

    Raises:
        FileNotFoundError: If the prompt file does not exist.
    """
    if prompts_dir is None:
        prompts_dir = Path(__file__).resolve().parent.parent / "prompts"

    # Accept with or without .txt extension
    if not prompt_name.endswith(".txt"):
        prompt_name = f"{prompt_name}.txt"

    prompt_path = prompts_dir / prompt_name

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8").strip()


def generate_project_id() -> str:
    """Generate a unique project identifier."""
    short_id = uuid.uuid4().hex[:12]
    return f"dxv-{short_id}"


def sanitize_filename(name: str, max_length: int = 64) -> str:
    """
    Sanitize a string for use as a filename.

    Removes special characters, replaces spaces with underscores,
    and truncates to max_length.
    """
    # Replace spaces and common separators with underscores
    clean = re.sub(r"[\s\-]+", "_", name)
    # Remove anything that isn't alphanumeric or underscore
    clean = re.sub(r"[^\w]", "", clean)
    # Lowercase and truncate
    return clean.lower()[:max_length]


def truncate_text(text: str, max_chars: int = 500) -> str:
    """Truncate text to a maximum character count with ellipsis."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 3] + "..."


def build_chat_messages(
    system_prompt: str,
    user_message: str,
    context: Optional[str] = None,
) -> list[dict[str, str]]:
    """
    Build an OpenAI-compatible chat messages list.

    Args:
        system_prompt: The system instruction.
        user_message: The user's input.
        context: Optional additional context injected as assistant prelude.

    Returns:
        List of message dicts for the chat completions API.
    """
    messages = [{"role": "system", "content": system_prompt}]

    if context:
        messages.append({
            "role": "assistant",
            "content": f"[Context from prior agents]\n{context}",
        })

    messages.append({"role": "user", "content": user_message})
    return messages
