'use client';

import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { observabilityApi } from '../../../shared/services/api';
import { useOperationsStore } from '../stores/operationsStore';
import { DataGrid, TreeView, TreeItem, SkeletonLoader } from '../../../shared/components/DesignSystem';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Layers, Terminal, Eye, HelpCircle } from 'lucide-react';
import { Trace, TraceSpan } from '../../../shared/types';

export const TraceExplorer: React.FC = () => {
  const { selectedTraceId, selectTrace } = useOperationsStore();

  // Query traces list
  const { data: traces = [], isLoading } = useQuery({
    queryKey: ['live-operations-traces'],
    queryFn: () => observabilityApi.listTraces(),
    refetchInterval: 5000,
  });

  const selectedTrace = useMemo(() => {
    if (!selectedTraceId) return null;
    
    // Exact correlation ID match
    const match = traces.find((t: any) => t.correlation_id === selectedTraceId);
    if (match) return match;

    // Fallback: match by session ID in spans attributes or session_id
    return traces.find((t: any) =>
      t.spans.some((s: any) => s.attributes?.session_id === selectedTraceId || s.attributes?.correlation_id === selectedTraceId)
    ) || null;
  }, [selectedTraceId, traces]);

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

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      {/* 1. Correlation ID Selector */}
      <div className="lg:col-span-1 space-y-4">
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-xs font-bold flex items-center gap-1.5">
              <Layers className="h-4 w-4 text-primary" /> Active Trace Spans
            </CardTitle>
            <CardDescription className="text-[10px]">Select correlation trace to audit span trees.</CardDescription>
          </CardHeader>
          <CardContent className="p-0 max-h-[400px] overflow-y-auto scrollbar-thin">
            {isLoading ? (
              <div className="p-4"><SkeletonLoader rows={3} /></div>
            ) : (
              <DataGrid
                columns={traceColumns}
                data={traces}
                onRowClick={(row) => selectTrace(row.correlation_id)}
                className="border-0 rounded-none border-t border-border/50"
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* 2. Span Hierarchy Tree View */}
      <div className="lg:col-span-2 space-y-4">
        {selectedTrace ? (
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="text-xs font-bold flex items-center gap-1.5">
                <Terminal className="h-4 w-4 text-primary" /> Trace Span Hierarchy
              </CardTitle>
              <CardDescription className="text-[10px]">Distributed parent-child nodes hierarchy trees.</CardDescription>
            </CardHeader>
            <CardContent className="max-h-[400px] overflow-y-auto scrollbar-thin">
              <TreeView items={traceTreeItems} />
            </CardContent>
          </Card>
        ) : (
          <div className="h-[250px] border border-dashed border-border rounded-lg bg-card/40 flex flex-col items-center justify-center text-center p-8">
            <Eye className="h-8 w-8 text-muted-foreground mb-2" />
            <span className="text-xs font-semibold text-foreground">Select a trace correlation</span>
            <span className="text-[10px] text-muted-foreground mt-0.5">Click a correlation row or search trace ID to view distributed spans.</span>
          </div>
        )}
      </div>
    </div>
  );
};
