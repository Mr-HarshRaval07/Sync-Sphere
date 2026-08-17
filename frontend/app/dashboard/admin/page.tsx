'use client';

import React from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../../../components/ui/tabs';
import { Input } from '../../../components/ui/input';
import { Shield, Settings } from 'lucide-react';
import {
  useAdminStore,
  OrgManagement,
  RbacMatrix,
  UserManagement,
  ApiKeyManager,
  SecretsManager,
  ConnectorAdmin,
  OrgSettings,
  AuditLogs,
  BillingPlaceholder,
  UsageAnalytics,
} from '../../../features/admin';

export default function AdminPage() {
  const { activeAdminTab, setActiveAdminTab, isImpersonating, impersonatedUser, stopImpersonation } = useAdminStore();

  const handleTabChange = (value: string) => {
    setActiveAdminTab(value);
  };

  return (
    <div className="space-y-6">
      {/* Impersonation Indicator Overlay */}
      {isImpersonating && impersonatedUser && (
        <div className="flex items-center justify-between px-4 py-3 rounded-lg bg-amber-500/10 border border-amber-500/25 text-amber-500 animate-pulse">
          <span className="text-xs font-semibold">
            Simulating admin audits for <strong>{impersonatedUser.first_name} {impersonatedUser.last_name}</strong> (Read-Only)
          </span>
          <Button size="sm" variant="ghost" className="h-7 text-amber-500 hover:bg-amber-500/20" onClick={stopImpersonation}>
            Exit Impersonate Mode
          </Button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" /> Enterprise Administration Portal
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Manage organization members, switch directories context, customize feature flags, and rotate secrets.
          </p>
        </div>
      </div>

      {/* Main Tabs Sheet Layout */}
      <Tabs value={activeAdminTab} onValueChange={handleTabChange} className="space-y-4">
        <TabsList className="bg-muted border border-border p-1 rounded-md flex flex-wrap h-auto gap-1">
          <TabsTrigger value="org" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">Organization</TabsTrigger>
          <TabsTrigger value="users" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">Users & Sessions</TabsTrigger>
          <TabsTrigger value="rbac" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">RBAC Matrix</TabsTrigger>
          <TabsTrigger value="api-keys" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">API Keys</TabsTrigger>
          <TabsTrigger value="secrets" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">Secrets Vault</TabsTrigger>
          <TabsTrigger value="connectors" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">Connectors Admin</TabsTrigger>
          <TabsTrigger value="analytics" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">Usage Analytics</TabsTrigger>
          <TabsTrigger value="audit" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">Audit Trails</TabsTrigger>
          <TabsTrigger value="settings" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">Settings & Flags</TabsTrigger>
          <TabsTrigger value="billing" className="text-xs px-3 py-1.5 data-[state=active]:bg-card">Billing & Compliance</TabsTrigger>
        </TabsList>

        {/* Tab 1: Organization switcher */}
        <TabsContent value="org">
          <OrgManagement />
        </TabsContent>

        {/* Tab 2: User management dashboard */}
        <TabsContent value="users">
          <UserManagement />
        </TabsContent>

        {/* Tab 3: RBAC permission inspector matrix */}
        <TabsContent value="rbac">
          <RbacMatrix />
        </TabsContent>

        {/* Tab 4: External API Key generator */}
        <TabsContent value="api-keys">
          <ApiKeyManager />
        </TabsContent>

        {/* Tab 5: Secret rotation dashboard */}
        <TabsContent value="secrets">
          <SecretsManager />
        </TabsContent>

        {/* Tab 6: Connector scopes config */}
        <TabsContent value="connectors">
          <ConnectorAdmin />
        </TabsContent>

        {/* Tab 7: AI/Runtime Usage analytics */}
        <TabsContent value="analytics">
          <UsageAnalytics />
        </TabsContent>

        {/* Tab 8: Audit timeline logs */}
        <TabsContent value="audit">
          <AuditLogs />
        </TabsContent>

        {/* Tab 9: Feature flags overrides */}
        <TabsContent value="settings">
          <OrgSettings />
        </TabsContent>

        {/* Tab 10: Pricing plans & compliance */}
        <TabsContent value="billing">
          <BillingPlaceholder />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Simple Helper Button wrapper since imported from page wrapper
const Button: React.FC<any> = ({ children, className, onClick, ...props }) => (
  <button
    onClick={onClick}
    className={`h-7 px-3 rounded text-[10px] font-bold border transition-colors ${className}`}
    {...props}
  >
    {children}
  </button>
);
