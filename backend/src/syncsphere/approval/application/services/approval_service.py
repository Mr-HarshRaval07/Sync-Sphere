import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from syncsphere.shared_kernel.types.result import Result
from syncsphere.shared_kernel.domain.domain_exception import EntityNotFoundException, ConflictException
from syncsphere.approval.domain.entities.approval_request import ApprovalRequest
from syncsphere.approval.domain.entities.approval_delegate import ApprovalDelegate
from syncsphere.approval.domain.entities.approval_policy import ApprovalPolicy
from syncsphere.approval.domain.entities.approval_template import ApprovalTemplate
from syncsphere.approval.domain.value_objects import (
    ApprovalChain,
    ApprovalStage,
    ApprovalAssignment,
    ApprovalDecisionType,
    ApprovalHistory,
    ApprovalComment,
    ApprovalStatistics,
    ApprovalMetrics
)
from syncsphere.approval.domain.repositories import (
    ApprovalRequestRepository,
    ApprovalDelegateRepository,
    ApprovalPolicyRepository,
    ApprovalTemplateRepository
)
from syncsphere.approval.application.commands import (
    CreateApprovalCommand,
    ApproveCommand,
    RejectCommand,
    DelegateCommand,
    EscalateCommand,
    CancelApprovalCommand,
    AddCommentCommand
)
from syncsphere.approval.application.queries import (
    GetApprovalStatusQuery,
    GetApprovalHistoryQuery,
    GetPendingApprovalsQuery,
    GetApprovalStatisticsQuery
)
from syncsphere.approval.application.pipeline import ApprovalPipeline
from syncsphere.approval.application.services.sla import SLAService
from syncsphere.approval.application.services.escalation import EscalationService
from syncsphere.core.events.interfaces import EventPublisher

logger = logging.getLogger("syncsphere.approval.application.services.approval_service")

