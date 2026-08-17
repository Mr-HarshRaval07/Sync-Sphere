'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { aiApi } from '../../../shared/services/api';
import { DataGrid, SkeletonLoader } from '../../../shared/components/DesignSystem';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { BrainCircuit, CheckCircle2, AlertCircle, Coins, Cpu, Eye } from 'lucide-react';
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
    { key: 'context_window', header: 'Context size', render: (row: AIModel) => <span className="text-xs font-medium">{(row.context_window / 1000)}k tokens</span> },
    {
      key: 'pricing',
      header: 'Pricing (In / Out)',
      render: (row: AIModel) => (
        <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
          <Coins className="h-3.5 w-3.5 text-amber-500" />
          ${row.cost_per_1k_input.toFixed(4)} / ${row.cost_per_1k_output.toFixed(4)} <span className="text-[10px] font-normal text-muted-foreground">per 1k</span>
        </span>
      ),
    },
    {
      key: 'capabilities',
      header: 'Capabilities',
      render: (row: AIModel) => (
        <div className="flex gap-1 flex-wrap">
          {row.capabilities.map((c, idx) => (
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
          <Badge className={`text-xs font-semibold px-2 py-0.5 border ${
            isHealthy ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-rose-500/10 text-rose-500 border-rose-500/20"
          }`}>
            {isHealthy ? <CheckCircle2 className="h-3.5 w-3.5 mr-1 inline" /> : <AlertCircle className="h-3.5 w-3.5 mr-1 inline" />}
            {isHealthy ? 'Online' : 'Degraded'}
          </Badge>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight">AI Models & Gateways</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Review active large language model mappings, pricing parameters, and failover router priority levels.
        </p>
      </div>

      {isLoading ? (
        <SkeletonLoader rows={6} />
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Models Grid List */}
          <div className="lg:col-span-2 space-y-4">
            <Card className="border-border bg-card">
              <CardHeader>
                <CardTitle className="text-base font-bold flex items-center gap-1.5">
                  <BrainCircuit className="h-4 w-4 text-primary" /> Active Model Registry
                </CardTitle>
                <CardDescription className="text-xs">
                  Active models resolved dynamically by AI platform policies.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <DataGrid
                  columns={modelColumns}
                  data={models}
                  className="border-0 rounded-none border-t border-border/50"
                />
              </CardContent>
            </Card>
          </div>

          {/* Providers Health Check panel */}
          <div className="space-y-4">
            <Card className="border-border bg-card">
              <CardHeader>
                <CardTitle className="text-base font-bold flex items-center gap-1.5">
                  <Cpu className="h-4 w-4 text-primary" /> API Provider Endpoints
                </CardTitle>
                <CardDescription className="text-xs">
                  Gateway status and circuit breaker settings.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <DataGrid
                  columns={providerColumns}
                  data={providers}
                  className="border-0 rounded-none border-t border-border/50"
                />
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
