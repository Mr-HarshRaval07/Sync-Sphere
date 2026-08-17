import { create } from 'zustand';
import { ExecutionSession, Trace, Alert } from '../../../shared/types';

// ==========================================
// Types
// ==========================================

export type TimeRange = '15m' | '1h' | '24h' | '7d' | '30d' | 'custom';

export interface SlaTarget {
  metricName: string;
  target: number;
  actual: number;
  unit: string;
  isBreached: boolean;
}

export interface CostBreakdownItem {
  id: string;
  name: string;
  type: 'org' | 'workflow' | 'prompt' | 'model' | 'user';
  tokens: number;
  cost: number;
  requests: number;
}

export interface ActivityEvent {
  id: string;
  timestamp: string;
  type: 'execution_started' | 'execution_completed' | 'execution_failed' | 'alert_triggered' | 'approval_requested' | 'approval_decision';
  message: string;
  meta?: Record<string, any>;
}

export interface OperationsState {
  // Global Range & Layouts
  timeRange: TimeRange;
  customTimeRange: { start: string; end: string } | null;
  dashboardLayout: string[]; // Order of widget IDs: ['active-workflows', 'running-executions', 'queue-length', 'workers', 'active-users', 'ai-requests', 'connector-calls', 'approvals', 'failures', 'health']
  
  // Real-time Telemetry Metrics
  activeWorkflowsCount: number;
  runningExecutionsCount: number;
  failedExecutionsCount: number;
  queueLengths: {
    execution: number;
    approval: number;
    embedding: number;
    planner: number;
    retry: number;
    deadLetter: number;
  };
  connectedWorkers: Record<string, { cpu: number; memory: number; activeJobs: number; healthy: boolean; failures: number; heartbeat: string }>;
  systemHealth: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY';

  // Live Lists
  activeExecutions: ExecutionSession[];
  alerts: Alert[];
  traces: Trace[];
  activityFeed: ActivityEvent[];

  // SLA Indicators
  slaTargets: Record<string, SlaTarget>;

  // Analytics Aggregates
  aiAnalytics: Record<string, { latency: number; tokens: number; cost: number; cacheHitRate: number; requests: number }>;
  aiCostBreakdown: CostBreakdownItem[];
  connectorHealth: Record<string, { latency: number; availability: number; errorRate: number; usageCount: number; retries: number }>;
  runtimeAnalytics: {
    avgDurationMs: number;
    successRate: number;
    sagaRollbacks: number;
    timeouts: number;
  };

  // Search & Navigation
  selectedTraceId: string | null;
  searchQuery: string;
  filters: {
    orgId: string;
    workflowId: string;
    status: string;
    connectorId: string;
    modelId: string;
    workerId: string;
  };
  drillDownTab: string | null;

  // Actions
  setTimeRange: (range: TimeRange, customRange?: { start: string; end: string } | null) => void;
  setDashboardLayout: (layout: string[]) => void;
  resetDashboardLayout: () => void;
  setTelemetryData: (payload: any) => void;
  addActivityEvent: (event: ActivityEvent) => void;
  setActiveExecutions: (sessions: ExecutionSession[]) => void;
  updateExecutionStatus: (sessionId: string, status: string) => void;
  setAlerts: (alerts: Alert[]) => void;
  acknowledgeAlert: (alertId: string) => void;
  resolveAlert: (alertId: string) => void;
  setSearchQuery: (query: string) => void;
  setFilters: (filters: Partial<OperationsState['filters']>) => void;
  selectTrace: (traceId: string | null) => void;
  setDrillDownTab: (tab: string | null) => void;
  updateSlaTarget: (metricName: string, actual: number) => void;
}

// ==========================================
// Default Dashboard Layout
// ==========================================
const DEFAULT_LAYOUT = [
  'active-workflows',
  'running-executions',
  'queue-length',
  'workers',
  'active-users',
  'ai-requests',
  'connector-calls',
  'approvals',
  'failures',
  'health',
];

