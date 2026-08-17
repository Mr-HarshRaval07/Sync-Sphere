'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { observabilityApi } from '../../../shared/services/api';
import { DataGrid, TreeView, TreeItem, SkeletonLoader, EmptyState } from '../../../shared/components/DesignSystem';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../../../components/ui/tabs';
import { Eye, ShieldAlert, Cpu, Layers, Activity, Clock, Terminal } from 'lucide-react';
import { Trace, TraceSpan, Alert } from '../../../shared/types';

export default function ObservabilityPage() {
  const [selectedCorrelationId, setSelectedCorrelationId] = useState<string | null>(null);

  // Query traces list
  const { data: traces = [], isLoading: tracesLoading } = useQuery({
    queryKey: ['traces-list'],
    queryFn: () => observabilityApi.listTraces(),
  });

  // Query active alerts
  const { data: alerts = [], isLoading: alertsLoading } = useQuery({
    queryKey: ['alerts-list'],
    queryFn: () => observabilityApi.listAlerts(),
  });

  const selectedTrace = traces.find((t: any) => t.correlation_id === selectedCorrelationId);

  // Map trace spans into TreeView hierarchy items
  const buildTraceTreeItems = (spans: TraceSpan[]): TreeItem[] => {
    const itemMap: Record<string, TreeItem> = {};
    const roots: TreeItem[] = [];

    // Initialize all items
    spans.forEach((span) => {
      const isOk = span.status === 'COMPLETED' || span.status === 'success';
      const badgeColor = isOk ? 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20' : 'text-rose-500 bg-rose-500/10 border-rose-500/20';

      itemMap[span.span_id] = {
        id: span.span_id,
        label: span.name,
        subLabel: `${span.status} • start: ${new Date(span.start_time).toLocaleTimeString()}`,
        children: [],
        icon: <Badge className={`text-[9px] scale-90 border font-semibold shrink-0 px-1 py-0 ${badgeColor}`}>{span.status}</Badge>,
      };
    });

    // Link parents & children
    spans.forEach((span) => {
      const item = itemMap[span.span_id];
      if (span.parent_span_id && itemMap[span.parent_span_id]) {
        itemMap[span.parent_span_id].children?.push(item);
      } else {
        roots.push(item);
      }
    });

    return roots;
  };

  const traceTreeItems = selectedTrace ? buildTraceTreeItems(selectedTrace.spans) : [];

  const traceColumns = [
    {
      key: 'correlation_id',
      header: 'Trace Correlation ID',
      render: (row: Trace) => <span className="font-semibold text-xs font-mono">{row.correlation_id}</span>,
    },
    { key: 'spans_count', header: 'Span nodes count', render: (row: Trace) => <span>{row.spans.length} spans</span> },
  ];

  const alertColumns = [
    { key: 'name', header: 'Alert Title', render: (row: Alert) => <span className="font-semibold text-foreground">{row.name}</span> },
    { key: 'message', header: 'Description' },
    {
      key: 'severity',
      header: 'Severity',
      render: (row: Alert) => {
        const isCritical = row.severity === 'CRITICAL';
        return (
          <Badge className={`text-xs px-2 py-0.5 border ${
            isCritical ? "bg-rose-500/10 text-rose-500 border-rose-500/20 font-bold" : "bg-amber-500/10 text-amber-500 border-amber-500/20"
          }`}>
            {row.severity}
          </Badge>
        );
      },
    },
    {
      key: 'status',
      header: 'Status',
      render: (row: Alert) => (
        <Badge variant={row.status === 'ACTIVE' ? 'destructive' : 'secondary'} className="capitalize border border-border">
          {row.status.toLowerCase()}
        </Badge>
      ),
    },
    { key: 'created_at', header: 'Triggered Date', render: (row: Alert) => new Date(row.created_at).toLocaleString() },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight">Observability Center</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Monitor distributed pipeline traces, active metric alerts, and execution logs.
        </p>
      </div>

      <Tabs defaultValue="traces" className="space-y-4">
        <TabsList className="bg-muted border border-border p-1 rounded-md max-w-sm">
          <TabsTrigger value="traces" className="text-xs">Distributed Traces</TabsTrigger>
          <TabsTrigger value="alerts" className="text-xs">Active Alerts</TabsTrigger>
        </TabsList>

        {/* Traces Tab */}
        <TabsContent value="traces">
          {tracesLoading ? (
            <SkeletonLoader rows={4} />
          ) : traces.length === 0 ? (
            <EmptyState
              title="No Traces Logged"
              description="Execute workflows or trigger connector handshakes to record telemetry traces."
              icon={<Eye className="h-10 w-10 text-muted-foreground" />}
            />
          ) : (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              {/* Correlation ID Selector */}
              <div className="lg:col-span-1 space-y-4">
                <Card className="border-border bg-card">
                  <CardHeader>
                    <CardTitle className="text-base font-bold flex items-center gap-1.5">
                      <Layers className="h-4 w-4 text-primary" /> Active Trace Spans
                    </CardTitle>
                    <CardDescription className="text-xs">Select correlation trace to audit span trees.</CardDescription>
                  </CardHeader>
                  <CardContent className="p-0">
                    <DataGrid
                      columns={traceColumns}
                      data={traces}
                      onRowClick={(row) => setSelectedCorrelationId(row.correlation_id)}
                      className="border-0 rounded-none border-t border-border/50"
                    />
                  </CardContent>
                </Card>
              </div>

              {/* Span Hierarchy ViewTree */}
              <div className="lg:col-span-2 space-y-4">
                {selectedTrace ? (
                  <Card className="border-border bg-card">
                    <CardHeader>
                      <CardTitle className="text-base font-bold flex items-center gap-1.5">
                        <Terminal className="h-4 w-4 text-primary" /> Trace Span Hierarchy
                      </CardTitle>
                      <CardDescription className="text-xs">Distributed parent-child nodes hierarchy trees.</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <TreeView items={traceTreeItems} />
                    </CardContent>
                  </Card>
                ) : (
                  <div className="h-[40vh] border border-dashed border-border rounded-lg bg-card/40 flex flex-col items-center justify-center text-center p-8">
                    <Eye className="h-10 w-10 text-muted-foreground mb-3" />
                    <span className="text-sm font-semibold text-foreground">Select a trace trace</span>
                    <span className="text-xs text-muted-foreground mt-0.5">Click a correlation row to view nested distributed spans.</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts">
          {alertsLoading ? (
            <SkeletonLoader rows={4} />
          ) : alerts.length === 0 ? (
            <EmptyState
              title="All Systems Healthy"
              description="No active anomalies, latency threshold breaches, or failures recorded."
              icon={<ShieldAlert className="h-10 w-10 text-muted-foreground" />}
            />
          ) : (
            <Card className="border-border bg-card">
              <CardHeader>
                <CardTitle className="text-base font-bold flex items-center gap-1.5">
                  <ShieldAlert className="h-4 w-4 text-rose-500" /> Active Alert Log
                </CardTitle>
                <CardDescription className="text-xs">Unresolved threshold warnings and exceptions raised across contexts.</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <DataGrid
                  columns={alertColumns}
                  data={alerts}
                  className="border-0 rounded-none border-t border-border/50"
                />
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
