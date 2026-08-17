import { apiClient } from '../api-client';
import * as T from '../../types';

interface ApiResponse<T> {
  status: string;
  data: T;
}

// ==========================================
// 1. Identity & Access API Calls
// ==========================================
export const identityApi = {
  register: (payload: any) => apiClient.post('/v1/auth/register', payload).then(r => r.data.data),
  login: (payload: any) => apiClient.post('/v1/auth/login', payload).then(r => r.data.data),
  getMe: () => apiClient.get('/v1/users/me').then(r => r.data.data),
  getOrgs: () => apiClient.get('/v1/organizations/current').then(r => r.data.data),

  getApiKeys: () => apiClient.get('/v1/users/me/keys').then(r => r.data.data),
  createApiKey: (payload: { name: string }) => apiClient.post('/v1/users/me/keys', payload).then(r => r.data.data),
};

// ==========================================
// 2. Connector Framework API Calls
// ==========================================
export const connectorApi = {
  listConnectors: () => apiClient.get<ApiResponse<T.Connector[]>>('/v1/connectors').then(r => r.data.data),
  getConnector: (id: string) => apiClient.get<ApiResponse<T.Connector>>(`/v1/connectors/${id}`).then(r => r.data.data),
  registerConnector: (payload: any) => apiClient.post('/v1/connectors', payload).then(r => r.data.data),
  deleteConnector: (id: string) => apiClient.delete(`/v1/connectors/${id}`).then(r => r.data.data),
  callTool: (connectorName: string, toolName: string, payload: any) =>
    apiClient.post<ApiResponse<T.ToolResult>>(`/v1/connectors/${connectorName}/tools/${toolName}/call`, payload).then(r => r.data.data),
};

// ==========================================
// 3. AI Infrastructure API Calls
// ==========================================
export const aiApi = {
  listModels: () => apiClient.get<ApiResponse<T.AIModel[]>>('/v1/ai/models').then(r => r.data.data),
  listProviders: () => apiClient.get<ApiResponse<T.ModelProvider[]>>('/v1/ai/providers').then(r => r.data.data),
  listPrompts: () => apiClient.get<ApiResponse<T.PromptTemplate[]>>('/v1/ai/prompts').then(r => r.data.data),
  createPrompt: (payload: any) => apiClient.post('/v1/ai/prompts', payload).then(r => r.data.data),
  getPromptHistory: (templateId: string) => apiClient.get(`/v1/ai/prompts/${templateId}/history`).then(r => r.data.data),
};

// ==========================================
// 4. Agentic Planner API Calls
// ==========================================
export const plannerApi = {
  generatePlan: (prompt: string, strategy: string = 'simple') =>
    apiClient.post('/v1/planner/generate', { prompt, strategy }).then(r => r.data.data),
  improvePlan: (sessionId: string, feedback: string) =>
    apiClient.post('/v1/planner/improve', { session_id: sessionId, feedback }).then(r => r.data.data),
  explainPlan: (sessionId: string) =>
    apiClient.post('/v1/planner/explain', { session_id: sessionId }).then(r => r.data.data),
  getPlanningTraces: (sessionId: string) =>
    apiClient.get<ApiResponse<T.PlannerTrace[]>>(`/v1/planner/traces?session_id=${sessionId}`).then(r => r.data.data),
};

// ==========================================
// 5. Workflow Bounded Context API Calls
// ==========================================
export const workflowApi = {
  listWorkflows: () => apiClient.get<ApiResponse<T.Workflow[]>>('/v1/workflows').then(r => r.data.data),
  getWorkflow: (id: string) => apiClient.get<ApiResponse<T.Workflow>>(`/v1/workflows/${id}`).then(r => r.data.data),
  createWorkflow: (payload: any) => apiClient.post('/v1/workflows', payload).then(r => r.data.data),
  updateWorkflow: (id: string, payload: any) => apiClient.put(`/v1/workflows/${id}`, payload).then(r => r.data.data),
  deleteWorkflow: (id: string) => apiClient.delete(`/v1/workflows/${id}`).then(r => r.data.data),
};

// ==========================================
// 6. Execution Runtime API Calls
// ==========================================
export const runtimeApi = {
  startExecution: (workflowId: string, variables: Record<string, any> = {}) =>
    apiClient.post<ApiResponse<T.ExecutionSession>>('/v1/runtime/start', { workflow_id: workflowId, variables }).then(r => r.data.data),
  getExecutions: () => apiClient.get<ApiResponse<T.ExecutionSession[]>>('/v1/runtime/executions').then(r => r.data.data),
  getExecutionDetails: (sessionId: string) =>
    apiClient.get<ApiResponse<T.ExecutionSession>>(`/v1/runtime/executions/${sessionId}`).then(r => r.data.data),
  getExecutionTraces: (sessionId: string) =>
    apiClient.get<ApiResponse<T.ExecutionTrace[]>>(`/v1/runtime/executions/${sessionId}/traces`).then(r => r.data.data),
  pauseExecution: (sessionId: string) => apiClient.post(`/v1/runtime/executions/${sessionId}/pause`).then(r => r.data.data),
  resumeExecution: (sessionId: string) => apiClient.post(`/v1/runtime/executions/${sessionId}/resume`).then(r => r.data.data),
  cancelExecution: (sessionId: string) => apiClient.post(`/v1/runtime/executions/${sessionId}/cancel`).then(r => r.data.data),
};

