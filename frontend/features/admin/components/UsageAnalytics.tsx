'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/table';
import { Badge } from '../../../components/ui/badge';
import { Activity, Brain, Radio, Coins, Database } from 'lucide-react';

export const UsageAnalytics: React.FC = () => {
  const usageStats = [
    { label: 'AI Inference Tasks', value: '45,824 requests', change: '+12.4%', icon: <Brain className="h-4 w-4 text-rose-500" /> },
    { label: 'Runtime Execution Seconds', value: '1.2M seconds', change: '+8.1%', icon: <Activity className="h-4 w-4 text-emerald-500" /> },
    { label: 'Knowledge Base Embeddings', value: '840 MB indexed', change: '+4.5%', icon: <Database className="h-4 w-4 text-sky-500" /> },
    { label: 'MCP Connector Invocations', value: '98,400 invokes', change: '+14.2%', icon: <Radio className="h-4 w-4 text-violet-500" /> },
  ];

  return (
    <div className="space-y-6">
      {/* 1. Usage Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {usageStats.map((stat) => (
          <Card key={stat.label} className="border-border bg-card hover:shadow-sm transition-all duration-200">
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <span className="text-[10px] text-muted-foreground font-semibold uppercase">{stat.label}</span>
              {stat.icon}
            </CardHeader>
            <CardContent>
              <div className="text-xl font-bold text-foreground">{stat.value}</div>
              <div className="text-[10px] text-emerald-500 font-medium mt-1">
                {stat.change} vs last month
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 2. Monthly Resource Cost Allocations */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-xs font-bold flex items-center gap-1.5">
            <Coins className="h-4 w-4 text-amber-500" /> Resource Cost Allocation (Current Billing Cycle)
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto scrollbar-thin">
          <Table>
            <TableHeader className="bg-muted/40">
              <TableRow>
                <TableHead className="font-semibold text-xs text-muted-foreground">Resource Class</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Consumption</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Avg Unit Price</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground text-right">Aggregated Cost</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow className="hover:bg-muted/30 transition-colors">
                <TableCell className="font-semibold text-xs text-foreground">AI Inference (GPT-4o/Claude)</TableCell>
                <TableCell className="text-xs text-muted-foreground font-mono">24.5M Tokens</TableCell>
                <TableCell className="text-xs text-muted-foreground font-mono">$0.008 / 1k</TableCell>
                <TableCell className="text-xs text-foreground font-bold font-mono text-right">$196.00</TableCell>
              </TableRow>
              <TableRow className="hover:bg-muted/30 transition-colors">
                <TableCell className="font-semibold text-xs text-foreground">Runtime Container Nodes</TableCell>
                <TableCell className="text-xs text-muted-foreground font-mono">320 hours active</TableCell>
                <TableCell className="text-xs text-muted-foreground font-mono">$0.08 / hr</TableCell>
                <TableCell className="text-xs text-foreground font-bold font-mono text-right">$25.60</TableCell>
              </TableRow>
              <TableRow className="hover:bg-muted/30 transition-colors">
                <TableCell className="font-semibold text-xs text-foreground">Knowledge Platform Vector DB</TableCell>
                <TableCell className="text-xs text-muted-foreground font-mono">1.2M dimensions</TableCell>
                <TableCell className="text-xs text-muted-foreground font-mono">$0.01 / 100k</TableCell>
                <TableCell className="text-xs text-foreground font-bold font-mono text-right">$0.12</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};
