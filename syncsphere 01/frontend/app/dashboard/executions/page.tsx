'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { runtimeApi } from '../../../shared/services/api';
import { ExecutionCard, DataGrid, Timeline, TimelineItem, EmptyState, SkeletonLoader } from '../../../shared/components/DesignSystem';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { Activity, Clock, ShieldAlert, CheckCircle2, ChevronRight, Layers, FileCode } from 'lucide-react';
import { ExecutionSession, ExecutionTrace } from '../../../shared/types';

export default function ExecutionsPage() {
  const [selectedExecId, setSelectedExecId] = useState<string | null>(null);

  // Query executions list
  const { data: executions = [], isLoading } = useQuery({
    queryKey: ['executions-list'],
    queryFn: () => runtimeApi.getExecutions(),
  });

  // Query execution traces
  const { data: traces = [], isLoading: tracesLoading } = useQuery({
    queryKey: ['execution-traces', selectedExecId],
    queryFn: () => (selectedExecId ? runtimeApi.getExecutionTraces(selectedExecId) : Promise.resolve([])),
    enabled: !!selectedExecId,
  });

  const selectedExec = executions.find((e: any) => e.id === selectedExecId);

  const getStatusBadge = (status: string) => {
    const colors = {
      completed: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
      failed: 'bg-rose-500/10 text-rose-500 border-rose-500/20',
      running: 'bg-sky-500/10 text-sky-500 border-sky-500/20',
      paused: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
      cancelled: 'bg-muted text-muted-foreground border-border',
    };
    const cls = colors[status as keyof typeof colors] || colors.cancelled;
    return <Badge className={`text-xs px-2 py-0.5 border ${cls} capitalize`}>{status}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight">Execution Runs</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Audit and trace active or completed workflow run instances.
        </p>
      </div>

      {isLoading ? (
        <SkeletonLoader rows={5} />
      ) : executions.length === 0 ? (
        <EmptyState
          title="No Executions Logged"
          description="Build and publish workflows in the builder canvas, then trigger them to see execution logs here."
          icon={<Activity className="h-10 w-10 text-muted-foreground" />}
        />
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Executions Card Selector */}
          <div className="lg:col-span-1 space-y-4">
            <span className="text-xs font-semibold text-muted-foreground block mb-2">Select Run Session</span>
            <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-2">
              {executions.map((exec: any) => (
                <ExecutionCard
                  key={exec.id}
                  execution={exec}
                  onSelect={(id) => setSelectedExecId(id)}
                  className={selectedExecId === exec.id ? "border-primary shadow-md bg-primary/[2%]" : ""}
                />
              ))}
            </div>
          </div>

          {/* Execution Details & Spans Timeline */}
          <div className="lg:col-span-2 space-y-4">
            {selectedExec ? (
              <div className="space-y-4">
                {/* Summary Card */}
                <Card className="border-border bg-card">
                  <CardHeader className="flex flex-row items-center justify-between pb-3">
                    <div>
                      <CardTitle className="text-base font-bold">Run #{selectedExec.id.slice(-8)} Details</CardTitle>
                      <CardDescription className="text-xs">Workflow: {selectedExec.workflow_id} (v{selectedExec.version})</CardDescription>
                    </div>
                    {getStatusBadge(selectedExec.status)}
                  </CardHeader>
                  <CardContent className="space-y-4 text-xs">
                    <div className="grid grid-cols-2 gap-4 border-t border-border/50 pt-4">
                      <div>
                        <span className="font-semibold text-muted-foreground block">Session ID</span>
                        <span className="font-mono text-foreground">{selectedExec.id}</span>
                      </div>
                      <div>
                        <span className="font-semibold text-muted-foreground block">Dispatched Date</span>
                        <span className="text-foreground">{new Date(selectedExec.created_at).toLocaleString()}</span>
                      </div>
                    </div>

                    <div>
                      <span className="font-semibold text-muted-foreground block mb-1">State Variables (Inputs)</span>
                      <pre className="font-mono bg-muted/30 border border-border p-3 rounded overflow-x-auto text-[10px]">
                        {JSON.stringify(selectedExec.variables, null, 2)}
                      </pre>
                    </div>
                  </CardContent>
                </Card>

                {/* Spans Timeline */}
                <Card className="border-border bg-card">
                  <CardHeader>
                    <CardTitle className="text-base font-bold flex items-center gap-1.5">
                      <Layers className="h-4 w-4 text-primary" /> Node Spans Timeline
                    </CardTitle>
                    <CardDescription className="text-xs">Trace segments and state changes during execution.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {tracesLoading ? (
                      <SkeletonLoader rows={2} />
                    ) : traces.length === 0 ? (
                      <span className="text-xs text-muted-foreground block py-4">No node traces synchronized for this run.</span>
                    ) : (
                      <Timeline>
                        {traces.map((t: any) => {
                          const status = t.status === 'completed' ? 'success' : t.status === 'failed' ? 'error' : 'info';
                          return (
                            <TimelineItem
                              key={t.id}
                              title={`Node: ${t.node_id}`}
                              time={new Date(t.started_at).toLocaleTimeString()}
                              status={status}
                              description={`Status: ${t.status}`}
                            >
                              {t.error && (
                                <div className="mt-1 flex items-center gap-2 rounded bg-rose-500/10 border border-rose-500/25 p-2 text-[10px] text-rose-500 font-medium">
                                  <ShieldAlert className="h-3.5 w-3.5" />
                                  <span>{t.error}</span>
                                </div>
                              )}
                            </TimelineItem>
                          );
                        })}
                      </Timeline>
                    )}
                  </CardContent>
                </Card>
              </div>
            ) : (
              <div className="h-[50vh] border border-dashed border-border rounded-lg bg-card/40 flex flex-col items-center justify-center text-center p-8">
                <FileCode className="h-10 w-10 text-muted-foreground mb-3" />
                <span className="text-sm font-semibold text-foreground">Select an execution run</span>
                <span className="text-xs text-muted-foreground mt-0.5">Click an execution session to audit trace details.</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
