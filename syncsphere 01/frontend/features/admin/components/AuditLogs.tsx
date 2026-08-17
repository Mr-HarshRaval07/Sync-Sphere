'use client';

import React, { useMemo } from 'react';
import { useAdminStore } from '../stores/adminStore';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/table';
import { Badge } from '../../../components/ui/badge';
import { Input } from '../../../components/ui/input';
import { Button } from '../../../components/ui/button';
import { ShieldCheck, Search, Download, Clock, Globe } from 'lucide-react';
import { toast } from 'sonner';

export const AuditLogs: React.FC = () => {
  const { auditLogs, setAuditLogs, auditSearchQuery, setAuditSearchQuery } = useAdminStore();

  const defaultLogs = [
    { id: 'l-1', actor: 'admin@acme.ai', action: 'ROLE_PRIVILEGES_MUTATE', resource: 'role:developer', timestamp: new Date(Date.now() - 1000 * 60 * 4).toISOString(), ipAddress: '192.168.1.14' },
    { id: 'l-2', actor: 'admin@acme.ai', action: 'API_KEY_ROTATE', resource: 'key:slack_alert_gw', timestamp: new Date(Date.now() - 1000 * 60 * 18).toISOString(), ipAddress: '192.168.1.14' },
    { id: 'l-3', actor: 'system-gateway', action: 'SECRET_ROTATED', resource: 'secret:OpenAI API Token', timestamp: new Date(Date.now() - 1000 * 60 * 42).toISOString(), ipAddress: '127.0.0.1' },
    { id: 'l-4', actor: 'admin@acme.ai', action: 'USER_ACCOUNT_SUSPEND', resource: 'user:u-3', timestamp: new Date(Date.now() - 1000 * 3600 * 3).toISOString(), ipAddress: '192.168.1.14' },
    { id: 'l-5', actor: 'developer@acme.ai', action: 'WORKFLOW_VERSION_PUBLISH', resource: 'workflow:slack_bug_triage', timestamp: new Date(Date.now() - 1000 * 3600 * 14).toISOString(), ipAddress: '10.0.0.12' },
  ];

  const displayLogs = auditLogs.length > 0 ? auditLogs : defaultLogs;

  const filteredLogs = useMemo(() => {
    if (!auditSearchQuery) return displayLogs;
    const q = auditSearchQuery.toLowerCase();
    return displayLogs.filter((l) =>
      l.actor.toLowerCase().includes(q) ||
      l.action.toLowerCase().includes(q) ||
      l.resource.toLowerCase().includes(q)
    );
  }, [displayLogs, auditSearchQuery]);

  const handleExport = (format: 'csv' | 'json') => {
    if (format === 'json') {
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(filteredLogs, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', `syncsphere_audit_log_${Date.now()}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    } else {
      const headers = ['id', 'actor', 'action', 'resource', 'timestamp', 'ipAddress'];
      const rows = filteredLogs.map((l) => [l.id, l.actor, l.action, l.resource, l.timestamp, l.ipAddress]);
      const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', encodeURI(csvContent));
      downloadAnchor.setAttribute('download', `syncsphere_audit_log_${Date.now()}.csv`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    }
    toast.success('Audit Log Exported', { description: `Downloaded ${format.toUpperCase()} archive.` });
  };

  return (
    <div className="space-y-6">
      {/* 1. Visual Audit Event Timeline */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-bold flex items-center gap-1.5">
            <Clock className="h-4 w-4 text-primary" /> Core Security Audit Timeline
          </CardTitle>
          <CardDescription className="text-[10px]">Real-time visual sequence of administrative actions</CardDescription>
        </CardHeader>
        <CardContent className="py-4">
          <div className="relative pl-6 border-l border-border space-y-4 max-h-[160px] overflow-y-auto scrollbar-thin">
            {filteredLogs.slice(0, 4).map((log) => (
              <div key={log.id} className="relative">
                <span className="absolute -left-[30px] top-0.5 flex h-4 w-4 items-center justify-center rounded-full border-2 border-primary bg-background text-primary">
                  <ShieldCheck className="h-2.5 w-2.5 fill-current" />
                </span>
                <div className="text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-foreground">{log.action.replace(/_/g, ' ')}</span>
                    <span className="text-[9px] text-muted-foreground">{new Date(log.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <div className="text-[10px] text-muted-foreground mt-0.5">
                    Actor: <strong className="text-foreground">{log.actor}</strong> • Resource: <strong className="text-foreground">{log.resource}</strong>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 2. Audit Table & Searching */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <CardTitle className="text-xs font-bold">Comprehensive Security Trails</CardTitle>
            <CardDescription className="text-[10px]">Search administrative operations</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative w-48 sm:w-64">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                placeholder="Search audit trail..."
                value={auditSearchQuery}
                onChange={(e) => setAuditSearchQuery(e.target.value)}
                className="h-8 pl-8 text-xs bg-card border-border placeholder:text-muted-foreground focus-visible:ring-primary w-full"
                aria-label="Search security audit logs"
              />
            </div>
            <Button size="sm" variant="outline" className="h-8 border-border text-foreground hover:bg-muted" onClick={() => handleExport('csv')} aria-label="Export audit logs to CSV">
              <Download className="h-3.5 w-3.5 mr-1" /> Export
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto scrollbar-thin">
          <Table>
            <TableHeader className="bg-muted/40">
              <TableRow>
                <TableHead className="font-semibold text-xs text-muted-foreground">Actor</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Action</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Resource</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">IP Address</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground text-right">Timestamp</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLogs.map((l) => (
                <TableRow key={l.id} className="hover:bg-muted/30 transition-colors">
                  <TableCell className="font-semibold text-xs text-foreground">{l.actor}</TableCell>
                  <TableCell>
                    <Badge className="text-[10px] scale-90 border font-semibold px-2 py-0.5 bg-muted text-muted-foreground border-border">
                      {l.action}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono">{l.resource}</TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono">
                    <div className="flex items-center gap-1">
                      <Globe className="h-3 w-3" />
                      <span>{l.ipAddress}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono text-right">
                    {new Date(l.timestamp).toLocaleString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};
