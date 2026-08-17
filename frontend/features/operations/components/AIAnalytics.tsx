'use client';

import React, { useState, useMemo } from 'react';
import { useOperationsStore } from '../stores/operationsStore';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/table';
import { Badge } from '../../../components/ui/badge';
import { Brain, Coins, Cpu, Zap, Activity } from 'lucide-react';

export const AIAnalytics: React.FC = () => {
  const { aiAnalytics, aiCostBreakdown } = useOperationsStore();
  const [breakdownType, setBreakdownType] = useState<'org' | 'workflow' | 'prompt' | 'model' | 'user'>('model');

  // Default models data
  const defaultModels = {
    'gpt-4o': { latency: 1850, tokens: 1250000, cost: 6.25, cacheHitRate: 35, requests: 1420 },
    'gpt-4o-mini': { latency: 840, tokens: 4200000, cost: 0.63, cacheHitRate: 48, requests: 2840 },
    'claude-3-5-sonnet': { latency: 2200, tokens: 840000, cost: 12.60, cacheHitRate: 24, requests: 642 },
    'claude-3-opus': { latency: 4500, tokens: 120000, cost: 9.00, cacheHitRate: 15, requests: 94 },
    'gemini-1.5-pro': { latency: 1650, tokens: 2100000, cost: 2.10, cacheHitRate: 40, requests: 1102 },
  };

  const displayModels = Object.keys(aiAnalytics).length > 0 ? aiAnalytics : defaultModels;

  // Default breakdown data
  const defaultBreakdown = [
    { id: 'org-1', name: 'Acme Corp (Default)', type: 'org', tokens: 4500000, cost: 18.42, requests: 2800 },
    { id: 'org-2', name: 'Stark Industries', type: 'org', tokens: 3200000, cost: 11.25, requests: 1980 },
    
    { id: 'wf-1', name: 'Slack Bug Triage Pipeline', type: 'workflow', tokens: 1800000, cost: 9.54, requests: 1200 },
    { id: 'wf-2', name: 'Daily Report Summarizer', type: 'workflow', tokens: 1400000, cost: 3.22, requests: 840 },
    
    { id: 'p-1', name: 'classify_bug_severity', type: 'prompt', tokens: 850000, cost: 4.12, requests: 600 },
    { id: 'p-2', name: 'generate_summary_email', type: 'prompt', tokens: 620000, cost: 1.84, requests: 480 },
    
    { id: 'gpt-4o', name: 'GPT-4o (OpenAI)', type: 'model', tokens: 1250000, cost: 6.25, requests: 1420 },
    { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet (Anthropic)', type: 'model', tokens: 840000, cost: 12.60, requests: 642 },
    
    { id: 'u-1', name: 'John Doe (Admin)', type: 'user', tokens: 2200000, cost: 10.45, requests: 1400 },
    { id: 'u-2', name: 'Jane Smith (Operator)', type: 'user', tokens: 1400000, cost: 4.82, requests: 920 },
  ];

  const displayBreakdown = aiCostBreakdown.length > 0 ? aiCostBreakdown : defaultBreakdown;

  const filteredBreakdown = useMemo(() => {
    return displayBreakdown.filter((item) => item.type === breakdownType);
  }, [displayBreakdown, breakdownType]);

  return (
    <div className="space-y-6">
      {/* 1. Model Analytics Summary */}
      <div className="space-y-4">
        <div>
          <h4 className="text-sm font-bold text-foreground flex items-center gap-1.5">
            <Brain className="h-4 w-4 text-rose-500" /> Model Performance Analytics
          </h4>
          <p className="text-[10px] text-muted-foreground mt-0.5">Average latencies, token consumption, and cache hit rates</p>
        </div>

        <div className="rounded-md border border-border bg-card overflow-hidden">
          <Table>
            <TableHeader className="bg-muted/40">
              <TableRow>
                <TableHead className="font-semibold text-xs text-muted-foreground">Model Provider ID</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Prompt Latency</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Tokens Spent</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Cache Hit Rate</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Calls Count</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground text-right">Est. Cost</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(displayModels).map(([id, stats]) => (
                <TableRow key={id} className="hover:bg-muted/30 transition-colors">
                  <TableCell className="font-semibold text-xs text-foreground flex items-center gap-2">
                    <Cpu className="h-3.5 w-3.5 text-rose-400" />
                    {id}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono">{stats.latency} ms</TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono">{stats.tokens.toLocaleString()}</TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono">{stats.cacheHitRate}%</TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono">{stats.requests}</TableCell>
                  <TableCell className="text-xs text-foreground font-bold font-mono text-right">${stats.cost.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* 2. AI Cost Breakdown Matrix */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h4 className="text-sm font-bold text-foreground flex items-center gap-1.5">
              <Coins className="h-4 w-4 text-amber-500" /> AI Cost Breakdown Matrix
            </h4>
            <p className="text-[10px] text-muted-foreground mt-0.5">Audit cost allocation by categories</p>
          </div>

          {/* Breakdown category selector */}
          <div className="flex bg-muted border border-border rounded p-0.5 w-fit">
            {(['model', 'workflow', 'prompt', 'org', 'user'] as const).map((type) => (
              <button
                key={type}
                onClick={() => setBreakdownType(type)}
                className={`px-2.5 py-1 text-[10px] font-bold rounded capitalize transition-all
                  ${breakdownType === type ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}
                `}
              >
                By {type}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-md border border-border bg-card overflow-hidden">
          <Table>
            <TableHeader className="bg-muted/40">
              <TableRow>
                <TableHead className="font-semibold text-xs text-muted-foreground">Entity Name / ID</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Tokens Spent</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Requests Count</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground text-right">Aggregated Cost</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredBreakdown.map((item) => (
                <TableRow key={item.id} className="hover:bg-muted/30 transition-colors">
                  <TableCell className="font-semibold text-xs text-foreground">{item.name}</TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono">{item.tokens.toLocaleString()}</TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono">{item.requests}</TableCell>
                  <TableCell className="text-xs text-foreground font-bold font-mono text-right">${item.cost.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
};
