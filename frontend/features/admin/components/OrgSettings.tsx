'use client';

import React, { useState } from 'react';
import { useAdminStore } from '../stores/adminStore';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Switch } from '../../../components/ui/switch';
import { Progress } from '../../../components/ui/progress';
import { Badge } from '../../../components/ui/badge';
import { Settings, Image, Sliders, Globe, AlertCircle, ArrowUpRight, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';

export const OrgSettings: React.FC = () => {
  const { orgFeatureFlags, toggleFeatureFlag, quotaForecast } = useAdminStore();
  const [displayName, setDisplayName] = useState('Acme Corp Operations');
  const [primaryColor, setPrimaryColor] = useState('#2563eb');
  const [selectedRegion, setSelectedRegion] = useState('us-east-1');

  const handleSaveBranding = (e: React.FormEvent) => {
    e.preventDefault();
    toast.success('Branding Settings Updated', { description: 'Portal customizations saved.' });
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 1. Custom Branding Settings */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-bold flex items-center gap-1.5">
              <Image className="h-4 w-4 text-primary" /> Portal Visual Branding
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSaveBranding} className="space-y-3">
              <div className="space-y-1">
                <label className="text-[10px] text-muted-foreground font-medium block">Display Name</label>
                <Input
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="h-8 text-xs bg-card border-border"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] text-muted-foreground font-medium block">Brand Hex Accent Color</label>
                <div className="flex gap-2">
                  <Input
                    type="color"
                    value={primaryColor}
                    onChange={(e) => setPrimaryColor(e.target.value)}
                    className="h-8 w-12 p-0 bg-transparent border-0 cursor-pointer"
                  />
                  <Input
                    value={primaryColor}
                    onChange={(e) => setPrimaryColor(e.target.value)}
                    className="h-8 text-xs bg-card border-border flex-1"
                  />
                </div>
              </div>
              <Button type="submit" size="sm" className="w-full bg-primary hover:bg-primary/90 text-primary-foreground">
                Save Customize Branding
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* 2. Feature Flags Console */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-bold flex items-center gap-1.5">
              <Sliders className="h-4 w-4 text-primary" /> Feature Flags Console
            </CardTitle>
            <CardDescription className="text-[10px]">Toggle administrative flag controls for organization runtime environments</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3.5">
            {Object.entries(orgFeatureFlags).map(([flag, enabled]) => (
              <div key={flag} className="flex items-center justify-between text-xs">
                <div>
                  <div className="font-semibold text-foreground capitalize">{flag.replace(/([A-Z])/g, ' $1')}</div>
                  <div className="text-[9px] text-muted-foreground mt-0.5">Toggle runtime enablement behavior</div>
                </div>
                <button
                  onClick={() => {
                    toggleFeatureFlag(flag);
                    toast.success('Feature Flag Mutated', { description: `Feature ${flag} is now ${!enabled ? 'enabled' : 'disabled'}.` });
                  }}
                  className={`w-9 h-5 rounded-full p-0.5 transition-colors focus:outline-none
                    ${enabled ? 'bg-primary' : 'bg-muted'}
                  `}
                  aria-label={`Toggle feature flag ${flag}`}
                >
                  <div className={`w-4 h-4 rounded-full bg-card shadow transition-transform
                    ${enabled ? 'translate-x-4' : 'translate-x-0'}
                  `} />
                </button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 3. Global Region Selector */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-bold flex items-center gap-1.5">
              <Globe className="h-4 w-4 text-primary" /> Organization Host Regions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-[10px] text-muted-foreground font-medium block">Default Regional Anchor</label>
                <select
                  value={selectedRegion}
                  onChange={(e) => {
                    setSelectedRegion(e.target.value);
                    toast.success('Primary Region Selected', { description: `Active cluster nodes default to ${e.target.value}.` });
                  }}
                  className="h-8 w-full px-2.5 rounded-md border border-border bg-card text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  aria-label="Select default hosting region"
                >
                  <option value="us-east-1">US East (N. Virginia)</option>
                  <option value="us-west-2">US West (Oregon)</option>
                  <option value="eu-central-1">Europe (Frankfurt)</option>
                  <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
                </select>
              </div>
              <div className="text-[9px] text-muted-foreground flex items-center gap-1.5 leading-relaxed">
                <AlertCircle className="h-3.5 w-3.5 text-primary shrink-0" />
                <span>Modifying default anchors scales down existing nodes in active locations.</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 4. Quota Forecasting */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-bold flex items-center gap-1.5">
              <TrendingUp className="h-4 w-4 text-emerald-500" /> Quota Forecasting (Next 30 Days)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">API Requests Quota</span>
                <span className="font-semibold text-foreground">
                  {quotaForecast.currentUsage} / {quotaForecast.limit} calls
                </span>
              </div>
              <div className="relative">
                <Progress value={(quotaForecast.currentUsage / quotaForecast.limit) * 100} className="h-1.5 bg-muted" />
                {/* Projected marker dot */}
                <div
                  className="absolute top-0 w-2 h-2 rounded-full bg-amber-500 shadow border border-background animate-pulse"
                  style={{ left: `${(quotaForecast.projectedUsage / quotaForecast.limit) * 100}%` }}
                  title={`Projected usage: ${quotaForecast.projectedUsage}`}
                />
              </div>
            </div>

            <div className="border-t border-border/50 pt-3.5 flex justify-between items-center text-xs">
              <div>
                <div className="text-muted-foreground text-[10px] uppercase">Growth Trend</div>
                <div className="font-bold text-foreground mt-0.5">+{quotaForecast.growthPercentage}% / mo</div>
              </div>
              <div className="text-right">
                <div className="text-muted-foreground text-[10px] uppercase">Forecasted Breach Risk</div>
                <Badge className="text-[10px] scale-90 border font-semibold px-2 py-0.5 bg-amber-500/10 text-amber-500 border-amber-500/25">
                  High Risk (day 28)
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
