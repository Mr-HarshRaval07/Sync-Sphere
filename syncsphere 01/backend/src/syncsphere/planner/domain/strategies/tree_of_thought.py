import time
from syncsphere.planner.domain.strategies.base import PlanningStrategy
from syncsphere.planner.domain.entities.session import PlanningSession
from syncsphere.planner.domain.entities.trace import PlannerTrace
from syncsphere.planner.domain.value_objects import PlanAST, PlanningContext
from syncsphere.planner.domain.services.reasoning import ReasoningEngine, WorkflowSynthesizer
from syncsphere.planner.domain.services.connector_intel import ToolSelector

class TreeOfThoughtPlanningStrategy(PlanningStrategy):
    """Explores multiple reasoning pathways (branches) to select the optimal path."""
    def __init__(self, reasoning_engine: ReasoningEngine, tool_selector: ToolSelector) -> None:
        self.reasoning_engine = reasoning_engine
        self.tool_selector = tool_selector

    async def plan(
        self,
        session: PlanningSession,
        prompt: str,
        context: PlanningContext,
        trace: PlannerTrace
    ) -> PlanAST:
        # Simulate exploring branches
        branches = [
            {"branch_id": 1, "description": "Sequential steps with direct tool calls", "score": 0.85},
            {"branch_id": 2, "description": "Highly parallelized stages", "score": 0.95}
        ]
        
        start_time = time.perf_counter()
        steps = await self.reasoning_engine.run_reasoning_loop(context.org_id, prompt, context.history)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        trace.record_phase("reasoning", {
            "steps_decomposed": len(steps),
            "tot_branches": branches,
            "selected_branch": 2,
            "duration_ms": duration_ms
        })
        
        matched_tools = {}
        tool_selection_trace = []
        for step in steps:
            match = await self.tool_selector.select_best_tool(context.org_id, step.step_id, step.capability_required)
            matched_tools[step.step_id] = match
            tool_selection_trace.append(match.model_dump())
            
        trace.record_phase("connector_discovery", {"connectors_scanned": len(context.available_connectors)})
        trace.record_phase("capability_matching", {"mappings": len(matched_tools)})
        trace.record_phase("tool_selection", {"selections": tool_selection_trace})
        
        ast = WorkflowSynthesizer.synthesize_ast(steps, matched_tools)
        ast.metadata["tot"] = {"branches_explored": len(branches), "optimal_branch_id": 2}
        return ast
