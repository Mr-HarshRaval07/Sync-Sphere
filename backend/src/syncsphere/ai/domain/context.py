from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    """Value object representing a single message in a conversation thread."""
    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ContextWindow(BaseModel):
    """ContextWindow evaluates active token usage against model capacity limits."""
    model_name: str
    max_tokens: int
    used_tokens: int = 0

    @property
    def remaining_tokens(self) -> int:
        return max(0, self.max_tokens - self.used_tokens)

    def is_exceeded(self) -> bool:
        return self.used_tokens > self.max_tokens


class HistoryBuilder(BaseModel):
    """
    HistoryBuilder builds structured chat message histories
    for LLM input validation.
    """
    messages: List[ChatMessage] = Field(default_factory=list)

    def add_system(self, content: str, name: Optional[str] = None) -> "HistoryBuilder":
        self.messages.append(ChatMessage(role="system", content=content, name=name))
        return self

    def add_user(self, content: str, name: Optional[str] = None) -> "HistoryBuilder":
        self.messages.append(ChatMessage(role="user", content=content, name=name))
        return self

    def add_assistant(self, content: str, name: Optional[str] = None) -> "HistoryBuilder":
        self.messages.append(ChatMessage(role="assistant", content=content, name=name))
        return self

    def add_tool_response(self, content: str, tool_call_id: str, name: Optional[str] = None) -> "HistoryBuilder":
        self.messages.append(ChatMessage(role="tool", content=content, tool_call_id=tool_call_id, name=name))
        return self

    def build(self) -> List[Dict[str, Any]]:
        """Formats the messages to standard API list of dict format."""
        formatted = []
        for msg in self.messages:
            item = {"role": msg.role, "content": msg.content}
            if msg.name:
                item["name"] = msg.name
            if msg.tool_call_id:
                item["tool_call_id"] = msg.tool_call_id
            formatted.append(item)
        return formatted


class ContextManager:
    """
    ContextManager implements context pruning and summarization logic
    when limits are reached.
    """
    def __init__(self, max_context_tokens: int) -> None:
        self.max_context_tokens = max_context_tokens

    def prune_history(self, builder: HistoryBuilder, current_tokens: int) -> HistoryBuilder:
        """
        Prunes message history (removing oldest messages after system prompt)
        to fit inside the allowed context window.
        """
        if current_tokens <= self.max_context_tokens:
            return builder

        # Retain the system message if there is one
        system_msgs = [m for m in builder.messages if m.role == "system"]
        other_msgs = [m for m in builder.messages if m.role != "system"]

        # Basic sliding window pruning: remove the oldest 2 non-system messages until within limit
        while other_msgs and len(other_msgs) > 2:
            other_msgs = other_msgs[2:] # Keep sliding forward
            
        pruned_builder = HistoryBuilder()
        pruned_builder.messages.extend(system_msgs)
        pruned_builder.messages.extend(other_msgs)
        return pruned_builder

    def build_summary_instruction(self, conversation_history: List[ChatMessage]) -> str:
        """Constructs instructions to summarize history to compress token footprint."""
        serialized = "\n".join([f"{m.role}: {m.content}" for m in conversation_history])
        return f"Summarize the following chat history concisely, preserving all key decisions, tools, inputs, and results:\n\n{serialized}"
