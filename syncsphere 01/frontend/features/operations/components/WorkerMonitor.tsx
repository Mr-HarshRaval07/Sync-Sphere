'use client';

import React from 'react';
import { useOperationsStore } from '../stores/operationsStore';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Progress } from '../../../components/ui/progress';
import { Cpu, HardDrive, ShieldCheck, ShieldAlert, Heart, Calendar } from 'lucide-react';

export const WorkerMonitor: React.FC = () => {
  const { connectedWorkers } = useOperationsStore();

  const workerList = Object.entries(connectedWorkers);

  const getHeatmapColor = (cpu: number) => {
    if (cpu < 30) return 'bg-emerald-500/20 text-emerald-500 border-emerald-500/30';
    if (cpu < 70) return 'bg-amber-500/20 text-amber-500 border-amber-500/30';
    return 'bg-rose-500/20 text-rose-500 border-rose-500/30 animate-pulse';
  };

  return (
    <div className="space-y-6">
      {/* 1. Worker Load Heatmap Grid */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-bold flex items-center gap-1.5">
            <Cpu className="h-4 w-4 text-primary" /> Cluster Load Heatmap
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-2">
            {workerList.length === 0 ? (
              <div className="col-span-full py-4 text-center text-xs text-muted-foreground italic">
                No telemetry heartbeat received from cluster workers.
              </div>
            ) : (
              workerList.map(([id, stats]) => (
                <div
                  key={id}
                  className={`p-2 rounded border text-center transition-all ${getHeatmapColor(stats.cpu)}`}
                  title={`Worker ${id}: CPU ${stats.cpu}%`}
                >
                  <div className="text-[9px] font-bold truncate">{id}</div>
                  <div className="text-sm font-extrabold mt-1">{stats.cpu}%</div>
                  <div className="text-[8px] text-muted-foreground mt-0.5">{stats.activeJobs} jobs</div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* 2. Worker Detailed Status Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {workerList.length === 0 ? (
          <Card className="border-border bg-card col-span-full p-8 text-center text-xs text-muted-foreground italic">
            Waiting for cluster nodes metrics initialization...
          </Card>
        ) : (
          workerList.map(([id, stats]) => {
            const lastHeartbeat = new Date(stats.heartbeat).toLocaleTimeString();
            
            return (
              <Card key={id} className="border-border bg-card hover:shadow-sm transition-all duration-200">
                <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
                  <div className="flex items-center gap-2">
                    <HardDrive className="h-4 w-4 text-primary" />
                    <CardTitle className="text-xs font-bold text-foreground truncate max-w-[120px]">
                      {id}
                    </CardTitle>
                  </div>
                  <Badge className={`text-[10px] scale-90 border font-semibold px-2 py-0.5 ${
                    stats.healthy
                      ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/25'
                      : 'bg-rose-500/10 text-rose-500 border-rose-500/25'
                  }`}>
                    {stats.healthy ? 'Healthy' : 'Offline'}
                  </Badge>
                </CardHeader>
                <CardContent className="space-y-3.5">
                  {/* Metric Progress Levels */}
                  <div className="space-y-2">
                    <div className="space-y-1">
                      <div className="flex justify-between text-[10px] text-muted-foreground">
                        <span className="flex items-center gap-1"><Cpu className="h-3 w-3" /> CPU Load</span>
                        <span>{stats.cpu}%</span>
                      </div>
                      <Progress value={stats.cpu} className="h-1 bg-muted" />
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between text-[10px] text-muted-foreground">
                        <span className="flex items-center gap-1"><HardDrive className="h-3 w-3" /> RAM Utilization</span>
                        <span>{stats.memory}%</span>
                      </div>
                      <Progress value={stats.memory} className="h-1 bg-muted" />
                    </div>
                  </div>

                  {/* Worker status lines */}
                  <div className="border-t border-border/50 pt-3 flex flex-wrap gap-x-4 gap-y-2 text-[10px] text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <ShieldCheck className="h-3 w-3 text-sky-500" />
                      Active Jobs: <strong className="text-foreground">{stats.activeJobs}</strong>
                    </span>
                    <span className="flex items-center gap-1">
                      <ShieldAlert className="h-3 w-3 text-rose-500" />
                      Failed Tasks: <strong className="text-foreground">{stats.failures}</strong>
                    </span>
                    <span className="flex items-center gap-1">
                      <Heart className="h-3 w-3 text-rose-400" />
                      Heartbeat: <strong className="text-foreground">{lastHeartbeat}</strong>
                    </span>
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
};
