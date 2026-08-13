'use client';

import React, { useMemo } from 'react';
import { useWorkflowBuilderStore } from '../../shared/stores/workflowBuilderStore';
import { simulateWorkflow, formatDuration, formatCost } from './WorkflowSimulation';
import { validateWorkflow, hasErrors, getErrorCount, getWarningCount } from './WorkflowValidation';
import {
  X, Play, Zap, Clock, Coins, Radio, ShieldCheck,
  AlertTriangle, CheckCircle, XCircle, Info, ArrowRight,
  Loader2,
} from 'lucide-react';
import { toast } from 'sonner';

// ==========================================
// Execution Preview Panel
// ==========================================
export const ExecutionPreview: React.FC = () => {
  const {
    nodes, edges, isPreviewOpen, togglePreview,
    simulationResult, setSimulationResult, isSimulating, setIsSimulating,
    validationMessages, setValidationMessages,
  } = useWorkflowBuilderStore();

  // Run validation
  const validationResult = useMemo(() => validateWorkflow(nodes, edges), [nodes, edges]);
  const errorCount = getErrorCount(validationResult);
  const warningCount = getWarningCount(validationResult);

  const handleRunSimulation = () => {
    setIsSimulating(true);
    setValidationMessages(validationResult);

    // Small delay to show loading state, then run simulation
    setTimeout(() => {
      const result = simulateWorkflow(nodes, edges);
      setSimulationResult(result);
      setIsSimulating(false);
      toast.success('Simulation Completed', { description: 'Workflow dry-run metrics generated successfully.' });
    }, 800);
  };

  if (!isPreviewOpen) return null;

  return (
    <div className="absolute right-0 top-0 w-[380px] h-full bg-card border-l border-border flex flex-col z-20 shadow-xl overflow-hidden" role="dialog" aria-label="Execution preview">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-3 pb-2 border-b border-border">
        <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
          <Zap className="h-4 w-4 text-amber-500" />
          Execution Preview
        </h3>
        <button onClick={togglePreview} className="p-1 rounded hover:bg-accent transition-colors" aria-label="Close preview">
          <X className="h-4 w-4 text-muted-foreground" />
        </button>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4 scrollbar-thin">
        {/* Validation Section */}
        <div>
          <h4 className="text-xs font-bold text-foreground mb-2 flex items-center gap-1.5">
            {errorCount > 0 ? (
              <XCircle className="h-3.5 w-3.5 text-rose-500" />
            ) : (
              <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
            )}
            Validation ({errorCount} errors, {warningCount} warnings)
          </h4>

          {validationResult.length === 0 && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-emerald-500/10 border border-emerald-500/20">
              <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
              <span className="text-xs text-emerald-600">All validations passed.</span>
            </div>
          )}

          <div className="space-y-1.5 max-h-[180px] overflow-y-auto">
            {validationResult.map((msg, i) => (
              <div
                key={i}
                className={`flex items-start gap-2 px-2.5 py-1.5 rounded-md text-xs border ${msg.severity === 'error'
                  ? 'bg-rose-500/5 border-rose-500/20 text-rose-600'
                  : msg.severity === 'warning'
                    ? 'bg-amber-500/5 border-amber-500/20 text-amber-600'
                    : 'bg-sky-500/5 border-sky-500/20 text-sky-600'
                  }`}
              >
                {msg.severity === 'error' ? <XCircle className="h-3 w-3 mt-0.5 shrink-0" /> :
                  msg.severity === 'warning' ? <AlertTriangle className="h-3 w-3 mt-0.5 shrink-0" /> :
                    <Info className="h-3 w-3 mt-0.5 shrink-0" />}
                <span>{msg.message}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Simulate Button */}
        <button
          onClick={handleRunSimulation}
          disabled={isSimulating || hasErrors(validationResult)}
          className="w-full flex items-center justify-center gap-2 h-9 rounded-md text-xs font-bold
            bg-primary text-primary-foreground hover:bg-primary/90
            disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Run simulation"
        >
          {isSimulating ? (
            <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Simulating...</>
          ) : (
            <><Play className="h-3.5 w-3.5" /> Run Simulation</>
          )}
        </button>

        {/* Simulation Results */}
        {simulationResult && !isSimulating && (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-md border border-border p-2.5 bg-background">
                <div className="flex items-center gap-1.5 mb-1">
                  <Clock className="h-3 w-3 text-sky-500" />
                  <span className="text-[10px] text-muted-foreground font-medium">Est. Duration</span>
                </div>
                <span className="text-sm font-bold text-foreground">{formatDuration(simulationResult.totalLatencyMs)}</span>
              </div>
              <div className="rounded-md border border-border p-2.5 bg-background">
                <div className="flex items-center gap-1.5 mb-1">
                  <Coins className="h-3 w-3 text-amber-500" />
                  <span className="text-[10px] text-muted-foreground font-medium">Est. Cost</span>
                </div>
                <span className="text-sm font-bold text-foreground">{formatCost(simulationResult.estimatedCost)}</span>
              </div>
              <div className="rounded-md border border-border p-2.5 bg-background">
                <div className="flex items-center gap-1.5 mb-1">
                  <Zap className="h-3 w-3 text-violet-500" />
                  <span className="text-[10px] text-muted-foreground font-medium">AI Tokens</span>
                </div>
                <span className="text-sm font-bold text-foreground">{simulationResult.totalTokens.toLocaleString()}</span>
              </div>
              <div className="rounded-md border border-border p-2.5 bg-background">
                <div className="flex items-center gap-1.5 mb-1">
                  <ArrowRight className="h-3 w-3 text-emerald-500" />
                  <span className="text-[10px] text-muted-foreground font-medium">Steps</span>
                </div>
                <span className="text-sm font-bold text-foreground">{simulationResult.executionOrder.length}</span>
              </div>
            </div>

            {/* Required Connectors */}
            {simulationResult.requiredConnectors.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-foreground mb-1.5 flex items-center gap-1.5">
                  <Radio className="h-3.5 w-3.5 text-sky-500" />
                  Required Connectors
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {simulationResult.requiredConnectors.map((c) => (
                    <span key={c} className="px-2 py-0.5 rounded-full bg-sky-500/10 border border-sky-500/20 text-[10px] text-sky-600 font-medium">
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Approval Gates */}
            {simulationResult.approvalGates.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-foreground mb-1.5 flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5 text-orange-500" />
                  Approval Gates
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {simulationResult.approvalGates.map((g) => (
                    <span key={g} className="px-2 py-0.5 rounded-full bg-orange-500/10 border border-orange-500/20 text-[10px] text-orange-600 font-medium">
                      {g}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Execution Order / DAG */}
            <div>
              <h4 className="text-xs font-bold text-foreground mb-2">Compiled DAG — Execution Order</h4>
              <div className="space-y-1">
                {simulationResult.executionOrder.map((nodeId, i) => {
                  const nr = simulationResult.nodeResults[nodeId];
                  const node = nodes.find((n) => n.id === nodeId);
                  return (
                    <div
                      key={nodeId}
                      className="flex items-center gap-2 px-2.5 py-1.5 rounded-md border border-border bg-background"
                    >
                      <span className="text-[10px] text-muted-foreground font-mono w-5">{i + 1}.</span>
                      <span className="text-xs text-foreground font-medium flex-1 truncate">
                        {node?.data?.label || nodeId}
                      </span>
                      <span className="text-[10px] text-muted-foreground">{formatDuration(nr?.latencyMs || 0)}</span>
                      <span className={`h-1.5 w-1.5 rounded-full ${nr?.status === 'success' ? 'bg-emerald-500' : nr?.status === 'skipped' ? 'bg-muted-foreground' : 'bg-amber-500'}`} />
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
