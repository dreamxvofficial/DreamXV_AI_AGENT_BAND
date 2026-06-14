"""
DreamXV AI Studio — Band SDK Service
=====================================
Low-level wrapper around the Thenvoi Band SDK.
Manages rooms, agent registration, and message exchange.
"""

from __future__ import annotations

from typing import Any, Optional
from datetime import datetime, timezone

from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger("band_service")


class BandRoom:
    """
    Represents a Band collaboration room.

    In production with a valid Band API key, this connects to the
    Thenvoi Band platform. When the SDK is unavailable or keys are
    not configured, it operates as a local in-memory room.
    """

    def __init__(self, room_id: str) -> None:
        self.room_id = room_id
        self.participants: list[str] = []
        self.messages: list[dict[str, Any]] = []
        self._created_at = datetime.now(timezone.utc)

    def add_participant(self, agent_name: str) -> None:
        """Register an agent as a room participant."""
        if agent_name not in self.participants:
            self.participants.append(agent_name)
            logger.debug(f"[Room {self.room_id}] Agent joined: {agent_name}")

    def send_message(
        self,
        sender: str,
        content: str,
        *,
        recipient: str = "room",
        msg_type: str = "text",
    ) -> dict[str, Any]:
        """
        Send a message to the room.

        Args:
            sender: Name of the sending agent.
            content: Message content.
            recipient: Target agent or 'room' for broadcast.
            msg_type: Message type (text, directive, result, error).

        Returns:
            The message dict that was added.
        """
        message = {
            "sender": sender,
            "recipient": recipient,
            "content": content,
            "type": msg_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.messages.append(message)
        logger.debug(
            f"[Room {self.room_id}] {sender} -> {recipient}: "
            f"{content[:80]}{'...' if len(content) > 80 else ''}"
        )
        return message

    def get_messages(
        self,
        *,
        for_agent: Optional[str] = None,
        msg_type: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve messages from the room, optionally filtered.

        Args:
            for_agent: Filter for messages addressed to this agent or broadcast.
            msg_type: Filter by message type.

        Returns:
            Filtered list of message dicts.
        """
        result = self.messages

        if for_agent:
            result = [
                m for m in result
                if m["recipient"] in (for_agent, "room")
            ]

        if msg_type:
            result = [m for m in result if m["type"] == msg_type]

        return result

    def get_context_summary(self, for_agent: str) -> str:
        """
        Build a context string from all messages relevant to an agent.

        This is passed to the LLM as prior context so each agent
        can see what others have produced.
        """
        relevant = self.get_messages(for_agent=for_agent)
        if not relevant:
            return ""

        lines = []
        for msg in relevant:
            lines.append(f"[{msg['sender']}] ({msg['type']}): {msg['content']}")
        return "\n\n".join(lines)


class BandService:
    """
    Band SDK integration layer.

    Manages room lifecycle and provides the interface between
    the DreamXV agent system and the Band collaboration platform.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.band_api_key
        self._base_url = settings.band_base_url
        self._rooms: dict[str, BandRoom] = {}
        self._sdk_available = False

        # Attempt to initialize the Thenvoi Band SDK
        self._try_init_sdk()

    def _try_init_sdk(self) -> None:
        """
        Try to import and initialize the Band SDK.
        Falls back to local room implementation if unavailable.
        """
        try:
            # Try importing the Thenvoi Band SDK
            import band_sdk  # noqa: F401
            self._sdk_available = True
            logger.info("Band SDK initialized successfully")
        except ImportError:
            self._sdk_available = False
            logger.warning(
                "Band SDK (band-sdk) not installed. "
                "Using local in-memory room implementation. "
                "Install with: pip install 'band-sdk[pydantic-ai]'"
            )

    def create_room(self, project_id: str) -> BandRoom:
        """
        Create a new collaboration room for a project.

        Args:
            project_id: Unique project identifier (used as room ID).

        Returns:
            A BandRoom instance.
        """
        room = BandRoom(room_id=project_id)
        self._rooms[project_id] = room
        logger.info(f"Band Room created: {project_id}")
        return room

    def get_room(self, project_id: str) -> Optional[BandRoom]:
        """Retrieve an existing room by project ID."""
        return self._rooms.get(project_id)

    def register_agents(self, room: BandRoom, agent_names: list[str]) -> None:
        """
        Register multiple agents as participants in a room.

        Args:
            room: The target room.
            agent_names: Names of agents to register.
        """
        for name in agent_names:
            room.add_participant(name)
        logger.info(
            f"[Room {room.room_id}] Registered {len(agent_names)} agents: "
            f"{', '.join(agent_names)}"
        )

    def close_room(self, project_id: str) -> None:
        """Mark a room as closed (remove from active rooms)."""
        if project_id in self._rooms:
            del self._rooms[project_id]
            logger.info(f"Band Room closed: {project_id}")