class ApprovalApplicationService:
    """CQRS interface facade exposing all Command and Query orchestration actions for human approvals."""
    
    def __init__(
        self,
        request_repo: ApprovalRequestRepository,
        delegate_repo: ApprovalDelegateRepository,
        policy_repo: ApprovalPolicyRepository,
        template_repo: ApprovalTemplateRepository,
        pipeline: ApprovalPipeline,
        event_bus: EventPublisher
    ) -> None:
        self.request_repo = request_repo
        self.delegate_repo = delegate_repo
        self.policy_repo = policy_repo
        self.template_repo = template_repo
        self.pipeline = pipeline
        self.event_bus = event_bus

    # COMMANDS
    async def create_approval(self, cmd: CreateApprovalCommand) -> Result[ApprovalRequest, Exception]:
        """Creates and triggers a new human approval request lifecycle."""
        logger.info("Creating approval request: '%s' in org: %s", cmd.title, cmd.org_id)
        
        # Reuse pipeline loop to validate, resolve policy, assign delegates, notify and persist
        res = await self.pipeline.execute_creation_flow(
            org_id=cmd.org_id,
            title=cmd.title,
            context_data=cmd.context,
            workflow_id=cmd.workflow_id,
            node_id=cmd.node_id,
            session_id=cmd.session_id,
            description=cmd.description,
            template_id=cmd.template_id
        )
        if res.is_ok:
            # Publish Domain Events collected from aggregate
            req = res.value()
            for event in req.get_domain_events():
                corr_id = cmd.correlation_id or str(uuid.uuid4())
                event.correlation_id = corr_id
                if self.event_bus:
                    await self.event_bus.publish(event)
                else:
                    logger.warning(f"Event bus unavailable. Dropping event: {event}")
            req.clear_domain_events()
            
        return res

    async def submit_approval(self, cmd: ApproveCommand) -> Result[bool, Exception]:
        """Submits an approval decision vote for a specific stage assignment."""
        print(f"--- submit_approval called! id: {cmd.approval_id} org: {cmd.org_id} user: {cmd.user_id}")
        req = await self.request_repo.get_by_id(cmd.approval_id)
        if not req:
            print(f"--- Approval {cmd.approval_id} not found in DB!")
            return Result.fail(EntityNotFoundException("APPROVAL_NOT_FOUND", "Request not found."))
        if req.org_id != cmd.org_id:
            print(f"--- Org mismatch! req org: {req.org_id}, cmd org: {cmd.org_id}")
            return Result.fail(EntityNotFoundException("APPROVAL_NOT_FOUND", "Request not found."))
            
        try:
            print("--- Submitting decision to domain model")
            req.submit_decision(cmd.user_id, ApprovalDecisionType.APPROVE, cmd.comment)
            print("--- Saving decision to DB")
            await self.request_repo.save(req)
            
            # Publish Domain Events
            for event in req.get_domain_events():
                event.correlation_id = cmd.correlation_id or str(uuid.uuid4())
                if self.event_bus:
                    await self.event_bus.publish(event)
                else:
                    logger.warning(f"Event bus unavailable. Dropping event: {event}")
            req.clear_domain_events()
            
            print("--- Approval success inside service")
            return Result.ok(True)
        except Exception as e:
            print(f"--- submit_approval Exception: {type(e).__name__} - {e}")
            return Result.fail(e)

    async def submit_rejection(self, cmd: RejectCommand) -> Result[bool, Exception]:
        """Submits a reject vote, terminating the request chain immediately."""
        req = await self.request_repo.get_by_id(cmd.approval_id)
        if not req or req.org_id != cmd.org_id:
            return Result.fail(EntityNotFoundException("APPROVAL_NOT_FOUND", "Request not found."))
            
        try:
            req.submit_decision(cmd.user_id, ApprovalDecisionType.REJECT, cmd.comment)
            await self.request_repo.save(req)
            
            # Publish Domain Events
            for event in req.get_domain_events():
                event.correlation_id = cmd.correlation_id or str(uuid.uuid4())
                if self.event_bus:
                    await self.event_bus.publish(event)
                else:
                    import logging; logging.warning(f"Event bus unavailable. Dropping event: {event}")
            req.clear_domain_events()
            
            return Result.ok(True)
        except Exception as e:
            return Result.fail(e)

    async def delegate_task(self, cmd: DelegateCommand) -> Result[bool, Exception]:
        """Reassigns the current active stage assignee redirecting to a delegate."""
        req = await self.request_repo.get_by_id(cmd.approval_id)
        if not req or req.org_id != cmd.org_id:
            return Result.fail(EntityNotFoundException("APPROVAL_NOT_FOUND", "Request not found."))
            
        try:
            req.delegate(cmd.from_user_id, cmd.to_user_id, cmd.reason)
            await self.request_repo.save(req)
            
            # Publish Domain Events
            for event in req.get_domain_events():
                event.correlation_id = cmd.correlation_id or str(uuid.uuid4())
                if self.event_bus:
                    await self.event_bus.publish(event)
                else:
                    import logging; logging.warning(f"Event bus unavailable. Dropping event: {event}")
            req.clear_domain_events()
            
            return Result.ok(True)
        except Exception as e:
            return Result.fail(e)

    async def escalate_task(self, cmd: EscalateCommand) -> Result[bool, Exception]:
        """Forces manual escalation of a stage block."""
        req = await self.request_repo.get_by_id(cmd.approval_id)
        if not req or req.org_id != cmd.org_id:
            return Result.fail(EntityNotFoundException("APPROVAL_NOT_FOUND", "Request not found."))
            
        try:
            req.escalate(cmd.level, cmd.assigned_role_id, cmd.assigned_user_id, cmd.reason)
            await self.request_repo.save(req)
            
            # Publish Domain Events
            for event in req.get_domain_events():
                event.correlation_id = cmd.correlation_id or str(uuid.uuid4())
                if self.event_bus:
                    await self.event_bus.publish(event)
                else:
                    import logging; logging.warning(f"Event bus unavailable. Dropping event: {event}")
            req.clear_domain_events()
            
            return Result.ok(True)
        except Exception as e:
            return Result.fail(e)

    async def cancel_approval(self, cmd: CancelApprovalCommand) -> Result[bool, Exception]:
        """Cancels a pending or active approval request."""
        req = await self.request_repo.get_by_id(cmd.approval_id)
        if not req or req.org_id != cmd.org_id:
            return Result.fail(EntityNotFoundException("APPROVAL_NOT_FOUND", "Request not found."))
            
        try:
            req.cancel()
            await self.request_repo.save(req)
            
            # Publish Domain Events
            for event in req.get_domain_events():
                event.correlation_id = cmd.correlation_id or str(uuid.uuid4())
                if self.event_bus:
                    await self.event_bus.publish(event)
                else:
                    import logging; logging.warning(f"Event bus unavailable. Dropping event: {event}")
            req.clear_domain_events()
            
            return Result.ok(True)
        except Exception as e:
            return Result.fail(e)

    async def add_comment(self, cmd: AddCommentCommand) -> Result[bool, Exception]:
        """Appends discussion comments to approval thread audit logs."""
        req = await self.request_repo.get_by_id(cmd.approval_id)
        if not req or req.org_id != cmd.org_id:
            return Result.fail(EntityNotFoundException("APPROVAL_NOT_FOUND", "Request not found."))
            
        try:
            req.add_comment(cmd.user_id, cmd.text)
            await self.request_repo.save(req)
            return Result.ok(True)
        except Exception as e:
            return Result.fail(e)

    # QUERIES
    async def get_approval_status(self, query: GetApprovalStatusQuery) -> Result[ApprovalRequest, Exception]:
        """Retrieves a single request mapping variables."""
        req = await self.request_repo.get_by_id(query.approval_id)
        if not req or req.org_id != query.org_id:
            return Result.fail(EntityNotFoundException("APPROVAL_NOT_FOUND", "Request not found."))
            
        # Update SLA remaining time telemetry on reading
        SLAService.evaluate_sla_status(req)
        await self.request_repo.save(req)
        
        return Result.ok(req)

    async def get_approval_history(self, query: GetApprovalHistoryQuery) -> Result[List[ApprovalHistory], Exception]:
        """Retrieves audit log timeline entries."""
        req = await self.request_repo.get_by_id(query.approval_id)
        if not req or req.org_id != query.org_id:
            return Result.fail(EntityNotFoundException("APPROVAL_NOT_FOUND", "Request not found."))
        return Result.ok(req.history)

    async def get_pending_approvals(self, query: GetPendingApprovalsQuery) -> Result[List[ApprovalRequest], Exception]:
        """Lists active approvals assigned to user ID."""
        requests = await self.request_repo.list_pending_by_user(query.org_id, query.user_id)
        return Result.ok(requests)

    async def get_approval_statistics(self, query: GetApprovalStatisticsQuery) -> Result[ApprovalStatistics, Exception]:
        """
        Calculates organizational/workflow analytics:
        - Average approval duration
        - SLA compliance percentage
        - Total escalations triggered
        - Workload counts by approver
        - Delay bottlenecks grouped by stage names
        """
        all_requests = await self.request_repo.list_by_org(query.org_id)
        if query.workflow_id:
            all_requests = [r for r in all_requests if r.workflow_id == query.workflow_id]
            
        completed = [r for r in all_requests if r.status in ("APPROVED", "REJECTED") and r.completed_at]
        pending = [r for r in all_requests if r.status == "ACTIVE"]
        
        # 1. Average approval duration
        durations = []
        sla_compliant_count = 0
        for r in completed:
            diff = (r.completed_at - r.created_at).total_seconds()
            durations.append(diff)
            if r.sla and not r.sla.is_overdue:
                sla_compliant_count += 1
                
        avg_dur = sum(durations) / len(durations) if durations else 0.0
        sla_comp = (sla_compliant_count / len(completed)) * 100.0 if completed else 100.0
        
        # 2. Total escalations count
        tot_escalations = sum(r.escalation_count for r in all_requests)
        
        # 3. Workloads mapping (count of active pending assignments per user)
        workloads = {}
        for r in pending:
            stage = r.chain.stages[r.chain.current_stage_index]
            for ass in stage.assignments:
                if ass.user_id:
                    workloads[ass.user_id] = workloads.get(ass.user_id, 0) + 1
                    
        # 4. Bottlenecks (find average duration grouped by stage name)
        stage_times: Dict[str, List[float]] = {}
        for r in completed:
            for stage in r.chain.stages:
                # Approximate duration per stage from timeline actions
                # Find activation and completion timeline times
                act_time = r.created_at
                comp_time = r.completed_at
                for entry in r.history:
                    if entry.action == "StageActivated" and entry.details.get("stage_id") == stage.stage_id:
                        act_time = entry.timestamp
                    elif entry.action == "DecisionSubmitted" and entry.details.get("stage_id") == stage.stage_id:
                        comp_time = entry.timestamp
                stage_times.setdefault(stage.name, []).append((comp_time - act_time).total_seconds())
                
        bottlenecks = {name: (sum(times)/len(times)) for name, times in stage_times.items()}
        
        metrics = ApprovalMetrics(
            average_duration_seconds=avg_dur,
            sla_compliance_percentage=sla_comp,
            escalation_count=tot_escalations,
            approver_workloads=workloads,
            stage_bottlenecks=bottlenecks
        )
        
        stats = ApprovalStatistics(
            total_requests=len(all_requests),
            pending_count=len(pending),
            approved_count=len([r for r in all_requests if r.status == "APPROVED"]),
            rejected_count=len([r for r in all_requests if r.status == "REJECTED"]),
            metrics=metrics
        )
        
        return Result.ok(stats)
