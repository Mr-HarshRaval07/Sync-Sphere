import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from syncsphere.approval.domain.value_objects import (
    ApprovalChain,
    ApprovalStage,
    ApprovalAssignment,
    ApprovalDecisionType,
    ApprovalRule,
    ApprovalCondition,
    ApprovalContext,
    ApprovalPolicyType,
    RoutingStrategyType,
    DelegationType,
    ApprovalSLA,
    ApprovalEscalation
)
from syncsphere.approval.domain.entities.approval_request import ApprovalRequest
from syncsphere.approval.domain.entities.approval_delegate import ApprovalDelegate
from syncsphere.approval.domain.entities.approval_policy import ApprovalPolicy
from syncsphere.approval.domain.entities.approval_template import ApprovalTemplate
from syncsphere.approval.domain.exceptions import (
    UnauthorizedApproverException,
    DelegationCycleException,
    InvalidDecisionException
)
from syncsphere.approval.application.services.rule_engine import ApprovalRuleEngine
from syncsphere.approval.application.services.assignment import DelegationResolver, ApproverResolver
from syncsphere.approval.application.services.sla import SLAService
from syncsphere.approval.application.services.escalation import EscalationService
from tests.mocks import (
    InMemoryUserRepository,
    InMemoryOrgRepository
)

# 1. Rule Engine Tests
def test_rule_engine_cost_policy():
    rule = ApprovalRule(
        rule_id="r1",
        name="Cost Threshold",
        policy_type=ApprovalPolicyType.COST_BASED,
        cost_threshold=5000.0
    )
    context_match = ApprovalContext(cost=6000.0)
    context_fail = ApprovalContext(cost=4000.0)
    
    assert ApprovalRuleEngine.evaluate_rule(rule, context_match) is True
    assert ApprovalRuleEngine.evaluate_rule(rule, context_fail) is False

def test_rule_engine_risk_policy():
    rule = ApprovalRule(
        rule_id="r2",
        name="Risk Threshold",
        policy_type=ApprovalPolicyType.RISK_BASED,
        risk_threshold="MEDIUM"
    )
    context_match = ApprovalContext(risk_level="HIGH")
    context_fail = ApprovalContext(risk_level="LOW")
    
    assert ApprovalRuleEngine.evaluate_rule(rule, context_match) is True
    assert ApprovalRuleEngine.evaluate_rule(rule, context_fail) is False

def test_rule_engine_condition_evaluator():
    rule = ApprovalRule(
        rule_id="r3",
        name="Sensitive Operation",
        policy_type=ApprovalPolicyType.SENSITIVE_OPERATION,
        conditions=[
            ApprovalCondition(left_operand="operation", operator="EQUAL", right_operand="delete_db")
        ]
    )
    context_match = ApprovalContext(operation_name="delete_db")
    context_fail = ApprovalContext(operation_name="read_db")
    
    assert ApprovalRuleEngine.evaluate_rule(rule, context_match) is True
    assert ApprovalRuleEngine.evaluate_rule(rule, context_fail) is False


# 2. Routing Strategy Tests
def test_sequential_routing_strategy():
    assignments = [
        ApprovalAssignment(user_id="user_a", weight=1.0),
        ApprovalAssignment(user_id="user_b", weight=1.0)
    ]
    stage = ApprovalStage(
        stage_id="s1",
        name="Stage 1",
        order=1,
        routing_strategy=RoutingStrategyType.SEQUENTIAL,
        assignments=assignments
    )
    chain = ApprovalChain(stages=[stage])
    request = ApprovalRequest(org_id="org_1", title="Seq Flow", chain=chain)
    
    # 1 approver votes APPROVE -> Stage is not complete yet
    request.submit_decision("user_a", ApprovalDecisionType.APPROVE)
    assert request.status == "ACTIVE"
    assert request.chain.current_stage_index == 0
    
    # 2nd approver votes APPROVE -> Stage completes and request is approved (since only 1 stage)
    request.submit_decision("user_b", ApprovalDecisionType.APPROVE)
    assert request.status == "APPROVED"
    assert request.completed_at is not None

