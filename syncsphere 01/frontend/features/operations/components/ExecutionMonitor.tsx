'use client';

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { runtimeApi } from '../../../shared/services/api';
import { useOperationsStore } from '../stores/operationsStore';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { Progress } from '../../../components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/table';
import { Play, Pause, XCircle, Search, RefreshCw, Layers } from 'lucide-react';
import { toast } from 'sonner';

export const ExecutionMonitor: React.FC = () => {
  const queryClient = useQueryClient();
  const { searchQuery, filters, selectTrace, activeExecutions, setActiveExecutions } = useOperationsStore();

  // Query execution lists
  const { data: executions = [], isLoading, refetch } = useQuery({
    queryKey: ['live-executions-monitor'],
    queryFn: async () => {
      const data = await runtimeApi.getExecutions();
      setActiveExecutions(data);
      return data;
    },
    refetchInterval: 5000, // Poll fallback
  });

  // Action mutations
  const pauseMutation = useMutation({
    mutationFn: (id: string) => runtimeApi.pauseExecution(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['live-executions-monitor'] });
      toast.success('Execution Paused', { description: `Session #${id.slice(-6)} runtime paused.` });
    },
  });

  const resumeMutation = useMutation({
    mutationFn: (id: string) => runtimeApi.resumeExecution(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['live-executions-monitor'] });
      toast.success('Execution Resumed', { description: `Session #${id.slice(-6)} restarted.` });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => runtimeApi.cancelExecution(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['live-executions-monitor'] });
      toast.success('Execution Cancelled', { description: `Session #${id.slice(-6)} cancelled.` });
    },
  });

  // Filters application
  const filtered = (activeExecutions.length > 0 ? activeExecutions : executions).filter((item: any) => {
    // Search query matches
    if (searchQuery) {
      const matchQuery = searchQuery.toLowerCase();
      const matchId = item.id.toLowerCase().includes(matchQuery);
      const matchWf = item.workflow_id.toLowerCase().includes(matchQuery);
      if (!matchId && !matchWf) return false;
    }
    // Filter parameters matches
    if (filters.workflowId && item.workflow_id !== filters.workflowId) return false;
    if (filters.status && item.status !== filters.status) return false;
    return true;
  });

  // Math helper for node completion percentages
  const getProgress = (stepStates: Record<string, any> = {}) => {
    const total = Object.keys(stepStates).length;
    if (total === 0) return { percent: 0, current: 'Start', total: 0, completed: 0 };
    const completed = Object.values(stepStates).filter((s) => s.status === 'success' || s.status === 'completed').length;
    const current = Object.keys(stepStates).find((k) => stepStates[k].status === 'running') || 'Start';
    return {
      percent: Math.round((completed / total) * 100),
      current,
      total,
      completed,
    };
  };

  const getRuntimeStr = (created: string) => {
    const elapsed = Date.now() - new Date(created).getTime();
    if (elapsed < 1000) return '0s';
    const sec = Math.floor(elapsed / 1000);
    if (sec < 60) return `${sec}s`;
    const min = Math.floor(sec / 60);
    return `${min}m ${sec % 60}s`;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-bold text-foreground">Live Execution Monitor</h4>
          <p className="text-[10px] text-muted-foreground mt-0.5">Control and watch running workflow DAG instances</p>
        </div>
        <Button size="icon" variant="ghost" className="h-8 w-8 hover:bg-muted border border-border" onClick={() => refetch()} aria-label="Refresh executions list">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      <div className="rounded-md border border-border bg-card overflow-hidden">
        <Table>
          <TableHeader className="bg-muted/40">
            <TableRow>
              <TableHead className="font-semibold text-xs text-muted-foreground">Execution ID</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground">Workflow ID</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground">Status</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground">Step Progress</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground">Runtime</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground">Est. Completion</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-xs text-muted-foreground">
                  Loading executions logs...
                </TableCell>
              </TableRow>
            ) : filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-xs text-muted-foreground">
                  No active or matching executions found.
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((item: any) => {
                const prog = getProgress(item.step_states);
                const runtime = getRuntimeStr(item.created_at);
                
                return (
                  <TableRow key={item.id} className="hover:bg-muted/30 transition-colors">
                    <TableCell className="font-mono text-xs font-semibold text-foreground">
                      <button
                        onClick={() => selectTrace(item.id)}
                        className="hover:underline text-primary text-left"
                      >
                        #{item.id.slice(-6)}
                      </button>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{item.workflow_id}</TableCell>
                    <TableCell>
                      <Badge className={`text-[10px] scale-90 border font-semibold px-2 py-0.5 capitalize ${
                        item.status === 'running'
                          ? 'text-sky-500 bg-sky-500/10 border-sky-500/20'
                          : item.status === 'completed'
                          ? 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20'
                          : item.status === 'failed'
                          ? 'text-rose-500 bg-rose-500/10 border-rose-500/20'
                          : 'text-amber-500 bg-amber-500/10 border-amber-500/20'
                      }`}>
                        {item.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="w-[200px]">
                      <div className="space-y-1">
                        <div className="flex justify-between text-[10px] text-muted-foreground">
                          <span className="truncate max-w-[120px]">Step: {prog.current}</span>
                          <span>{prog.completed}/{prog.total} ({prog.percent}%)</span>
                        </div>
                        <Progress value={prog.percent} className="h-1 bg-muted" />
                      </div>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground font-mono">{runtime}</TableCell>
                    <TableCell className="text-xs text-muted-foreground font-mono">
                      {item.status === 'running' ? '~15s' : 'Done'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex gap-1 justify-end">
                        {item.status === 'running' ? (
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-7 w-7 text-amber-500 hover:bg-amber-500/10"
                            onClick={() => pauseMutation.mutate(item.id)}
                            title="Pause execution"
                          >
                            <Pause className="h-3.5 w-3.5" />
                          </Button>
                        ) : item.status === 'paused' ? (
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-7 w-7 text-emerald-500 hover:bg-emerald-500/10"
                            onClick={() => resumeMutation.mutate(item.id)}
                            title="Resume execution"
                          >
                            <Play className="h-3.5 w-3.5 fill-current" />
                          </Button>
                        ) : null}
                        
                        {(item.status === 'running' || item.status === 'paused') && (
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-7 w-7 text-rose-500 hover:bg-rose-500/10"
                            onClick={() => cancelMutation.mutate(item.id)}
                            title="Cancel execution"
                          >
                            <XCircle className="h-3.5 w-3.5" />
                          </Button>
                        )}
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7 text-muted-foreground hover:bg-muted"
                          onClick={() => selectTrace(item.id)}
                          title="Open execution trace explorer"
                        >
                          <Layers className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};
