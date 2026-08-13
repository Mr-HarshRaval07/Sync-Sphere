'use client';

import React from 'react';
import { useOperationsStore } from '../stores/operationsStore';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Layers, ArrowRight, CornerDownRight, AlertTriangle } from 'lucide-react';

export const QueueMonitor: React.FC = () => {
  const { queueLengths } = useOperationsStore();

  const queues = [
    { key: 'planner', label: 'Planner Queue', color: 'bg-violet-500/10 text-violet-500 border-violet-500/25', desc: 'Decomposes request instructions' },
    { key: 'execution', label: 'Execution Queue', color: 'bg-sky-500/10 text-sky-500 border-sky-500/25', desc: 'Active execution worker channels' },
    { key: 'embedding', label: 'Embedding Queue', color: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/25', desc: 'Vector indexing database tasks' },
    { key: 'approval', label: 'Approval Queue', color: 'bg-orange-500/10 text-orange-500 border-orange-500/25', desc: 'Awaiting human authorization decision' },
    { key: 'retry', label: 'Retry Queue', color: 'bg-amber-500/10 text-amber-500 border-amber-500/25', desc: 'Exponential backoff schedule retries' },
    { key: 'deadLetter', label: 'Dead Letter Queue', color: 'bg-rose-500/10 text-rose-500 border-rose-500/25', desc: 'Failed tasks requiring manual triage' },
  ];

  return (
    <div className="space-y-6">
      {/* 1. Queue Flow Diagram (Visual SVG Path representation) */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-xs font-bold flex items-center gap-1.5">
            <Layers className="h-4 w-4 text-primary" /> Active Queue Flow Path
          </CardTitle>
        </CardHeader>
        <CardContent className="py-6">
          <div className="flex flex-col md:flex-row items-center justify-around gap-4 md:gap-2">
            {/* Planner */}
            <div className="flex flex-col items-center">
              <div className="px-3 py-2 rounded-lg border border-violet-500/25 bg-violet-500/5 text-center min-w-[110px]">
                <div className="text-[10px] font-bold text-violet-500 uppercase">Planner</div>
                <div className="text-lg font-bold text-foreground mt-1">{queueLengths.planner}</div>
              </div>
              <span className="text-[8px] text-muted-foreground mt-1">Ingress decomposition</span>
            </div>

            <ArrowRight className="h-4 w-4 text-muted-foreground hidden md:block" />

            {/* Execution */}
            <div className="flex flex-col items-center">
              <div className="px-3 py-2 rounded-lg border border-sky-500/25 bg-sky-500/5 text-center min-w-[110px]">
                <div className="text-[10px] font-bold text-sky-500 uppercase">Execution</div>
                <div className="text-lg font-bold text-foreground mt-1">{queueLengths.execution}</div>
              </div>
              <span className="text-[8px] text-muted-foreground mt-1">DAG runner</span>
            </div>

            <div className="flex flex-col items-center justify-center md:h-12">
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] text-muted-foreground">Fail</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground hidden md:block" />
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] text-muted-foreground">Gate</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground hidden md:block" />
              </div>
            </div>

            {/* Approval */}
            <div className="flex flex-col items-center">
              <div className="px-3 py-2 rounded-lg border border-orange-500/25 bg-orange-500/5 text-center min-w-[110px]">
                <div className="text-[10px] font-bold text-orange-500 uppercase">Approval</div>
                <div className="text-lg font-bold text-foreground mt-1">{queueLengths.approval}</div>
              </div>
              <span className="text-[8px] text-muted-foreground mt-1">Human approvals</span>
            </div>

            <ArrowRight className="h-4 w-4 text-muted-foreground hidden md:block" />

            {/* Retry */}
            <div className="flex flex-col items-center">
              <div className="px-3 py-2 rounded-lg border border-amber-500/25 bg-amber-500/5 text-center min-w-[110px]">
                <div className="text-[10px] font-bold text-amber-500 uppercase">Retry</div>
                <div className="text-lg font-bold text-foreground mt-1">{queueLengths.retry}</div>
              </div>
              <span className="text-[8px] text-muted-foreground mt-1">Task retries schedule</span>
            </div>

            <ArrowRight className="h-4 w-4 text-muted-foreground hidden md:block" />

            {/* DLQ */}
            <div className="flex flex-col items-center">
              <div className={`px-3 py-2 rounded-lg border text-center min-w-[110px] ${
                queueLengths.deadLetter > 0
                  ? 'border-rose-500 bg-rose-500/10 text-rose-500 animate-pulse'
                  : 'border-rose-500/25 bg-rose-500/5'
              }`}>
                <div className="text-[10px] font-bold text-rose-500 uppercase">Dead Letter</div>
                <div className="text-lg font-bold text-foreground mt-1">{queueLengths.deadLetter}</div>
              </div>
              <span className="text-[8px] text-muted-foreground mt-1">Triage pool</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 2. Grid Table Lists of individual Queues */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {queues.map((q) => {
          const depth = (queueLengths as any)[q.key] || 0;
          
          return (
            <Card key={q.key} className="border-border bg-card hover:shadow-sm transition-all duration-200">
              <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-xs font-bold text-foreground">{q.label}</CardTitle>
                <Badge className={`text-[10px] scale-90 border font-semibold px-2 py-0.5 ${q.color}`}>
                  {depth} items
                </Badge>
              </CardHeader>
              <CardContent>
                <p className="text-[10px] text-muted-foreground leading-relaxed">{q.desc}</p>
                
                {/* Backlog Alert banner inside cards */}
                {depth > 5 && (
                  <div className="mt-3 flex items-center gap-1.5 text-[9px] text-amber-500 font-medium">
                    <AlertTriangle className="h-3 w-3 shrink-0" />
                    <span>Backlog threshold breached. Scale workers.</span>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
