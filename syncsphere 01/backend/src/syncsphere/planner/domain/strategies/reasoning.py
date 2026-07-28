import time
from syncsphere.planner.domain.strategies.base import PlanningStrategy
from syncsphere.planner.domain.entities.session import PlanningSession
from syncsphere.planner.domain.entities.trace import PlannerTrace
from syncsphere.planner.domain.value_objects import PlanAST, PlanningContext, ReasoningStep
from syncsphere.planner.domain.services.reasoning import ReasoningEngine, WorkflowSynthesizer
from syncsphere.planner.domain.services.connector_intel import ToolSelector

class ReasoningPlanningStrategy(PlanningStrategy):
    """Executes stateful Chain-of-Thought (CoT) reasoning, logging step thought loops."""
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
        # Simulate chain of thought reasoning logs
        cot_steps = [
            ReasoningStep(step_index=1, thought="Decompose prompt into required tools.", action="Decompose prompt"),
            ReasoningStep(step_index=2, thought="Identify necessary connector tools with matching capabilities.", action="Match connectors")
        ]
        
        start_time = time.perf_counter()
        steps = await self.reasoning_engine.run_reasoning_loop(context.org_id, prompt, context.history)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        trace.record_phase("reasoning", {
            "steps_decomposed": len(steps),
            "cot_trace": [c.model_dump() for c in cot_steps],
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
        return ast
