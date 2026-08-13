'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useOrgStore } from '../../../shared/stores/orgStore';
import { useAdminStore } from '../stores/adminStore';
import { identityApi } from '../../../shared/services/api';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Building, UserPlus, Users, RotateCcw, Shield } from 'lucide-react';
import { toast } from 'sonner';

export const OrgManagement: React.FC = () => {
  const { orgs, currentOrg, setCurrentOrg } = useOrgStore();
  const { invitations, addInvitation, revokeInvitation } = useAdminStore();
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('viewer');

  // Query org member list
  const { data: members = [], refetch } = useQuery({
    queryKey: ['org-members-list', currentOrg?.id],
    queryFn: async () => {
      // Reuses standard endpoint which returns members or users
      const data = await identityApi.getMe();
      // Mock list since we need multiple members for management view
      return [
        { id: data.id, email: data.email, first_name: data.first_name || 'Owner', last_name: data.last_name || '', role: 'Admin' },
        { id: 'u-2', email: 'developer@acme.ai', first_name: 'Dev', last_name: 'User', role: 'Developer' },
        { id: 'u-3', email: 'operator@acme.ai', first_name: 'Ops', last_name: 'User', role: 'Operator' },
      ];
    },
    enabled: !!currentOrg,
  });

  const handleInvite = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    addInvitation(inviteEmail.trim(), inviteRole);
    toast.success('Invitation Dispatched', { description: `Invite link sent to ${inviteEmail}.` });
    setInviteEmail('');
  };

  const handleSwitchOrg = (orgId: string) => {
    const target = orgs.find((o) => o.id === orgId);
    if (target) {
      setCurrentOrg(target);
      toast.success('Organization Context Swapped', { description: `Now auditing ${target.name}.` });
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Org Switcher Details Card */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-bold flex items-center gap-1.5">
            <Building className="h-4 w-4 text-primary" /> Switch Organization Context
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="flex-1">
            <div className="text-xs font-semibold text-foreground">Active Org Context</div>
            <select
              value={currentOrg?.id || ''}
              onChange={(e) => handleSwitchOrg(e.target.value)}
              className="h-9 w-full sm:w-64 px-2.5 rounded-md border border-border bg-card text-xs text-foreground mt-1 focus:outline-none focus:ring-1 focus:ring-primary"
              aria-label="Active Organization switcher"
            >
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>{o.name}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-6 border-l border-border pl-6 text-xs text-muted-foreground mt-2 sm:mt-0">
            <div>
              <div>Org Slug:</div>
              <strong className="text-foreground font-mono">{currentOrg?.slug || 'n/a'}</strong>
            </div>
            <div>
              <div>Established:</div>
              <strong className="text-foreground font-mono">{currentOrg ? new Date(currentOrg.created_at).toLocaleDateString() : 'n/a'}</strong>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 2. Member Management */}
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-bold flex items-center gap-1.5">
              <Users className="h-4 w-4 text-sky-500" /> Organization Members
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border/50">
              {members.map((m) => (
                <div key={m.id} className="flex justify-between items-center p-3 text-xs">
                  <div>
                    <div className="font-semibold text-foreground">{m.first_name} {m.last_name}</div>
                    <div className="text-[10px] text-muted-foreground mt-0.5">{m.email}</div>
                  </div>
                  <Badge className="text-[9px] border font-semibold px-2 py-0.5 bg-muted text-muted-foreground">
                    {m.role}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 3. Send Invitations */}
        <div className="space-y-4">
          <Card className="border-border bg-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-bold flex items-center gap-1.5">
                <UserPlus className="h-4 w-4 text-emerald-500" /> Send New Invitation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleInvite} className="space-y-3">
                <div className="space-y-1">
                  <label className="text-[10px] text-muted-foreground font-medium block">Email Address</label>
                  <Input
                    type="email"
                    placeholder="user@acme.ai"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    required
                    className="h-8 text-xs placeholder:text-muted-foreground bg-card border-border focus-visible:ring-primary"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] text-muted-foreground font-medium block">Portal Role Access</label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="h-8 w-full px-2.5 rounded-md border border-border bg-card text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                    aria-label="Invite role selector"
                  >
                    <option value="admin">Admin</option>
                    <option value="developer">Developer</option>
                    <option value="operator">Operator</option>
                    <option value="viewer">Viewer</option>
                  </select>
                </div>
                <Button type="submit" size="sm" className="w-full bg-primary hover:bg-primary/90 text-primary-foreground">
                  Send Invitation Code
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Active Invitations List */}
          {invitations.length > 0 && (
            <Card className="border-border bg-card">
              <CardHeader className="pb-1">
                <CardTitle className="text-xs font-bold text-foreground">Pending Invitations</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-border/50">
                  {invitations.map((i) => (
                    <div key={i.email} className="flex justify-between items-center p-3 text-xs">
                      <div>
                        <div className="font-semibold text-foreground">{i.email}</div>
                        <div className="text-[9px] text-muted-foreground mt-0.5">Expires: {new Date(i.expiresAt).toLocaleDateString()}</div>
                      </div>
                      <div className="flex gap-2 items-center">
                        <Badge className="text-[9px] border font-semibold px-2 py-0.5 bg-amber-500/10 text-amber-500 border-amber-500/25">
                          {i.role}
                        </Badge>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 text-[10px] text-rose-500 hover:bg-rose-500/10"
                          onClick={() => revokeInvitation(i.email)}
                        >
                          Revoke
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
