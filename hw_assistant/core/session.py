"""Session and conversation memory manager with hardware fact caching."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message text")
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ConversationSession:
    """Maintains multi-turn context and cached hardware data across an interactive session."""

    def __init__(self):
        self.messages: List[ChatMessage] = []
        self.cached_hardware_facts: Dict[str, Any] = {}

    def add_user_message(self, content: str) -> None:
        self.messages.append(ChatMessage(role="user", content=content))

    def add_assistant_message(self, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> None:
        self.messages.append(ChatMessage(role="assistant", content=content, tool_calls=tool_calls))

    def cache_tool_data(self, tool_name: str, data: Dict[str, Any]) -> None:
        """Caches hardware data to allow follow-up questions to resolve without re-executing binaries."""
        self.cached_hardware_facts[tool_name] = data

    def get_cached_tool_data(self, tool_name: str) -> Optional[Dict[str, Any]]:
        return self.cached_hardware_facts.get(tool_name)

    def clear(self) -> None:
        self.messages.clear()
        self.cached_hardware_facts.clear()
