'use client';

import React from 'react';
import { useAdminStore } from '../stores/adminStore';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { Progress } from '../../../components/ui/progress';
import { CheckCircle2, ShieldCheck, CreditCard, ChevronRight, Check } from 'lucide-react';
import { toast } from 'sonner';

export const BillingPlaceholder: React.FC = () => {
  const { complianceItems } = useAdminStore();

  const billingPlans = [
    { name: 'Developer', price: '$0', desc: 'Ideal for prototyping workflows and MCP testing.', features: ['5 Active Workflows', '1 organization context', '1,000 AI tokens quota', 'Basic audit logs'], current: false },
    { name: 'Professional', price: '$89', desc: 'Scale pipeline automation with active workers.', features: ['50 Active Workflows', '3 organization context instances', '10,000 AI tokens/month', 'SLA monitoring dashboards', '90-day audit trails'], current: true },
    { name: 'Enterprise', price: 'Custom', desc: 'Production-ready portal with RBAC custom policies.', features: ['Unlimited Workflows', 'Unlimited organizations switch', 'Saga transactional rollback logic', 'SOC2 / ISO compliance controls', 'Advanced trace explorer debugger'], current: false },
  ];

  const handleUpgrade = (planName: string) => {
    toast.success('Subscription Requested', { description: `Quotas upgrade to ${planName} tier initiated.` });
  };

  return (
    <div className="space-y-6">
      {/* 1. Compliance Dashboard Placeholders (SOC2 / ISO27001 / HIPAA Checklist) */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-xs font-bold flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-emerald-500" /> Enterprise Compliance Controls Dashboard
          </CardTitle>
          <CardDescription className="text-[10px]">Verify framework alignment for SOC2, ISO27001, and HIPAA compliance policies</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {complianceItems.map((item) => (
            <div key={item.id} className="flex items-start justify-between text-xs pb-3.5 border-b border-border/50 last:border-0 last:pb-0">
              <div>
                <div className="flex items-center gap-2">
                  <Badge className="text-[9px] border font-bold px-1.5 py-0 bg-muted text-muted-foreground uppercase">
                    {item.framework}
                  </Badge>
                  <span className="font-semibold text-foreground">{item.controlName}</span>
                </div>
                <div className="text-[10px] text-muted-foreground mt-0.5">{item.description}</div>
              </div>
              <Badge className={`text-[10px] scale-90 border font-semibold px-2 py-0.5 capitalize ${
                item.status === 'compliant'
                  ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/25'
                  : 'bg-amber-500/10 text-amber-500 border-amber-500/25 animate-pulse'
              }`}>
                {item.status}
              </Badge>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* 2. Billing & Subscription Tiers Plan selection cards */}
      <div className="space-y-4">
        <div>
          <h4 className="text-sm font-bold text-foreground flex items-center gap-1.5">
            <CreditCard className="h-4 w-4 text-primary" /> Active Plans & Quotas Limits
          </h4>
          <p className="text-[10px] text-muted-foreground mt-0.5">Upgrade capabilities or scale execution concurrency limits</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {billingPlans.map((plan) => (
            <Card key={plan.name} className={`border-border bg-card flex flex-col group relative overflow-hidden
              ${plan.current ? 'ring-2 ring-primary border-primary/20 shadow-md' : 'hover:shadow-sm'}
            `}>
              {plan.current && (
                <div className="absolute right-0 top-0 bg-primary text-primary-foreground text-[8px] font-extrabold uppercase px-2.5 py-1 rounded-bl">
                  Active
                </div>
              )}
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-extrabold text-foreground">{plan.name}</CardTitle>
                <div className="flex items-baseline gap-1 mt-1.5">
                  <span className="text-3xl font-extrabold text-foreground">{plan.price}</span>
                  {plan.price !== 'Custom' && <span className="text-xs text-muted-foreground">/ month</span>}
                </div>
                <CardDescription className="text-[10px] leading-relaxed mt-2">{plan.desc}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 flex-1 pb-4 border-t border-border/50 pt-4">
                {plan.features.map((f) => (
                  <div key={f} className="flex items-start gap-2 text-[10px] text-muted-foreground">
                    <Check className="h-3.5 w-3.5 text-emerald-500 shrink-0 mt-0.5" />
                    <span>{f}</span>
                  </div>
                ))}
              </CardContent>
              <CardFooter className="pt-2 pb-4">
                <Button
                  size="sm"
                  variant={plan.current ? 'outline' : 'default'}
                  className="w-full text-xs"
                  onClick={() => handleUpgrade(plan.name)}
                >
                  {plan.current ? 'Manage Billing' : 'Upgrade Plan'}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};
