from typing import Optional, List, Dict, Any
from syncsphere.identity.domain.repositories import (
    UserRepository,
    OrgRepository,
    RoleRepository,
    ApiKeyRepository,
    RefreshTokenRepository,
)
from syncsphere.identity.domain.entities.user import User
from syncsphere.identity.domain.entities.organization import Organization
from syncsphere.identity.domain.entities.role import Role
from syncsphere.identity.domain.entities.api_key import ApiKey
from syncsphere.identity.domain.entities.refresh_token import RefreshToken

class InMemoryUserRepository(UserRepository):
    """In-memory mock repository for User aggregate."""
    
    def __init__(self) -> None:
        self.store: Dict[str, User] = {}

    async def save(self, user: User) -> None:
        self.store[user.id] = user

    async def get_by_id(self, user_id: str) -> Optional[User]:
        return self.store.get(user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        for user in self.store.values():
            if user.email == email.lower().strip():
                return user
        return None

    async def list_by_org(self, org_id: str, page: int, page_size: int) -> List[User]:
        org_users = [u for u in self.store.values() if u.org_id == org_id]
        skip = (page - 1) * page_size
        return org_users[skip : skip + page_size]

    async def count_by_org(self, org_id: str) -> int:
        return len([u for u in self.store.values() if u.org_id == org_id])


class InMemoryOrgRepository(OrgRepository):
    """In-memory mock repository for Organization aggregate."""
    
    def __init__(self) -> None:
        self.store: Dict[str, Organization] = {}

    async def save(self, org: Organization) -> None:
        self.store[org.id] = org

    async def get_by_id(self, org_id: str) -> Optional[Organization]:
        return self.store.get(org_id)

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        for org in self.store.values():
            if org.slug == slug.lower().strip():
                return org
        return None


class InMemoryRoleRepository(RoleRepository):
    """In-memory mock repository for Role entity."""
    
    def __init__(self) -> None:
        self.store: Dict[str, Role] = {}

    async def save(self, role: Role) -> None:
        self.store[role.id] = role

    async def get_by_id(self, role_id: str) -> Optional[Role]:
        return self.store.get(role_id)

    async def get_by_name(self, org_id: str, name: str) -> Optional[Role]:
        for role in self.store.values():
            if role.org_id == org_id and role.name == name:
                return role
        return None

    async def list_by_org(self, org_id: str) -> List[Role]:
        return [r for r in self.store.values() if r.org_id == org_id]

    async def delete(self, role_id: str) -> None:
        if role_id in self.store:
            del self.store[role_id]


class InMemoryApiKeyRepository(ApiKeyRepository):
    """In-memory mock repository for ApiKey entity."""
    
    def __init__(self) -> None:
        self.store: Dict[str, ApiKey] = {}

    async def save(self, api_key: ApiKey) -> None:
        self.store[api_key.id] = api_key

    async def get_by_id(self, key_id: str) -> Optional[ApiKey]:
        return self.store.get(key_id)

    async def get_by_hash(self, key_hash: str) -> Optional[ApiKey]:
        for key in self.store.values():
            if key.key_hash == key_hash:
                return key
        return None

    async def list_by_user(self, org_id: str, user_id: str) -> List[ApiKey]:
        return [k for k in self.store.values() if k.org_id == org_id and k.user_id == user_id]


class InMemoryRefreshTokenRepository(RefreshTokenRepository):
    """In-memory mock repository for RefreshToken entity."""
    
    def __init__(self) -> None:
        self.store: Dict[str, RefreshToken] = {}

    async def save(self, token: RefreshToken) -> None:
        self.store[token.id] = token

    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        for tok in self.store.values():
            if tok.token_hash == token_hash:
                return tok
        return None

    async def revoke_all_for_user(self, user_id: str) -> None:
        for tok in self.store.values():
            if tok.user_id == user_id:
                tok.is_revoked = True

from syncsphere.connectors.infrastructure.mcp.transport import MCPTransport
from tests.mock_mcp_server import MockMCPServer
import asyncio

class InMemoryMCPTransport(MCPTransport):
    """In-memory mock transport for testing MCPClient operations without subprocesses."""
    
    def __init__(self, connector_type: str) -> None:
        self.connector_type = connector_type
        self.server = MockMCPServer()
        self.queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False

    async def start(self) -> None:
        self.is_running = True

    async def send_message(self, message: Dict[str, Any]) -> None:
        if not self.is_running:
            raise IOError("Transport is closed.")
        # Process request synchronously using MockMCPServer and queue response
        response = self.server.handle_message(message, self.connector_type)
        await self.queue.put(response)

    async def receive_message(self) -> Optional[Dict[str, Any]]:
        return await self.queue.get()

    async def close(self) -> None:
        self.is_running = False

from syncsphere.connectors.domain.repositories import ConnectorRepository, CredentialRepository
from syncsphere.connectors.domain.entities.connector import Connector
from syncsphere.connectors.domain.entities.credential import ConnectorCredential

class InMemoryConnectorRepository(ConnectorRepository):
    """In-memory mock repository for Connector aggregate."""
    
    def __init__(self) -> None:
        self.store: Dict[str, Connector] = {}

    async def save(self, connector: Connector) -> None:
        self.store[connector.id] = connector

    async def get_by_id(self, connector_id: str) -> Optional[Connector]:
        return self.store.get(connector_id)

    async def get_by_name(self, org_id: str, name: str) -> Optional[Connector]:
        for conn in self.store.values():
            if conn.org_id == org_id and conn.name == name.lower().strip():
                return conn
        return None

    async def list_by_org(self, org_id: str) -> List[Connector]:
        return [c for c in self.store.values() if c.org_id == org_id]

    async def delete(self, connector_id: str) -> None:
        if connector_id in self.store:
            del self.store[connector_id]


class InMemoryCredentialRepository(CredentialRepository):
    """In-memory mock repository for ConnectorCredential entity."""
    
    def __init__(self) -> None:
        self.store: Dict[str, ConnectorCredential] = {}

    async def save(self, credential: ConnectorCredential) -> None:
        self.store[credential.connector_id] = credential

    async def get_by_connector(self, org_id: str, connector_id: str) -> Optional[ConnectorCredential]:
        return self.store.get(connector_id)

    async def delete(self, org_id: str, connector_id: str) -> None:
        if connector_id in self.store:
            del self.store[connector_id]


# ──────────────────────────────────────────────────────────────
# Workflow Bounded Context In-Memory Repositories
# ──────────────────────────────────────────────────────────────

from syncsphere.workflow.domain.repositories import WorkflowRepository, WorkflowVersionRepository
from syncsphere.workflow.domain.entities.workflow import Workflow
from syncsphere.workflow.domain.entities.workflow_version import WorkflowVersion


class InMemoryWorkflowRepository(WorkflowRepository):
    """In-memory mock repository for Workflow aggregate."""

    def __init__(self) -> None:
        self.store: Dict[str, Workflow] = {}

    async def save(self, workflow: Workflow) -> None:
        self.store[workflow.id] = workflow

    async def get_by_id(self, workflow_id: str) -> Optional[Workflow]:
        return self.store.get(workflow_id)

    async def get_by_name(self, org_id: str, name: str) -> Optional[Workflow]:
        for wf in self.store.values():
            if wf.org_id == org_id and wf.name.strip() == name.strip():
                return wf
        return None

    async def list_by_org(self, org_id: str, page: int, page_size: int) -> List[Workflow]:
        org_workflows = [
            w for w in self.store.values()
            if w.org_id == org_id and getattr(w, 'status', None) != "ARCHIVED"
        ]
        skip = (page - 1) * page_size
        return org_workflows[skip : skip + page_size]

    async def count_by_org(self, org_id: str) -> int:
        return len([
            w for w in self.store.values()
            if w.org_id == org_id and getattr(w, 'status', None) != "ARCHIVED"
        ])

    async def delete(self, workflow_id: str) -> None:
        if workflow_id in self.store:
            del self.store[workflow_id]


class InMemoryWorkflowVersionRepository(WorkflowVersionRepository):
    """In-memory mock repository for WorkflowVersion snapshots."""

    def __init__(self) -> None:
        self.store: Dict[str, WorkflowVersion] = {}

    async def save(self, version: WorkflowVersion) -> None:
        self.store[version.id] = version

    async def get_by_version(self, workflow_id: str, version: int) -> Optional[WorkflowVersion]:
        for v in self.store.values():
            if v.workflow_id == workflow_id and v.version == version:
                return v
        return None

    async def list_versions(self, workflow_id: str) -> List[WorkflowVersion]:
        return [v for v in self.store.values() if v.workflow_id == workflow_id]


# ──────────────────────────────────────────────────────────────
# AI Bounded Context In-Memory Repositories
# ──────────────────────────────────────────────────────────────

from syncsphere.ai.domain.repositories import (
    AIModelRepository,
    ModelProviderRepository,
    PromptTemplateRepository,
    PromptVersionRepository,
    PromptExecutionRepository,
)
from syncsphere.ai.domain.entities.model import AIModel, ModelProvider
from syncsphere.ai.domain.entities.prompt import PromptTemplate, PromptVersion
from syncsphere.ai.domain.entities.execution import PromptExecution

class InMemoryAIModelRepository(AIModelRepository):
    def __init__(self) -> None:
        self.store: Dict[str, AIModel] = {}

    async def save(self, model: AIModel) -> None:
        self.store[model.id] = model

    async def get_by_id(self, model_id: str) -> Optional[AIModel]:
        return self.store.get(model_id)

    async def get_by_name(self, org_id: str, name: str) -> Optional[AIModel]:
        for model in self.store.values():
            if model.org_id == org_id and model.name.strip() == name.strip():
                return model
        return None

    async def list_by_org(self, org_id: str) -> List[AIModel]:
        return [m for m in self.store.values() if m.org_id == org_id]

    async def delete(self, model_id: str) -> None:
        if model_id in self.store:
            del self.store[model_id]


class InMemoryModelProviderRepository(ModelProviderRepository):
    def __init__(self) -> None:
        self.store: Dict[str, ModelProvider] = {}

    async def save(self, provider: ModelProvider) -> None:
        self.store[provider.id] = provider

    async def get_by_id(self, provider_id: str) -> Optional[ModelProvider]:
        return self.store.get(provider_id)

    async def get_by_name(self, org_id: str, name: str) -> Optional[ModelProvider]:
        for provider in self.store.values():
            if provider.org_id == org_id and provider.name.strip() == name.strip():
                return provider
        return None

    async def list_by_org(self, org_id: str) -> List[ModelProvider]:
        return [p for p in self.store.values() if p.org_id == org_id]

    async def delete(self, provider_id: str) -> None:
        if provider_id in self.store:
            del self.store[provider_id]


class InMemoryPromptTemplateRepository(PromptTemplateRepository):
    def __init__(self) -> None:
        self.store: Dict[str, PromptTemplate] = {}

    async def save(self, template: PromptTemplate) -> None:
        self.store[template.id] = template

    async def get_by_id(self, template_id: str) -> Optional[PromptTemplate]:
        return self.store.get(template_id)

    async def get_by_name(self, org_id: str, name: str) -> Optional[PromptTemplate]:
        for t in self.store.values():
            if t.org_id == org_id and t.name.strip() == name.strip():
                return t
        return None

    async def list_by_org(self, org_id: str, page: int, page_size: int) -> List[PromptTemplate]:
        org_templates = [t for t in self.store.values() if t.org_id == org_id]
        skip = (page - 1) * page_size
        return org_templates[skip : skip + page_size]

    async def count_by_org(self, org_id: str) -> int:
        return len([t for t in self.store.values() if t.org_id == org_id])

    async def delete(self, template_id: str) -> None:
        if template_id in self.store:
            del self.store[template_id]


class InMemoryPromptVersionRepository(PromptVersionRepository):
    def __init__(self) -> None:
        self.store: Dict[str, PromptVersion] = {}

    async def save(self, version: PromptVersion) -> None:
        self.store[version.id] = version

    async def get_by_version(self, template_id: str, version: int) -> Optional[PromptVersion]:
        for v in self.store.values():
            if v.prompt_template_id == template_id and v.version == version:
                return v
        return None

    async def list_versions(self, template_id: str) -> List[PromptVersion]:
        return [v for v in self.store.values() if v.prompt_template_id == template_id]


class InMemoryPromptExecutionRepository(PromptExecutionRepository):
    def __init__(self) -> None:
        self.store: Dict[str, PromptExecution] = {}

    async def save(self, execution: PromptExecution) -> None:
        self.store[execution.id] = execution

    async def get_by_id(self, execution_id: str) -> Optional[PromptExecution]:
        return self.store.get(execution_id)

    async def list_by_org(self, org_id: str, page: int, page_size: int) -> List[PromptExecution]:
        org_executions = [e for e in self.store.values() if e.org_id == org_id]
        skip = (page - 1) * page_size
        return org_executions[skip : skip + page_size]


from syncsphere.planner.domain.repositories import (
    PlanningSessionRepository,
    PlannerTraceRepository,
    PlannerPromptRepository,
)
from syncsphere.planner.domain.entities import PlanningSession, PlannerTrace

class InMemoryPlanningSessionRepository(PlanningSessionRepository):
    def __init__(self) -> None:
        self.store: Dict[str, PlanningSession] = {}

    async def save(self, session: PlanningSession) -> None:
        self.store[session.id] = session

    async def get_by_id(self, session_id: str) -> Optional[PlanningSession]:
        return self.store.get(session_id)


class InMemoryPlannerTraceRepository(PlannerTraceRepository):
    def __init__(self) -> None:
        self.store: Dict[str, PlannerTrace] = {}

    async def save(self, trace: PlannerTrace) -> None:
        self.store[trace.id] = trace

    async def get_by_id(self, trace_id: str) -> Optional[PlannerTrace]:
        return self.store.get(trace_id)

    async def list_by_session(self, session_id: str) -> List[PlannerTrace]:
        return [t for t in self.store.values() if t.session_id == session_id]


class InMemoryPlannerPromptRepository(PlannerPromptRepository):
    def __init__(self, defaults: Optional[Dict[str, str]] = None) -> None:
        self._prompts = defaults or {}

    async def get_by_name(self, name: str) -> Optional[str]:
        return self._prompts.get(name)

    async def save(self, name: str, content: str) -> None:
        self._prompts[name] = content


from syncsphere.runtime.domain.repositories import ExecutionSessionRepository, ExecutionTraceRepository
from syncsphere.runtime.domain.entities import ExecutionSession, ExecutionTrace

class InMemoryExecutionSessionRepository(ExecutionSessionRepository):
    def __init__(self) -> None:
        self.store: Dict[str, ExecutionSession] = {}

    async def save(self, session: ExecutionSession) -> None:
        self.store[session.id] = session

    async def get_by_id(self, session_id: str) -> Optional[ExecutionSession]:
        return self.store.get(session_id)

    async def list_active(self) -> List[ExecutionSession]:
        from syncsphere.runtime.domain.value_objects import ExecutionState
        active = [
            ExecutionState.CREATED,
            ExecutionState.QUEUED,
            ExecutionState.RUNNING,
            ExecutionState.RETRYING,
            ExecutionState.COMPENSATING,
            ExecutionState.AWAITING_APPROVAL
        ]
        return [s for s in self.store.values() if s.status in active]

class InMemoryExecutionTraceRepository(ExecutionTraceRepository):
    def __init__(self) -> None:
        self.store: Dict[str, ExecutionTrace] = {}

    async def save(self, trace: ExecutionTrace) -> None:
        self.store[trace.id] = trace

    async def get_by_id(self, trace_id: str) -> Optional[ExecutionTrace]:
        return self.store.get(trace_id)

    async def get_by_session(self, session_id: str) -> Optional[ExecutionTrace]:
        for t in self.store.values():
            if t.session_id == session_id:
                return t
        return None


# ──────────────────────────────────────────────────────────────
# Knowledge Platform Bounded Context In-Memory Repositories
# ──────────────────────────────────────────────────────────────

from syncsphere.knowledge.domain.repositories import (
    KnowledgeSourceRepository,
    KnowledgeDocumentRepository,
    KnowledgeChunkRepository,
    SemanticCacheRepository,
    MemoryRepository
)
from syncsphere.knowledge.domain.entities import (
    KnowledgeSource,
    KnowledgeDocument,
    KnowledgeChunk,
    SemanticCacheEntry
)

class InMemoryKnowledgeSourceRepository(KnowledgeSourceRepository):
    def __init__(self) -> None:
        self.store: Dict[str, KnowledgeSource] = {}

    async def save(self, source: KnowledgeSource) -> None:
        self.store[source.id] = source

    async def get_by_id(self, source_id: str) -> Optional[KnowledgeSource]:
        return self.store.get(source_id)

    async def list_by_org(self, org_id: str) -> List[KnowledgeSource]:
        return [s for s in self.store.values() if s.org_id == org_id]

    async def delete(self, source_id: str) -> None:
        if source_id in self.store:
            del self.store[source_id]


class InMemoryKnowledgeDocumentRepository(KnowledgeDocumentRepository):
    def __init__(self) -> None:
        self.store: Dict[str, KnowledgeDocument] = {}

    async def save(self, document: KnowledgeDocument) -> None:
        self.store[document.id] = document

    async def get_by_id(self, doc_id: str) -> Optional[KnowledgeDocument]:
        return self.store.get(doc_id)

    async def list_by_source(self, source_id: str) -> List[KnowledgeDocument]:
        return [d for d in self.store.values() if d.source_id == source_id]

    async def list_by_org(self, org_id: str) -> List[KnowledgeDocument]:
        return [d for d in self.store.values() if d.org_id == org_id]

    async def delete(self, doc_id: str) -> None:
        if doc_id in self.store:
            del self.store[doc_id]


class InMemoryKnowledgeChunkRepository(KnowledgeChunkRepository):
    def __init__(self) -> None:
        self.store: Dict[str, KnowledgeChunk] = {}

    async def save(self, chunk: KnowledgeChunk) -> None:
        self.store[chunk.id] = chunk

    async def get_by_id(self, chunk_id: str) -> Optional[KnowledgeChunk]:
        return self.store.get(chunk_id)

    async def list_by_document(self, doc_id: str) -> List[KnowledgeChunk]:
        return [c for c in self.store.values() if c.document_id == doc_id]

    async def list_by_org(self, org_id: str) -> List[KnowledgeChunk]:
        return [c for c in self.store.values() if c.org_id == org_id]

    async def delete(self, chunk_id: str) -> None:
        if chunk_id in self.store:
            del self.store[chunk_id]

    async def delete_by_document(self, doc_id: str) -> None:
        to_del = [cid for cid, c in self.store.items() if c.document_id == doc_id]
        for cid in to_del:
            del self.store[cid]

    async def delete_by_source(self, source_id: str) -> None:
        to_del = [cid for cid, c in self.store.items() if c.source_id == source_id]
        for cid in to_del:
            del self.store[cid]


class InMemorySemanticCacheRepository(SemanticCacheRepository):
    def __init__(self) -> None:
        self.store: Dict[str, SemanticCacheEntry] = {}

    async def save(self, entry: SemanticCacheEntry) -> None:
        self.store[entry.id] = entry

    async def get_by_id(self, cache_id: str) -> Optional[SemanticCacheEntry]:
        return self.store.get(cache_id)

    async def list_by_org(self, org_id: str) -> List[SemanticCacheEntry]:
        return [e for e in self.store.values() if e.org_id == org_id]

    async def delete(self, cache_id: str) -> None:
        if cache_id in self.store:
            del self.store[cache_id]

    async def clear_by_org(self, org_id: str) -> None:
        to_del = [cid for cid, e in self.store.items() if e.org_id == org_id]
        for cid in to_del:
            del self.store[cid]


class InMemoryMemoryRepository(MemoryRepository):
    def __init__(self) -> None:
        self.store: Dict[str, Dict[str, Any]] = {}

    def _key(self, org_id: str, memory_type: str, resource_id: str) -> str:
        return f"{org_id}:{memory_type}:{resource_id}"

    async def get_memory(self, org_id: str, memory_type: str, resource_id: str) -> Optional[Dict[str, Any]]:
        return self.store.get(self._key(org_id, memory_type, resource_id))

    async def save_memory(self, org_id: str, memory_type: str, resource_id: str, payload: Dict[str, Any]) -> None:
        self.store[self._key(org_id, memory_type, resource_id)] = payload

    async def delete_memory(self, org_id: str, memory_type: str, resource_id: str) -> None:
        key = self._key(org_id, memory_type, resource_id)
        if key in self.store:
            del self.store[key]


# ──────────────────────────────────────────────────────────────
# Approval Context In-Memory Repositories
# ──────────────────────────────────────────────────────────────

from datetime import datetime
from syncsphere.approval.domain.repositories import (
    ApprovalRequestRepository,
    ApprovalDelegateRepository,
    ApprovalPolicyRepository,
    ApprovalTemplateRepository,
)
from syncsphere.approval.domain.entities.approval_request import ApprovalRequest
from syncsphere.approval.domain.entities.approval_delegate import ApprovalDelegate
from syncsphere.approval.domain.entities.approval_policy import ApprovalPolicy
from syncsphere.approval.domain.entities.approval_template import ApprovalTemplate

class InMemoryApprovalRequestRepository(ApprovalRequestRepository):
    def __init__(self) -> None:
        self.store: Dict[str, ApprovalRequest] = {}

    async def get_by_id(self, approval_id: str) -> Optional[ApprovalRequest]:
        return self.store.get(approval_id)

    async def list_by_org(self, org_id: str) -> List[ApprovalRequest]:
        return [r for r in self.store.values() if r.org_id == org_id]

    async def list_pending_by_user(self, org_id: str, user_id: str) -> List[ApprovalRequest]:
        pending = []
        for r in self.store.values():
            if r.org_id == org_id and r.status == "ACTIVE":
                # check if user_id is assigned in current active stage
                active_stage = r.chain.get_current_stage()
                if active_stage:
                    for assignment in active_stage.assignments:
                        if assignment.user_id == user_id:
                            has_voted = any(d.user_id == user_id for d in active_stage.decisions)
                            if not has_voted:
                                pending.append(r)
                                break
        return pending

    async def list_all_pending(self, org_id: str) -> List[ApprovalRequest]:
        return [r for r in self.store.values() if r.org_id == org_id and r.status == "ACTIVE"]

    async def save(self, request: ApprovalRequest) -> None:
        self.store[request.id] = request

    async def delete(self, approval_id: str) -> None:
        if approval_id in self.store:
            del self.store[approval_id]


class InMemoryApprovalDelegateRepository(ApprovalDelegateRepository):
    def __init__(self) -> None:
        self.store: Dict[str, ApprovalDelegate] = {}

    async def get_by_id(self, delegate_id: str) -> Optional[ApprovalDelegate]:
        return self.store.get(delegate_id)

    async def list_by_org(self, org_id: str) -> List[ApprovalDelegate]:
        return [d for d in self.store.values() if d.org_id == org_id]

    async def list_active_delegates_for_user(self, org_id: str, user_id: str) -> List[ApprovalDelegate]:
        now = datetime.utcnow()
        active = []
        for d in self.store.values():
            if d.org_id == org_id and d.from_user_id == user_id:
                # check if currently active
                if d.is_active_at(now):
                    active.append(d)
        return active

    async def save(self, delegate: ApprovalDelegate) -> None:
        self.store[delegate.id] = delegate

    async def delete(self, delegate_id: str) -> None:
        if delegate_id in self.store:
            del self.store[delegate_id]


class InMemoryApprovalPolicyRepository(ApprovalPolicyRepository):
    def __init__(self) -> None:
        self.store: Dict[str, ApprovalPolicy] = {}

    async def get_by_id(self, policy_id: str) -> Optional[ApprovalPolicy]:
        return self.store.get(policy_id)

    async def list_by_org(self, org_id: str) -> List[ApprovalPolicy]:
        return [p for p in self.store.values() if p.org_id == org_id]

    async def save(self, policy: ApprovalPolicy) -> None:
        self.store[policy.id] = policy

    async def delete(self, policy_id: str) -> None:
        if policy_id in self.store:
            del self.store[policy_id]


class InMemoryApprovalTemplateRepository(ApprovalTemplateRepository):
    def __init__(self) -> None:
        self.store: Dict[str, ApprovalTemplate] = {}

    async def get_by_id(self, template_id: str) -> Optional[ApprovalTemplate]:
        return self.store.get(template_id)

    async def list_by_org(self, org_id: str) -> List[ApprovalTemplate]:
        return [t for t in self.store.values() if t.org_id == org_id]

    async def save(self, template: ApprovalTemplate) -> None:
        self.store[template.id] = template

    async def delete(self, template_id: str) -> None:
        if template_id in self.store:
            del self.store[template_id]


# ──────────────────────────────────────────────────────────────
# Observability Bounded Context In-Memory Repositories
# ──────────────────────────────────────────────────────────────

from syncsphere.observability.domain.repositories import (
    TraceRepository, ReplayRepository, MetricRepository, AlertRepository, HealthRepository, LogRepository, EventStoreRepository
)
from syncsphere.observability.domain.entities.trace import Trace
from syncsphere.observability.domain.entities.replay import ExecutionReplay, WorkflowReplay, PlannerReplay
from syncsphere.observability.domain.entities.log import StructuredLog
from syncsphere.observability.domain.entities.metric_series import MetricSeries
from syncsphere.observability.domain.entities.alert import Alert
from syncsphere.observability.domain.entities.health import HealthCheck
from syncsphere.observability.domain.entities.event_store import EventStoreEntry
from syncsphere.observability.domain.value_objects import HealthStatus, ServiceStatus, Metric, AlertPolicy, AlertRule, AlertCondition

class InMemoryTraceRepository(TraceRepository):
    def __init__(self) -> None:
        self.traces: Dict[str, Trace] = {}

    async def save(self, trace: Trace) -> None:
        self.traces[trace.correlation_id] = trace

    async def get_by_correlation_id(self, org_id: str, correlation_id: str) -> Optional[Trace]:
        return self.traces.get(correlation_id)

    async def list_by_org(self, org_id: str, limit: int = 100) -> List[Trace]:
        return [t for t in self.traces.values() if t.org_id == org_id][:limit]

class InMemoryReplayRepository(ReplayRepository):
    def __init__(self) -> None:
        self.exe_replays: Dict[str, ExecutionReplay] = {}
        self.wf_replays: Dict[str, WorkflowReplay] = {}
        self.pl_replays: Dict[str, PlannerReplay] = {}

    async def save_execution_replay(self, replay: ExecutionReplay) -> None:
        self.exe_replays[replay.session_id] = replay

    async def get_execution_replay(self, org_id: str, session_id: str) -> Optional[ExecutionReplay]:
        return self.exe_replays.get(session_id)

    async def save_workflow_replay(self, replay: WorkflowReplay) -> None:
        self.wf_replays[replay.workflow_id] = replay

    async def get_workflow_replay(self, org_id: str, workflow_id: str) -> Optional[WorkflowReplay]:
        return self.wf_replays.get(workflow_id)

    async def save_planner_replay(self, replay: PlannerReplay) -> None:
        self.pl_replays[replay.planner_session_id] = replay

    async def get_planner_replay(self, org_id: str, planner_session_id: str) -> Optional[PlannerReplay]:
        return self.pl_replays.get(planner_session_id)

class InMemoryMetricRepository(MetricRepository):
    def __init__(self) -> None:
        self.series: Dict[str, MetricSeries] = {}

    async def save_series(self, series: MetricSeries) -> None:
        self.series[series.metric_name] = series

    async def get_series(self, org_id: str, metric_name: str, start_time: Optional[Any] = None, end_time: Optional[Any] = None) -> Optional[MetricSeries]:
        s = self.series.get(metric_name)
        if s and s.org_id == org_id:
            return s
        return None

    async def list_metric_names(self, org_id: str) -> List[str]:
        return [s.metric_name for s in self.series.values() if s.org_id == org_id]

class InMemoryAlertRepository(AlertRepository):
    def __init__(self) -> None:
        self.alerts: Dict[str, Alert] = {}

    async def save(self, alert: Alert) -> None:
        self.alerts[alert.id] = alert

    async def get_by_id(self, org_id: str, alert_id: str) -> Optional[Alert]:
        return self.alerts.get(alert_id)

    async def list_active(self, org_id: str) -> List[Alert]:
        return [a for a in self.alerts.values() if a.org_id == org_id and a.status == "ACTIVE"]

    async def list_all(self, org_id: str, limit: int = 100) -> List[Alert]:
        return [a for a in self.alerts.values() if a.org_id == org_id][:limit]

class InMemoryHealthRepository(HealthRepository):
    def __init__(self) -> None:
        self.checks: List[HealthCheck] = []

    async def save(self, check: HealthCheck) -> None:
        self.checks.append(check)

    async def get_latest(self, org_id: str) -> Optional[HealthCheck]:
        valid = [c for c in self.checks if c.org_id == org_id]
        return valid[-1] if valid else None

class InMemoryLogRepository(LogRepository):
    def __init__(self) -> None:
        self.logs: List[StructuredLog] = []

    async def save(self, log: StructuredLog) -> None:
        self.logs.append(log)

    async def list_logs(self, org_id: str, correlation_id: Optional[str] = None, level: Optional[str] = None, limit: int = 100) -> List[StructuredLog]:
        res = [l for l in self.logs if l.org_id == org_id]
        if correlation_id:
            res = [l for l in res if l.correlation_id == correlation_id]
        if level:
            res = [l for l in res if l.level == level]
        return res[:limit]

class InMemoryEventStoreRepository(EventStoreRepository):
    def __init__(self) -> None:
        self.events: List[EventStoreEntry] = []

    async def save(self, entry: EventStoreEntry) -> None:
        self.events.append(entry)

    async def get_by_id(self, org_id: str, event_id: str) -> Optional[EventStoreEntry]:
        for e in self.events:
            if e.org_id == org_id and e.event_id == event_id:
                return e
        return None

    async def search(self, org_id: str, event_type: Optional[str] = None, correlation_id: Optional[str] = None, limit: int = 100) -> List[EventStoreEntry]:
        res = [e for e in self.events if e.org_id == org_id]
        if event_type:
            res = [e for e in res if e.event_type == event_type]
        if correlation_id:
            res = [e for e in res if e.correlation_id == correlation_id]
        return res[:limit]




