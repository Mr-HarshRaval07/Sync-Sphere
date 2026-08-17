import time
from typing import Dict, Any, List
from syncsphere.planner.domain.pipeline.base import PlanningPipeline
from syncsphere.planner.domain.entities.session import PlanningSession
from syncsphere.planner.domain.entities.trace import PlannerTrace
from syncsphere.planner.domain.value_objects import (
    PlanningContext,
    ConfidenceScore,
    RiskAssessment,
    PlanningExplanation,
    PlanningMetrics,
    UserIntent
)
from syncsphere.planner.domain.services.intent import (
    IntentClassifier,
    EntityExtractor,
    GoalExtractor,
    ConstraintExtractor
)
from syncsphere.planner.domain.services.compiler import WorkflowCompiler
from syncsphere.planner.domain.services.optimizer import GraphOptimizer
from syncsphere.planner.domain.services.validator import WorkflowValidator
from syncsphere.planner.domain.strategies.base import PlanningStrategy
from syncsphere.workflow.domain.entities.workflow import Workflow

class DefaultPlanningPipeline(PlanningPipeline):
    """Orchestrates intent parsing, strategy execution, compilation, optimization, and validation."""
    
    def __init__(
        self,
        intent_classifier: IntentClassifier,
        entity_extractor: EntityExtractor,
        goal_extractor: GoalExtractor,
        constraint_extractor: ConstraintExtractor,
        strategies: Dict[str, PlanningStrategy],
        validator: WorkflowValidator
    ) -> None:
        self.intent_classifier = intent_classifier
        self.entity_extractor = entity_extractor
        self.goal_extractor = goal_extractor
        self.constraint_extractor = constraint_extractor
        self.strategies = strategies
        self.validator = validator

    async def execute(
        self,
        session: PlanningSession,
        prompt: str,
        context: PlanningContext,
        strategy_name: str,
        trace: PlannerTrace
    ) -> tuple:
        start_time = time.perf_counter()
        
        # 1. Intent Recognition
        intent_start = time.perf_counter()
        classification = await self.intent_classifier.classify(context.org_id, prompt)
        intent_duration = (time.perf_counter() - intent_start) * 1000.0
        trace.record_phase("intent_recognition", {
            "classification": classification.model_dump(),
            "duration_ms": intent_duration
        })
        
        # 2. Entity & Goal & Constraint Extraction
        extraction_start = time.perf_counter()
        entities = await self.entity_extractor.extract(context.org_id, prompt)
        goals = await self.goal_extractor.extract_goals(context.org_id, prompt)
        constraints = await self.constraint_extractor.extract_constraints(context.org_id, prompt)
        extraction_duration = (time.perf_counter() - extraction_start) * 1000.0
        
        trace.record_phase("entity_extraction", {
            "entities": [e.model_dump() for e in entities],
            "duration_ms": extraction_duration
        })
        trace.record_phase("goal_extraction", {
            "goals": [g.model_dump() for g in goals],
            "constraints": [c.model_dump() for c in constraints],
            "duration_ms": extraction_duration
        })
        
        # 3. Strategy Selection & Execution
        strategy = self.strategies.get(strategy_name)
        if not strategy:
            raise ValueError(f"Selected strategy '{strategy_name}' is not registered in pipeline.")
            
        ast = await strategy.plan(session, prompt, context, trace)
        
        # 4. Graph Optimization Passes
        opt_start = time.perf_counter()
        optimized_nodes, cost_saved, latency_saved = GraphOptimizer.optimize_graph(ast)
        opt_duration = (time.perf_counter() - opt_start) * 1000.0
        trace.record_phase("optimization", {
            "nodes_optimized": optimized_nodes,
            "cost_saved": cost_saved,
            "latency_saved_ms": latency_saved,
            "duration_ms": opt_duration
        })
        
        # 5. Workflow compilation
        comp_start = time.perf_counter()
        
        # Determine risk assessment
        risk_info = ast.metadata.get("reflection", {}).get("risk_assessment", {})
        risk_assessment = RiskAssessment(**risk_info) if risk_info else RiskAssessment()
        
        workflow, version, execution_plan = WorkflowCompiler.compile_workflow(
            org_id=context.org_id,
            name=classification.primary_goal[:64],
            description=f"Auto-generated plan for prompt: {prompt}",
            ast=ast,
            risk_level=risk_assessment.risk_level
        )
        comp_duration = (time.perf_counter() - comp_start) * 1000.0
        trace.record_phase("workflow_compilation", {
            "workflow_id": workflow.id,
            "version": version.version,
            "nodes_compiled": len(workflow.graph.nodes),
            "edges_compiled": len(workflow.graph.edges),
            "duration_ms": comp_duration
        })
        
        # 6. Safety & Confidence validation
        val_start = time.perf_counter()
        
        # Calculate Confidence Scores
        tool_scores = [node.inputs[0].value for node in ast.nodes if node.inputs] # simple proxy
        avg_tool_score = sum(t if isinstance(t, (int, float)) else 0.8 for t in tool_scores) / max(len(tool_scores), 1)
        avg_tool_score = min(max(avg_tool_score, 0.0), 1.0)
        
        confidence = ConfidenceScore(
            intent_confidence=classification.confidence.confidence_score,
            connector_confidence=risk_assessment.safety_score,
            tool_confidence=avg_tool_score,
            step_confidence=avg_tool_score,
            overall_confidence=(classification.confidence.confidence_score + risk_assessment.safety_score + avg_tool_score) / 3.0
        )
        
        # Estimate Cost
        estimated_cost = len(workflow.graph.nodes) * 0.01
        
        self.validator.validate_workflow(workflow, confidence, risk_assessment, estimated_cost)
        val_duration = (time.perf_counter() - val_start) * 1000.0
        trace.record_phase("validation", {
            "is_valid": True,
            "confidence_scores": confidence.model_dump(),
            "risk_assessment": risk_assessment.model_dump(),
            "estimated_cost": estimated_cost,
            "duration_ms": val_duration
        })
        
        # 7. Finalize trace & metrics
        total_duration = (time.perf_counter() - start_time) * 1000.0
        trace.complete(total_duration)
        
        # Bind results to Session
        session.update_intent(UserIntent(raw_prompt=prompt, classification=classification, entities=entities))
        session.update_ast(ast)
        session.update_generated_workflow(workflow.id)
        session.explanation = PlanningExplanation(
            tool_selections={node.node_id: f"Selected tool {node.tool_name}" for node in ast.nodes if node.tool_name},
            approval_gate_reasons={node.id: "Auto-inserted for safety due to destructive command" for node in workflow.graph.nodes.values() if node.type == "approval"},
            risk_rationales=risk_assessment.identified_risks
        )
        session.metrics = PlanningMetrics(
            prompt_tokens=150,
            completion_tokens=250,
            total_cost=estimated_cost,
            planning_time_ms=total_duration
        )
        
        return workflow, version, execution_plan
