'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { observabilityApi } from '../../../shared/services/api';
import { useOperationsStore } from '../stores/operationsStore';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/table';
import { ShieldAlert, Bell, Check, Trash2, ShieldCheck, Zap } from 'lucide-react';
import { toast } from 'sonner';

export const AlertsCenter: React.FC = () => {
  const { alerts, setAlerts, acknowledgeAlert, resolveAlert, activityFeed } = useOperationsStore();

  // Query live active alerts
  const { data: serverAlerts = [], isLoading } = useQuery({
    queryKey: ['live-operations-alerts'],
    queryFn: async () => {
      const data = await observabilityApi.listAlerts();
      setAlerts(data);
      return data;
    },
    refetchInterval: 5000,
  });

  const displayAlerts = alerts.length > 0 ? alerts : serverAlerts;

  const handleAcknowledge = (id: string) => {
    acknowledgeAlert(id);
    toast.success('Alert Acknowledged', { description: 'Incident response owner assigned.' });
  };

  const handleResolve = (id: string) => {
    resolveAlert(id);
    toast.success('Alert Resolved', { description: 'Telemetry threshold return values checked.' });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* 1. Alerts Table Center (Left/Center Col) */}
      <div className="lg:col-span-2 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-foreground flex items-center gap-1.5">
              <ShieldAlert className="h-4 w-4 text-rose-500" /> Active System Alarms
            </h4>
            <p className="text-[10px] text-muted-foreground mt-0.5">Warnings, exceptions, and resource load alerts</p>
          </div>
        </div>

        <div className="rounded-md border border-border bg-card overflow-hidden">
          <Table>
            <TableHeader className="bg-muted/40">
              <TableRow>
                <TableHead className="font-semibold text-xs text-muted-foreground">Alert Name</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Severity</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Status</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Triggered Date</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading && displayAlerts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-xs text-muted-foreground">
                    Querying unresolved anomalies log...
                  </TableCell>
                </TableRow>
              ) : displayAlerts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-xs text-emerald-500 font-semibold">
                    <ShieldCheck className="h-6 w-6 text-emerald-500 mx-auto mb-2" />
                    All operational limits healthy.
                  </TableCell>
                </TableRow>
              ) : (
                displayAlerts.map((a: any) => {
                  const isCritical = a.severity === 'CRITICAL';
                  const isResolved = a.status === 'RESOLVED';
                  
                  return (
                    <TableRow key={a.id} className="hover:bg-muted/30 transition-colors">
                      <TableCell className="font-semibold text-xs text-foreground">
                        <div>
                          <span>{a.name}</span>
                          <div className="text-[9px] text-muted-foreground font-normal mt-0.5">{a.message}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={`text-[10px] scale-90 border font-semibold px-2 py-0.5 ${
                          isCritical
                            ? 'bg-rose-500/10 text-rose-500 border-rose-500/25 animate-pulse'
                            : 'bg-amber-500/10 text-amber-500 border-amber-500/25'
                        }`}>
                          {a.severity}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={`text-[10px] scale-90 border font-semibold px-2 py-0.5 capitalize ${
                          isResolved ? 'bg-muted text-muted-foreground border-border' : 'bg-rose-500/10 text-rose-500 border-rose-500/25'
                        }`}>
                          {a.status.toLowerCase()}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground font-mono">
                        {new Date(a.created_at).toLocaleTimeString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex gap-1 justify-end">
                          {!isResolved ? (
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 text-[10px] border-border text-foreground hover:bg-muted"
                              onClick={() => handleAcknowledge(a.id)}
                            >
                              <Check className="h-3 w-3 mr-1" /> Ack
                            </Button>
                          ) : null}
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 text-[10px] text-rose-500 hover:bg-rose-500/10"
                            onClick={() => handleResolve(a.id)}
                          >
                            <Trash2 className="h-3 w-3 mr-1" /> Resolve
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* 2. Live Activity Scrolling Feed (Right Col) */}
      <div className="space-y-4">
        <div>
          <h4 className="text-sm font-bold text-foreground flex items-center gap-1.5">
            <Bell className="h-4 w-4 text-primary" /> Live Activity Feed
          </h4>
          <p className="text-[10px] text-muted-foreground mt-0.5">Scrolling stream of execution milestones</p>
        </div>

        <Card className="border-border bg-card h-[400px] flex flex-col overflow-hidden">
          <CardContent className="p-3 overflow-y-auto flex-1 divide-y divide-border/30 scrollbar-thin">
            {activityFeed.length === 0 ? (
              <div className="py-8 text-center text-xs text-muted-foreground italic h-full flex items-center justify-center">
                Waiting for pipeline execution triggers...
              </div>
            ) : (
              activityFeed.map((event: any) => {
                const eventTime = new Date(event.timestamp).toLocaleTimeString();
                
                return (
                  <div key={event.id} className="py-2.5 flex items-start gap-2.5 text-xs">
                    <span className="mt-0.5 shrink-0">
                      {event.type.includes('fail') || event.type.includes('alert') ? (
                        <ShieldAlert className="h-3.5 w-3.5 text-rose-500" />
                      ) : (
                        <Zap className="h-3.5 w-3.5 text-emerald-500" />
                      )}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-foreground leading-normal">{event.message}</p>
                      <span className="text-[9px] text-muted-foreground mt-1 block font-mono">{eventTime}</span>
                    </div>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
