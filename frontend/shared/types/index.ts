// --- Auth & Identity Types ---
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  org_id: string;
  role_ids: string[];
  status: 'registered' | 'active' | 'suspended';
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
}

export interface Role {
  id: string;
  org_id: string;
  name: string;
  description: string;
  permissions: Permission[];
}

export interface Permission {
  resource_type: string;
  resource_id: string;
  actions: string[];
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  expires_at?: string;
}

// --- Connector Types ---
export interface Connector {
  id: string;
  org_id: string;
  name: string;
  connector_type: 'slack' | 'github' | 'jira' | 'custom' | string;
  status: 'enabled' | 'disabled' | 'error';
  config: Record<string, any>;
  tools: ToolDefinition[];
  created_at: string;
}

export interface ToolDefinition {
  name: string;
  description: string;
  input_schema: Record<string, any>;
}

export interface ToolResult {
  is_error: boolean;
  content: string;
  meta?: Record<string, any>;
}

// --- AI Platform Types ---
export interface AIModel {
  id: string;
  org_id: string;
  provider_id: string;
  name: string;
  display_name: string;
  capabilities: string[];
  context_window: number;
  max_output_tokens: number;
  cost_per_1k_input: number;
  cost_per_1k_output: number;
  is_active: boolean;
}

export interface ModelProvider {
  id: string;
  org_id: string;
  name: string;
  api_url_override?: string;
  priority_level: number;
  is_healthy: boolean;
}

export interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  latest_version: number;
  versions_count?: number;
  created_at: string;
  variables?: Record<string, any>[];
  versions?: {
    version: number;
    system_template: string;
    user_template: string;
    created_at: string;
    hash?: string;
  }[];
}

export interface PromptVersion {
  id: string;
  prompt_template_id: string;
  version: number;
  system_template: string;
  user_template: string;
  created_at: string;
}

export interface PromptExecution {
  id: string;
  org_id: string;
  prompt_template_id: string;
  version: number;
  model_id: string;
  latency_ms: number;
  tokens_used: number;
  cost: number;
}

// --- Workflow Types ---
export interface WorkflowNode {
  id: string;
  type: string;
  label: string;
  config: Record<string, any>;
}

export interface WorkflowEdge {
  source: string;
  target: string;
  condition?: string;
}

export interface Workflow {
  id: string;
  org_id: string;
  name: string;
  description: string;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  active_version: number;
  created_at: string;
}

// --- Planner Types ---
export interface PlanningSession {
  id: string;
  org_id: string;
  user_prompt: string;
  status: 'planning' | 'completed' | 'failed';
  workflow_id?: string;
}

export interface PlannerTrace {
  id: string;
  session_id: string;
  phase: string;
  status: string;
  payload: Record<string, any>;
  timestamp: string;
}

// --- Runtime Types ---
export interface ExecutionSession {
  id: string;
  org_id: string;
  workflow_id: string;
  version: number;
  status: 'running' | 'completed' | 'failed' | 'paused' | 'cancelled';
  variables: Record<string, any>;
  step_states: Record<string, any>;
  created_at: string;
}

export interface ExecutionTrace {
  id: string;
  session_id: string;
  span_id: string;
  node_id: string;
  status: string;
  output?: Record<string, any>;
  error?: string;
  started_at: string;
  completed_at?: string;
}

// --- Approval Types ---
export interface ApprovalRequest {
  id: string;
  org_id: string;
  title: string;
  description?: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'ESCALATED' | 'CANCELLED';
  context?: Record<string, any>;
  workflow_id?: string;
  node_id?: string;
  session_id?: string;
  chain?: any;
  created_at: string;
  completed_at?: string;
}

export interface ApprovalDelegate {
  id: string;
  org_id: string;
  from_user_id: string;
  to_user_id: string;
  is_active: boolean;
}

// --- Observability Types ---
export interface TraceSpan {
  span_id: string;
  parent_span_id?: string;
  name: string;
  status: string;
  start_time: string;
  end_time?: string;
  attributes: Record<string, any>;
}

export interface Trace {
  correlation_id: string;
  org_id: string;
  spans: TraceSpan[];
}

export interface MetricPoint {
  timestamp: string;
  value: number;
}

export interface MetricSeries {
  metric_name: string;
  org_id: string;
  data_points: MetricPoint[];
}

export interface Alert {
  id: string;
  org_id: string;
  name: string;
  message: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  status: 'ACTIVE' | 'RESOLVED';
  created_at: string;
}

export interface HealthCheck {
  overall_status: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY';
  services: {
    name: string;
    status: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY';
    latency_ms: number;
  }[];
  timestamp: string;
}

// --- Task Management Types ---
export type TaskPriority = 'High' | 'Medium' | 'Low';
export type TaskStatus = 'Pending' | 'In Progress' | 'Completed';

export interface TaskAutomation {
  action: string;
  config: Record<string, any>;
  status: string;
  error?: string;
  executed_at?: string;
  result?: Record<string, any>;
}

export interface Task {
  id: string;
  org_id: string;
  title: string;
  description: string;
  assigned_to: string;
  priority: TaskPriority;
  status: TaskStatus;
  due_date: string | null;
  automations?: TaskAutomation[];
  created_at: string;
  updated_at: string;
}
