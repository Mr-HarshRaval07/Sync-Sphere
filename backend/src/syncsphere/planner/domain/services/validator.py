import logging
from typing import List, Dict, Any
from syncsphere.shared_kernel.domain.domain_exception import ValidationException
from syncsphere.planner.domain.value_objects import PlanAST, ConfidenceScore, RiskAssessment
from syncsphere.workflow.domain.entities.workflow import Workflow
from syncsphere.workflow.infrastructure.dag.validator import DAGValidator

logger = logging.getLogger("syncsphere.planner.domain.services.validator")

class CycleValidator:
    """Ensures no cyclical dependencies exist within the workflow graph."""
    @staticmethod
    def validate_cycles(workflow: Workflow) -> None:
        try:
            DAGValidator.validate(workflow.graph, workflow.variables)
        except Exception as e:
            raise ValidationException("CYCLE_DETECTED", f"Workflow has circular references: {str(e)}")


class VariableValidator:
    """Validates parameter types and input binding bindings compatibility."""
    @staticmethod
    def validate_variables(workflow: Workflow) -> None:
        # Check that target bindings map to existing parameters
        node_ids = set(workflow.graph.nodes.keys())
        for nid, node in workflow.graph.nodes.items():
            for binding in node.input_bindings:
                if binding.source_node_id not in node_ids:
                    raise ValidationException(
                        "INVALID_BINDING",
                        f"Step '{nid}' attempts to bind input from non-existent step '{binding.source_node_id}'"
                    )


class CostValidator:
    """Checks cost thresholds against organization quotas."""
    @staticmethod
    def validate_cost(estimated_cost: float, max_quota: float = 10.0) -> None:
        if estimated_cost > max_quota:
            raise ValidationException(
                "COST_LIMIT_EXCEEDED",
                f"Estimated planning execution cost (${estimated_cost}) exceeds organization budget threshold (${max_quota})"
            )


class ConfidenceValidator:
    """Enforces minimum confidence scoring limits."""
    @staticmethod
    def validate_confidence(score: ConfidenceScore, min_threshold: float = 0.6) -> None:
        if score.overall_confidence < min_threshold:
            raise ValidationException(
                "LOW_CONFIDENCE",
                f"Overall planner confidence ({score.overall_confidence}) is below safety threshold ({min_threshold})"
            )


class RiskValidator:
    """Validates plan safety parameters."""
    @staticmethod
    def validate_risk(risk: RiskAssessment) -> None:
        if risk.safety_score < 0.5:
            raise ValidationException(
                "HIGH_RISK_PLAN",
                f"Plan safety score too low ({risk.safety_score}) due to destructive actions: {', '.join(risk.identified_risks)}"
            )


class WorkflowValidator:
    """Consolidated orchestrator validating cycle, variables, cost, and safety limits."""
    @staticmethod
    def validate_workflow(
        workflow: Workflow,
        confidence: ConfidenceScore,
        risk: RiskAssessment,
        estimated_cost: float
    ) -> None:
        CycleValidator.validate_cycles(workflow)
        VariableValidator.validate_variables(workflow)
        ConfidenceValidator.validate_confidence(confidence)
        RiskValidator.validate_risk(risk)
        CostValidator.validate_cost(estimated_cost)
