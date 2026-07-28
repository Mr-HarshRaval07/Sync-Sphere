from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

class ExecutionState(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    WAITING = "WAITING"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    RETRYING = "RETRYING"
    COMPENSATING = "COMPENSATING"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class ExecutionPolicy(str, Enum):
    BALANCED = "BalancedExecution"
    AGGRESSIVE_PARALLEL = "AggressiveParallelExecution"
    SAFE = "SafeExecution"
    LOW_MEMORY = "LowMemoryExecution"

class ExecutionContext(BaseModel):
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

class ExecutionResult(BaseModel):
    node_id: str
    status: ExecutionState
    outputs: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0.0

class ExecutionMetrics(BaseModel):
    total_execution_time_ms: float = 0.0
    steps_completed: int = 0
    steps_failed: int = 0
    retry_count: int = 0

class ExecutionLock(BaseModel):
    lock_key: str
    owner_id: str
    acquired_at: datetime = Field(default_factory=datetime.utcnow)

class ExecutionLease(BaseModel):
    lease_id: str
    resource_id: str
    expires_at: datetime

class ExecutionStep(BaseModel):
    node_id: str
    name: str
    type: str
    status: ExecutionState = ExecutionState.CREATED
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retries_attempted: int = 0

class ExecutionCheckpoint(BaseModel):
    checkpoint_id: str
    session_id: str
    step_states: Dict[str, ExecutionStep] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ExecutionSnapshot(BaseModel):
    snapshot_id: str
    checkpoint_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class ExecutionTimeline(BaseModel):
    events: List[Dict[str, Any]] = Field(default_factory=list)

class ExecutionHistory(BaseModel):
    history_id: str
    events: List[Dict[str, Any]] = Field(default_factory=list)

class ExecutionError(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

class ExecutionFailure(BaseModel):
    error: ExecutionError
    fatal: bool = False

class ExecutionWarning(BaseModel):
    node_id: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ExecutionRetry(BaseModel):
    node_id: str
    attempt: int
    next_retry_at: datetime
    error_message: str

class ASTNode(BaseModel):
    node_id: str
    name: str
    type: str
    dependencies: List[str] = Field(default_factory=list)

class ExecutionAST(BaseModel):
    """Internal runtime representation derived from ExecutionPlan which can be modified during runs."""
    workflow_id: str
    version: int
    nodes: Dict[str, ASTNode] = Field(default_factory=dict)
    topological_order: List[str] = Field(default_factory=list)

class WorkerLease(BaseModel):
    worker_id: str
    heartbeat_at: datetime = Field(default_factory=datetime.utcnow)
    active_slots: int = 10

class ExecutionCursor(BaseModel):
    current_nodes: List[str] = Field(default_factory=list)
    completed_nodes: List[str] = Field(default_factory=list)

class ExecutionStatistics(BaseModel):
    success_rate: float = 1.0
    average_latency_ms: float = 0.0

class ExecutionArtifacts(BaseModel):
    created_files: List[str] = Field(default_factory=list)
