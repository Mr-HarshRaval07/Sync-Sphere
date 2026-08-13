'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useTheme } from 'next-themes';
import { useQuery } from '@tanstack/react-query';
import { runtimeApi, observabilityApi } from '../../../shared/services/api';
import { apiClient } from '../../../shared/services/api-client';
import { DataGrid, SkeletonLoader, EmptyState } from '../../../shared/components/DesignSystem';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../../../components/ui/tabs';
import { Eye, ShieldAlert, Activity, Terminal, Layers, ArrowRight } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from 'recharts';

const TraceNode = ({ span, isLast }: { span: any; isLast: boolean }) => {
  const isOk = span.status === 'success' || span.status === 'completed';
  const isFailed = span.status === 'failed';

  const badgeColor = isOk
    ? 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20'
    : isFailed
      ? 'text-rose-500 bg-rose-500/10 border-rose-500/20'
      : 'text-amber-500 bg-amber-500/10 border-amber-500/20';

  return (
    <div className="flex w-full group">
      <div className="flex flex-col items-center mr-3" style={{ width: '20px' }}>
        <div className="h-4 w-px bg-border/40" />
        <div className={`h-3 w-3 rounded-full border-2 ${isOk ? 'border-emerald-500 bg-emerald-500/20' : isFailed ? 'border-rose-500 bg-rose-500/20' : 'border-amber-500 bg-amber-500/20'} z-10 flex-shrink-0`} />
        {!isLast && <div className="flex-1 w-px bg-border/40 min-h-[2rem]" />}
      </div>
      <div className="flex-1 py-1">
        <div className="border border-border/40 bg-card/60 backdrop-blur-sm rounded-md p-3 max-w-full">
          <div className="flex justify-between items-start gap-4">
            <div className="flex items-start gap-2 max-w-[85%]">
              <ArrowRight className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
              <div>
                <div className="font-mono text-sm font-semibold text-foreground capitalize truncate">{span.label}</div>
                <div className="text-xs text-muted-foreground mt-1 flex items-center gap-2 flex-wrap">
                  <Badge variant="outline" className={`text-[10px] uppercase font-bold py-0 ${badgeColor}`}>
                    {span.status}
                  </Badge>
                  <span className="opacity-60 tabular-nums">{span.subLabel}</span>
                </div>
                {span.error && (
                  <div className="mt-3 text-xs font-mono text-rose-400 bg-rose-950/30 p-2.5 rounded border border-rose-900/50 break-words whitespace-pre-wrap">
                    {span.error}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function ObservabilityPage() {
  const [selectedCorrelationId, setSelectedCorrelationId] = useState<string | null>(null);
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const isDark = mounted && resolvedTheme === 'dark';

  // High-contrast chart styling variables tailored for full dark mode visibility
  const axisProps = {
    tick: { fill: isDark ? '#F3F4F6' : '#4B5563', fontSize: 12, fontWeight: 600 },
    axisLine: { stroke: isDark ? '#6B7280' : '#9CA3AF', strokeWidth: 2 },
    tickLine: { stroke: isDark ? '#6B7280' : '#9CA3AF', strokeWidth: 2 }
  };

  const gridProps = {
    stroke: isDark ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.1)',
    strokeDasharray: '4 4'
  };

  const chartColors = {
    success: isDark ? '#34D399' : '#10B981', // Emerald for success
    failed: isDark ? '#F87171' : '#EF4444',  // Rose for failures
    primary: isDark ? '#A78BFA' : '#8B5CF6', // Purple/Indigo for API tokens
    connector: isDark ? '#60A5FA' : '#3B82F6' // Blue for connectors
  };

  const tooltipProps = {
    contentStyle: {
      backgroundColor: isDark ? '#111827' : '#FFFFFF',
      borderColor: isDark ? '#374151' : '#E5E7EB',
      color: isDark ? '#F9FAFB' : '#111827',
      borderRadius: '8px',
      borderWidth: '2px',
      boxShadow: isDark ? '0 10px 25px -5px rgba(0, 0, 0, 0.9)' : '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
    },
    itemStyle: {
      fontWeight: 600,
    }
  };

  const { data: executions = [], isLoading: executionsLoading } = useQuery({
    queryKey: ['observability-executions'],
    queryFn: () => runtimeApi.getExecutions(),
  });

  const { data: apiLogs = [], isLoading: apiLogsLoading } = useQuery({
    queryKey: ['observability-api-logs'],
    queryFn: () => apiClient.get('/v1/observability/ai/executions/raw').then((r: any) => r.data.data),
    refetchInterval: 5000 // Realtime data update expectation simulated lightly to meet "automatically update whenever new ai request is made" closely
  });

  const { data: backendAlerts = [] } = useQuery({
    queryKey: ['backend-alerts'],
    queryFn: () => observabilityApi.listAlerts(),
    refetchInterval: 5000,
  });

  // Calculate Metrics Data natively from Executions, API logs, and Backend Alerts
  const { apiUsageData, connectorData, alertsData } = useMemo(() => {

    // 1. Graph 1: API Usage Trend
    const apiDataMap = new Map<string, any>();
    if (apiLogs && Array.isArray(apiLogs) && apiLogs.length > 0) {
      let minDate = new Date().getTime();
      let maxDate = 0;
      apiLogs.forEach(log => {
        if (!log.created_at) return;
        const time = new Date(log.created_at).getTime();
        if (time < minDate) minDate = time;
        if (time > maxDate) maxDate = time;
      });

      const isHourly = (maxDate - minDate) <= (24 * 60 * 60 * 1000); // Hourly if timeframe is exactly 24H or less

      apiLogs.forEach(log => {
        if (!log.created_at) return;
        const d = new Date(log.created_at);
        let bucketKey = '';
        let timeLabel = '';
        if (isHourly) {
          bucketKey = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}-${d.getHours()}`;
          timeLabel = d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
        } else {
          bucketKey = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
          timeLabel = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
        }

        if (!apiDataMap.has(bucketKey)) {
          apiDataMap.set(bucketKey, {
            sortKey: d.getTime(), // Numerical boundary for absolute sorting
            time: timeLabel,
            requestCount: 0,
            promptTokens: 0,
            completionTokens: 0,
            totalTokens: 0,
            timestamp: log.created_at
          });
        }
        const b = apiDataMap.get(bucketKey)!;
        b.requestCount++;
        b.promptTokens += (log.prompt_tokens || 0);
        b.completionTokens += (log.completion_tokens || 0);
        b.totalTokens += (log.total_tokens || 0);
        if (d.getTime() > new Date(b.timestamp).getTime()) {
          b.timestamp = log.created_at;
        }
      });
    }
    const finalApiData = Array.from(apiDataMap.values()).sort((a, b) => a.sortKey - b.sortKey);

    // 2. Graph 2: Connector Usage & 3. Active Alerts
    const connMap = new Map<string, number>();
    const alertsMap = new Map<string, any>();

    if (Array.isArray(backendAlerts)) {
      backendAlerts.forEach((a: any) => {
        const key = a.alert_id || a.id;
        if (key && (a.status === 'ACTIVE' || !a.status)) {
          alertsMap.set(key, {
            id: key,
            name: a.name || 'System Alert',
            message: a.message || 'System alert triggered.',
            severity: a.severity || 'HIGH',
            status: a.status || 'ACTIVE',
            created_at: a.created_at || new Date().toISOString()
          });
        }
      });
    }

    if (executions && Array.isArray(executions)) {
      executions.forEach(ex => {
        if (ex.status === 'failed') {
          const key = ex.id + '-exec';
          alertsMap.set(key, {
            id: key,
            name: 'Execution Failed',
            message: ex.error || `Workflow "${ex.workflow_name || 'Execution'}" failed.`,
            severity: 'CRITICAL',
            status: 'ACTIVE',
            created_at: ex.started_at || new Date().toISOString()
          });
        }

        if (ex.action_results && Array.isArray(ex.action_results)) {
          ex.action_results.forEach((act: any) => {
            const status = (act.status || '').toLowerCase();
            if (status === 'success' || status === 'completed') {
              const name = (act.action || 'Unknown').replace(/_/g, ' ');
              connMap.set(name, (connMap.get(name) || 0) + 1);
            }
          });
        }
      });
    }

    const finalConn = Array.from(connMap.entries())
      .map(([name, count]) => ({ name: name.charAt(0).toUpperCase() + name.slice(1), count }))
      .sort((a, b) => b.count - a.count);

    const finalAlerts = Array.from(alertsMap.values()).sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    return { apiUsageData: finalApiData, connectorData: finalConn, alertsData: finalAlerts };
  }, [executions, apiLogs, backendAlerts]);

  const selectedTrace = executions?.find((t: any) => (t.id || t.workflow_id) === selectedCorrelationId);

  // Map trace spans into serial hierarchical items matching pipeline
  const buildTraceSpans = (execution: any) => {
    if (!execution) return [];

    const spans = [];
    const executionStart = execution.started_at ? new Date(execution.started_at).toLocaleTimeString() : 'Unknown';

    // 1. Root Trigger
    spans.push({
      id: 'trigger',
      label: execution.trigger_type || 'Trigger',
      subLabel: executionStart,
      status: 'success'
    });

    // 2. Automated AI Planner step if marked natively
    if (execution.ai_execution_summary) {
      spans.push({
        id: 'ai_planner',
        label: 'AI Planner',
        subLabel: 'Orchestrating workflow graph',
        status: 'success'
      });
    }

    // 3. Connectors Execution
    if (execution.action_results && Array.isArray(execution.action_results)) {
      execution.action_results.forEach((action: any, i: number) => {
        const time = action.started_at ? new Date(action.started_at).toLocaleTimeString() : '';
        spans.push({
          id: `action-${i}`,
          label: (action.action || 'Unknown Connector').replace(/_/g, ' '),
          subLabel: time,
          status: action.status || 'completed',
          error: action.error
        });
      });
    }

    // 4. End State Node
    const isEndOk = execution.status === 'success' || execution.status === 'completed';
    spans.push({
      id: 'completed',
      label: isEndOk ? 'Completed' : 'Execution Failed',
      subLabel: execution.completed_at ? new Date(execution.completed_at).toLocaleTimeString() : 'N/A',
      status: isEndOk ? 'success' : 'failed',
      error: !isEndOk ? (execution.error || 'Execution halted unexpectedly.') : undefined,
    });

    return spans;
  };

  const currentSpans = selectedTrace ? buildTraceSpans(selectedTrace) : [];

  const traceColumns = [
    { key: 'id', header: 'Execution ID', render: (row: any) => <span className="font-mono text-xs">{row.id || row.workflow_id}</span> },
    { key: 'workflow_name', header: 'Workflow Name', render: (row: any) => <span className="font-semibold">{row.workflow_name || 'Workflow'}</span> },
    {
      key: 'status', header: 'Status', render: (row: any) => (
        <Badge variant={row.status === 'failed' ? 'destructive' : row.status === 'running' ? 'secondary' : 'default'} className="capitalize border-border">
          {row.status}
        </Badge>
      )
    },
    {
      key: 'duration', header: 'Duration', render: (row: any) => {
        let calc = '-';
        if (row.duration_ms) calc = `${(row.duration_ms / 1000).toFixed(1)}s`;
        else if (row.started_at && row.completed_at) calc = `${((new Date(row.completed_at).getTime() - new Date(row.started_at).getTime()) / 1000).toFixed(1)}s`;
        return <span className="font-mono">{calc}</span>;
      }
    },
    { key: 'steps', header: 'Steps', render: (row: any) => <span>{row.action_results?.length || 0}</span> },
    { key: 'started_at', header: 'Started At', render: (row: any) => <span>{row.started_at ? new Date(row.started_at).toLocaleString() : '-'}</span> },
    { key: 'completed_at', header: 'Completed At', render: (row: any) => <span>{row.completed_at ? new Date(row.completed_at).toLocaleString() : '-'}</span> },
  ];

  const alertColumns = [
    { key: 'name', header: 'Alert Title', render: (row: any) => <span className="font-semibold text-foreground">{row.name}</span> },
    { key: 'message', header: 'Description', render: (row: any) => <span className="text-muted-foreground break-words max-w-[300px] inline-block">{row.message}</span> },
    { key: 'severity', header: 'Severity', render: (row: any) => <Badge className="bg-rose-500/10 text-rose-500 border-rose-500/20 font-bold tracking-wider">{row.severity}</Badge> },
    { key: 'created_at', header: 'Triggered Date', render: (row: any) => <span className="text-muted-foreground whitespace-nowrap">{new Date(row.created_at).toLocaleString()}</span> },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight">Observability Center</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Monitor distributed pipeline traces, active metric alerts, and runtime analysis.
        </p>
      </div>

      <Tabs defaultValue="dashboard" className="space-y-4">
        <TabsList className="bg-muted border border-border p-1 rounded-md max-w-lg flex w-fit">
          <TabsTrigger value="dashboard" className="text-xs px-4">Metrics Dashboard</TabsTrigger>
          <TabsTrigger value="traces" className="text-xs px-4">Distributed Traces</TabsTrigger>
          <TabsTrigger value="alerts" className="text-xs px-4">Active Alerts</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard" className="space-y-6 flex flex-col items-center">
          {executionsLoading || apiLogsLoading ? (
            <div className="w-full"><SkeletonLoader rows={5} /></div>
          ) : (
            <div className="grid grid-cols-1 gap-6 w-full max-w-7xl">

              {/* GRAPH 1: API Usage */}
              <Card className="border-border rounded-xl shadow-md bg-card/30">
                <CardHeader className="pb-4 border-b border-border/50">
                  <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                    <Activity className="h-4 w-4" /> API Usage (OpenRouter Requests)
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-6">
                  {!apiUsageData || apiUsageData.length === 0 ? (
                    <div className="h-[350px] w-full flex items-center justify-center border border-dashed border-border/50 rounded-lg bg-card/40">
                      <span className="text-muted-foreground text-sm font-semibold">No API requests recorded yet.</span>
                    </div>
                  ) : (
                    <div className="h-[350px] w-full">
                      <ResponsiveContainer width="99%" height="100%">
                        <LineChart data={apiUsageData} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
                          <CartesianGrid vertical={false} {...gridProps} />
                          <XAxis dataKey="time" {...axisProps} dy={15} />
                          <YAxis {...axisProps} dx={-10} allowDecimals={false} />
                          <Tooltip
                            content={({ active, payload }) => {
                              if (active && payload && payload.length) {
                                const data = payload[0].payload;
                                return (
                                  <div className="bg-background/95 border border-border p-3.5 rounded-lg shadow-2xl text-sm min-w-[200px]" style={{ borderColor: tooltipProps.contentStyle.borderColor, color: tooltipProps.contentStyle.color }}>
                                    <div className="font-bold border-b border-border/50 pb-2 mb-3 font-mono text-[11px] opacity-70 tracking-tight">
                                      {new Date(data.timestamp).toLocaleString()}
                                    </div>
                                    <div className="flex justify-between gap-8 mb-1.5">
                                      <span className="text-muted-foreground text-[13px]">Request Count</span>
                                      <span className="font-bold text-foreground tabular-nums">{data.requestCount}</span>
                                    </div>
                                    <div className="flex justify-between gap-8 mb-1.5">
                                      <span className="text-muted-foreground text-[13px]">Prompt Tokens</span>
                                      <span className="font-bold text-emerald-400 tabular-nums drop-shadow-sm">{data.promptTokens}</span>
                                    </div>
                                    <div className="flex justify-between gap-8 mb-1.5">
                                      <span className="text-muted-foreground text-[13px]">Completion Tokens</span>
                                      <span className="font-bold text-indigo-400 tabular-nums drop-shadow-sm">{data.completionTokens}</span>
                                    </div>
                                    <div className="flex justify-between gap-8 pt-2.5 mt-2.5 border-t border-border/50">
                                      <span className="font-bold text-foreground text-[13px]">Total Tokens</span>
                                      <span className="font-bold tabular-nums text-primary text-[15px] drop-shadow-sm">{data.totalTokens}</span>
                                    </div>
                                  </div>
                                );
                              }
                              return null;
                            }}
                            cursor={{ stroke: isDark ? '#4B5563' : '#D1D5DB', strokeWidth: 1, strokeDasharray: '4 4' }}
                          />
                          <Legend wrapperStyle={{ paddingTop: '20px' }} />
                          <Line type="monotone" dataKey="requestCount" name="OpenRouter Queries" stroke={chartColors.primary} strokeWidth={3} dot={{ r: 4, fill: chartColors.primary }} activeDot={{ r: 7 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* GRAPH 2: Connector Usage */}
              <Card className="border-border rounded-xl shadow-md bg-card/30">
                <CardHeader className="pb-4 border-b border-border/50">
                  <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                    <Layers className="h-4 w-4" /> Connector Usage
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-6">
                  {!connectorData || connectorData.length === 0 ? (
                    <div className="h-[350px] w-full flex items-center justify-center border border-dashed border-border rounded-lg bg-card/40">
                      <span className="text-muted-foreground text-sm font-semibold">No successful connections traced.</span>
                    </div>
                  ) : (
                    <div className="h-[350px] w-full">
                      <ResponsiveContainer width="99%" height="100%">
                        <BarChart data={connectorData} layout="vertical" margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                          <CartesianGrid horizontal={true} vertical={false} {...gridProps} />
                          <XAxis type="number" {...axisProps} hide={false} dy={10} allowDecimals={false} />
                          <YAxis type="category" dataKey="name" {...axisProps} width={100} dx={-10} />
                          <Tooltip cursor={{ fill: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)' }} {...tooltipProps} />
                          <Bar dataKey="count" name="Successful Executions" fill={chartColors.connector} radius={[0, 4, 4, 0]} barSize={32} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </CardContent>
              </Card>

            </div>
          )}
        </TabsContent>

        <TabsContent value="traces">
          {executionsLoading ? (
            <SkeletonLoader rows={4} />
          ) : executions.length === 0 ? (
            <EmptyState
              title="No Traces Logged"
              description="Execute workflows to record and map distributed telemetry traces."
              icon={<Eye className="h-10 w-10 text-muted-foreground" />}
            />
          ) : (
            <div className="space-y-6">
              <Card className="border-border bg-card shadow-sm">
                <CardHeader className="pb-4 border-b border-border/50">
                  <CardTitle className="text-base font-bold">Workflow Executions List</CardTitle>
                  <CardDescription className="text-xs mt-1">Select any pipeline row to inspect exact execution flows sequentially.</CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  <DataGrid
                    columns={traceColumns}
                    data={executions}
                    className="border-0 rounded-none border-t border-border/50"
                    onRowClick={(row: any) => setSelectedCorrelationId(row.id || row.workflow_id)}
                  />
                </CardContent>
              </Card>

              {selectedTrace && (
                <Card className="border-border bg-card mt-6 shadow-2xl relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none" />
                  <CardHeader className="border-b border-border/20 pb-4 relative z-10">
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-base font-bold flex items-center gap-2">
                          <Terminal className="h-5 w-5 text-primary" /> Execution Timeline
                        </CardTitle>
                        <CardDescription className="text-xs mt-1 font-mono text-muted-foreground tracking-tight">{selectedCorrelationId}</CardDescription>
                      </div>
                      <Badge variant="outline" className="bg-background shadow-xs font-semibold py-1">Timeline Trace</Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="bg-background/20 p-6 lg:px-12 border-dashed border-t border-border/20 overflow-y-auto custom-scrollbar max-h-[600px] relative z-10">
                    <div className="py-2 max-w-2xl mx-auto">
                      {currentSpans.map((span: any, i: number) => (
                        <TraceNode key={span.id} span={span} isLast={i === currentSpans.length - 1} />
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </TabsContent>

        <TabsContent value="alerts">
          {executionsLoading ? (
            <SkeletonLoader rows={4} />
          ) : alertsData.length === 0 ? (
            <div className="border border-dashed border-border/50 rounded-lg bg-card/10 flex flex-col items-center justify-center text-center p-16 mt-6 shadow-inner tracking-tight">
              <ShieldAlert className="h-12 w-12 text-emerald-500/80 mb-4 drop-shadow-[0_0_15px_rgba(16,185,129,0.3)]" />
              <span className="text-xl font-bold text-foreground">No Active Alerts</span>
              <span className="text-sm text-muted-foreground mt-2 font-medium">All monitored runtimes are executing securely without detected bounds anomalies.</span>
            </div>
          ) : (
            <Card className="border-border bg-card shadow-sm">
              <CardHeader className="border-b border-border/50 bg-muted/20 pb-4">
                <CardTitle className="text-base font-bold flex items-center gap-1.5">
                  <ShieldAlert className="h-4 w-4 text-rose-500" /> Anomalies Log
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <DataGrid
                  columns={alertColumns}
                  data={alertsData}
                  className="border-0 rounded-none border-t border-border/50"
                  onRowClick={() => { }}
                />
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
