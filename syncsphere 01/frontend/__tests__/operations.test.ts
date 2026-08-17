// ==========================================
// Module 13 — Operations Center Unit Tests
// ==========================================

import { useOperationsStore } from '../features/operations/stores/operationsStore';
import { useOperationsTelemetry } from '../features/operations/hooks/useOperationsTelemetry';
import { Alert, TraceSpan } from '../shared/types';

describe('Operations Store Unit Tests', () => {
  beforeEach(() => {
    useOperationsStore.setState({
      timeRange: '24h',
      customTimeRange: null,
      dashboardLayout: [
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
      ],
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
    });
  });

  // 1. Time Range & Layouts
  test('setTimeRange modifies active time period', () => {
    const store = useOperationsStore.getState();
    expect(store.timeRange).toBe('24h');
    
    store.setTimeRange('7d');
    expect(useOperationsStore.getState().timeRange).toBe('7d');
  });

  test('setDashboardLayout updates card configurations order', () => {
    const store = useOperationsStore.getState();
    const newLayout = ['workers', 'active-workflows', 'queue-length'];
    
    store.setDashboardLayout(newLayout);
    expect(useOperationsStore.getState().dashboardLayout).toEqual(newLayout);
  });

  test('resetDashboardLayout restores default widgets list', () => {
    const store = useOperationsStore.getState();
    store.setDashboardLayout(['workers']);
    expect(useOperationsStore.getState().dashboardLayout).toEqual(['workers']);

    store.resetDashboardLayout();
    expect(useOperationsStore.getState().dashboardLayout).toHaveLength(10);
  });

  // 2. Metrics & Telemetry
  test('setTelemetryData maps counters and queue levels', () => {
    const store = useOperationsStore.getState();
    store.setTelemetryData({
      activeWorkflowsCount: 14,
      runningExecutionsCount: 8,
      failedExecutionsCount: 2,
      systemHealth: 'DEGRADED',
      queueLengths: { deadLetter: 4, planner: 1 },
    });

    const state = useOperationsStore.getState();
    expect(state.activeWorkflowsCount).toBe(14);
    expect(state.runningExecutionsCount).toBe(8);
    expect(state.failedExecutionsCount).toBe(2);
    expect(state.systemHealth).toBe('DEGRADED');
    expect(state.queueLengths.deadLetter).toBe(4);
    expect(state.queueLengths.planner).toBe(1);
    expect(state.queueLengths.execution).toBe(0); // Kept default
  });

  test('addActivityEvent appends to feed and limits list length', () => {
    const store = useOperationsStore.getState();
    expect(store.activityFeed).toHaveLength(0);

    store.addActivityEvent({
      id: 'e-1',
      timestamp: new Date().toISOString(),
      type: 'execution_started',
      message: 'Workflow SLA breach detected',
    });

    expect(useOperationsStore.getState().activityFeed).toHaveLength(1);
    expect(useOperationsStore.getState().activityFeed[0].id).toBe('e-1');
  });

  // 3. SLA Targets
  test('updateSlaTarget adjusts metrics and evaluates breaches', () => {
    const store = useOperationsStore.getState();
    
    // Latency target is 2000ms. Set actual to 1800ms (no breach)
    store.updateSlaTarget('latency', 1800);
    expect(useOperationsStore.getState().slaTargets.latency.actual).toBe(1800);
    expect(useOperationsStore.getState().slaTargets.latency.isBreached).toBe(false);

    // Set actual to 2500ms (breach)
    useOperationsStore.getState().updateSlaTarget('latency', 2500);
    expect(useOperationsStore.getState().slaTargets.latency.isBreached).toBe(true);

    // SuccessRate target is 99%. Set actual to 98% (breach)
    useOperationsStore.getState().updateSlaTarget('successRate', 98);
    expect(useOperationsStore.getState().slaTargets.successRate.isBreached).toBe(true);
  });

  // 4. Alerts
  test('setAlerts sets list, resolveAlert removes items', () => {
    const store = useOperationsStore.getState();
    const mockAlerts: Alert[] = [
      { id: 'al-1', org_id: 'org-1', name: 'DLQ breach', message: 'DLQ is above threshold', severity: 'CRITICAL', status: 'ACTIVE', created_at: new Date().toISOString() },
    ];

    store.setAlerts(mockAlerts);
    expect(useOperationsStore.getState().alerts).toHaveLength(1);

    useOperationsStore.getState().resolveAlert('al-1');
    expect(useOperationsStore.getState().alerts).toHaveLength(0);
  });

  // 5. Search & Filters
  test('setSearchQuery and setFilters updates state values', () => {
    const store = useOperationsStore.getState();
    
    store.setSearchQuery('Slack');
    expect(useOperationsStore.getState().searchQuery).toBe('Slack');

    store.setFilters({ workflowId: 'wf-bug-triage', status: 'failed' });
    expect(useOperationsStore.getState().filters.workflowId).toBe('wf-bug-triage');
    expect(useOperationsStore.getState().filters.status).toBe('failed');
  });

  test('setDrillDownTab manages active navigation targets', () => {
    const store = useOperationsStore.getState();
    expect(store.drillDownTab).toBeNull();

    store.setDrillDownTab('ai');
    expect(useOperationsStore.getState().drillDownTab).toBe('ai');
  });
});
