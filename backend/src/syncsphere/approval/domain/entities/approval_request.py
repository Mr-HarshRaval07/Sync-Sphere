import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot
from syncsphere.approval.domain.value_objects import (
    ApprovalChain,
    ApprovalStage,
    ApprovalAssignment,
    ApprovalDecision,
    ApprovalDecisionType,
    ApprovalComment,
    ApprovalHistory,
    ApprovalSLA,
    ApprovalEscalation,
    ApprovalReminder,
    RoutingStrategyType
)
from syncsphere.approval.domain.exceptions import (
    InvalidDecisionException,
    UnauthorizedApproverException
)
from syncsphere.approval.domain.events import (
    ApprovalCreated,
    ApprovalAssigned,
    ApprovalRequested,
    ApprovalDelegated,
    ApprovalEscalated,
    ApprovalReminderSent,
    ApprovalApproved,
    ApprovalRejected,
    ApprovalCompleted,
    ApprovalCancelled
)

class ApprovalRequest(AggregateRoot):
    def __init__(
        self,
        org_id: str,
        title: str,
        chain: ApprovalChain,
        workflow_id: Optional[str] = None,
        node_id: Optional[str] = None,
        session_id: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "PENDING",  # PENDING, ACTIVE, APPROVED, REJECTED, CANCELLED
        sla: Optional[ApprovalSLA] = None,
        escalation_policy: Optional[List[ApprovalEscalation]] = None,
        reminder_policy: Optional[ApprovalReminder] = None,
        comments: Optional[List[ApprovalComment]] = None,
        history: Optional[List[ApprovalHistory]] = None,
        version: int = 1,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        escalation_count: int = 0,
        id: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.org_id = org_id
        self.title = title
        self.chain = chain
        self.workflow_id = workflow_id
        self.node_id = node_id
        self.session_id = session_id
        self.description = description
        self.status = status
        self.sla = sla
        self.escalation_policy = escalation_policy or []
        self.reminder_policy = reminder_policy
        self.comments = comments or []
        self.history = history or []
        self.version = version
        self.completed_at = completed_at
        self.escalation_count = escalation_count
        self.context = kwargs.get("context", {})
        
        # Publish initial created event if this is a new entity
        if not id:
            self.record_history("Created", details={"title": title, "version": version})
            self.add_domain_event(ApprovalCreated(approval_id=self.id, org_id=self.org_id, correlation_id=str(uuid.uuid4())))

    def record_history(self, action: str, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Adds a permanent audit log timeline entry."""
        entry = ApprovalHistory(
            history_id=str(uuid.uuid4()),
            action=action,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            details=details or {}
        )
        self.history.append(entry)

    def activate(self) -> None:
        """Transitions request to ACTIVE and notifies the first stage assignees."""
        if self.status != "PENDING":
            return
            
        self.status = "ACTIVE"
        self.record_history("Activated")
        self._initialize_current_stage()

    def _initialize_current_stage(self) -> None:
        """Sets active flags and triggers assignment notification triggers."""
        if self.chain.current_stage_index >= len(self.chain.stages):
            self._complete_request(approved=True)
            return
            
        stage = self.chain.stages[self.chain.current_stage_index]
        stage.status = "ACTIVE"
        
        assignee_ids = [a.user_id for a in stage.assignments if a.user_id]
        
        self.record_history("StageActivated", details={
            "stage_id": stage.stage_id,
            "name": stage.name,
            "routing": stage.routing_strategy.value,
            "assignee_ids": assignee_ids
        })
        
        self.add_domain_event(ApprovalAssigned(
            approval_id=self.id,
            org_id=self.org_id,
            stage_id=stage.stage_id,
            assignee_ids=assignee_ids,
            correlation_id=str(uuid.uuid4())
        ))
        self.add_domain_event(ApprovalRequested(
            approval_id=self.id,
            org_id=self.org_id,
            stage_id=stage.stage_id,
            assignee_ids=assignee_ids,
            correlation_id=str(uuid.uuid4())
        ))

    def submit_decision(self, user_id: str, decision: ApprovalDecisionType, comment: Optional[str] = None) -> None:
        """Processes an approver's vote decision and triggers routing strategy resolutions."""
        if self.status == "PENDING":
            self.activate()
            
        if self.status != "ACTIVE":
            raise InvalidDecisionException(f"Approval Request is not in ACTIVE state (current: {self.status}).")
            
        stage = self.chain.stages[self.chain.current_stage_index]
        
        # Verify user is assigned to this stage
        is_assigned = any(
            (a.user_id == user_id or a.role_id is not None) # role mappings resolved dynamically in app layer
            for a in stage.assignments
        )
        if not is_assigned:
            raise UnauthorizedApproverException(user_id, stage.stage_id)
            
        # Register comment if provided
        if comment:
            self.add_comment(user_id, comment)
            
        # Append decision
        dec_obj = ApprovalDecision(user_id=user_id, decision=decision, comment=comment, timestamp=datetime.utcnow())
        stage.decisions.append(dec_obj)
        
        self.record_history("DecisionSubmitted", user_id=user_id, details={
            "stage_id": stage.stage_id,
            "decision": decision.value,
            "comment": comment
        })
        
        if decision == ApprovalDecisionType.REJECT:
            # Under standard sequential/parallel pipelines, a reject aborts the chain (unless overridden)
            stage.status = "REJECTED"
            self._complete_request(approved=False, decision_maker_id=user_id)
            return

        # Evaluate stage completion strategy
        if self._evaluate_stage_completion(stage):
            stage.status = "COMPLETED"
            self.chain.current_stage_index += 1
            self._initialize_current_stage()

    def _evaluate_stage_completion(self, stage: ApprovalStage) -> bool:
        """Applies routing strategy rules to check if the current level completes."""
        decisions = [d for d in stage.decisions if d.decision == ApprovalDecisionType.APPROVE]
        total_assignments = len(stage.assignments)
        
        if stage.routing_strategy == RoutingStrategyType.SEQUENTIAL:
            # Must be approved by all assignees in sequential order
            return len(decisions) >= total_assignments
            
        elif stage.routing_strategy == RoutingStrategyType.PARALLEL:
            # Must be approved by all assignees in parallel
            return len(decisions) >= total_assignments
            
        elif stage.routing_strategy == RoutingStrategyType.CONSENSUS:
            # Complete agreement (all assigned users must approve)
            return len(decisions) >= total_assignments
            
        elif stage.routing_strategy == RoutingStrategyType.MAJORITY:
            # > 50% approvals
            required = (total_assignments // 2) + 1
            return len(decisions) >= required
            
        elif stage.routing_strategy == RoutingStrategyType.FIRST_RESPONSE:
            # First approval completes the stage
            return len(decisions) >= 1
            
        elif stage.routing_strategy == RoutingStrategyType.WEIGHTED:
            # Sum of assignee weights must exceed 50% of total weights
            total_weight = sum(a.weight for a in stage.assignments)
            approved_weight = sum(
                a.weight for a in stage.assignments
                if any(d.user_id == a.user_id for d in decisions)
            )
            return approved_weight > (total_weight / 2.0)
            
        return len(decisions) >= total_assignments

    def delegate(self, from_user_id: str, to_user_id: str, reason: Optional[str] = None) -> None:
        """Delegates task assignment to another user in the active stage."""
        if self.status != "ACTIVE":
            raise InvalidDecisionException("Can only delegate tasks on ACTIVE requests.")
            
        stage = self.chain.stages[self.chain.current_stage_index]
        delegated = False
        
        for assignment in stage.assignments:
            if assignment.user_id == from_user_id:
                assignment.user_id = to_user_id
                assignment.is_delegated = True
                assignment.original_assignee_id = from_user_id
                delegated = True
                break
                
        if not delegated:
            raise InvalidDecisionException(f"User '{from_user_id}' has no assignment in current stage.")
            
        self.record_history("Delegated", user_id=from_user_id, details={
            "stage_id": stage.stage_id,
            "to_user_id": to_user_id,
            "reason": reason
        })
        self.add_domain_event(ApprovalDelegated(
            approval_id=self.id,
            org_id=self.org_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            reason=reason,
            correlation_id=str(uuid.uuid4())
        ))
        
        # Send new request notification to the delegate
        self.add_domain_event(ApprovalRequested(
            approval_id=self.id,
            org_id=self.org_id,
            stage_id=stage.stage_id,
            assignee_ids=[to_user_id],
            correlation_id=str(uuid.uuid4())
        ))

    def escalate(self, level: int, role_id: Optional[str] = None, user_id: Optional[str] = None, reason: Optional[str] = None) -> None:
        """Triggers SLA timeout escalation, re-routing assignments to manager/VP level."""
        self.escalation_count += 1
        stage = self.chain.stages[self.chain.current_stage_index]
        
        # Wipe old assignments and append escalation targets
        new_assignee = ApprovalAssignment(user_id=user_id, role_id=role_id, weight=1.0)
        stage.assignments = [new_assignee]
        stage.status = "ACTIVE"
        
        self.record_history("Escalated", details={
            "stage_id": stage.stage_id,
            "level": level,
            "assigned_user_id": user_id,
            "assigned_role_id": role_id,
            "reason": reason
        })
        
        self.add_domain_event(ApprovalEscalated(
            approval_id=self.id,
            org_id=self.org_id,
            escalation_level=level,
            assigned_user_id=user_id,
            assigned_role_id=role_id,
            correlation_id=str(uuid.uuid4())
        ))
        
        # Dispatch notification to escalation assignee
        self.add_domain_event(ApprovalRequested(
            approval_id=self.id,
            org_id=self.org_id,
            stage_id=stage.stage_id,
            assignee_ids=[user_id] if user_id else [],
            correlation_id=str(uuid.uuid4())
        ))

    def _complete_request(self, approved: bool, decision_maker_id: Optional[str] = None) -> None:
        """Transitions request to end state and registers execution completion events."""
        self.status = "APPROVED" if approved else "REJECTED"
        self.completed_at = datetime.utcnow()
        self.record_history("Completed", details={"approved": approved})
        
        # Publish final events
        maker = decision_maker_id or "system"
        if approved:
            self.add_domain_event(ApprovalApproved(approval_id=self.id, org_id=self.org_id, decision_maker_id=maker, correlation_id=str(uuid.uuid4())))
        else:
            self.add_domain_event(ApprovalRejected(approval_id=self.id, org_id=self.org_id, decision_maker_id=maker, correlation_id=str(uuid.uuid4())))
            
        self.add_domain_event(ApprovalCompleted(
            approval_id=self.id,
            org_id=self.org_id,
            approved=approved,
            session_id=self.session_id,
            node_id=self.node_id,
            correlation_id=str(uuid.uuid4())
        ))

    def cancel(self) -> None:
        """Cancels/archives the approval request."""
        if self.status in ("APPROVED", "REJECTED", "CANCELLED"):
            return
            
        self.status = "CANCELLED"
        self.completed_at = datetime.utcnow()
        self.record_history("Cancelled")
        self.add_domain_event(ApprovalCancelled(approval_id=self.id, org_id=self.org_id, correlation_id=str(uuid.uuid4())))
        self.add_domain_event(ApprovalCompleted(
            approval_id=self.id,
            org_id=self.org_id,
            approved=False,
            session_id=self.session_id,
            node_id=self.node_id,
            correlation_id=str(uuid.uuid4())
        ))

    def add_comment(self, user_id: str, text: str) -> None:
        """Appends comments to discussion logs."""
        comment = ApprovalComment(
            comment_id=str(uuid.uuid4()),
            user_id=user_id,
            text=text,
            timestamp=datetime.utcnow()
        )
        self.comments.append(comment)
        self.record_history("CommentAdded", user_id=user_id, details={"comment_id": comment.comment_id})
