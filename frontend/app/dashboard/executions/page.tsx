'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { runtimeApi, workflowApi } from '../../../shared/services/api';
import { ExecutionCard, Timeline, TimelineItem, EmptyState, SkeletonLoader } from '../../../shared/components/DesignSystem';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../../../components/ui/tabs';
import { Activity, Clock, ShieldAlert, CheckCircle2, ChevronRight, Layers, FileCode, Network, Terminal, Sparkles, Download, Copy, Play, GitFork, Loader2 } from 'lucide-react';
import { ReactFlow, Background, Controls, Edge, Node } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { customNodeTypes } from '../../../features/workflows/CustomNodeRegistry';
import { formatConnectorError } from '../../../shared/utils/errorParser';
import { toast } from 'sonner';
import { mapReactFlowToSyncSphere } from '../../../features/workflows/adapters';

export default function ExecutionsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialId = searchParams.get('id');
  const [selectedExecId, setSelectedExecId] = useState<string | null>(initialId);
  const [activeTab, setActiveTab] = useState('summary');
  const [isDuplicating, setIsDuplicating] = useState(false);

  useEffect(() => {
    if (initialId) {
      setSelectedExecId(initialId);
    }
  }, [initialId]);

  const { data: executions = [], isLoading } = useQuery({
    queryKey: ['executions-list'],
    queryFn: () => runtimeApi.getExecutions(),
  });

  const selectedExec = useMemo(() => executions.find((e: any) => e.id === selectedExecId), [executions, selectedExecId]);

  const handleDuplicateExecution = async () => {
    if (!selectedExec) return;
    setIsDuplicating(true);
    try {
      const baseName = selectedExec.workflow_name || 'Workflow';
      const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const newName = `Copy of ${baseName} (${timeStr})`;

      let newWorkflowId = '';

      if (selectedExec.workflow_id) {
        try {
          const cloned = await workflowApi.createWorkflow({
            name: newName,
            description: `Cloned from execution ${selectedExec.id}`,
            variables: []
          });
          newWorkflowId = cloned.id;

          try {
            const srcWf = await workflowApi.getWorkflow(selectedExec.workflow_id);
            if (srcWf && srcWf.nodes) {
              await workflowApi.updateWorkflow(newWorkflowId, {
                name: newName,
                description: srcWf.description || '',
                nodes: srcWf.nodes,
                edges: srcWf.edges || [],
                variables: (srcWf as any).variables || []
              });
            }
          } catch {
            /* Fallback to node generation */
          }
        } catch {
          /* Fallback */
        }
      }

      if (!newWorkflowId) {
        const draftNodes: any[] = [{
          id: 'start_1',
          type: 'start',
          position: { x: 100, y: 200 },
          data: { label: 'Start Trigger', description: selectedExec.trigger_type || 'Manual', nodeType: 'start', status: 'idle', config: {} }
        }];
        const draftEdges: any[] = [];
        let lastId = 'start_1';

        (selectedExec.action_results || []).forEach((act: any, idx: number) => {
          const nid = `node_${idx}`;
          let nType = 'connector';
          if (act.action?.includes('delay')) nType = 'delay';
          else if (act.action?.includes('approval')) nType = 'approval';
          else if (act.action?.includes('condition')) nType = 'condition';

          draftNodes.push({
            id: nid,
            type: nType,
            position: { x: 100 + (idx + 1) * 250, y: 200 },
            data: { label: act.action || 'Step', description: nType, nodeType: nType, status: 'idle', config: act.input_summary || {} }
          });
          draftEdges.push({
            id: `e_${lastId}-${nid}`,
            source: lastId,
            target: nid,
            type: 'smoothstep'
          });
          lastId = nid;
        });

        const newWf = await workflowApi.createWorkflow({
          name: newName,
          description: `Duplicated from execution run #${selectedExec.id.slice(-6)}`,
          variables: []
        });
        newWorkflowId = newWf.id;

        const mapped = mapReactFlowToSyncSphere(draftNodes, draftEdges);
        await workflowApi.updateWorkflow(newWorkflowId, {
          name: newName,
          description: `Duplicated from execution run #${selectedExec.id.slice(-6)}`,
          nodes: mapped.nodes,
          edges: mapped.edges,
          variables: []
        });
      }

      toast.success("Workflow duplicated successfully", {
        description: `Opening "${newName}" in workflow builder...`
      });

      router.push(`/dashboard/workflows/${newWorkflowId}`);
    } catch (err: any) {
      console.error('[DuplicateExecution] Failed:', err);
      toast.error("Failed to duplicate execution", {
        description: err?.response?.data?.detail?.message || err?.message || "An unexpected error occurred."
      });
    } finally {
      setIsDuplicating(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      completed: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
      success: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
      failed: 'bg-rose-500/10 text-rose-500 border-rose-500/20',
      running: 'bg-sky-500/10 text-sky-500 border-sky-500/20',
      paused: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
      partial: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
      cancelled: 'bg-muted text-muted-foreground border-border',
    };
    const cls = colors[status as keyof typeof colors] || colors.cancelled;
    return <Badge className={`text-xs px-2 py-0.5 border ${cls} capitalize`}>{status}</Badge>;
  };

  const downloadJson = () => {
    if (!selectedExec) return;
    const blob = new Blob([JSON.stringify(selectedExec, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `execution_${selectedExec.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Exported Execution JSON", { description: "The execution context was successfully exported." });
  };

  return (
    <div className="space-y-6 h-[calc(100vh-100px)] flex flex-col">
      <div className="flex justify-between items-end flex-shrink-0">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Execution Observability</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Enterprise tracing, payloads, and visualizations for workflow executions.
          </p>
        </div>
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
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[300px_1fr] flex-grow overflow-hidden">

          {/* Left Panel: Executions List */}
          <div className="flex flex-col space-y-4 overflow-hidden rounded-xl border border-border bg-card">
            <div className="p-4 border-b border-border bg-muted/20 font-semibold text-sm flex justify-between items-center">
              <span>Execution Runs</span>
              <Badge variant="secondary">{executions.length}</Badge>
            </div>
            <div className="space-y-1 p-2 overflow-y-auto flex-grow">
              {executions.map((exec: any) => (
                <div
                  key={exec.id}
                  onClick={() => setSelectedExecId(exec.id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${selectedExecId === exec.id ? 'border-primary bg-primary/5' : 'border-transparent hover:bg-muted/50'} `}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className="font-semibold text-xs truncate max-w-[150px]">{exec.workflow_name || exec.workflow_id}</span>
                    {getStatusBadge(exec.status)}
                  </div>
                  <div className="flex justify-between items-center text-[10px] text-muted-foreground mt-2">
                    <span className="truncate">{new Date(exec.started_at).toLocaleString()}</span>
                    <span>{exec.duration_ms ? `${exec.duration_ms}ms` : ''}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Panel: Execution Diagnostics */}
          <div className="overflow-hidden flex flex-col rounded-xl border border-border bg-card shadow-sm">
            {selectedExec ? (
              <>
                {/* Header Actions */}
                <div className="p-5 border-b border-border bg-muted/10 flex flex-wrap gap-4 items-center justify-between">
                  <div>
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-bold">Trace: {selectedExec.id}</h3>
                      {getStatusBadge(selectedExec.status)}
                    </div>
                    <div className="flex gap-4 items-center text-xs text-muted-foreground mt-2 font-medium">
                      <span className="flex items-center gap-1.5"><Play className="w-3 h-3" /> {selectedExec.trigger_type || 'Manual'} Trigger</span>
                      <span className="flex items-center gap-1.5"><Clock className="w-3 h-3" /> {selectedExec.duration_ms || 0}ms Duration</span>
                      <span className="bg-muted px-2 py-0.5 rounded text-[10px]">{selectedExec.environment || 'Production'}</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={handleDuplicateExecution} disabled={isDuplicating}>
                      {isDuplicating ? <Loader2 className="w-3 h-3 mr-2 animate-spin" /> : <GitFork className="w-3 h-3 mr-2" />}
                      Duplicate
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => { navigator.clipboard.writeText(selectedExec.id); toast.success("Copied Execution ID"); }}><Copy className="w-3 h-3 mr-2" /> Copy ID</Button>
                    <Button variant="outline" size="sm" onClick={downloadJson}><Download className="w-3 h-3 mr-2" /> Export JSON</Button>
                  </div>
                </div>

                {/* Tabs */}
                <div className="flex-grow flex flex-col overflow-hidden">
                  <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
                    <div className="px-5 pt-3 border-b border-border">
                      <TabsList className="bg-transparent border-b-0 h-auto p-0 gap-6 justify-start w-full gap-x-2">
                        <TabsTrigger value="summary" className="data-[state=active]:bg-muted/50 data-[state=active]:shadow-none rounded-b-none border-b-2 border-transparent data-[state=active]:border-primary pb-3 rounded-t-lg"><Layers className="w-4 h-4 mr-2" /> Timeline</TabsTrigger>
                        <TabsTrigger value="graph" className="data-[state=active]:bg-muted/50 data-[state=active]:shadow-none rounded-b-none border-b-2 border-transparent data-[state=active]:border-primary pb-3 rounded-t-lg"><Network className="w-4 h-4 mr-2" /> Interactive Graph</TabsTrigger>
                        <TabsTrigger value="ai" className="data-[state=active]:bg-muted/50 data-[state=active]:shadow-none rounded-b-none border-b-2 border-transparent data-[state=active]:border-primary pb-3 rounded-t-lg"><Sparkles className="w-4 h-4 mr-2" /> AI Usage</TabsTrigger>
                        <TabsTrigger value="logs" className="data-[state=active]:bg-muted/50 data-[state=active]:shadow-none rounded-b-none border-b-2 border-transparent data-[state=active]:border-primary pb-3 rounded-t-lg"><Terminal className="w-4 h-4 mr-2" /> JSON Payloads</TabsTrigger>
                      </TabsList>
                    </div>

                    <div className="flex-grow overflow-auto p-5 relative bg-muted/5">
                      <TabsContent value="summary" className="m-0 h-full">
                        <ExecutionTimelineTab exec={selectedExec} />
                      </TabsContent>
                      <TabsContent value="graph" className="m-0 h-full">
                        <ExecutionGraphTab exec={selectedExec} />
                      </TabsContent>
                      <TabsContent value="ai" className="m-0 h-full">
                        <ExecutionAiTab exec={selectedExec} />
                      </TabsContent>
                      <TabsContent value="logs" className="m-0 h-full">
                        <ExecutionLogsTab exec={selectedExec} />
                      </TabsContent>
                    </div>
                  </Tabs>
                </div>
              </>
            ) : (
              <div className="h-full border-dashed border-border flex flex-col items-center justify-center text-center p-8 bg-muted/5">
                <FileCode className="h-10 w-10 text-muted-foreground mb-3" />
                <span className="text-sm font-semibold text-foreground">Select an execution run</span>
                <span className="text-xs text-muted-foreground mt-1">Audit granular traces, payloads, and topologies.</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ===============================================
// TAB COMPONENTS
// ===============================================

function ExecutionTimelineTab({ exec }: { exec: any }) {
  if (!exec.action_results || exec.action_results.length === 0) {
    return <span className="text-xs text-muted-foreground block py-4">No node traces synchronized for this run.</span>;
  }

  return (
    <div className="space-y-6">
      <Card className="border-border shadow-none">
        <CardContent className="pt-6">
          <Timeline>
            <TimelineItem title="Execution Started" time={new Date(exec.started_at).toLocaleTimeString()} status="success" description={`Trigger: ${exec.trigger_type || 'Manual'}`} />

            {exec.action_results.map((t: any, idx: number) => {
              const status = t.status === 'success' ? 'success' : t.status === 'failed' || t.status === 'blocked' ? 'error' : t.status === 'awaiting_approval' ? 'pending' : 'info';
              return (
                <TimelineItem
                  key={idx}
                  title={`${t.action?.replace('_', ' ').toUpperCase()}`}
                  time={t.completed_at ? new Date(t.completed_at).toLocaleTimeString() : new Date(exec.started_at).toLocaleTimeString()}
                  status={status as any}
                  description={`Node Executed in ${t.attempts || 1} attempt(s)`}
                >
                  <div className="mt-2 space-y-2">
                    {t.status === 'awaiting_approval' && (
                      <div className="flex items-center gap-2 rounded bg-amber-500/10 border border-amber-500/25 p-2 text-xs text-amber-500 font-medium shadow-sm">
                        <Clock className="h-4 w-4 shrink-0 animate-pulse" />
                        <span>Execution paused awaiting Human Approval decision.</span>
                      </div>
                    )}
                    {t.error && (
                      <div className="flex items-center gap-2 rounded bg-rose-500/10 border border-rose-500/25 p-2 text-xs text-rose-500 font-medium">
                        <ShieldAlert className="h-4 w-4 shrink-0" />
                        <span>{t.error}</span>
                      </div>
                    )}

                    {(() => {
                      const links: Record<string, string> = { ...(t.resource_links || {}) };
                      const out = t.output_summary || {};
                      const slackUrl = out.message_permalink || out.permalink || out.slack_link || out.channel_url;
                      if (slackUrl && !links.slack && !links.slack_message && !links.slack_channel) {
                        links.slack = slackUrl;
                      }
                      const calendarUrl = out.htmlLink || out.event_link || out.event_url;
                      if (calendarUrl && !links.calendar && !links.google_calendar) {
                        links.google_calendar = calendarUrl;
                      }
                      if (Object.keys(links).length === 0) return null;
                      return (
                        <div className="flex flex-col gap-1.5 mt-2">
                          <span className="text-xs font-semibold text-muted-foreground">Generated Resources:</span>
                          {Object.entries(links).map(([key, url]: [string, any]) => (
                            <a key={key} href={url} target="_blank" rel="noreferrer" className="text-xs text-indigo-500 hover:underline flex items-center gap-1 font-semibold pr-2 border border-border bg-card rounded-md w-fit p-1.5">
                              {key.replace('_url', '').replace('_', ' ').toUpperCase()} <ChevronRight className="h-3 w-3" />
                            </a>
                          ))}
                        </div>
                      );
                    })()}

                    {t.input_summary && Object.keys(t.input_summary).length > 0 && (
                      <details className="text-xs">
                        <summary className="font-semibold text-muted-foreground cursor-pointer hover:text-foreground">View Request Context</summary>
                        <pre className="mt-2 font-mono bg-card border border-border p-3 rounded-lg overflow-x-auto text-[10px]">
                          {JSON.stringify(t.input_summary, null, 2)}
                        </pre>
                      </details>
                    )}

                    {t.http_metadata && Object.keys(t.http_metadata).length > 0 && (
                      <details className="text-xs mt-2">
                        <summary className="font-semibold text-sky-500 cursor-pointer hover:text-sky-400">View Network Payload</summary>
                        <pre className="mt-2 font-mono bg-muted/40 border border-border p-3 rounded-lg overflow-x-auto text-[10px]">
                          {JSON.stringify(t.http_metadata, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                </TimelineItem>
              );
            })}

            <TimelineItem title="Execution Terminated" time={exec.completed_at ? new Date(exec.completed_at).toLocaleTimeString() : 'N/A'} status={exec.status === 'success' ? 'success' : 'error'} description={`Flow returned ${exec.status.toUpperCase()}`} />
          </Timeline>
        </CardContent>
      </Card>
    </div>
  );
}

function ExecutionGraphTab({ exec }: { exec: any }) {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  useEffect(() => {
    if (!exec.action_results) return;

    const draftNodes: Node[] = [];
    const draftEdges: Edge[] = [];
    let currentX = 50;
    const Y_MAIN = 200;

    // Start Node
    draftNodes.push({
      id: 'start_1', type: 'start', position: { x: currentX, y: Y_MAIN },
      data: { label: 'Start Trigger', description: exec.trigger_type || 'Manual', nodeType: 'start', status: 'success', config: {} }
    });
    let lastNodeId = 'start_1';
    currentX += 300;

    // Iterate traces
    exec.action_results.forEach((res: any, idx: number) => {
      let nType = 'connector';
      if (res.action?.includes('delay')) nType = 'delay';
      else if (res.action?.includes('approval')) nType = 'approval';
      else if (res.action?.includes('condition')) nType = 'condition';

      const nodeId = `node_${idx}`;
      const nodeStatus = res.status === 'success' ? 'success' : res.status === 'failed' ? 'failed' : 'idle';

      draftNodes.push({
        id: nodeId, type: nType, position: { x: currentX, y: Y_MAIN },
        data: { label: res.action, description: nType, nodeType: nType, status: nodeStatus, config: res.input_summary }
      });

      draftEdges.push({
        id: `e_${lastNodeId}-${nodeId}`,
        source: lastNodeId,
        target: nodeId,
        type: 'smoothstep',
        animated: nodeStatus === 'success',
        style: { stroke: nodeStatus === 'failed' ? '#ef4444' : '#10b981', strokeWidth: 2 }
      });

      lastNodeId = nodeId;
      currentX += 300;
    });

    // End Nodes
    const endNodeId = 'end_final';
    draftNodes.push({
      id: endNodeId, type: 'end', position: { x: currentX, y: Y_MAIN },
      data: { label: 'End', description: `Execution ${exec.status}`, nodeType: 'end', status: exec.status === 'success' ? 'success' : 'failed', config: {} }
    });
    draftEdges.push({
      id: `e_${lastNodeId}-${endNodeId}`,
      source: lastNodeId,
      target: endNodeId,
      type: 'smoothstep',
      animated: exec.status === 'success',
      style: { stroke: exec.status === 'failed' ? '#ef4444' : '#10b981', strokeWidth: 2 }
    });

    setNodes(draftNodes);
    setEdges(draftEdges);
  }, [exec]);

  return (
    <div className="w-full h-full border border-border rounded-xl overflow-hidden bg-card/50 relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={customNodeTypes}
        fitView
        minZoom={0.5}
        maxZoom={1.5}
        fitViewOptions={{ padding: 0.2 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={true}
      >
        <Background />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

function ExecutionAiTab({ exec }: { exec: any }) {
  if (!exec.ai_execution_summary) {
    return (
      <div className="flex flex-col items-center justify-center p-10 border border-dashed border-border rounded-lg bg-card">
        <Sparkles className="w-10 h-10 text-muted-foreground mb-3 opacity-50" />
        <span className="font-semibold text-sm">No AI Usage Found</span>
        <span className="text-xs text-muted-foreground text-center max-w-[300px] mt-1">This execution did not invoke the Agentic AI Planner, therefore no OpenRouter usage logs were generated.</span>
      </div>
    );
  }

  const ai = exec.ai_execution_summary;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="shadow-none border-border">
          <CardContent className="p-4 flex flex-col justify-center">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Model Executed</span>
            <span className="text-sm font-bold font-mono mt-1 text-primary">{ai.model_used || 'N/A'}</span>
          </CardContent>
        </Card>
        <Card className="shadow-none border-border">
          <CardContent className="p-4 flex flex-col justify-center">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Input Tokens</span>
            <span className="text-sm font-bold font-mono mt-1">{ai.input_tokens || 0}</span>
          </CardContent>
        </Card>
        <Card className="shadow-none border-border">
          <CardContent className="p-4 flex flex-col justify-center">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Output Tokens</span>
            <span className="text-sm font-bold font-mono mt-1">{ai.output_tokens || 0}</span>
          </CardContent>
        </Card>
        <Card className="shadow-none border-border">
          <CardContent className="p-4 flex flex-col justify-center">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Estimated Cost</span>
            <span className="text-sm font-bold font-mono mt-1 text-emerald-500">${ai.cost_usd ? ai.cost_usd.toFixed(4) : '0.00'}</span>
          </CardContent>
        </Card>
      </div>

      <Card className="shadow-none border-border">
        <CardHeader>
          <CardTitle className="text-sm font-bold flex items-center gap-2"><Terminal className="w-4 h-4 text-violet-500" /> Prompt Injection</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="font-mono text-xs bg-muted/30 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap border border-border text-primary/80">
            {ai.prompt_sent || 'Prompt context unavailable.'}
          </pre>
        </CardContent>
      </Card>

      {ai.response && (
        <Card className="shadow-none border-border">
          <CardHeader>
            <CardTitle className="text-sm font-bold flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-500" /> AI Response Payload</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="font-mono text-xs bg-muted/30 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap border border-border text-emerald-500/80">
              {typeof ai.response === 'string' ? ai.response : JSON.stringify(ai.response, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function ExecutionLogsTab({ exec }: { exec: any }) {
  return (
    <Card className="shadow-none border-border h-full flex flex-col overflow-hidden bg-[#0A0A0A]">
      <div className="p-3 border-b border-[#222] bg-[#111] flex justify-between items-center text-xs text-[#888] font-mono">
        <span>/var/logs/executions/{exec.id}.json</span>
        <span className="bg-[#222] px-2 py-1 rounded">UTF-8</span>
      </div>
      <div className="flex-grow overflow-auto p-4">
        <pre className="font-mono text-[11px] leading-relaxed text-[#00FF00]">
          {JSON.stringify(exec, null, 2)}
        </pre>
      </div>
    </Card>
  );
}
