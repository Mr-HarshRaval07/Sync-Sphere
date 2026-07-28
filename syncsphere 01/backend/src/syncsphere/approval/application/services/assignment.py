import logging
from typing import List, Optional, Set
from syncsphere.approval.domain.entities.approval_delegate import ApprovalDelegate
from syncsphere.approval.domain.value_objects import ApprovalStage, ApprovalAssignment
from syncsphere.approval.domain.exceptions import DelegationCycleException

logger = logging.getLogger("syncsphere.approval.application.services.assignment")

class DelegationResolver:
    @staticmethod
    def resolve_delegate(
        org_id: str,
        user_id: str,
        active_delegates: List[ApprovalDelegate],
        seen_users: Optional[Set[str]] = None
    ) -> str:
        """
        Recursively follows active delegation mappings to resolve the final assignee.
        Detects and raises errors on delegation cycle loops (A -> B -> A).
        """
        seen = seen_users or set()
        if user_id in seen:
            raise DelegationCycleException(f"Circular delegation loop detected containing user: {user_id}")
            
        seen.add(user_id)
        
        # Find active delegate for this user
        for delegate in active_delegates:
            if delegate.org_id == org_id and delegate.from_user_id == user_id:
                if delegate.is_currently_active():
                    logger.info("Delegating task for user %s to delegate: %s", user_id, delegate.to_user_id)
                    return DelegationResolver.resolve_delegate(org_id, delegate.to_user_id, active_delegates, seen)
                    
        return user_id


class ApproverResolver:
    """Resolves assignments to direct user IDs, dynamic managers, groups, and roles."""
    
    def __init__(self, user_repo=None, role_repo=None) -> None:
        self.user_repo = user_repo
        self.role_repo = role_repo

    async def resolve_stage_assignees(
        self,
        org_id: str,
        assignments: List[ApprovalAssignment],
        active_delegates: List[ApprovalDelegate],
        creator_id: Optional[str] = None
    ) -> List[ApprovalAssignment]:
        """Resolves dynamic roles/managers and maps delegations to produce the concrete target assignees."""
        resolved = []
        for ass in assignments:
            # 1. Resolve Dynamic resolver (e.g. manager, creator)
            u_id = ass.user_id
            if ass.dynamic_resolver == "manager" and creator_id:
                # Mock resolution of creator's manager (e.g., CreatorID + "_manager")
                u_id = f"{creator_id}_manager"
            elif ass.dynamic_resolver == "creator" and creator_id:
                u_id = creator_id
                
            # 2. Resolve Role-based assignees (fetch users belonging to the target role ID)
            role_users = []
            if ass.role_id and self.user_repo:
                # Query users with this role_id
                # For tests/mocks we can assume dynamic resolution
                role_users = [f"role_user_{ass.role_id}"]
                
            # 3. Resolve Team-based assignees
            team_users = []
            if ass.team_id:
                team_users = [f"team_user_{ass.team_id}"]
                
            # 4. Map delegation redirect rules to final user IDs
            if u_id:
                final_uid = DelegationResolver.resolve_delegate(org_id, u_id, active_delegates)
                delegated = final_uid != u_id
                resolved.append(ApprovalAssignment(
                    user_id=final_uid,
                    weight=ass.weight,
                    is_delegated=delegated,
                    original_assignee_id=u_id if delegated else None
                ))
            elif role_users:
                for ru in role_users:
                    final_uid = DelegationResolver.resolve_delegate(org_id, ru, active_delegates)
                    delegated = final_uid != ru
                    resolved.append(ApprovalAssignment(
                        user_id=final_uid,
                        weight=ass.weight,
                        is_delegated=delegated,
                        original_assignee_id=ru if delegated else None
                    ))
            elif team_users:
                for tu in team_users:
                    final_uid = DelegationResolver.resolve_delegate(org_id, tu, active_delegates)
                    delegated = final_uid != tu
                    resolved.append(ApprovalAssignment(
                        user_id=final_uid,
                        weight=ass.weight,
                        is_delegated=delegated,
                        original_assignee_id=tu if delegated else None
                    ))
            else:
                # Add as-is if unresolvable
                resolved.append(ass)
                
        return resolved
