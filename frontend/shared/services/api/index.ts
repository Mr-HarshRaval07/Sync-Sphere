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
  updateProfile: (payload: any) => apiClient.patch('/v1/users/me', payload).then(r => r.data.data),
  getOrgs: () => apiClient.get('/v1/organizations/current').then(r => r.data.data),

  getApiKeys: () => apiClient.get('/v1/developer-keys').then(r => r.data),
  createApiKey: (payload: { name: string }) => apiClient.post('/v1/developer-keys', payload).then(r => r.data),
  deleteApiKey: (id: string) => apiClient.delete(`/v1/developer-keys/${id}`).then(r => r.data),
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
  listModels: () => apiClient.get('/v1/tasks/debug-models').then(r => r.data.models || []),
  listProviders: () => apiClient.get('/v1/tasks/debug-models').then(r => r.data.providers || []),
  listPrompts: () => apiClient.get<ApiResponse<T.PromptTemplate[]>>('/v1/ai/prompts').then(r => r.data.data),
  getPrompt: (name: string) => apiClient.get<ApiResponse<T.PromptTemplate>>(`/v1/ai/prompts/${name}`).then(r => r.data.data),
  createPrompt: (payload: any) => apiClient.post('/v1/ai/prompts', payload).then(r => r.data.data),
  updatePrompt: (name: string, payload: any) => apiClient.put(`/v1/ai/prompts/${name}`, payload).then(r => r.data.data),
  compilePrompt: (name: string, payload: any) => apiClient.post(`/v1/ai/prompts/${name}/compile`, payload).then(r => r.data.data),
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
  updateWorkflow: (id: string, payload: any) => apiClient.patch(`/v1/workflows/${id}`, payload).then(r => r.data.data),
  deleteWorkflow: (id: string) => apiClient.delete(`/v1/workflows/${id}`).then(r => r.data.data),
  publishWorkflow: (id: string, payload: any = {}) => apiClient.post(`/v1/workflows/${id}/publish`, payload).then(r => r.data.data),
  getWorkflowVersions: (id: string) => apiClient.get(`/v1/workflows/${id}/versions`).then(r => r.data.data),
};

export const automationApi = {
  listAutomations: () => apiClient.get<ApiResponse<any[]>>('/v1/automations').then(r => r.data.data),
  createAutomation: (payload: any) => apiClient.post('/v1/automations', payload).then(r => r.data.data),
  triggerAutomation: (id: string) => apiClient.post(`/v1/automations/${id}/trigger`).then(r => r.data.data),
  toggleAutomation: (id: string) => apiClient.patch(`/v1/automations/${id}/toggle`).then(r => r.data.data),
  deleteAutomation: (id: string) => apiClient.delete(`/v1/automations/${id}`).then(r => r.data.data),
  duplicateAutomation: (id: string) => apiClient.post(`/v1/automations/${id}/duplicate`).then(r => r.data.data),
  scheduleAutomation: (id: string, payload: any) => apiClient.post(`/v1/automations/${id}/schedule`, payload).then(r => r.data.data),
  listScheduled: () => apiClient.get('/v1/automations/scheduled').then(r => r.data.data),
};

// ==========================================
// 6. Execution Runtime API Calls
// ==========================================
export const runtimeApi = {
  startExecution: (workflowId: string, inputs: Record<string, any> = {}) =>
    apiClient.post<ApiResponse<T.ExecutionSession>>('/v1/runtime/start', { workflow_id: workflowId, inputs }).then(r => r.data.data),
  getExecutions: () => apiClient.get<ApiResponse<any[]>>('/v1/automations/executions').then(r => r.data.data),
  getExecutionDetails: (sessionId: string) =>
    apiClient.get<ApiResponse<T.ExecutionSession>>(`/v1/runtime/status/${sessionId}`).then(r => r.data.data),
  getExecutionTraces: (sessionId: string) =>
    apiClient.get<ApiResponse<T.ExecutionTrace[]>>(`/v1/runtime/history/${sessionId}`).then(r => r.data.data),
  pauseExecution: (sessionId: string) => apiClient.post(`/v1/runtime/pause`, { session_id: sessionId }).then(r => r.data.data),
  resumeExecution: (sessionId: string) => apiClient.post(`/v1/runtime/resume`, { session_id: sessionId }).then(r => r.data.data),
  cancelExecution: (sessionId: string) => apiClient.post(`/v1/runtime/cancel`, { session_id: sessionId }).then(r => r.data.data),
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
  listPendingApprovals: () => apiClient.get<ApiResponse<T.ApprovalRequest[]>>('/v1/approvals').then(r => r.data.data),
  submitDecision: (approvalId: string, approved: boolean, notes: string = '') =>
    apiClient.post(`/v1/approvals/${approvalId}/${approved ? 'approve' : 'reject'}`, { comment: notes }).then(r => r.data.data),
  listDelegates: () => apiClient.get<ApiResponse<T.ApprovalDelegate[]>>('/v1/approvals/delegates').then(r => r.data.data),
  createDelegate: (payload: any) => apiClient.post(`/v1/approvals/${payload.approval_id}/delegate`, payload).then(r => r.data.data),
  getHistory: (approvalId: string) => apiClient.get(`/v1/approvals/${approvalId}/history`).then(r => r.data.data),
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
  resolveAlert: (alertId: string, status: string = 'RESOLVED') => apiClient.patch(`/v1/observability/alerts/${alertId}/resolve`, { status }).then(r => r.data.data),
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
  saveAsWorkflow: (id: string) =>
    apiClient.post(`/v1/tasks/${id}/save-as-workflow`).then(r => r.data.data),
  executeTaskAutomation: (id: string) =>
    apiClient.post(`/v1/tasks/${id}/execute-automation`).then(r => r.data.data),
  scheduleTask: (id: string, payload: any) =>
    apiClient.post(`/v1/tasks/${id}/schedule`, payload).then(r => r.data.data),
};

// ==========================================
// 11. Scheduled Workflows API Calls
// ==========================================
export const scheduleApi = {
  listSchedules: () => apiClient.get('/v1/schedules').then(r => r.data.data),
  createSchedule: (payload: any) => apiClient.post('/v1/schedules', payload).then(r => r.data.data),
  updateSchedule: (id: string, payload: any) => apiClient.put(`/v1/schedules/${id}`, payload).then(r => r.data.data),
  deleteSchedule: (id: string) => apiClient.delete(`/v1/schedules/${id}`).then(r => r.data.data),
  toggleSchedule: (id: string, enabled: boolean) => apiClient.patch(`/v1/schedules/${id}/toggle`, { enabled }).then(r => r.data.data),
  runScheduleNow: (id: string) => apiClient.post(`/v1/schedules/${id}/run-now`).then(r => r.data.data),
};
