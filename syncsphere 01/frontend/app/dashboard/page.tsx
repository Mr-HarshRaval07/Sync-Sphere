'use client';

import React from 'react';

// NOTE: Dashboard calls multiple telemetry/runtime endpoints.
// In dev environments where backend websocket/endpoints are not wired yet,
// we still want the page to render without hard failing the whole dashboard.

import { useQuery } from '@tanstack/react-query';
import { observabilityApi, runtimeApi } from '../../shared/services/api';
import { MetricCard, DataGrid, ErrorState, SkeletonLoader } from '../../shared/components/DesignSystem';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Activity, ShieldAlert, Zap, Cpu, Sparkles, CheckCircle2, Clock } from 'lucide-react';
import { cn } from '../../lib/utils';

export default function DashboardPage() {
  // Query dashboard telemetry statistics
  const { data: stats, isLoading: statsLoading, error: statsError, refetch: refetchStats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => observabilityApi.getDashboardStats(),
    refetchInterval: 15000, // Auto refresh stats every 15s
  });

  // Query health reports
  const { data: health, isLoading: healthLoading, error: healthError } = useQuery({
    queryKey: ['health-report'],
    queryFn: () => observabilityApi.getHealthReport(),
    refetchInterval: 10000,
  });

  // Query executions list
  const { data: executions, isLoading: execsLoading, error: execsError } = useQuery({
    queryKey: ['recent-executions'],
    queryFn: () => runtimeApi.getExecutions(),
  });

  // Avoid blocking the whole dashboard if backend telemetry endpoints are not yet available.
  // The UI can still render with partial/empty datasets.
  const hasHardError = false;
  if (hasHardError && (statsError || healthError || execsError)) {
    return (
      <ErrorState
        title="Telemetry Pipeline Sync Failed"
        message="Unable to establish connection with the central observability metrics engine."
        onRetry={() => {
          refetchStats();
        }}
      />
    );
  }


  const isPageLoading = statsLoading || healthLoading || execsLoading;

  if (isPageLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, idx) => (
            <div key={idx} className="h-28 rounded-lg bg-card animate-pulse border border-border" />
          ))}
        </div>
        <SkeletonLoader rows={5} />
      </div>
    );
  }

  // Formatting values
  const totalCalls = stats?.connectors?.total_calls || 0;
  const failureRate = (stats?.connectors?.failure_rate * 100).toFixed(1) + '%';
  const averageDuration = (stats?.executions?.average_duration_sec || 0).toFixed(1) + 's';
  const successRate = (stats?.executions?.success_rate * 100).toFixed(1) + '%';

  const executionColumns = [
    {
      key: 'id',
      header: 'Run ID',
      render: (row: any) => <span className="font-semibold text-xs">Run #{row.id.slice(-6)}</span>,
    },
    { key: 'workflow_id', header: 'Workflow ID' },
    {
      key: 'status',
      header: 'Execution Status',
      render: (row: any) => {
        const colors = {
          completed: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
          failed: 'bg-rose-500/10 text-rose-500 border-rose-500/20',
          running: 'bg-sky-500/10 text-sky-500 border-sky-500/20',
          paused: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
          cancelled: 'bg-muted text-muted-foreground border-border',
        };
        const cls = colors[row.status as keyof typeof colors] || colors.cancelled;
        return <Badge className={`text-xs px-2 py-0.5 border ${cls}`}>{row.status}</Badge>;
      },
    },
    {
      key: 'created_at',
      header: 'Started At',
      render: (row: any) => new Date(row.created_at).toLocaleString(),
    },
  ];

  const healthColumns = [
    { key: 'name', header: 'Bounded Context Domain', render: (row: any) => <span className="capitalize font-medium">{row.name.replace('_', ' ')}</span> },
    {
      key: 'status',
      header: 'Health Condition',
      render: (row: any) => {
        const isHealthy = row.status === 'HEALTHY';
        return (
          <Badge className={`text-xs font-semibold px-2 py-0.5 border ${
            isHealthy ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-rose-500/10 text-rose-500 border-rose-500/20"
          }`}>
            {isHealthy ? <CheckCircle2 className="h-3 w-3 inline mr-1" /> : <ShieldAlert className="h-3 w-3 inline mr-1" />}
            {row.status}
          </Badge>
        );
      },
    },
    { key: 'latency_ms', header: 'Internal API Latency', render: (row: any) => <code>{row.latency_ms}ms</code> },
  ];

  return (
    <div className="space-y-6">
      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Tokens Consumed"
          value={stats?.ai_gateway?.token_usage?.toLocaleString() || '0'}
          description="Prompt & Completion Tokens"
          icon={<Cpu className="h-4 w-4" />}
          trend={{ value: 12, isPositive: true }}
        />
        <MetricCard
          title="Inference Cost"
          value={`$${stats?.ai_gateway?.total_cost?.toFixed(2) || '0.00'}`}
          description="Total model gateway spend"
          icon={<Sparkles className="h-4 w-4 text-amber-500" />}
          trend={{ value: 4, isPositive: false }}
        />
        <MetricCard
          title="Connector Activity"
          value={totalCalls}
          description={`Failure rate: ${failureRate}`}
          icon={<Zap className="h-4 w-4 text-emerald-500" />}
          trend={{ value: 8, isPositive: true }}
        />
        <MetricCard
          title="Workflow Runs"
          value={stats?.executions?.total_runs || '0'}
          description={`Success SLA: ${successRate} (Avg: ${averageDuration})`}
          icon={<Activity className="h-4 w-4 text-sky-500" />}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Recent Execution Runs DataGrid */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="text-base font-bold">Recent Pipeline Executions</CardTitle>
              <CardDescription className="text-xs">Timeline of recent automated workflow runs.</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <DataGrid
                columns={executionColumns}
                data={executions?.slice(0, 5) || []}
                className="border-0 rounded-none border-t border-border/50"
              />
            </CardContent>
          </Card>
        </div>

        {/* Live Service Health status */}
        <div className="space-y-4">
          <Card className="border-border bg-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle className="text-base font-bold">Domain Node Health</CardTitle>
                <CardDescription className="text-xs">Real-time latency check across internal gateways.</CardDescription>
              </div>
              <Badge variant="outline" className={cn(
                "text-xs font-semibold px-2 py-0.5 border flex items-center gap-1",
                health?.overall_status === 'HEALTHY' ? "text-emerald-500 bg-emerald-500/10 border-emerald-500/25" : "text-rose-500 bg-rose-500/10 border-rose-500/25"
              )}>
                {health?.overall_status || 'OFFLINE'}
              </Badge>
            </CardHeader>
            <CardContent className="p-0">
              <DataGrid
                columns={healthColumns}
                data={health?.services || []}
                className="border-0 rounded-none border-t border-border/50"
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
