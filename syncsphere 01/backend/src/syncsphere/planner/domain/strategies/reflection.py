import time
from syncsphere.planner.domain.strategies.base import PlanningStrategy
from syncsphere.planner.domain.entities.session import PlanningSession
from syncsphere.planner.domain.entities.trace import PlannerTrace
from syncsphere.planner.domain.value_objects import PlanAST, PlanningContext
from syncsphere.planner.domain.services.reasoning import ReasoningEngine, WorkflowSynthesizer, PlannerReflectionEngine
from syncsphere.planner.domain.services.connector_intel import ToolSelector

class ReflectionPlanningStrategy(PlanningStrategy):
    """Executes a dual-loop planning process: generation followed by self-critique/improvement."""
    def __init__(
        self,
        reasoning_engine: ReasoningEngine,
        tool_selector: ToolSelector,
        reflection_engine: PlannerReflectionEngine
    ) -> None:
        self.reasoning_engine = reasoning_engine
        self.tool_selector = tool_selector
        self.reflection_engine = reflection_engine

    async def plan(
        self,
        session: PlanningSession,
        prompt: str,
        context: PlanningContext,
        trace: PlannerTrace
    ) -> PlanAST:
        # Loop 1: Generate initial AST
        start_time = time.perf_counter()
        steps = await self.reasoning_engine.run_reasoning_loop(context.org_id, prompt, context.history)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        matched_tools = {}
        tool_selection_trace = []
        for step in steps:
            match = await self.tool_selector.select_best_tool(context.org_id, step.step_id, step.capability_required)
            matched_tools[step.step_id] = match
            tool_selection_trace.append(match.model_dump())
            
        ast = WorkflowSynthesizer.synthesize_ast(steps, matched_tools)
        
        # Loop 2: Reflect/Self-Critique
        reflection_start = time.perf_counter()
        critique = await self.reflection_engine.reflect(context.org_id, ast)
        reflection_duration = (time.perf_counter() - reflection_start) * 1000.0
        
        trace.record_phase("reasoning", {
            "steps_decomposed": len(steps),
            "reflection_critique": critique,
            "duration_ms": duration_ms + reflection_duration
        })
        trace.record_phase("connector_discovery", {"connectors_scanned": len(context.available_connectors)})
        trace.record_phase("capability_matching", {"mappings": len(matched_tools)})
        trace.record_phase("tool_selection", {"selections": tool_selection_trace})
        
        # Apply critique suggestions to metadata
        ast.metadata["reflection"] = {
            "risk_assessment": critique["risk_assessment"].model_dump(),
            "recommendations": critique["recommendations"]
        }
        
        return ast
