'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { aiApi } from '../../../shared/services/api';
import { DataGrid, SkeletonLoader } from '../../../shared/components/DesignSystem';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { BrainCircuit, CheckCircle2, AlertCircle, Coins, Cpu } from 'lucide-react';
import { AIModel, ModelProvider } from '../../../shared/types';

export default function AIModelsPage() {
  // Query active models
  const { data: models = [], isLoading: modelsLoading } = useQuery({
    queryKey: ['ai-models-list'],
    queryFn: () => aiApi.listModels(),
  });

  // Query active providers
  const { data: providers = [], isLoading: providersLoading } = useQuery({
    queryKey: ['ai-providers-list'],
    queryFn: () => aiApi.listProviders(),
  });

  const isLoading = modelsLoading || providersLoading;

  const modelColumns = [
    { key: 'display_name', header: 'Model Name', render: (row: AIModel) => <span className="font-semibold text-foreground">{row.display_name}</span> },
    { key: 'name', header: 'API Name', render: (row: AIModel) => <code className="text-xs bg-muted p-1 rounded font-mono">{row.name}</code> },
    { key: 'context_window', header: 'Context size', render: (row: AIModel) => <span className="text-xs font-medium">{(row.context_window ? row.context_window / 1000 : 0)}k tokens</span> },
    {
      key: 'pricing',
      header: 'Pricing (In / Out)',
      render: (row: AIModel) => (
        <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
          <Coins className="h-3.5 w-3.5 text-amber-500" />
          ${(row.cost_per_1k_input || 0).toFixed(4)} / ${(row.cost_per_1k_output || 0).toFixed(4)} <span className="text-[10px] font-normal text-muted-foreground">per 1k</span>
        </span>
      ),
    },
    {
      key: 'capabilities',
      header: 'Capabilities',
      render: (row: AIModel) => (
        <div className="flex gap-1 flex-wrap">
          {(row.capabilities || []).map((c, idx) => (
            <Badge key={idx} variant="outline" className="text-[10px] capitalize border-border">
              {c.replace('_', ' ')}
            </Badge>
          ))}
        </div>
      ),
    },
  ];

  const providerColumns = [
    { key: 'name', header: 'Provider Name', render: (row: ModelProvider) => <span className="font-semibold capitalize text-foreground">{row.name}</span> },
    { key: 'priority_level', header: 'Failover priority', render: (row: ModelProvider) => <Badge variant="outline" className="border-border">Priority {row.priority_level}</Badge> },
    {
      key: 'is_healthy',
      header: 'Gateway Health',
      render: (row: ModelProvider) => {
        const isHealthy = row.is_healthy;
        return (
          <Badge className={`text-xs font-semibold px-2 py-0.5 border ${isHealthy ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-rose-500/10 text-rose-500 border-rose-500/20"
            }`}>
            {isHealthy ? <CheckCircle2 className="h-3.5 w-3.5 mr-1 inline" /> : <AlertCircle className="h-3.5 w-3.5 mr-1 inline" />}
            {isHealthy ? 'Online' : 'Degraded'}
          </Badge>
        );
      },
    },
  ];

  // We should try to extract the primary configure model if available to populate the main Production Card
  const activeProvider = providers.find((p: any) => p.priority_level === 1) || providers[0] || { name: 'OpenRouter' };
  const mainModel = models.length > 0 ? models[0] : { display_name: 'Ling Tiny 3.0', name: 'inclusionai/ling-3.0-tiny:free' };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold tracking-tight">AI Models & Gateways</h2>
        <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
          View the AI providers and models powering SyncSphere's planning and orchestration.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Model Details Card */}
        <Card className="border-border bg-card shadow-sm h-full">
          <CardHeader className="pb-4 border-b border-border/50">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-bold flex items-center gap-2">
                <BrainCircuit className="h-5 w-5 text-primary" />
                Production AI Model
              </CardTitle>
              <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 hover:bg-emerald-500/20 flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" /> Active
              </Badge>
            </div>
            <CardDescription className="text-xs">
              The primary large language model responsible for dynamic workflow generation.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="space-y-5">
              <div className="grid grid-cols-3 gap-4 pb-4 border-b border-border/40">
                <div className="col-span-1 text-sm font-medium text-muted-foreground">Provider</div>
                <div className="col-span-2 text-sm font-bold text-foreground capitalize">{activeProvider.name}</div>
              </div>
              <div className="grid grid-cols-3 gap-4 pb-4 border-b border-border/40">
                <div className="col-span-1 text-sm font-medium text-muted-foreground">Model</div>
                <div className="col-span-2 text-sm font-bold text-foreground">{mainModel.display_name && mainModel.display_name !== 'Ling-3.0-flash' ? mainModel.display_name : 'Ling Tiny 3.0'}</div>
              </div>
              <div className="grid grid-cols-3 gap-4 pb-4 border-b border-border/40">
                <div className="col-span-1 text-sm font-medium text-muted-foreground">Identifier</div>
                <div className="col-span-2 text-sm font-mono text-muted-foreground bg-muted p-1 px-2 rounded w-fit">{mainModel.name}</div>
              </div>
              <div className="grid grid-cols-3 gap-4 pb-4 border-b border-border/40">
                <div className="col-span-1 text-sm font-medium text-muted-foreground">Purpose</div>
                <div className="col-span-2 text-sm text-foreground">AI workflow planning and task decomposition</div>
              </div>
              <div className="grid grid-cols-3 gap-4 pb-4 border-b border-border/40">
                <div className="col-span-1 text-sm font-medium text-muted-foreground">Used by</div>
                <div className="col-span-2 text-sm font-semibold text-foreground bg-primary/10 text-primary px-2 py-0.5 rounded w-fit">Plan with AI</div>
              </div>
              <div className="grid grid-cols-3 gap-4 pt-1">
                <div className="col-span-1 text-sm font-medium text-muted-foreground">Fallback</div>
                <div className="col-span-2 text-sm text-foreground font-semibold">OpenRouter (Free)</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Architecture Card */}
        <Card className="border-border bg-card shadow-sm h-full">
          <CardHeader className="pb-4 border-b border-border/50">
            <CardTitle className="text-lg font-bold flex items-center gap-2">
              <Cpu className="h-5 w-5 text-indigo-500" />
              Runtime Architecture
            </CardTitle>
            <CardDescription className="text-xs">
              Zero-friction telemetry illustrating how LLMs orchestrate execution via the API Gateway.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-8 px-8">
            {/* Real-Time Flow Visualization styled organically */}
            <div className="flex flex-col items-center justify-center space-y-2">

              <div className="bg-slate-900 border border-slate-700 text-slate-200 px-6 py-2 rounded-lg text-sm font-bold shadow-lg z-10 uppercase tracking-widest min-w-[220px] text-center">
                User
              </div>

              <div className="h-6 w-px bg-gradient-to-b from-slate-700 to-primary flex justify-center relative">
                {/* Glowing Pulse */}
                <div className="absolute w-2 h-2 rounded-full bg-primary animate-ping" style={{ top: 0 }} />
                <div className="absolute -bottom-1 text-primary text-[10px]">▼</div>
              </div>

              <div className="bg-primary/20 border border-primary/50 text-primary px-6 py-2 rounded-lg text-sm font-bold shadow-[0_0_15px_rgba(var(--primary-rgb),0.2)] z-10 uppercase tracking-widest min-w-[220px] text-center">
                Plan With AI
              </div>

              <div className="h-6 w-px border-l-2 border-dashed border-border flex justify-center relative">
                <div className="absolute -bottom-1 text-border text-[10px]">▼</div>
              </div>

              <div className="bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 px-6 py-2 rounded-lg text-sm font-bold z-10 uppercase tracking-widest min-w-[220px] text-center flex flex-col">
                <span className="capitalize">{activeProvider.name}</span>
                <span className="text-[10px] text-indigo-500/70 opacity-80 mt-1">{mainModel.display_name || mainModel.name}</span>
              </div>

              <div className="h-6 w-px border-l-2 border-dashed border-border flex justify-center relative">
                <div className="absolute w-2 h-2 rounded-full bg-indigo-500 animate-ping opacity-50" style={{ top: '20%' }} />
                <div className="absolute -bottom-1 text-border text-[10px]">▼</div>
              </div>

              <div className="bg-amber-500/10 border border-amber-500/30 text-amber-500 px-6 py-2 rounded-lg text-sm font-bold z-10 uppercase tracking-widest min-w-[220px] text-center">
                Workflow Plan
              </div>

              <div className="h-6 w-px border-l-2 border-dashed border-border flex justify-center relative">
                <div className="absolute -bottom-1 text-border text-[10px]">▼</div>
              </div>

              <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-500 px-6 py-2 rounded-lg text-sm font-bold z-10 uppercase tracking-widest min-w-[220px] text-center flex flex-col">
                <span>Connectors</span>
                <span className="text-[10px] text-emerald-500/70 lowercase opacity-80 mt-1">gmail, github, slack...</span>
              </div>

              <div className="h-6 w-px bg-gradient-to-b from-border to-emerald-500 flex justify-center relative">
                <div className="absolute -bottom-1 text-emerald-500 text-[10px]">▼</div>
              </div>

              <div className="bg-emerald-600 text-white px-6 py-2 rounded-lg text-sm font-black shadow-[0_0_20px_rgba(16,185,129,0.4)] z-10 uppercase tracking-widest min-w-[220px] text-center">
                Execution
              </div>

            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8 space-y-8">
        <div>
          <h3 className="text-lg font-bold tracking-tight mb-4">Fallback Matrix & Gateway States</h3>
          {isLoading ? (
            <SkeletonLoader rows={3} />
          ) : providers.length === 0 ? (
            <div className="bg-card border border-border rounded-lg p-6 flex flex-col items-center justify-center text-center gap-2">
              <Cpu className="h-8 w-8 text-muted-foreground mb-2" />
              <h4 className="font-bold text-foreground">No Providers Configured</h4>
              <p className="text-xs text-muted-foreground max-w-sm">There are no external AI model providers configured or reachable. AI orchestration may failover to internal routing or stop.</p>
            </div>
          ) : (
            <DataGrid
              columns={providerColumns}
              data={providers}
              className="border-border bg-card"
            />
          )}
        </div>

        <div>
          <h3 className="text-lg font-bold tracking-tight mb-4">Configured Models</h3>
          {isLoading ? (
            <SkeletonLoader rows={3} />
          ) : models.length === 0 ? (
            <div className="bg-card border border-border rounded-lg p-6 flex flex-col items-center justify-center text-center gap-2">
              <Cpu className="h-8 w-8 text-muted-foreground mb-2" />
              <h4 className="font-bold text-foreground">No Models Configured</h4>
            </div>
          ) : (
            <DataGrid
              columns={modelColumns}
              data={models}
              className="border-border bg-card"
            />
          )}
        </div>
      </div>

    </div>
  );
}
