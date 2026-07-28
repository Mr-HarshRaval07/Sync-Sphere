import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';
import { useAuthStore } from '../stores/authStore';
import { useOrgStore } from '../stores/orgStore';

// Determine the base backend URL
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
console.log("API_BASE_URL =", API_BASE_URL);
console.log("MOCK_API =", process.env.NEXT_PUBLIC_MOCK_API);

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 90000,  // 90s — Gemini AI calls can take 20-40s
});

// Cache for mock DB to maintain state in offline mode
const MOCK_DB: Record<string, any[]> = {
  connectors: [
    {
      id: 'conn-slack-id',
      org_id: 'org-default',
      name: 'Slack Sync',
      connector_type: 'slack',
      status: 'enabled',
      config: { channel: '#all-janhvi' },
      tools: [{ name: 'post_message', description: 'Post Slack msg', input_schema: {} }],
      created_at: new Date().toISOString(),
    },
    {
      id: 'conn-github-id',
      org_id: 'org-default',
      name: 'GitHub Agent',
      connector_type: 'github',
      status: 'disabled',
      config: { repo: 'syncsphere/backend' },
      tools: [{ name: 'create_branch', description: 'Create git branch', input_schema: {} }],
      created_at: new Date().toISOString(),
    },
  ],
  models: [
    { id: 'm-gpt4o', org_id: 'org-default', provider_id: 'openai', name: 'gpt-4o', display_name: 'GPT-4 Omni', capabilities: ['text_generation'], context_window: 128000, max_output_tokens: 4096, cost_per_1k_input: 0.005, cost_per_1k_output: 0.015, is_active: true },
    { id: 'm-claude35', org_id: 'org-default', provider_id: 'anthropic', name: 'claude-3-5-sonnet', display_name: 'Claude 3.5 Sonnet', capabilities: ['text_generation', 'reasoning'], context_window: 200000, max_output_tokens: 8192, cost_per_1k_input: 0.003, cost_per_1k_output: 0.015, is_active: true },
  ],
  prompts: [
    { id: 'pr-welcome', org_id: 'org-default', name: 'Customer Welcome', description: 'Template to welcome new signups', system_template: 'You are custom service. Welcome {{name}}.', user_template: 'Generate welcome message for {{name}}.', variables: [{ name: 'name', required: true }], active_version: 1 },
  ],
  workflows: [
    {
      id: 'wf-1',
      org_id: 'org-default',
      name: 'GitHub to Slack Notifier',
      description: 'Auto notify Slack on Git PR actions',
      status: 'PUBLISHED',
      nodes: [
        { id: 'n1', type: 'trigger', label: 'PR Opened', config: {} },
        { id: 'n2', type: 'action', label: 'Slack Msg', config: {} },
      ],
      edges: [{ source: 'n1', target: 'n2' }],
      active_version: 1,
      created_at: new Date().toISOString(),
    },
  ],
  executions: [
    { id: 'exe-1', org_id: 'org-default', workflow_id: 'wf-1', version: 1, status: 'completed', variables: { pr_id: '123' }, step_states: { n1: 'success', n2: 'success' }, created_at: new Date().toISOString() },
  ],
  approvals: [
    { id: 'appr-1', org_id: 'org-default', session_id: 'exe-1', node_id: 'n2', status: 'APPROVED', routing_strategy: 'Sequential', created_at: new Date().toISOString() },
  ],
  alerts: [
    { id: 'alert-1', org_id: 'org-default', name: 'Slack Rate Breach', message: 'Slack API rate limit warning.', severity: 'WARNING', status: 'ACTIVE', created_at: new Date().toISOString() },
  ],
  tasks: [
    { id: 'task-1', org_id: 'org-default', title: 'Set up Slack integration', description: 'Configure Slack OAuth and test notifications', assigned_to: 'Alice', priority: 'High', status: 'In Progress', due_date: '2026-08-01', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    { id: 'task-2', org_id: 'org-default', title: 'Review workflow DAG design', description: 'Check the planner DAG for edge case handling', assigned_to: 'Bob', priority: 'Medium', status: 'Pending', due_date: '2026-08-15', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  ],
};

// Request Interceptor: Attach Auth & Multi-Tenancy headers
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    const currentOrg = useOrgStore.getState().currentOrg;
    if (currentOrg) {
      config.headers['X-Org-ID'] = currentOrg.id;
    }
    // Generate simple correlation ID for tracing
    config.headers['X-Correlation-ID'] = `frontend-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    return config;
  },
  (error) => Promise.reject(error)
);

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response Interceptor: Manage JWT Rotation & Token Refresh, or handle mock fallbacks
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Dev/offline/mock fallback:
    // - explicit mock mode (NEXT_PUBLIC_MOCK_API=true)
    // - or validation failures (400) from backend while DB is empty
    const isMockMode = process.env.NEXT_PUBLIC_MOCK_API === 'true';
    if (isMockMode) {
      return handleMockRequest(originalRequest);
    }

    // Handle 401: only force-logout if a token was actually sent with the request.
    // If originalRequest.headers.Authorization is absent the call was made before
    // Zustand had a chance to hydrate the token from localStorage (e.g. right after
    // an OAuth redirect).  In that case we must NOT wipe auth state — the user IS
    // logged in, the store just hasn't rehydrated yet.
    if (error.response?.status === 401 && !originalRequest._retry) {
      const tokenWasSent = !!originalRequest.headers?.Authorization;
      if (tokenWasSent) {
        if (isRefreshing) {
          return new Promise(function (resolve, reject) {
            failedQueue.push({ resolve, reject });
          }).then(token => {
            originalRequest.headers.Authorization = 'Bearer ' + token;
            return apiClient(originalRequest);
          }).catch(err => Promise.reject(err));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        return new Promise(function (resolve, reject) {
          axios.post(`${API_BASE_URL}/v1/auth/refresh`, {}, { withCredentials: true })
            .then(res => {
              const { access_token } = res.data.data;
              // Update Zustand store without relying on user! by doing a partial update if needed,
              // but since user should exist, use getState().user
              const user = useAuthStore.getState().user;
              if (user) {
                useAuthStore.getState().login(access_token, user);
              }
              originalRequest.headers.Authorization = 'Bearer ' + access_token;
              processQueue(null, access_token);
              resolve(apiClient(originalRequest));
            })
            .catch(err => {
              processQueue(err, null);

              const isInvalidGrant = err.response?.status === 400 || err.response?.status === 401;
              if (isInvalidGrant) {
                useAuthStore.getState().logout();
                if (typeof window !== 'undefined') {
                  window.location.href = '/login';
                }
              }

              reject(err);
            })
            .finally(() => {
              isRefreshing = false;
            });
        });
      } else {
        useAuthStore.getState().logout();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      }
      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

// Helper Mock Handler for offline mock databases
async function handleMockRequest(config: any): Promise<AxiosResponse<any>> {
  const url = config.url || '';
  const method = (config.method || 'get').toLowerCase();
  const data = config.data ? JSON.parse(config.data) : null;

  console.log(`[Mock API] Intercepted ${method.toUpperCase()} ${url}`, data);

  // Helper builder function for mock Axios response envelopes
  const respond = (status: number, payload: any): AxiosResponse<any> => ({
    data: { data: payload },
    status,
    statusText: 'OK',
    headers: {},
    config,
  });

  // Mock Identity Paths
  if (url.includes('/v1/auth/register')) {
    const user = { id: 'u-' + Date.now(), email: data.email, first_name: data.first_name, last_name: data.last_name, org_id: 'org-123', role_ids: ['admin'], status: 'registered', created_at: new Date().toISOString() };
    return respond(201, { user_id: user.id, status: 'registered' });
  }
  if (url.includes('/v1/auth/login')) {
    const user = { id: 'u-admin', email: data.email, first_name: 'Admin', last_name: 'User', org_id: 'org-123', role_ids: ['admin'], status: 'active', created_at: new Date().toISOString() };
    const org = { id: 'org-123', name: 'Acme Corp', slug: 'acme-corp', created_at: new Date().toISOString() };
    return respond(200, { access_token: 'mock-jwt-token', refresh_token: 'mock-refresh-token', user, org });
  }
  if (url.includes('/v1/users/me')) {
    const user = { id: 'u-admin', email: 'admin@syncsphere.ai', first_name: 'Admin', last_name: 'User', org_id: 'org-123', role_ids: ['admin'], status: 'active', created_at: new Date().toISOString() };
    return respond(200, user);
  }

  // Mock Connectors Paths
  if (url.includes('/v1/connectors')) {
    if (method === 'post') {
      const conn = { id: 'conn-' + Date.now(), org_id: 'org-default', ...data, status: 'enabled', tools: [], created_at: new Date().toISOString() };
      MOCK_DB.connectors.push(conn);
      return respond(200, conn);
    }
    return respond(200, MOCK_DB.connectors);
  }
  if (url.match(/\/v1\/connectors\/[^/]+$/)) {
    const id = url.split('/').pop();
    if (method === 'delete') {
      MOCK_DB.connectors = MOCK_DB.connectors.filter((c) => c.id !== id);
      return respond(200, { success: true });
    }
    const conn = MOCK_DB.connectors.find((c) => c.id === id);
    return respond(200, conn);
  }

  // Mock AI models/providers
  if (url.includes('/v1/ai/models')) {
    return respond(200, MOCK_DB.models);
  }
  if (url.includes('/v1/ai/prompts')) {
    if (method === 'post') {
      const prompt = { id: 'pr-' + Date.now(), org_id: 'org-default', ...data, active_version: 1 };
      MOCK_DB.prompts.push(prompt);
      return respond(200, prompt);
    }
    return respond(200, MOCK_DB.prompts);
  }

  // Mock Planner
  if (url.includes('/v1/planner/generate')) {
    const wf = {
      id: 'wf-' + Date.now(),
      org_id: 'org-default',
      name: 'Dynamic ' + data.prompt.slice(0, 15),
      description: data.prompt,
      status: 'DRAFT',
      nodes: [
        { id: 'n1', type: 'trigger', label: 'Webhook Inbound', config: {} },
        { id: 'n2', type: 'action', label: 'OpenAI Call', config: {} },
      ],
      edges: [{ source: 'n1', target: 'n2' }],
      active_version: 1,
      created_at: new Date().toISOString(),
    };
    MOCK_DB.workflows.push(wf);
    return respond(200, { workflow_id: wf.id, steps: 2 });
  }

  // Mock Workflows
  if (url.includes('/v1/workflows')) {
    return respond(200, MOCK_DB.workflows);
  }

  // Mock Executions/Runtime
  if (url.includes('/v1/runtime/start')) {
    const exec = { id: 'exe-' + Date.now(), org_id: 'org-default', workflow_id: data.workflow_id, version: 1, status: 'running', variables: {}, step_states: {}, created_at: new Date().toISOString() };
    MOCK_DB.executions.push(exec);
    return respond(200, exec);
  }
  if (url.includes('/v1/runtime/executions')) {
    return respond(200, MOCK_DB.executions);
  }

  // Mock Approvals
  if (url.includes('/v1/approvals')) {
    return respond(200, MOCK_DB.approvals);
  }

  // Mock Observability traces, alerts, health
  if (url.includes('/v1/observability/traces')) {
    const mockTrace = {
      correlation_id: 'corr-api-trace-123',
      org_id: 'org-default',
      spans: [
        { span_id: 'span-root', name: 'workflow.run', status: 'COMPLETED', start_time: new Date().toISOString(), attributes: {} },
      ],
    };
    return respond(200, [mockTrace]);
  }
  if (url.includes('/v1/observability/alerts')) {
    return respond(200, MOCK_DB.alerts);
  }
  if (url.includes('/v1/observability/health')) {
    const check = {
      overall_status: 'HEALTHY',
      services: [
        { name: 'identity', status: 'HEALTHY', latency_ms: 12 },
        { name: 'connectors', status: 'HEALTHY', latency_ms: 45 },
        { name: 'ai_gateway', status: 'HEALTHY', latency_ms: 110 },
        { name: 'runtime', status: 'HEALTHY', latency_ms: 8 },
        { name: 'observability', status: 'HEALTHY', latency_ms: 15 },
      ],
      timestamp: new Date().toISOString(),
    };
    return respond(200, check);
  }
  if (url.includes('/v1/observability/dashboard')) {
    const dashboardStats = {
      health: { overall_status: 'HEALTHY' },
      ai_gateway: { total_completions: 342, token_usage: 412000, total_cost: 2.34, cache_hit_rate: 0.65 },
      connectors: { active_count: 3, total_calls: 125, failure_rate: 0.02 },
      executions: { total_runs: 84, success_rate: 0.98, average_duration_sec: 4.2 },
    };
    return respond(200, dashboardStats);
  }

  // Mock Tasks
  if (url.match(/\/v1\/tasks\/[^/]+$/)) {
    const id = url.split('/').pop();
    if (method === 'put') {
      const idx = MOCK_DB.tasks.findIndex((t: any) => t.id === id);
      if (idx >= 0) {
        MOCK_DB.tasks[idx] = { ...MOCK_DB.tasks[idx], ...data, updated_at: new Date().toISOString() };
        return respond(200, MOCK_DB.tasks[idx]);
      }
      return respond(404, { message: 'Task not found' });
    }
    if (method === 'delete') {
      MOCK_DB.tasks = MOCK_DB.tasks.filter((t: any) => t.id !== id);
      return respond(200, true);
    }
    const task = MOCK_DB.tasks.find((t: any) => t.id === id);
    return respond(200, task || null);
  }
  if (url.includes('/v1/tasks')) {
    if (method === 'post') {
      const task = { id: 'task-' + Date.now(), org_id: 'org-default', ...data, created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
      MOCK_DB.tasks.push(task);
      return respond(201, task);
    }
    return respond(200, MOCK_DB.tasks);
  }

  return respond(404, { message: 'Mock path not found' });
}

export const integrationApi = {
  async connectGithub() {
    const res = await apiClient.post('/v1/connect/github/init')
    window.location.href = res.data.auth_url || res.data.data.auth_url;
  },

  async connectSlack() {
    const res = await apiClient.post('/v1/connect/slack/init')
    window.location.href = res.data.auth_url || res.data.data.auth_url;
  },

  async connectGoogle() {
    const res = await apiClient.post('/v1/connect/google/init')
    window.location.href = res.data.auth_url || res.data.data.auth_url;
  },

  disconnectGithub() {
    return fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/v1/connect/github`,
      {
        method: "DELETE",
        credentials: "include",
      }
    );
  },

  disconnectSlack() {
    return fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/v1/connect/slack`,
      {
        method: "DELETE",
        credentials: "include",
      }
    );
  },

  getStatus() {
    return fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/v1/connectors/status`,
      {
        credentials: "include",
      }
    ).then((r) => r.json());
  },
};