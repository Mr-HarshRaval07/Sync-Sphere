'use client';

import React from 'react';
import { useOperationsStore } from '../stores/operationsStore';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/table';
import { Badge } from '../../../components/ui/badge';
import { Radio, Heart, Activity, AlertTriangle, ShieldCheck } from 'lucide-react';

export const ConnectorHealth: React.FC = () => {
  const { connectorHealth } = useOperationsStore();

  const connectorList = Object.entries(connectorHealth);

  const defaultConnectors = [
    { id: 'slack', label: 'Slack Connector', type: 'slack', latency: 320, availability: 100, errorRate: 0, usage: 1420, retries: 2 },
    { id: 'jira', label: 'Jira Software', type: 'jira', latency: 840, availability: 99.8, errorRate: 0.2, usage: 844, retries: 8 },
    { id: 'github', label: 'GitHub Actions', type: 'github', latency: 460, availability: 100, errorRate: 0, usage: 1102, retries: 4 },
    { id: 'pagerduty', label: 'PagerDuty Gateway', type: 'pagerduty', latency: 280, availability: 100, errorRate: 0, usage: 242, retries: 0 },
    { id: 'email', label: 'SMTP Mailer', type: 'email', latency: 1250, availability: 98.6, errorRate: 1.4, usage: 584, retries: 14 },
  ];

  const displayList = connectorList.length > 0
    ? connectorList.map(([id, stats]) => ({
        id,
        label: id.charAt(0).toUpperCase() + id.slice(1),
        latency: stats.latency,
        availability: stats.availability,
        errorRate: stats.errorRate,
        usage: stats.usageCount,
        retries: stats.retries,
      }))
    : defaultConnectors;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-bold text-foreground flex items-center gap-1.5">
            <Radio className="h-4 w-4 text-sky-500" /> MCP Connector Framework Health
          </h4>
          <p className="text-[10px] text-muted-foreground mt-0.5">Integrations latency, error ratios, and usage rates</p>
        </div>
      </div>

      <div className="rounded-md border border-border bg-card overflow-hidden">
        <Table>
          <TableHeader className="bg-muted/40">
            <TableRow>
              <TableHead className="font-semibold text-xs text-muted-foreground">Connector Name</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground">Status</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground">Latency (Avg)</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground">Availability</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground">Error Rate</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground">Retries</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground text-right">Invokes Count</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {displayList.map((c) => {
              const isHealthy = c.availability >= 99 && c.errorRate < 2;
              
              return (
                <TableRow key={c.id} className="hover:bg-muted/30 transition-colors">
                  <TableCell className="font-semibold text-xs text-foreground flex items-center gap-2">
                    <Radio className="h-3.5 w-3.5 text-sky-400" />
                    {c.label}
                  </TableCell>
                  <TableCell>
                    <Badge className={`text-[10px] scale-90 border font-semibold px-2 py-0.5 ${
                      isHealthy
                        ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/25'
                        : 'bg-amber-500/10 text-amber-500 border-amber-500/25'
                    }`}>
                      {isHealthy ? 'Healthy' : 'Degraded'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono">{c.latency} ms</TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono">{c.availability}%</TableCell>
                  <TableCell className="text-xs font-mono">
                    <span className={c.errorRate > 0 ? 'text-rose-500 font-semibold' : 'text-muted-foreground'}>
                      {c.errorRate}%
                    </span>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono">{c.retries}</TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono text-right">{c.usage.toLocaleString()}</TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};
