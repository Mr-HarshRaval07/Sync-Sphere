import logging
from typing import Any, Dict, List, Optional
from syncsphere.approval.domain.entities.approval_policy import ApprovalPolicy
from syncsphere.approval.domain.value_objects import (
    ApprovalRule,
    ApprovalCondition,
    ApprovalContext,
    ApprovalPolicyType
)

logger = logging.getLogger("syncsphere.approval.application.services.rule_engine")

class ConditionEvaluator:
    @staticmethod
    def evaluate(condition: ApprovalCondition, variables: Dict[str, Any]) -> bool:
        """Evaluates a single condition against context variables."""
        left = variables.get(condition.left_operand)
        if left is None:
            # Fallback direct string compare if left not in vars
            left = condition.left_operand
            
        right = condition.right_operand
        op = condition.operator.upper()
        
        try:
            if op == "EQUAL":
                return str(left) == str(right)
            elif op == "NOT_EQUAL":
                return str(left) != str(right)
            elif op == "GREATER_THAN":
                return float(left) > float(right)
            elif op == "LESS_THAN":
                return float(left) < float(right)
            elif op == "CONTAINS":
                return str(right) in str(left)
        except Exception as e:
            logger.warning("Condition evaluation failed: %s (left: %s, op: %s, right: %s)", e, left, op, right)
            return False
            
        return False


class ApprovalRuleEngine:
    """Evaluates cost thresholds, risk scores, operations, and general conditions."""
    
    @staticmethod
    def evaluate_rule(rule: ApprovalRule, context: ApprovalContext) -> bool:
        """Determines if a rule matches the provided approval context."""
        # 1. Cost Based Policy check
        if rule.policy_type == ApprovalPolicyType.COST_BASED:
            if context.cost is not None and rule.cost_threshold is not None:
                return context.cost >= rule.cost_threshold
                
        # 2. Risk Based Policy check
        if rule.policy_type == ApprovalPolicyType.RISK_BASED:
            risk_levels = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
            ctx_level = risk_levels.get(context.risk_level or "LOW", 1)
            rule_level = risk_levels.get(rule.risk_threshold or "LOW", 1)
            return ctx_level >= rule_level
            
        # 3. Sensitive Operation check
        if rule.policy_type == ApprovalPolicyType.SENSITIVE_OPERATION:
            if context.operation_name and rule.conditions:
                # Must match operation condition (e.g. op == 'delete_db')
                return any(ConditionEvaluator.evaluate(c, {"operation": context.operation_name}) for c in rule.conditions)
                
        # 4. Connector/Resource/Workflow/Org rules evaluate general conditions list
        if rule.conditions:
            return all(ConditionEvaluator.evaluate(cond, context.variables) for cond in rule.conditions)
            
        return False

    @staticmethod
    def resolve_matching_policies(
        policies: List[ApprovalPolicy],
        context: ApprovalContext
    ) -> List[ApprovalPolicy]:
        """Filters the policies list to those where at least one rule evaluates to True."""
        matched = []
        for policy in policies:
            for rule in policy.rules:
                if ApprovalRuleEngine.evaluate_rule(rule, context):
                    matched.append(policy)
                    break
        return matched
