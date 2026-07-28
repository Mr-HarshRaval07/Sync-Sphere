import logging
from datetime import datetime
from typing import List
from syncsphere.approval.domain.entities.approval_request import ApprovalRequest

logger = logging.getLogger("syncsphere.approval.application.services.sla")

class SLAService:
    @staticmethod
    def evaluate_sla_status(request: ApprovalRequest) -> bool:
        """
        Updates request SLA remaining time. 
        Returns True if request has breached SLA limits and transitioned to overdue.
        """
        if request.status != "ACTIVE" or not request.sla:
            return False
            
        now = datetime.utcnow()
        elapsed = (now - request.created_at).total_seconds()
        
        request.sla.remaining_seconds = max(0.0, float(request.sla.duration_seconds - elapsed))
        
        if elapsed > request.sla.duration_seconds and not request.sla.is_overdue:
            request.sla.is_overdue = True
            request.sla.breached_at = now
            request.record_history("SLABreached", details={"elapsed_seconds": elapsed})
            logger.warning("ApprovalRequest %s has breached its SLA of %d seconds.", request.id, request.sla.duration_seconds)
            return True
            
        return False
