from abc import ABC, abstractmethod
from syncsphere.planner.domain.entities.session import PlanningSession
from syncsphere.planner.domain.entities.trace import PlannerTrace
from syncsphere.planner.domain.value_objects import PlanAST, PlanningContext

class PlanningStrategy(ABC):
    """Abstract interface defining the execution structure for a specific planning strategy."""
    
    @abstractmethod
    async def plan(
        self,
        session: PlanningSession,
        prompt: str,
        context: PlanningContext,
        trace: PlannerTrace
    ) -> PlanAST:
        """Executes LLM-based reasoning and capability matching to compile a PlanAST."""
        pass