// ==========================================
// Store Implementation
// ==========================================
export const useOperationsStore = create<OperationsState>((set, get) => ({
  // State initialization
  timeRange: '24h',
  customTimeRange: null,
  dashboardLayout: DEFAULT_LAYOUT,
  
  activeWorkflowsCount: 0,
  runningExecutionsCount: 0,
  failedExecutionsCount: 0,
  queueLengths: {
    execution: 0,
    approval: 0,
    embedding: 0,
    planner: 0,
    retry: 0,
    deadLetter: 0,
  },
  connectedWorkers: {},
  systemHealth: 'HEALTHY',

  activeExecutions: [],
  alerts: [],
  traces: [],
  activityFeed: [],

  slaTargets: {
    latency: { metricName: 'latency', target: 2000, actual: 1250, unit: 'ms', isBreached: false },
    successRate: { metricName: 'successRate', target: 99, actual: 99.4, unit: '%', isBreached: false },
    errorRate: { metricName: 'errorRate', target: 1, actual: 0.6, unit: '%', isBreached: false },
    workerUtilization: { metricName: 'workerUtilization', target: 80, actual: 45, unit: '%', isBreached: false },
  },

  aiAnalytics: {},
  aiCostBreakdown: [],
  connectorHealth: {},
  runtimeAnalytics: {
    avgDurationMs: 3500,
    successRate: 99.4,
    sagaRollbacks: 0,
    timeouts: 0,
  },

  selectedTraceId: null,
  searchQuery: '',
  filters: {
    orgId: '',
    workflowId: '',
    status: '',
    connectorId: '',
    modelId: '',
    workerId: '',
  },
  drillDownTab: null,

  // Actions
  setTimeRange: (timeRange, customTimeRange = null) => set({ timeRange, customTimeRange }),
  
  setDashboardLayout: (dashboardLayout) => set({ dashboardLayout }),
  
  resetDashboardLayout: () => set({ dashboardLayout: DEFAULT_LAYOUT }),

  setTelemetryData: (payload) => {
    if (!payload) return;
    set((state) => {
      const updates: Partial<OperationsState> = {};
      
      // Update basic counters if present
      if (payload.activeWorkflowsCount !== undefined) updates.activeWorkflowsCount = payload.activeWorkflowsCount;
      if (payload.runningExecutionsCount !== undefined) updates.runningExecutionsCount = payload.runningExecutionsCount;
      if (payload.failedExecutionsCount !== undefined) updates.failedExecutionsCount = payload.failedExecutionsCount;
      if (payload.systemHealth !== undefined) updates.systemHealth = payload.systemHealth;

      // Update queues if present
      if (payload.queueLengths) {
        updates.queueLengths = { ...state.queueLengths, ...payload.queueLengths };
      }

      // Update workers if present
      if (payload.workers) {
        updates.connectedWorkers = { ...state.connectedWorkers, ...payload.workers };
      }

      // Update AI Metrics
      if (payload.aiAnalytics) {
        updates.aiAnalytics = { ...state.aiAnalytics, ...payload.aiAnalytics };
      }

      // Update AI Cost Breakdown
      if (payload.aiCostBreakdown) {
        updates.aiCostBreakdown = payload.aiCostBreakdown;
      }

      // Update Connectors
      if (payload.connectorHealth) {
        updates.connectorHealth = { ...state.connectorHealth, ...payload.connectorHealth };
      }

      // Update Runtime metrics
      if (payload.runtimeAnalytics) {
        updates.runtimeAnalytics = { ...state.runtimeAnalytics, ...payload.runtimeAnalytics };
      }

      return updates;
    });
  },

  addActivityEvent: (event) => set((s) => ({
    activityFeed: [event, ...s.activityFeed].slice(0, 100), // Cap at 100 entries
  })),

  setActiveExecutions: (activeExecutions) => set({ activeExecutions }),

  updateExecutionStatus: (sessionId, status) => set((s) => ({
    activeExecutions: s.activeExecutions.map((e) =>
      e.id === sessionId ? { ...e, status: status as any } : e
    ),
  })),

  setAlerts: (alerts) => set({ alerts }),

  acknowledgeAlert: (alertId) => set((s) => ({
    alerts: s.alerts.map((a) =>
      a.id === alertId ? { ...a, status: 'RESOLVED' as any } : a // Use simple resolved mapping or additional meta field
    ),
  })),

  resolveAlert: (alertId) => set((s) => ({
    alerts: s.alerts.filter((a) => a.id !== alertId),
  })),

  setSearchQuery: (searchQuery) => set({ searchQuery }),

  setFilters: (newFilters) => set((s) => ({
    filters: { ...s.filters, ...newFilters },
  })),

  selectTrace: (selectedTraceId) => set({ selectedTraceId }),

  setDrillDownTab: (drillDownTab) => set({ drillDownTab }),

  updateSlaTarget: (metricName, actual) => set((s) => {
    const targetItem = s.slaTargets[metricName];
    if (!targetItem) return {};
    
    // Determine breach condition based on target type
    let isBreached = false;
    if (metricName === 'latency' || metricName === 'errorRate') {
      isBreached = actual > targetItem.target;
    } else if (metricName === 'successRate') {
      isBreached = actual < targetItem.target;
    }

    return {
      slaTargets: {
        ...s.slaTargets,
        [metricName]: { ...targetItem, actual, isBreached },
      },
    };
  }),
}));
