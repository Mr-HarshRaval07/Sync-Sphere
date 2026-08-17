from abc import ABC, abstractmethod
from syncsphere.planner.domain.entities.session import PlanningSession
from syncsphere.planner.domain.entities.trace import PlannerTrace
from syncsphere.planner.domain.value_objects import PlanningContext
from syncsphere.workflow.domain.entities.workflow import Workflow

class PlanningPipeline(ABC):
    """Orchestrates all planning phases: intent, matching, reasoning, compiling, optimizing, and validation."""
    
    @abstractmethod
    async def execute(
        self,
        session: PlanningSession,
        prompt: str,
        context: PlanningContext,
        strategy_name: str,
        trace: PlannerTrace
    ) -> Workflow:
        """Runs the sequential pipeline phases, returning a generated Workflow aggregate."""
        pass