def test_majority_routing_strategy():
    assignments = [
        ApprovalAssignment(user_id="user_a", weight=1.0),
        ApprovalAssignment(user_id="user_b", weight=1.0),
        ApprovalAssignment(user_id="user_c", weight=1.0)
    ]
    stage = ApprovalStage(
        stage_id="s1",
        name="Stage 1",
        order=1,
        routing_strategy=RoutingStrategyType.MAJORITY,
        assignments=assignments
    )
    chain = ApprovalChain(stages=[stage])
    request = ApprovalRequest(org_id="org_1", title="Majority Flow", chain=chain)
    
    request.submit_decision("user_a", ApprovalDecisionType.APPROVE)
    assert request.status == "ACTIVE" # 1/3 is not majority
    
    request.submit_decision("user_b", ApprovalDecisionType.APPROVE)
    assert request.status == "APPROVED" # 2/3 is majority!

def test_weighted_routing_strategy():
    assignments = [
        ApprovalAssignment(user_id="user_vp", weight=3.0),
        ApprovalAssignment(user_id="user_lead", weight=1.0)
    ]
    stage = ApprovalStage(
        stage_id="s1",
        name="Stage 1",
        order=1,
        routing_strategy=RoutingStrategyType.WEIGHTED,
        assignments=assignments
    )
    chain = ApprovalChain(stages=[stage])
    request = ApprovalRequest(org_id="org_1", title="Weighted Flow", chain=chain)
    
    # VP votes APPROVE (weight 3 > total 4 / 2) -> Stage completes immediately!
    request.submit_decision("user_vp", ApprovalDecisionType.APPROVE)
    assert request.status == "APPROVED"


# 3. Delegation & Cycle Prevention Tests
def test_delegation_resolution():
    delegates = [
        ApprovalDelegate(org_id="org_1", from_user_id="user_a", to_user_id="user_b", delegation_type=DelegationType.PERMANENT),
        ApprovalDelegate(org_id="org_1", from_user_id="user_b", to_user_id="user_c", delegation_type=DelegationType.PERMANENT)
    ]
    
    # Resolves user_a to user_c recursively
    final_user = DelegationResolver.resolve_delegate("org_1", "user_a", delegates)
    assert final_user == "user_c"

def test_delegation_cycle_prevention():
    delegates = [
        ApprovalDelegate(org_id="org_1", from_user_id="user_a", to_user_id="user_b", delegation_type=DelegationType.PERMANENT),
        ApprovalDelegate(org_id="org_1", from_user_id="user_b", to_user_id="user_a", delegation_type=DelegationType.PERMANENT)
    ]
    
    with pytest.raises(DelegationCycleException):
        DelegationResolver.resolve_delegate("org_1", "user_a", delegates)


# 4. SLA & Escalation Tests
def test_sla_compliance_and_escalation():
    sla = ApprovalSLA(duration_seconds=5000, remaining_seconds=5000.0)
    escalation_policy = [
        ApprovalEscalation(escalation_level=1, assigned_user_id="user_vp")
    ]
    assignments = [ApprovalAssignment(user_id="user_lead")]
    stage = ApprovalStage(
        stage_id="s1",
        name="Stage 1",
        order=1,
        routing_strategy=RoutingStrategyType.FIRST_RESPONSE,
        assignments=assignments
    )
    chain = ApprovalChain(stages=[stage])
    request = ApprovalRequest(
        org_id="org_1",
        title="Escalated Flow",
        chain=chain,
        sla=sla,
        escalation_policy=escalation_policy
    )
    request.activate()
    
    # Trigger SLA check with creation time modified back in time
    request.created_at = datetime.utcnow() - timedelta(seconds=6000)
    
    # 1. SLA overdue detection
    breached = SLAService.evaluate_sla_status(request)
    assert breached is True
    assert request.sla.is_overdue is True
    
    # 2. Escalation trigger
    escalated = EscalationService.escalate_request_if_breached(request)
    assert escalated is True
    assert request.escalation_count == 1
    
    # Assert assignment shifted to VP
    active_stage = request.chain.stages[0]
    assert active_stage.assignments[0].user_id == "user_vp"

