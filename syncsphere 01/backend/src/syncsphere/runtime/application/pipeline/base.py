from abc import ABC, abstractmethod
from syncsphere.runtime.domain.entities.session import ExecutionSession
from syncsphere.runtime.domain.entities.trace import ExecutionTrace

class ExecutionPipeline(ABC):
    """
    Abstract interface for executing execution sessions.
    The Pipeline orchestrates stages sequentially:
    Queue -> Dependency Resolution -> Scheduling -> Dispatch -> Execution -> Checkpoint -> Metrics -> Completion
    """
    
    @abstractmethod
    async def execute(self, session: ExecutionSession, trace: ExecutionTrace) -> None:
        """Executes the pipeline stages for the given session."""
        pass
