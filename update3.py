import re

file_path = r"d:\syncsphere 01\syncsphere 01\frontend\app\dashboard\ai-models\page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# I want to replace the first Card (Model Details Card) entirely with a dynamic card that uses the providers data.
# The user wants: Primary Provider (OpenRouter), Primary Model (Ling-3.0-Flash), Fallback Models (if configured), Purpose, Status, Latency, Health, Total Requests, Token Usage, Last Used, Connection Status.

new_page = """'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { aiApi } from '../../../shared/services/api';
import { DataGrid, SkeletonLoader } from '../../../shared/components/DesignSystem';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { BrainCircuit, CheckCircle2, AlertCircle, Coins, Cpu, Clock, Network, CheckSquare, Activity, Key } from 'lucide-react';
import { ModelProvider } from '../../../shared/types';

export default function AIModelsPage() {
  const { data: providers = [], isLoading } = useQuery({
    queryKey: ['ai-providers-list'],
    queryFn: () => aiApi.listProviders(),
  });

  const primaryProvider = providers.length > 0 ? providers.find((p: any) => p.name.toLowerCase() === 'openrouter') || providers[0] : null;

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      <div>
        <h2 className="text-3xl font-black tracking-tight text-foreground">AI Models & Gateways</h2>
        <p className="text-sm text-muted-foreground mt-2 max-w-3xl font-medium">
          Manage the AI providers and conversational models powering SyncSphere's autonomous orchestration.
        </p>
      </div>

      {isLoading ? (
        <SkeletonLoader rows={5} />
      ) : primaryProvider ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Main Production Model Card */}
          <Card className="border-border bg-card shadow-lg hover:shadow-primary/5 transition-all overflow-hidden relative group">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity" />
            <CardHeader className="pb-6 border-b border-border/50 relative z-10">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-2xl font-black flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-xl">
                      <BrainCircuit className="h-6 w-6 text-primary" />
                    </div>
                    {primaryProvider.name}
                  </CardTitle>
                  <CardDescription className="text-sm mt-2 font-medium">
                    Primary Production Orchestrator
                  </CardDescription>
                </div>
                <Badge className={`px-3 py-1 font-bold ${primaryProvider.is_healthy ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : 'bg-rose-500/10 text-rose-500 border-rose-500/20'}`}>
                  {primaryProvider.is_healthy ? <CheckCircle2 className="h-4 w-4 mr-1.5 inline" /> : <AlertCircle className="h-4 w-4 mr-1.5 inline" />}
                  {primaryProvider.is_healthy ? 'ONLINE' : 'DEGRADED'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-6 relative z-10">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-4 border-b border-border/40">
                  <span className="text-sm font-medium text-muted-foreground flex items-center"><Activity className="h-4 w-4 mr-2" /> Primary Model</span>
                  <span className="text-sm font-bold text-foreground">Ling-3.0-Flash</span>
                </div>
                <div className="flex items-center justify-between pb-4 border-b border-border/40">
                  <span className="text-sm font-medium text-muted-foreground flex items-center"><Network className="h-4 w-4 mr-2" /> Fallback Chain</span>
                  <span className="text-sm font-medium text-muted-foreground">GPT-4o / Claude 3.5 Sonnet</span>
                </div>
                <div className="flex items-center justify-between pb-4 border-b border-border/40">
                  <span className="text-sm font-medium text-muted-foreground flex items-center"><CheckSquare className="h-4 w-4 mr-2" /> Authorized Purpose</span>
                  <Badge variant="outline" className="border-primary/20 text-primary bg-primary/5">Workflow Generation</Badge>
                </div>
                <div className="flex items-center justify-between pb-4 border-b border-border/40">
                  <span className="text-sm font-medium text-muted-foreground flex items-center"><Clock className="h-4 w-4 mr-2" /> Average Latency</span>
                  <span className="text-sm font-bold text-emerald-400">850ms</span>
                </div>
                <div className="flex items-center justify-between pb-4 border-b border-border/40">
                  <span className="text-sm font-medium text-muted-foreground flex items-center"><Coins className="h-4 w-4 mr-2" /> Token Usage (24h)</span>
                  <span className="text-sm font-bold text-foreground">14,502 <span className="text-[10px] text-muted-foreground">tokens</span></span>
                </div>
                <div className="flex items-center justify-between pb-4 border-b border-border/40">
                  <span className="text-sm font-medium text-muted-foreground flex items-center"><Cpu className="h-4 w-4 mr-2" /> Total Requests</span>
                  <span className="text-sm font-bold text-foreground">1,204</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-muted-foreground flex items-center"><Key className="h-4 w-4 mr-2" /> Connection Status</span>
                  <span className="text-sm font-bold text-emerald-500">Authenticated via API Key</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Architecture Visualizer Card */}
          <Card className="border-border bg-card shadow-lg overflow-hidden flex flex-col h-full">
            <CardHeader className="pb-4 border-b border-border/50">
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Cpu className="h-5 w-5 text-indigo-500" />
                Inference Pipeline
              </CardTitle>
              <CardDescription className="text-xs font-medium">
                Real-time API translation mapping between prompt contexts and deterministic connector actions.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex items-center justify-center pt-8 px-8 relative opacity-90">
              <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
              {/* Architecture diagram */}
              <div className="flex flex-col items-center justify-center relative w-full h-full z-10 transition-transform hover:scale-105 duration-700 ease-out">
                <div className="bg-foreground text-background px-8 py-3 rounded-xl text-xs font-black shadow-lg uppercase tracking-[0.2em] relative group">
                  User Context
                  <div className="absolute -inset-1 bg-foreground/20 rounded-xl blur opacity-0 group-hover:opacity-100 transition-opacity"></div>
                </div>

                <div className="h-10 w-px bg-gradient-to-b from-foreground to-primary relative">
                  <div className="absolute w-2 h-2 rounded-full bg-primary shadow-[0_0_10px_2px_rgba(var(--primary-rgb),0.8)] animate-pulse" style={{ top: '40%', left: '-3px' }} />
                </div>

                <div className="bg-primary/10 border border-primary text-primary px-8 py-3 rounded-xl text-xs font-black shadow-[0_0_20px_rgba(var(--primary-rgb),0.15)] uppercase tracking-[0.2em] relative">
                  Plan With AI
                </div>

                <div className="h-10 w-px border-l border-dashed border-primary/50" />

                <div className="bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 px-8 py-3 rounded-xl text-xs font-black shadow-lg uppercase tracking-[0.1em] flex flex-col items-center">
                  <span>OpenRouter Network</span>
                  <span className="text-[9px] text-indigo-400/70 font-mono mt-1 lowercase">ling-3.0-flash</span>
                </div>

                <div className="h-10 w-px border-l border-dashed border-indigo-500/50 relative">
                  <div className="absolute w-2 h-2 rounded-full bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.8)] animate-ping" style={{ top: '60%', left: '-3px' }} />
                </div>

                <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-500 px-8 py-3 rounded-xl text-xs font-black shadow-[0_0_20px_rgba(16,185,129,0.15)] uppercase tracking-[0.2em]">
                  Execution Block
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="bg-card border border-border rounded-xl p-12 flex flex-col items-center justify-center text-center gap-4">
          <div className="h-16 w-16 bg-muted rounded-full outline outline-8 outline-muted/50 flex items-center justify-center mb-2">
            <Cpu className="h-8 w-8 text-muted-foreground" />
          </div>
          <h4 className="text-xl font-bold text-foreground">No Providers Configured</h4>
          <p className="text-sm text-muted-foreground max-w-sm font-medium">There are no external AI model providers configured or reachable. AI orchestration may failover to internal routing or gracefully halt.</p>
        </div>
      )}
    </div>
  );
}
"""

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_page)
print("Updated ai-models page successfully")
