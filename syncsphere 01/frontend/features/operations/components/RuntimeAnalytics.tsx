'use client';

import React from 'react';
import { useOperationsStore } from '../stores/operationsStore';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../../../components/ui/card';
import { Progress } from '../../../components/ui/progress';
import { Badge } from '../../../components/ui/badge';
import { Activity, Clock, ShieldCheck, ShieldAlert, AlertTriangle, RefreshCw } from 'lucide-react';

export const RuntimeAnalytics: React.FC = () => {
  const { runtimeAnalytics, slaTargets } = useOperationsStore();

  const metrics = [
    { label: 'Saga Rollbacks', value: runtimeAnalytics.sagaRollbacks, desc: 'Transaction compensation triggers', type: 'error' },
    { label: 'Execution Timeouts', value: runtimeAnalytics.timeouts, desc: 'SLA threshold timeout breaches', type: 'warning' },
    { label: 'Task Retries', value: 8, desc: 'Automatic execution retries called', type: 'info' },
  ];

  return (
    <div className="space-y-6">
      {/* 1. SLA Performance Matrix */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-xs font-bold flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-emerald-500" /> SLA Target Performance Monitor
          </CardTitle>
          <CardDescription className="text-[10px]">Real-time operational SLA breaches and statistics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(slaTargets).map(([key, item]) => (
              <div key={key} className="rounded-lg border border-border p-3 space-y-2 bg-background relative overflow-hidden">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-muted-foreground font-semibold uppercase">{item.metricName}</span>
                  <Badge className={`text-[9px] scale-90 border font-semibold px-1.5 py-0.5 ${
                    item.isBreached
                      ? 'bg-rose-500/10 text-rose-500 border-rose-500/25 animate-pulse'
                      : 'bg-emerald-500/10 text-emerald-500 border-emerald-500/25'
                  }`}>
                    {item.isBreached ? 'Breached' : 'Within target'}
                  </Badge>
                </div>
                <div className="flex items-baseline gap-1.5 mt-1">
                  <span className="text-2xl font-extrabold text-foreground">{item.actual}</span>
                  <span className="text-[10px] text-muted-foreground">{item.unit}</span>
                </div>
                <div className="flex justify-between text-[9px] text-muted-foreground pt-1 border-t border-border/50">
                  <span>SLA Goal:</span>
                  <span>{key === 'latency' || key === 'errorRate' ? '<' : '>'} {item.target}{item.unit}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 2. Runtime Statistics Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Statistics progress card */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-xs font-bold flex items-center gap-1.5">
              <Activity className="h-4 w-4 text-primary" /> Core Engine Success Ratios
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span>Pipeline Success Rate</span>
                <span className="font-semibold text-emerald-500">{runtimeAnalytics.successRate}%</span>
              </div>
              <Progress value={runtimeAnalytics.successRate} className="h-1 bg-muted" />
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span>Target SLA Met Ratio</span>
                <span className="font-semibold text-primary">98.2%</span>
              </div>
              <Progress value={98.2} className="h-1 bg-muted" />
            </div>
          </CardContent>
        </Card>

        {/* Dynamic anomalies list card */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-xs font-bold flex items-center gap-1.5">
              <AlertTriangle className="h-4 w-4 text-amber-500" /> Runtime Anomalies Log
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border/50">
              {metrics.map((m) => (
                <div key={m.label} className="flex justify-between items-center p-3 text-xs">
                  <div>
                    <div className="font-semibold text-foreground">{m.label}</div>
                    <div className="text-[9px] text-muted-foreground mt-0.5">{m.desc}</div>
                  </div>
                  <Badge className={`text-[10px] scale-90 border font-semibold px-2 py-0.5 ${
                    m.type === 'error' && m.value > 0
                      ? 'bg-rose-500/10 text-rose-500 border-rose-500/25'
                      : m.type === 'warning' && m.value > 0
                      ? 'bg-amber-500/10 text-amber-500 border-amber-500/25'
                      : 'bg-muted text-muted-foreground'
                  }`}>
                    {m.value} counts
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
