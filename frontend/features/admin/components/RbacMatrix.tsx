'use client';

import React, { useState } from 'react';
import { useAdminStore } from '../stores/adminStore';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/table';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Shield, Check, X, ShieldAlert, Cpu, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

export const RbacMatrix: React.FC = () => {
  const { roles, addRole, permissionInspector, inspectPermission } = useAdminStore();
  const [newRoleName, setNewRoleName] = useState('');
  const [newRoleDesc, setNewRoleDesc] = useState('');
  
  // Debug Inspector Fields
  const [testUser, setTestUser] = useState('developer-1');
  const [testResource, setTestResource] = useState('workflows:Slack Alert');
  const [testAction, setTestAction] = useState('read');

  const defaultRoles = [
    { id: 'admin', name: 'Admin', description: 'Complete system access permissions' },
    { id: 'developer', name: 'Developer', description: 'Design pipelines & tools configurator' },
    { id: 'operator', name: 'Operator', description: 'Watch monitor centers & verify alerts' },
    { id: 'viewer', name: 'Viewer', description: 'Auditing view only' },
  ];

  const displayRoles = roles.length > 0 ? [...defaultRoles, ...roles] : defaultRoles;

  const resourcesList = [
    { key: 'workflows', label: 'Workflows Schema' },
    { key: 'connectors', label: 'MCP Connectors' },
    { key: 'secrets', label: 'Secrets Vault' },
    { key: 'approvals', label: 'Approvals Gate' },
    { key: 'analytics', label: 'Usage Metrics' },
  ];

  const handleCreateRole = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRoleName.trim()) return;
    addRole({
      id: `role_${Date.now()}`,
      org_id: 'org-1',
      name: newRoleName.trim(),
      description: newRoleDesc.trim(),
      permissions: [],
    });
    toast.success('Custom Role Created', { description: `RBAC list updated with ${newRoleName}.` });
    setNewRoleName('');
    setNewRoleDesc('');
  };

  const handleTestPermission = () => {
    inspectPermission(testUser, testResource, testAction);
    toast.info('Access Query Checked', { description: 'Audit logged simulated evaluation.' });
  };

  return (
    <div className="space-y-6">
      {/* 1. Permissions Matrix Table */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-xs font-bold flex items-center gap-1.5">
            <Shield className="h-4 w-4 text-primary" /> Role-Based Access Matrix
          </CardTitle>
          <CardDescription className="text-[10px]">Configure default system privileges or map operations</CardDescription>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto scrollbar-thin">
          <Table>
            <TableHeader className="bg-muted/40">
              <TableRow>
                <TableHead className="font-semibold text-xs text-muted-foreground w-40">Resource Name</TableHead>
                {displayRoles.map((r) => (
                  <TableHead key={r.id} className="font-semibold text-xs text-muted-foreground text-center">
                    {r.name}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {resourcesList.map((res) => (
                <TableRow key={res.key} className="hover:bg-muted/30 transition-colors">
                  <TableCell className="font-semibold text-xs text-foreground">{res.label}</TableCell>
                  {displayRoles.map((r) => {
                    // Simulated permission matrix checks: Admins can do everything, devs can do all except secrets, viewers read only
                    const canWrite = r.id === 'admin' || (r.id === 'developer' && res.key !== 'secrets');
                    
                    return (
                      <TableCell key={r.id} className="text-center">
                        <Badge className={`text-[10px] border font-semibold px-2 py-0.5 ${
                          canWrite
                            ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/25'
                            : r.id === 'viewer'
                            ? 'bg-sky-500/10 text-sky-500 border-sky-500/25'
                            : 'bg-muted text-muted-foreground border-border'
                        }`}>
                          {canWrite ? 'Read/Write' : r.id === 'viewer' ? 'Read-Only' : 'No Access'}
                        </Badge>
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 2. Custom Role Creator */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-bold flex items-center gap-1.5">
              <Sparkles className="h-4 w-4 text-primary" /> Create Custom Role
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateRole} className="space-y-3">
              <div className="space-y-1">
                <label className="text-[10px] text-muted-foreground font-medium block">Role Name</label>
                <Input
                  placeholder="Security Compliance Auditor"
                  value={newRoleName}
                  onChange={(e) => setNewRoleName(e.target.value)}
                  required
                  className="h-8 text-xs placeholder:text-muted-foreground bg-card border-border focus-visible:ring-primary"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] text-muted-foreground font-medium block">Description</label>
                <Input
                  placeholder="Can view audit timelines and sign off compliance checks"
                  value={newRoleDesc}
                  onChange={(e) => setNewRoleDesc(e.target.value)}
                  required
                  className="h-8 text-xs placeholder:text-muted-foreground bg-card border-border focus-visible:ring-primary"
                />
              </div>
              <Button type="submit" size="sm" className="w-full bg-primary hover:bg-primary/90 text-primary-foreground">
                Register Custom Role
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* 3. Permission Inspector Utility */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-bold flex items-center gap-1.5">
              <ShieldAlert className="h-4 w-4 text-violet-500" /> Permission Inspector Debugger
            </CardTitle>
            <CardDescription className="text-[10px]">Test privileges for any user, resource, and action combo</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-2">
              <div className="space-y-1">
                <label className="text-[9px] text-muted-foreground font-medium block">User ID</label>
                <Input
                  value={testUser}
                  onChange={(e) => setTestUser(e.target.value)}
                  className="h-7 text-xs bg-card border-border"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[9px] text-muted-foreground font-medium block">Resource</label>
                <Input
                  value={testResource}
                  onChange={(e) => setTestResource(e.target.value)}
                  className="h-7 text-xs bg-card border-border"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[9px] text-muted-foreground font-medium block">Action</label>
                <select
                  value={testAction}
                  onChange={(e) => setTestAction(e.target.value)}
                  className="h-7 w-full px-1.5 rounded border border-border bg-card text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  aria-label="Inspect action type selector"
                >
                  <option value="read">Read</option>
                  <option value="write">Write</option>
                  <option value="execute">Execute</option>
                </select>
              </div>
            </div>

            <Button size="sm" onClick={handleTestPermission} className="w-full bg-primary/10 text-primary hover:bg-primary/20">
              Evaluate Privileges
            </Button>

            {/* Results */}
            {permissionInspector.userId && (
              <div className={`p-3 rounded border text-xs flex items-center gap-2.5 ${
                permissionInspector.allowed
                  ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-600'
                  : 'bg-rose-500/10 border-rose-500/25 text-rose-600'
              }`}>
                {permissionInspector.allowed ? <Check className="h-4 w-4 shrink-0" /> : <X className="h-4 w-4 shrink-0" />}
                <div className="flex-1">
                  <span>Simulated Result: <strong>{permissionInspector.allowed ? 'ALLOWED' : 'DENIED'}</strong></span>
                  <p className="text-[9px] text-muted-foreground mt-0.5">
                    User &ldquo;{permissionInspector.userId}&rdquo; is {permissionInspector.allowed ? 'authorized' : 'restricted'} to perform action &ldquo;{permissionInspector.action}&rdquo; on resource &ldquo;{permissionInspector.resource}&rdquo;.
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
