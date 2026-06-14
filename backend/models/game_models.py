"""
DreamXV AI Studio — Internal Game Data Models
=============================================
Models used internally during agent processing.
These are not directly exposed via the API.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class GameGenre(BaseModel):
    """Identified game genre and sub-genres."""
    primary: str = Field(..., description="Primary genre (RPG, Platformer, etc.)")
    sub_genres: list[str] = Field(default_factory=list, description="Sub-genre tags")
    tone: str = Field(default="", description="Overall tone (dark, whimsical, epic…)")


class AgentMessage(BaseModel):
    """A message exchanged within a Band room between agents."""
    sender: str = Field(..., description="Agent name that sent the message")
    recipient: str = Field(default="room", description="Target agent or 'room' for broadcast")
    content: str = Field(..., description="Message content (may be JSON-encoded)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_type: str = Field(
        default="text",
        description="Message type: text, directive, result, error",
    )


class ProjectContext(BaseModel):
    """Shared context passed through the agent pipeline."""
    project_id: str
    user_prompt: str
    genre: Optional[GameGenre] = None
    messages: list[AgentMessage] = Field(default_factory=list)

    def add_message(self, sender: str, content: str, msg_type: str = "text") -> None:
        """Append a message to the context log."""
        self.messages.append(
            AgentMessage(sender=sender, content=content, message_type=msg_type)
        )

    def get_messages_for(self, agent_name: str) -> list[AgentMessage]:
        """Get all messages relevant to a specific agent."""
        return [
            m for m in self.messages
            if m.recipient in (agent_name, "room")
        ]


class ImageRequest(BaseModel):
    """Internal request for image generation."""
    prompt: str = Field(..., description="Image generation prompt")
    image_type: str = Field(
        default="character",
        description="Type: character, environment, cover",
    )
    project_id: str = Field(..., description="Associated project ID")
    filename: Optional[str] = Field(
        default=None,
        description="Override filename (auto-generated if None)",
    )
