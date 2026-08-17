import uuid
from typing import Dict, Any, List, Optional
from syncsphere.shared_kernel.types.result import Result
from syncsphere.approval.domain.entities.approval_request import ApprovalRequest
from syncsphere.approval.domain.entities.approval_policy import ApprovalPolicy
from syncsphere.approval.domain.entities.approval_template import ApprovalTemplate
from syncsphere.approval.domain.value_objects import (
    ApprovalContext,
    ApprovalChain,
    ApprovalStage,
    ApprovalAssignment,
    RoutingStrategyType,
    ApprovalSLA
)
from syncsphere.approval.domain.repositories import (
    ApprovalRequestRepository,
    ApprovalPolicyRepository,
    ApprovalTemplateRepository,
    ApprovalDelegateRepository
)
from syncsphere.approval.application.services.rule_engine import ApprovalRuleEngine
from syncsphere.approval.application.services.assignment import ApproverResolver
from syncsphere.approval.application.services.notification import NotificationService

class ApprovalPipeline:
    """
    Decoupled orchestrator executing the approval setup workflow stages:
    Request Validation -> Policy Resolution -> Routing -> Assignment -> Notification -> Audit.
    """
    
    def __init__(
        self,
        request_repo: ApprovalRequestRepository,
        policy_repo: ApprovalPolicyRepository,
        template_repo: ApprovalTemplateRepository,
        delegate_repo: ApprovalDelegateRepository,
        approver_resolver: ApproverResolver,
        notification_service: NotificationService
    ) -> None:
        self.request_repo = request_repo
        self.policy_repo = policy_repo
        self.template_repo = template_repo
        self.delegate_repo = delegate_repo
        self.approver_resolver = approver_resolver
        self.notification_service = notification_service

    async def execute_creation_flow(
        self,
        org_id: str,
        title: str,
        context_data: Dict[str, Any],
        workflow_id: Optional[str] = None,
        node_id: Optional[str] = None,
        session_id: Optional[str] = None,
        description: Optional[str] = None,
        template_id: Optional[str] = None
    ) -> Result[ApprovalRequest, Exception]:
        """Runs the lifecycle sequence to construct and initialize a human approval request."""
        try:
            # 1. Request Validation
            if not title.strip():
                return Result.fail(ValueError("Approval title cannot be blank."))
                
            # 2. Policy Resolution & Template matching
            target_chain = None
            sla_override = None
            escalations = []
            
            # Map context VO
            context = ApprovalContext(
                variables=context_data,
                operation_name=context_data.get("operation_name"),
                cost=context_data.get("cost"),
                risk_level=context_data.get("risk_level", "LOW"),
                creator_id=context_data.get("creator_id"),
                workflow_id=workflow_id
            )
            
            if template_id:
                # Load preconfigured template (organization-scoped)
                tmpl = await self.template_repo.get_by_id(template_id)
                if tmpl and tmpl.org_id == org_id:
                    target_chain = tmpl.chain
                    
            if not target_chain:
                # Resolve dynamically from matching policies in the organization
                policies = await self.policy_repo.list_by_org(org_id)
                matched = ApprovalRuleEngine.resolve_matching_policies(policies, context)
                if matched:
                    # Use the first matching policy chain configuration
                    target_chain = matched[0].target_chain
                    
            if not target_chain:
                # Default single-stage fallback (assign to admin role so anyone in org can approve in prototype)
                fallback_assignment = ApprovalAssignment(role_id="admin", weight=1.0)
                fallback_stage = ApprovalStage(
                    stage_id="default_lvl_1",
                    name="Default Manager Approval",
                    order=1,
                    routing_strategy=RoutingStrategyType.FIRST_RESPONSE,
                    assignments=[fallback_assignment]
                )
                target_chain = ApprovalChain(stages=[fallback_stage])

            # Copy/instantiate chain to keep it decoupled from template/policy entities
            chain_copy = ApprovalChain(
                stages=[
                    ApprovalStage(
                        stage_id=s.stage_id,
                        name=s.name,
                        order=s.order,
                        routing_strategy=s.routing_strategy,
                        assignments=[ApprovalAssignment(**a.model_dump()) for a in s.assignments],
                        decisions=[]
                    )
                    for s in target_chain.stages
                ],
                current_stage_index=0
            )

            # 3. Dynamic Assignment & Delegation Resolution
            # Load active delegates list for the organization
            delegates = await self.delegate_repo.list_by_org(org_id)
            
            for stage in chain_copy.stages:
                stage.assignments = await self.approver_resolver.resolve_stage_assignees(
                    org_id=org_id,
                    assignments=stage.assignments,
                    active_delegates=delegates,
                    creator_id=context.creator_id
                )

            # 4. Construct Request Entity
            # Default SLA = 24 hours (86400 seconds) if not configured
            default_sla = ApprovalSLA(duration_seconds=86400, remaining_seconds=86400.0)
            
            request = ApprovalRequest(
                org_id=org_id,
                title=title,
                chain=chain_copy,
                workflow_id=workflow_id,
                node_id=node_id,
                session_id=session_id,
                description=description,
                status="PENDING",
                sla=default_sla,
                escalation_policy=[],
                version=1,
                context=context_data
            )
            
            # 5. Persist request
            await self.request_repo.save(request)
            
            # 6. Activate and trigger notification dispatching
            request.activate()
            await self.request_repo.save(request)
            
            # Send notifications for the active stage assignees
            active_stage = request.chain.stages[request.chain.current_stage_index]
            assignee_ids = [a.user_id for a in active_stage.assignments if a.user_id]
            
            await self.notification_service.send_approval_requested_notification(
                org_id=org_id,
                approval_id=request.id,
                user_ids=assignee_ids,
                title=request.title
            )
            
            return Result.ok(request)
            
        except Exception as e:
            return Result.fail(e)
