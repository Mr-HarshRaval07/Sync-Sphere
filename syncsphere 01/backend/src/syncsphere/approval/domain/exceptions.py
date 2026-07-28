from syncsphere.shared_kernel.domain.domain_exception import DomainException

class ApprovalDomainException(DomainException):
    pass

class ApprovalNotFoundException(ApprovalDomainException):
    def __init__(self, approval_id: str) -> None:
        super().__init__("APPROVAL_NOT_FOUND", f"Approval Request '{approval_id}' was not found.")

class InvalidDecisionException(ApprovalDomainException):
    def __init__(self, msg: str) -> None:
        super().__init__("INVALID_DECISION", msg)

class UnauthorizedApproverException(ApprovalDomainException):
    def __init__(self, user_id: str, stage_id: str) -> None:
        super().__init__("UNAUTHORIZED_APPROVER", f"User '{user_id}' is not authorized to submit decisions for stage '{stage_id}'.")

class DelegationCycleException(ApprovalDomainException):
    def __init__(self, msg: str) -> None:
        super().__init__("DELEGATION_CYCLE_DETECTED", msg)

class PolicyValidationException(ApprovalDomainException):
    def __init__(self, msg: str) -> None:
        super().__init__("POLICY_VALIDATION_ERROR", msg)
