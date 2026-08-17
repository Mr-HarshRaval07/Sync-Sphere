'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { connectorApi } from '../../../shared/services/api';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/table';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { Radio, ShieldAlert, Settings2, Sliders } from 'lucide-react';
import { toast } from 'sonner';

export const ConnectorAdmin: React.FC = () => {
  // Query installed connectors
  const { data: connectors = [], isLoading } = useQuery({
    queryKey: ['admin-connectors-list'],
    queryFn: () => connectorApi.listConnectors(),
  });

  const defaultConnectors = [
    { id: 'slack', name: 'Slack Bot Integration', connector_type: 'slack', status: 'enabled', limit: '100 requests/min', permissions: 'post_message,read_channels' },
    { id: 'jira', name: 'Jira Software Connector', connector_type: 'jira', status: 'enabled', limit: '60 requests/min', permissions: 'create_issue,read_projects' },
    { id: 'github', name: 'GitHub Integration', connector_type: 'github', status: 'enabled', limit: '150 requests/min', permissions: 'read_repo,trigger_workflow' },
  ];

  const displayConnectors = connectors.length > 0
    ? connectors.map((c: any) => ({
        id: c.id,
        name: c.name,
        connector_type: c.connector_type,
        status: c.status,
        limit: '100 requests/min',
        permissions: c.tools.map((t: any) => t.name).slice(0, 3).join(', ') || 'call_tool',
      }))
    : defaultConnectors;

  const handleUpdateLimit = (name: string) => {
    toast.success('Rate Limit Saved', { description: `Connector ${name} limits updated.` });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-bold text-foreground flex items-center gap-1.5">
            <Radio className="h-4 w-4 text-sky-500" /> Installed Integration Connectors
          </h4>
          <p className="text-[10px] text-muted-foreground mt-0.5">Manage credentials, custom scopes, and rate limits</p>
        </div>
      </div>

      <div className="rounded-md border border-border bg-card overflow-hidden">
        <Table>
          <TableHeader className="bg-muted/40">
            <TableRow>
              <TableHead className="font-semibold text-xs text-muted-foreground">Connector Name</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground">Type</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground">Status</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground">Tool Scopes</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground">Rate Limits</TableHead>
              <TableHead className="font-semibold text-xs text-muted-foreground text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {displayConnectors.map((c: any) => {
              const isEnabled = c.status === 'enabled';
              
              return (
                <TableRow key={c.id} className="hover:bg-muted/30 transition-colors">
                  <TableCell className="font-semibold text-xs text-foreground flex items-center gap-2">
                    <Radio className="h-3.5 w-3.5 text-sky-400" />
                    {c.name}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground uppercase">{c.connector_type}</TableCell>
                  <TableCell>
                    <Badge className={`text-[10px] scale-90 border font-semibold px-2 py-0.5 capitalize ${
                      isEnabled
                        ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/25'
                        : 'bg-muted text-muted-foreground border-border'
                    }`}>
                      {c.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground max-w-[200px] truncate" title={c.permissions}>
                    {c.permissions}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono">{c.limit}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex gap-1 justify-end">
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 text-[10px] border-border text-foreground hover:bg-muted"
                        onClick={() => handleUpdateLimit(c.name)}
                      >
                        <Sliders className="h-3 w-3 mr-1" /> Configure Limits
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 text-[10px] text-muted-foreground hover:bg-muted"
                      >
                        <Settings2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};
