'use client';

import React, { useState } from 'react';
import { useOperationsStore } from '../stores/operationsStore';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { Progress } from '../../../components/ui/progress';
import {
  GitFork, Play, ShieldAlert, Users, Brain, Radio,
  Activity, AlertOctagon, Heart, ChevronUp, ChevronDown, Settings,
  RotateCcw, Sliders, CheckCircle2,
} from 'lucide-react';

export const LiveDashboard: React.FC = () => {
  const {
    activeWorkflowsCount,
    runningExecutionsCount,
    failedExecutionsCount,
    queueLengths,
    connectedWorkers,
    systemHealth,
    dashboardLayout,
    setDashboardLayout,
    resetDashboardLayout,
    setDrillDownTab,
    slaTargets,
  } = useOperationsStore();

  const [isCustomizing, setIsCustomizing] = useState(false);

  // Total workers calculations
  const workerList = Object.values(connectedWorkers);
  const activeWorkersCount = workerList.filter((w) => w.healthy).length;
  const totalCpuUsage = workerList.length > 0 ? workerList.reduce((acc, w) => acc + w.cpu, 0) / workerList.length : 0;
  const totalMemoryUsage = workerList.length > 0 ? workerList.reduce((acc, w) => acc + w.memory, 0) / workerList.length : 0;

  // Move layout item helper
  const moveItem = (index: number, direction: 'up' | 'down') => {
    const nextIndex = direction === 'up' ? index - 1 : index + 1;
    if (nextIndex < 0 || nextIndex >= dashboardLayout.length) return;
    
    const newLayout = [...dashboardLayout];
    const temp = newLayout[index];
    newLayout[index] = newLayout[nextIndex];
    newLayout[nextIndex] = temp;
    setDashboardLayout(newLayout);
  };

  // Widget specs dictionary
  const WIDGETS: Record<string, { title: string; content: React.ReactNode; icon: React.ReactNode; drillTab: string }> = {
    'active-workflows': {
      title: 'Active Workflows',
      drillTab: 'executions',
      icon: <GitFork className="h-4 w-4 text-sky-500" />,
      content: (
        <div className="flex flex-col">
          <span className="text-3xl font-bold">{activeWorkflowsCount}</span>
          <span className="text-[10px] text-muted-foreground mt-1">Configured pipeline schemas</span>
        </div>
      ),
    },
    'running-executions': {
      title: 'Running Executions',
      drillTab: 'executions',
      icon: <Play className="h-4 w-4 text-emerald-500 animate-pulse" />,
      content: (
        <div className="flex flex-col">
          <span className="text-3xl font-bold">{runningExecutionsCount}</span>
          <span className="text-[10px] text-muted-foreground mt-1">Active worker instances</span>
        </div>
      ),
    },
    'queue-length': {
      title: 'Execution Queue Length',
      drillTab: 'queues',
      icon: <Activity className="h-4 w-4 text-amber-500" />,
      content: (
        <div className="flex flex-col">
          <span className="text-3xl font-bold">
            {Object.values(queueLengths).reduce((acc, val) => acc + val, 0)}
          </span>
          <span className="text-[10px] text-muted-foreground mt-1">Backlog across 6 core channels</span>
        </div>
      ),
    },
    'workers': {
      title: 'Cluster Workers',
      drillTab: 'workers',
      icon: <Users className="h-4 w-4 text-violet-500" />,
      content: (
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Workers Online</span>
            <span className="font-semibold text-foreground">{activeWorkersCount} / {workerList.length}</span>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-[10px] text-muted-foreground">
              <span>Avg CPU Load</span>
              <span>{totalCpuUsage.toFixed(0)}%</span>
            </div>
            <Progress value={totalCpuUsage} className="h-1 bg-muted" />
          </div>
        </div>
      ),
    },
    'active-users': {
      title: 'Active Users',
      drillTab: 'executions',
      icon: <Users className="h-4 w-4 text-indigo-500" />,
      content: (
        <div className="flex flex-col">
          <span className="text-3xl font-bold">14</span>
          <span className="text-[10px] text-muted-foreground mt-1">Simultaneous portal sessions</span>
        </div>
      ),
    },
    'ai-requests': {
      title: 'AI Models Requests',
      drillTab: 'ai',
      icon: <Brain className="h-4 w-4 text-rose-500" />,
      content: (
        <div className="flex flex-col">
          <span className="text-3xl font-bold">1,824</span>
          <span className="text-[10px] text-muted-foreground mt-1">LLM prompts called today</span>
        </div>
      ),
    },
    'connector-calls': {
      title: 'Connector Invokes',
      drillTab: 'connectors',
      icon: <Radio className="h-4 w-4 text-cyan-500" />,
      content: (
        <div className="flex flex-col">
          <span className="text-3xl font-bold">4,192</span>
          <span className="text-[10px] text-muted-foreground mt-1">MCP tooling handshakes</span>
        </div>
      ),
    },
    'approvals': {
      title: 'Approval Backlog',
      drillTab: 'executions',
      icon: <CheckCircle2 className="h-4 w-4 text-orange-500" />,
      content: (
        <div className="flex flex-col">
          <span className="text-3xl font-bold">{queueLengths.approval}</span>
          <span className="text-[10px] text-muted-foreground mt-1">Pending manual gates</span>
        </div>
      ),
    },
    'failures': {
      title: 'Failed Executions',
      drillTab: 'runtime',
      icon: <AlertOctagon className="h-4 w-4 text-rose-500 animate-bounce" />,
      content: (
        <div className="flex flex-col">
          <span className="text-3xl font-bold text-rose-500">{failedExecutionsCount}</span>
          <span className="text-[10px] text-muted-foreground mt-1">Execution faults today</span>
        </div>
      ),
    },
    'health': {
      title: 'System Health',
      drillTab: 'alerts',
      icon: <Heart className={`h-4 w-4 ${systemHealth === 'HEALTHY' ? 'text-emerald-500' : systemHealth === 'DEGRADED' ? 'text-amber-500 animate-pulse' : 'text-rose-500 animate-ping'}`} />,
      content: (
        <div className="flex flex-col">
          <Badge className={`text-xs w-fit py-0.5 border ${
            systemHealth === 'HEALTHY'
              ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/25'
              : systemHealth === 'DEGRADED'
              ? 'bg-amber-500/10 text-amber-500 border-amber-500/25'
              : 'bg-rose-500/10 text-rose-500 border-rose-500/25 font-bold'
          }`}>
            {systemHealth}
          </Badge>
          <span className="text-[10px] text-muted-foreground mt-2">All gateway runtimes operational</span>
        </div>
      ),
    },
  };

  return (
    <div className="space-y-6">
      {/* SLA Breach Banner */}
      {Object.values(slaTargets).some((target) => target.isBreached) && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-rose-500/10 border border-rose-500/25 text-rose-500 animate-pulse">
          <ShieldAlert className="h-5 w-5 shrink-0" />
          <div className="flex-1 text-xs">
            <span className="font-bold">Active SLA Breach Alert:</span> Operational threshold requirements breached. Audit details below.
          </div>
          <Button size="sm" variant="ghost" className="h-7 text-rose-500 hover:bg-rose-500/20" onClick={() => setDrillDownTab('runtime')}>
            View Details
          </Button>
        </div>
      )}

      {/* Control Panel / Layout Selector */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
          <Activity className="h-4 w-4 text-primary" /> Live Operational Dashboard
        </h3>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            className="flex items-center gap-1.5 h-8 border-border text-foreground hover:bg-muted"
            onClick={() => setIsCustomizing(!isCustomizing)}
          >
            <Sliders className="h-3.5 w-3.5" />
            {isCustomizing ? 'Done Customizing' : 'Customize Layout'}
          </Button>
          {isCustomizing && (
            <Button
              size="sm"
              variant="ghost"
              className="flex items-center gap-1.5 h-8 text-muted-foreground hover:text-foreground"
              onClick={resetDashboardLayout}
            >
              <RotateCcw className="h-3.5 w-3.5" /> Reset
            </Button>
          )}
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {dashboardLayout.map((widgetId, index) => {
          const spec = WIDGETS[widgetId];
          if (!spec) return null;

          return (
            <Card
              key={widgetId}
              className={`border-border bg-card shadow-sm hover:shadow-md transition-all relative overflow-hidden group
                ${isCustomizing ? 'ring-2 ring-primary/45 border-primary/20 scale-95' : ''}
              `}
            >
              {/* Customizer controls overlay */}
              {isCustomizing && (
                <div className="absolute right-2 top-2 z-10 flex gap-0.5 bg-background/90 backdrop-blur rounded border border-border p-0.5">
                  <button
                    onClick={() => moveItem(index, 'up')}
                    disabled={index === 0}
                    className="p-1 hover:bg-muted text-muted-foreground disabled:opacity-20 rounded"
                    aria-label="Move widget left"
                  >
                    <ChevronUp className="h-3 w-3 -rotate-90" />
                  </button>
                  <button
                    onClick={() => moveItem(index, 'down')}
                    disabled={index === dashboardLayout.length - 1}
                    className="p-1 hover:bg-muted text-muted-foreground disabled:opacity-20 rounded"
                    aria-label="Move widget right"
                  >
                    <ChevronDown className="h-3 w-3 -rotate-90" />
                  </button>
                </div>
              )}

              <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
                <CardTitle className="text-xs font-semibold text-muted-foreground">{spec.title}</CardTitle>
                {!isCustomizing && spec.icon}
              </CardHeader>
              <CardContent className="pb-3">
                {spec.content}
                
                {/* Drill-down action */}
                {!isCustomizing && (
                  <button
                    onClick={() => setDrillDownTab(spec.drillTab)}
                    className="text-[10px] text-primary font-medium mt-3 block hover:underline opacity-0 group-hover:opacity-100 transition-opacity"
                    aria-label={`Drill down into ${spec.title}`}
                  >
                    Drill Down →
                  </button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