// ==========================================
// 7. Knowledge Platform API Calls
// ==========================================
export const knowledgeApi = {
  listSources: () => apiClient.get('/v1/knowledge/sources').then(r => r.data.data),
  importSource: (payload: any) => apiClient.post('/v1/knowledge/import', payload).then(r => r.data.data),
  searchKnowledge: (query: string, limit: number = 5) =>
    apiClient.post('/v1/knowledge/search', { query, limit }).then(r => r.data.data),
  getGraph: () => apiClient.get('/v1/knowledge/graph').then(r => r.data.data),
};

// ==========================================
// 8. Human Approval Gates API Calls
// ==========================================
export const approvalApi = {
  listPendingApprovals: () => apiClient.get<ApiResponse<T.ApprovalRequest[]>>('/v1/approvals/pending').then(r => r.data.data),
  submitDecision: (approvalId: string, approved: boolean, notes: string = '') =>
    apiClient.post(`/v1/approvals/submit`, { approval_id: approvalId, approved, notes }).then(r => r.data.data),
  listDelegates: () => apiClient.get<ApiResponse<T.ApprovalDelegate[]>>('/v1/approvals/delegates').then(r => r.data.data),
  createDelegate: (payload: any) => apiClient.post('/v1/approvals/delegate', payload).then(r => r.data.data),
};

// ==========================================
// 9. Enterprise Observability API Calls
// ==========================================
export const observabilityApi = {
  listTraces: () => apiClient.get<ApiResponse<T.Trace[]>>('/v1/observability/traces').then(r => r.data.data),
  getTraceDetails: (correlationId: string) =>
    apiClient.get<ApiResponse<T.Trace>>(`/v1/observability/traces/${correlationId}`).then(r => r.data.data),
  getReplay: (sessionId: string, type: 'execution' | 'workflow' | 'planner' = 'execution') =>
    apiClient.get(`/v1/observability/replay/${sessionId}?type=${type}`).then(r => r.data.data),
  getMetrics: (metricName: string) =>
    apiClient.get<ApiResponse<T.MetricSeries>>(`/v1/observability/metrics?metric_name=${metricName}`).then(r => r.data.data),
  getDashboardStats: () => apiClient.get('/v1/observability/dashboard').then(r => r.data.data),
  getHealthReport: () => apiClient.get<ApiResponse<T.HealthCheck>>('/v1/observability/health').then(r => r.data.data),
  listAlerts: () => apiClient.get<ApiResponse<T.Alert[]>>('/v1/observability/alerts').then(r => r.data.data),
  createAlert: (payload: any) => apiClient.post('/v1/observability/alerts', payload).then(r => r.data.data),
};

// ==========================================
// 10. Task Management API Calls
// ==========================================
export const tasksApi = {
  listTasks: (params?: { priority?: string; task_status?: string }) =>
    apiClient.get<ApiResponse<T.Task[]>>('/v1/tasks', { params }).then(r => r.data.data),
  getTask: (id: string) =>
    apiClient.get<ApiResponse<T.Task>>(`/v1/tasks/${id}`).then(r => r.data.data),
  createTask: (payload: {
    title: string;
    description?: string;
    assigned_to?: string;
    priority?: T.TaskPriority;
    status?: T.TaskStatus;
    due_date?: string | null;
    automations?: any[];
  }) => apiClient.post<ApiResponse<T.Task>>('/v1/tasks', payload).then(r => r.data.data),
  updateTask: (id: string, payload: Partial<{
    title: string;
    description: string;
    assigned_to: string;
    priority: T.TaskPriority;
    status: T.TaskStatus;
    due_date: string | null;
  }>) => apiClient.put<ApiResponse<T.Task>>(`/v1/tasks/${id}`, payload).then(r => r.data.data),
  deleteTask: (id: string) =>
    apiClient.delete<ApiResponse<boolean>>(`/v1/tasks/${id}`).then(r => r.data.data),
  planWithAI: (description: string) =>
    apiClient.post('/v1/tasks/plan-with-ai', { prompt: description }, { timeout: 60000 }).then(r => r.data.data),
  confirmPlan: (payload: any) =>
    apiClient.post('/v1/tasks/confirm-plan', payload).then(r => r.data.data),
};
