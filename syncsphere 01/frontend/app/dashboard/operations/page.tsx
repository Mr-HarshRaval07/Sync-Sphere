'use client';

import React, { useEffect } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../../../components/ui/tabs';
import { Input } from '../../../components/ui/input';
import { Search, RefreshCw, Activity } from 'lucide-react';
import {
  useOperationsStore,
  useOperationsTelemetry,
  LiveDashboard,
  ExecutionMonitor,
  WorkflowTimeline,
  IncidentTimeline,
  QueueMonitor,
  WorkerMonitor,
  ConnectorHealth,
  AIAnalytics,
  RuntimeAnalytics,
  AlertsCenter,
  TraceExplorer,
  TimeRangeSelector,
  ExportControls,
} from '../../../features/operations';

export default function OperationsPage() {
  const {
    searchQuery,
    setSearchQuery,
    drillDownTab,
    setDrillDownTab,
    systemHealth,
  } = useOperationsStore();

  // Activate WebSocket live stream connection
  const { isConnected } = useOperationsTelemetry();

  // Sync tab state when drilldown changes
  const handleTabChange = (value: string) => {
    setDrillDownTab(value);
  };

  const activeTab = drillDownTab || 'overview';

  return (
    <div className="space-y-6">
      {/* 1. Header controls panel */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold tracking-tight">Enterprise Operations Center</h2>
            <div className="flex items-center gap-1">
              <span className={`h-2 w-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-muted-foreground'}`} />
              <span className="text-[10px] text-muted-foreground">{isConnected ? 'Live Stream Linked' : 'Offline'}</span>
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Real-time dashboard controls and SLA statistics across all orchestrator nodes.
          </p>
        </div>

        {/* Global time & export controls */}
        <div className="flex flex-wrap items-center gap-2">
          <TimeRangeSelector />
          <ExportControls />
        </div>
      </div>

      {/* 2. Global search bar panel */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search execution IDs, workflows, connectors, user prompts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-card border-border placeholder-muted-foreground focus-visible:ring-primary w-full"
            aria-label="Search operational metrics"
          />
        </div>
      </div>

      {/* 3. Main tabs view list */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-4">
        <TabsList className="bg-muted border border-border p-1 rounded-md flex flex-wrap h-auto gap-1">
          <TabsTrigger value="overview" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">Overview</TabsTrigger>
          <TabsTrigger value="executions" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">Executions</TabsTrigger>
          <TabsTrigger value="queues" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">Queues</TabsTrigger>
          <TabsTrigger value="workers" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">Workers</TabsTrigger>
          <TabsTrigger value="connectors" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">Connectors</TabsTrigger>
          <TabsTrigger value="ai" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">AI Performance</TabsTrigger>
          <TabsTrigger value="runtime" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">Runtime SLAs</TabsTrigger>
          <TabsTrigger value="alerts" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">Alerts Log</TabsTrigger>
        </TabsList>

        {/* Tab 1: Overview Dashboard */}
        <TabsContent value="overview" className="space-y-6">
          <LiveDashboard />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <WorkflowTimeline />
            <IncidentTimeline />
          </div>
        </TabsContent>

        {/* Tab 2: Live Execution Monitor */}
        <TabsContent value="executions" className="space-y-6">
          <ExecutionMonitor />
          <TraceExplorer />
        </TabsContent>

        {/* Tab 3: Queue Monitoring */}
        <TabsContent value="queues">
          <QueueMonitor />
        </TabsContent>

        {/* Tab 4: Worker Monitoring */}
        <TabsContent value="workers">
          <WorkerMonitor />
        </TabsContent>

        {/* Tab 5: Connector Health */}
        <TabsContent value="connectors">
          <ConnectorHealth />
        </TabsContent>

        {/* Tab 6: AI Performance Analytics */}
        <TabsContent value="ai">
          <AIAnalytics />
        </TabsContent>

        {/* Tab 7: Runtime SLAs */}
        <TabsContent value="runtime">
          <RuntimeAnalytics />
        </TabsContent>

        {/* Tab 8: Alerts Log & Feed */}
        <TabsContent value="alerts">
          <AlertsCenter />
        </TabsContent>
      </Tabs>
    </div>
  );
}
