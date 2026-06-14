"""
DreamXV AI Studio — Input Validators
====================================
Validation logic for project generation requests.
"""

from __future__ import annotations

import re
from typing import Optional


# ─── Forbidden content patterns ────────────────────────────────────────────
_BLOCKED_PATTERNS: list[str] = [
    r"(?i)\b(hack|exploit|inject|drop\s+table)\b",
]


def validate_prompt(prompt: str) -> tuple[bool, Optional[str]]:
    """
    Validate a user-submitted project prompt.

    Returns:
        (is_valid, error_message) — error_message is None when valid.
    """
    # --- Length checks ---
    if not prompt or len(prompt.strip()) < 10:
        return False, "Prompt must be at least 10 characters long."

    if len(prompt) > 5000:
        return False, "Prompt exceeds maximum length of 5,000 characters."

    # --- Content safety ---
    for pattern in _BLOCKED_PATTERNS:
        if re.search(pattern, prompt):
            return False, "Prompt contains disallowed content."

    return True, None


def validate_user_id(user_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate a user ID string.

    Returns:
        (is_valid, error_message)
    """
    if not user_id or len(user_id.strip()) == 0:
        return False, "User ID is required."

    if len(user_id) > 128:
        return False, "User ID exceeds maximum length."

    return True, None
