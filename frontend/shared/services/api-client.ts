import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';
import { useAuthStore } from '../stores/authStore';
import { useOrgStore } from '../stores/orgStore';

// Determine the base backend URL
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
console.log("API_BASE_URL =", API_BASE_URL);

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 180000,  // 180s — Complex multi-integration AI calls can take 60-120s
});


// Request Interceptor: Attach Auth & Multi-Tenancy headers
apiClient.interceptors.request.use(
  (config) => {
    let token = useAuthStore.getState().accessToken;
    if (!token && typeof window !== 'undefined') {
      token = localStorage.getItem('access_token');
      if (!token) {
        try {
          const persisted = localStorage.getItem('syncsphere-auth');
          if (persisted) {
            const parsed = JSON.parse(persisted);
            token = parsed?.state?.accessToken || null;
          }
        } catch { /* ignore */ }
      }
      if (token) {
        useAuthStore.setState({ accessToken: token, isAuthenticated: true });
      }
    }
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

    // Do not attempt refresh on auth endpoints (login, register, refresh)
    const isAuthEndpoint = originalRequest?.url?.includes('/v1/auth/login') ||
                           originalRequest?.url?.includes('/v1/auth/register') ||
                           originalRequest?.url?.includes('/v1/auth/refresh');

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
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

      const storedRefreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;

      return new Promise(function (resolve, reject) {
        axios.post(
          `${API_BASE_URL}/v1/auth/refresh`,
          { refresh_token: storedRefreshToken },
          { withCredentials: true }
        )
          .then(res => {
            const { access_token, refresh_token: new_refresh_token } = res.data.data;
            
            if (typeof window !== 'undefined') {
              localStorage.setItem('access_token', access_token);
              if (new_refresh_token) {
                localStorage.setItem('refresh_token', new_refresh_token);
              }
            }

            const currentUser = useAuthStore.getState().user;
            useAuthStore.setState({
              accessToken: access_token,
              user: currentUser,
              isAuthenticated: true,
            });

            originalRequest.headers.Authorization = 'Bearer ' + access_token;
            processQueue(null, access_token);
            resolve(apiClient(originalRequest));
          })
          .catch(err => {
            processQueue(err, null);

            const isInvalidGrant = err.response?.status === 400 || err.response?.status === 401;
            if (isInvalidGrant) {
              if (typeof window !== 'undefined') {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
              }
              useAuthStore.getState().logout();
              if (typeof window !== 'undefined') {
                const path = window.location.pathname;
                if (path !== '/' && !path.startsWith('/login')) {
                  window.location.href = '/login';
                }
              }
            }

            reject(err);
          })
          .finally(() => {
            isRefreshing = false;
          });
      });
    }

    return Promise.reject(error);
  }
);


export const integrationApi = {
  async connectSlack(requestedAccount?: string) {
    const data = requestedAccount ? { requested_account: requestedAccount } : {};
    const res = await apiClient.post('/v1/connect/slack/init', data)
    window.location.href = res.data.auth_url || res.data.data.auth_url;
  },

  async connectGoogle(requestedAccount?: string) {
    const data = requestedAccount ? { requested_account: requestedAccount } : {};
    const res = await apiClient.post('/v1/connect/google/init', data)
    window.location.href = res.data.auth_url || res.data.data.auth_url;
  },

  async connectGithub(requestedAccount?: string) {
    const data = requestedAccount ? { requested_account: requestedAccount } : {};
    const res = await apiClient.post('/v1/connect/github/init', data)
    window.location.href = res.data.auth_url || res.data.data.auth_url;
  },

  async connectJira(requestedAccount?: string) {
    const data = requestedAccount ? { requested_account: requestedAccount } : {};
    const res = await apiClient.post('/v1/connect/jira/init', data)
    window.location.href = res.data.auth_url || res.data.data.auth_url;
  },

  async connectNotion(requestedAccount?: string) {
    const data = requestedAccount ? { requested_account: requestedAccount } : {};
    const res = await apiClient.post('/v1/connect/notion/init', data)
    window.location.href = res.data.auth_url || res.data.data.auth_url;
  },

  disconnectSlack() {
    return apiClient.delete('/v1/connect/slack');
  },

  disconnectGoogle() {
    return apiClient.delete('/v1/connect/google');
  },

  disconnectGithub() {
    return apiClient.delete('/v1/connect/github');
  },

  disconnectNotion() {
    return apiClient.delete('/v1/connect/notion');
  },

  getStatus() {
    return apiClient.get('/v1/connect/status').then((r) => r.data);
  },

  getJiraProjects() {
    return apiClient.get('/v1/connect/jira/projects').then((r) => r.data.projects);
  },

  getNotionParents() {
    return apiClient.get('/v1/connect/notion/accessible-pages').then((r) => r.data);
  },

  saveNotionParent(parentId: string, parentType: string) {
    return apiClient.patch('/v1/connect/notion/parent', { parent_id: parentId, parent_type: parentType }).then((r) => r.data);
  },

  refreshNotionParents() {
    return apiClient.post('/v1/connect/notion/refresh').then((r) => r.data);
  }
};