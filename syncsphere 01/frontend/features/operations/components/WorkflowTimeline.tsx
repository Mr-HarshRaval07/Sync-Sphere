'use client';

import React, { useMemo } from 'react';
import { useOperationsStore } from '../stores/operationsStore';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../../../components/ui/card';
import { AlertCircle, ShieldAlert, Zap, Clock, Play, CheckCircle2 } from 'lucide-react';

// ==========================================
// 1. Workflow Timeline Component
// ==========================================
export const WorkflowTimeline: React.FC = () => {
  const { selectedTraceId, activeExecutions } = useOperationsStore();

  const selectedExecution = useMemo(
    () => activeExecutions.find((e) => e.id === selectedTraceId),
    [selectedTraceId, activeExecutions]
  );

  const steps = [
    { key: 'planner', label: 'Planner', description: 'Agentic task decomposition' },
    { key: 'compiler', label: 'Compiler', description: 'DAG validation & dependency compilation' },
    { key: 'runtime', label: 'Runtime Engine', description: 'Worker queue allocation' },
    { key: 'connector', label: 'Connector Calls', description: 'External integration invocation' },
    { key: 'approval', label: 'Approvals Gate', description: 'Human authorization check' },
    { key: 'knowledge', label: 'Knowledge Base', description: 'RAG retrieval execution' },
    { key: 'ai', label: 'AI Completion', description: 'LLM inference process' },
    { key: 'completed', label: 'Completed', description: 'Pipeline run finalized' },
  ];

  // Helper to determine step status
  const getStepStatus = (stepKey: string): 'completed' | 'active' | 'pending' | 'failed' => {
    if (!selectedExecution) return 'pending';
    if (selectedExecution.status === 'failed') return 'failed';
    if (selectedExecution.status === 'completed') return 'completed';

    const states = selectedExecution.step_states || {};
    
    // Simplistic heuristic for current progress stage
    const runningNode = Object.values(states).find((s: any) => s.status === 'running');
    const runningType = runningNode?.type;

    if (stepKey === 'planner') return 'completed';
    if (stepKey === 'compiler') return 'completed';
    if (stepKey === 'runtime') return 'completed';

    if (stepKey === 'connector' && runningType === 'connector') return 'active';
    if (stepKey === 'approval' && runningType === 'approval') return 'active';
    if (stepKey === 'knowledge' && runningType === 'knowledge') return 'active';
    if (stepKey === 'ai' && runningType === 'ai') return 'active';
    
    // Check if we have completed any steps of this type
    const hasCompleted = Object.values(states).some((s: any) => s.type === stepKey && s.status === 'success');
    if (hasCompleted) return 'completed';

    return 'pending';
  };

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="text-xs font-bold flex items-center gap-1.5">
          <Zap className="h-4 w-4 text-primary" /> Visual Workflow Execution Timeline
        </CardTitle>
        <CardDescription className="text-[10px]">
          {selectedExecution ? `Stages path mapping for run #${selectedExecution.id.slice(-6)}` : 'Select an active execution to view pipeline progress'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {selectedExecution ? (
          <div className="relative pl-6 border-l border-border space-y-5">
            {steps.map((step) => {
              const status = getStepStatus(step.key);
              
              return (
                <div key={step.key} className="relative">
                  {/* Status Circle Indicator */}
                  <span className={`absolute -left-[30px] top-0.5 flex h-4 w-4 items-center justify-center rounded-full border-2 bg-background transition-colors
                    ${status === 'completed'
                      ? 'border-emerald-500 text-emerald-500'
                      : status === 'active'
                      ? 'border-sky-500 text-sky-500 animate-pulse'
                      : status === 'failed'
                      ? 'border-rose-500 text-rose-500 animate-bounce'
                      : 'border-border text-muted-foreground'
                    }`}
                  >
                    {status === 'completed' && <CheckCircle2 className="h-2.5 w-2.5 fill-current" />}
                    {status === 'active' && <Play className="h-2 w-2 fill-current" />}
                    {status === 'failed' && <AlertCircle className="h-2.5 w-2.5 fill-current" />}
                    {status === 'pending' && <span className="h-1.5 w-1.5 rounded-full bg-border" />}
                  </span>

                  <div className="flex flex-col">
                    <span className={`text-xs font-semibold ${status === 'active' ? 'text-sky-500' : 'text-foreground'}`}>
                      {step.label}
                    </span>
                    <span className="text-[10px] text-muted-foreground mt-0.5">{step.description}</span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-muted-foreground italic">
            No pipeline selected. Click an execution ID in the list to open.
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// ==========================================
// 2. Incident Timeline Component
// ==========================================
export const IncidentTimeline: React.FC = () => {
  const { alerts } = useOperationsStore();

  const incidents = useMemo(() => {
    return alerts.map((a) => ({
      id: a.id,
      title: a.name,
      description: a.message,
      time: new Date(a.created_at).toLocaleTimeString(),
      severity: a.severity,
    }));
  }, [alerts]);

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="text-xs font-bold flex items-center gap-1.5">
          <ShieldAlert className="h-4 w-4 text-rose-500" /> Operational Incident Log
        </CardTitle>
        <CardDescription className="text-[10px]">Real-time audit history of system events and alerts</CardDescription>
      </CardHeader>
      <CardContent>
        {incidents.length > 0 ? (
          <div className="relative pl-6 border-l border-border space-y-4">
            {incidents.map((incident) => (
              <div key={incident.id} className="relative">
                <span className={`absolute -left-[30px] top-0.5 flex h-4 w-4 items-center justify-center rounded-full border-2 bg-background
                  ${incident.severity === 'CRITICAL'
                    ? 'border-rose-500 text-rose-500 animate-ping'
                    : 'border-amber-500 text-amber-500'
                  }`}
                >
                  <Clock className="h-2 w-2" />
                </span>

                <div className="flex flex-col">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-foreground">{incident.title}</span>
                    <span className="text-[9px] text-muted-foreground">{incident.time}</span>
                  </div>
                  <span className="text-[10px] text-muted-foreground mt-0.5">{incident.description}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-emerald-500 font-medium flex items-center justify-center gap-1.5">
            <CheckCircle2 className="h-4 w-4" /> All systems functioning within normal thresholds.
          </div>
        )}
      </CardContent>
    </Card>
  );
};
