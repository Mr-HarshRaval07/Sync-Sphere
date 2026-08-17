from syncsphere.approval.domain.entities.approval_request import ApprovalRequest
from syncsphere.approval.domain.entities.approval_delegate import ApprovalDelegate
from syncsphere.approval.domain.entities.approval_policy import ApprovalPolicy
from syncsphere.approval.domain.entities.approval_template import ApprovalTemplate
from syncsphere.approval.infrastructure.documents.approval_request_document import ApprovalRequestDocument
from syncsphere.approval.infrastructure.documents.approval_delegate_document import ApprovalDelegateDocument
from syncsphere.approval.infrastructure.documents.approval_policy_document import ApprovalPolicyDocument
from syncsphere.approval.infrastructure.documents.approval_template_document import ApprovalTemplateDocument

class ApprovalMapper:
    @staticmethod
    def to_request_entity(doc: ApprovalRequestDocument) -> ApprovalRequest:
        return ApprovalRequest(
            id=str(doc.id),
            org_id=doc.org_id,
            title=doc.title,
            chain=doc.chain,
            workflow_id=doc.workflow_id,
            node_id=doc.node_id,
            session_id=doc.session_id,
            description=doc.description,
            status=doc.status,
            sla=doc.sla,
            escalation_policy=doc.escalation_policy,
            reminder_policy=doc.reminder_policy,
            comments=doc.comments,
            history=doc.history,
            version=doc.version,
            completed_at=doc.completed_at,
            escalation_count=doc.escalation_count,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            context=doc.context
        )

    @staticmethod
    def to_request_document(entity: ApprovalRequest) -> ApprovalRequestDocument:
        # If ID is valid string representation of MongoDB ObjectID, pass it, otherwise skip to let Beanie generate
        doc_id = None
        # Try to parse string ID as Beanie/Pymongo ObjectID is not strictly required if we set id on document replacement
        doc = ApprovalRequestDocument(
            title=entity.title,
            chain=entity.chain,
            workflow_id=entity.workflow_id,
            node_id=entity.node_id,
            session_id=entity.session_id,
            description=entity.description,
            status=entity.status,
            sla=entity.sla,
            escalation_policy=entity.escalation_policy,
            reminder_policy=entity.reminder_policy,
            comments=entity.comments,
            history=entity.history,
            version=entity.version,
            completed_at=entity.completed_at,
            escalation_count=entity.escalation_count,
            org_id=entity.org_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            context=getattr(entity, "context", {})
        )
        if entity.id:
            doc.id = entity.id
        return doc

    @staticmethod
    def to_delegate_entity(doc: ApprovalDelegateDocument) -> ApprovalDelegate:
        return ApprovalDelegate(
            id=str(doc.id),
            org_id=doc.org_id,
            from_user_id=doc.from_user_id,
            to_user_id=doc.to_user_id,
            delegation_type=doc.delegation_type,
            is_active=doc.is_active,
            start_date=doc.start_date,
            end_date=doc.end_date,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def to_delegate_document(entity: ApprovalDelegate) -> ApprovalDelegateDocument:
        doc = ApprovalDelegateDocument(
            from_user_id=entity.from_user_id,
            to_user_id=entity.to_user_id,
            delegation_type=entity.delegation_type,
            is_active=entity.is_active,
            start_date=entity.start_date,
            end_date=entity.end_date,
            org_id=entity.org_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
        if entity.id:
            doc.id = entity.id
        return doc

    @staticmethod
    def to_policy_entity(doc: ApprovalPolicyDocument) -> ApprovalPolicy:
        return ApprovalPolicy(
            id=str(doc.id),
            org_id=doc.org_id,
            name=doc.name,
            rules=doc.rules,
            target_chain=doc.target_chain,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def to_policy_document(entity: ApprovalPolicy) -> ApprovalPolicyDocument:
        doc = ApprovalPolicyDocument(
            name=entity.name,
            rules=entity.rules,
            target_chain=entity.target_chain,
            org_id=entity.org_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
        if entity.id:
            doc.id = entity.id
        return doc

    @staticmethod
    def to_template_entity(doc: ApprovalTemplateDocument) -> ApprovalTemplate:
        return ApprovalTemplate(
            id=str(doc.id),
            org_id=doc.org_id,
            name=doc.name,
            chain=doc.chain,
            description=doc.description,
            version=doc.version,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def to_template_document(entity: ApprovalTemplate) -> ApprovalTemplateDocument:
        doc = ApprovalTemplateDocument(
            name=entity.name,
            chain=entity.chain,
            description=entity.description,
            version=entity.version,
            org_id=entity.org_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
        if entity.id:
            doc.id = entity.id
        return doc
