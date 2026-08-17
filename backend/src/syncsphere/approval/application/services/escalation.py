import logging
from typing import List, Optional
from syncsphere.approval.domain.entities.approval_request import ApprovalRequest
from syncsphere.approval.domain.value_objects import ApprovalEscalation

logger = logging.getLogger("syncsphere.approval.application.services.escalation")

class EscalationService:
    @staticmethod
    def escalate_request_if_breached(request: ApprovalRequest) -> bool:
        """
        Applies escalation rules if request SLA has been breached.
        Returns True if escalation was triggered.
        """
        if not request.sla or not request.sla.is_overdue or not request.escalation_policy:
            return False
            
        current_level = request.escalation_count + 1
        
        # Find matching level in policy
        matching_escalation: Optional[ApprovalEscalation] = None
        for esc in request.escalation_policy:
            if esc.escalation_level == current_level:
                matching_escalation = esc
                break
                
        if not matching_escalation:
            # Reached max escalation, fallback to escalation level 1 or do nothing
            logger.info("No matching escalation level %d defined for request %s.", current_level, request.id)
            return False
            
        logger.warning("Triggering SLA escalation level %d for request %s.", current_level, request.id)
        request.escalate(
            level=current_level,
            role_id=matching_escalation.assigned_role_id,
            user_id=matching_escalation.assigned_user_id,
            reason=f"SLA breached. Escalation Level {current_level} triggered automatically."
        )
        return True
