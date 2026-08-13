'use client';

import React from 'react';
import { useOperationsStore, TimeRange } from '../stores/operationsStore';
import { Button } from '../../../components/ui/button';
import { Calendar, Download, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

// ==========================================
// 1. Time Range Selector Component
// ==========================================
export const TimeRangeSelector: React.FC = () => {
  const { timeRange, setTimeRange, customTimeRange } = useOperationsStore();

  const options: { value: TimeRange; label: string }[] = [
    { value: '15m', label: 'Last 15 Minutes' },
    { value: '1h', label: 'Last 1 Hour' },
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
  ];

  return (
    <div className="flex items-center gap-2">
      <Calendar className="h-4 w-4 text-muted-foreground" />
      <select
        value={timeRange}
        onChange={(e) => setTimeRange(e.target.value as TimeRange)}
        className="h-8 px-2.5 rounded-md border border-border bg-card text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        aria-label="Select global time range"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  );
};

// ==========================================
// 2. Export Controls Component
// ==========================================
export const ExportControls: React.FC = () => {
  const store = useOperationsStore();

  const handleExport = (format: 'csv' | 'json' | 'pdf') => {
    // Generate data representation
    const exportData = {
      timestamp: new Date().toISOString(),
      activeWorkflows: store.activeWorkflowsCount,
      runningExecutions: store.runningExecutionsCount,
      queueBacklogs: store.queueLengths,
      workersOnline: Object.keys(store.connectedWorkers).length,
      successRate: store.runtimeAnalytics.successRate,
      slaTargets: store.slaTargets,
    };

    if (format === 'json') {
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(exportData, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', `syncsphere_operations_report_${Date.now()}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      toast.success('JSON Exported', { description: 'Operations telemetry summary downloaded.' });
    } else if (format === 'csv') {
      const headers = ['metric', 'value', 'timestamp'];
      const rows = [
        ['Active Workflows', store.activeWorkflowsCount],
        ['Running Executions', store.runningExecutionsCount],
        ['SLA Success Rate %', store.runtimeAnalytics.successRate],
      ];
      const csvContent = 'data:text/csv;charset=utf-8,' 
        + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
      
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', encodeURI(csvContent));
      downloadAnchor.setAttribute('download', `syncsphere_operations_report_${Date.now()}.csv`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      toast.success('CSV Exported', { description: 'Tabular statistics report downloaded.' });
    } else if (format === 'pdf') {
      // Mock triggering layout PDF print/download
      toast.info('PDF Generation Triggered', { description: 'Compiling graphical summary report.' });
      setTimeout(() => {
        if (typeof window !== 'undefined') {
          window.print();
        }
      }, 1000);
    }
  };

  return (
    <div className="flex items-center gap-1.5">
      <Button
        size="sm"
        variant="outline"
        className="flex items-center gap-1.5 h-8 border-border text-foreground hover:bg-muted"
        onClick={() => handleExport('csv')}
      >
        <Download className="h-3.5 w-3.5" /> CSV
      </Button>
      <Button
        size="sm"
        variant="outline"
        className="flex items-center gap-1.5 h-8 border-border text-foreground hover:bg-muted"
        onClick={() => handleExport('json')}
      >
        <Download className="h-3.5 w-3.5" /> JSON
      </Button>
      <Button
        size="sm"
        variant="outline"
        className="flex items-center gap-1.5 h-8 border-border text-foreground hover:bg-muted"
        onClick={() => handleExport('pdf')}
      >
        <Download className="h-3.5 w-3.5" /> PDF
      </Button>
    </div>
  );
};
