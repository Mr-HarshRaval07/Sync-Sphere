from typing import List, Dict, Any, Optional

class ShortTermPlanningMemory:
    """Holds active execution parameters, step thoughts, and temporary planning thoughts."""
    def __init__(self) -> None:
        self._thoughts: List[str] = []
        self._context_variables: Dict[str, Any] = {}

    def add_thought(self, thought: str) -> None:
        self._thoughts.append(thought)

    def get_thoughts(self) -> List[str]:
        return self._thoughts

    def set_variable(self, key: str, value: Any) -> None:
        self._context_variables[key] = value

    def get_variable(self, key: str) -> Any:
        return self._context_variables.get(key)


class ConversationPlanningMemory:
    """Stores sequential dialog messages for a tenant planning session."""
    def __init__(self) -> None:
        self._messages: List[Dict[str, str]] = []

    def append_message(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})

    def get_messages(self) -> List[Dict[str, str]]:
        return self._messages

    def clear(self) -> None:
        self._messages = []


class ReflectionMemory:
    """Saves critique evaluations and validation recommendations from reflection runs."""
    def __init__(self) -> None:
        self._critique_history: List[Dict[str, Any]] = []

    def add_critique(self, critique: Dict[str, Any]) -> None:
        self._critique_history.append(critique)

    def get_latest_critique(self) -> Optional[Dict[str, Any]]:
        return self._critique_history[-1] if self._critique_history else None


class PlanningHistory:
    """Stores past trace execution status mappings for observational replay."""
    def __init__(self) -> None:
        self._trace_logs: List[Dict[str, Any]] = []

    def log_trace(self, trace_id: str, status: str, duration_ms: float) -> None:
        self._trace_logs.append({
            "trace_id": trace_id,
            "status": status,
            "duration_ms": duration_ms
        })

    def get_history(self) -> List[Dict[str, Any]]:
        return self._trace_logs
