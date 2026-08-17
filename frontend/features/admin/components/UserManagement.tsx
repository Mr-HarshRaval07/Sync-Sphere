'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { identityApi } from '../../../shared/services/api';
import { useAdminStore, UserSession } from '../stores/adminStore';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/table';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { ShieldAlert, User, ShieldX, Key, Eye, HelpCircle, Activity, Globe } from 'lucide-react';
import { toast } from 'sonner';

export const UserManagement: React.FC = () => {
  const {
    users, setUsers, updateUserStatus,
    activeSessions, setSessions, revokeSession,
    startImpersonation, stopImpersonation, impersonatedUser, isImpersonating,
  } = useAdminStore();

  // Query users
  const { data: serverUsers = [], isLoading, refetch } = useQuery({
    queryKey: ['admin-users-list'],
    queryFn: async () => {
      const data = await identityApi.getMe();
      // Mock user database
      const list = [
        { id: data.id, email: data.email, first_name: data.first_name || 'Admin', last_name: data.last_name || 'Owner', status: 'active' as const, mfaEnabled: true },
        { id: 'u-2', email: 'developer@acme.ai', first_name: 'Dev', last_name: 'User', status: 'active' as const, mfaEnabled: true },
        { id: 'u-3', email: 'operator@acme.ai', first_name: 'Ops', last_name: 'User', status: 'suspended' as const, mfaEnabled: false },
        { id: 'u-4', email: 'guest@acme.ai', first_name: 'Guest', last_name: 'User', status: 'registered' as const, mfaEnabled: false },
      ];
      setUsers(list as any);
      return list;
    },
  });

  const displayUsers = users.length > 0 ? users : serverUsers;

  // Mock sessions list
  const defaultSessions: UserSession[] = [
    { id: 'sess-1', userId: 'u-1', userName: 'Admin Owner', device: 'Chrome / Windows', ipAddress: '192.168.1.4', location: 'New York, US', activeSince: '2 hours ago' },
    { id: 'sess-2', userId: 'u-2', userName: 'Dev User', device: 'Firefox / macOS', ipAddress: '10.0.0.12', location: 'London, UK', activeSince: '14 mins ago' },
  ];

  const displaySessions = activeSessions.length > 0 ? activeSessions : defaultSessions;

  const handleUpdateStatus = (id: string, status: 'active' | 'suspended') => {
    updateUserStatus(id, status);
    toast.success('User Status Updated', { description: `Account state transitioned to ${status}.` });
  };

  const handleResetPassword = (email: string) => {
    toast.success('Password Reset Dispatched', { description: `Secure link emailed to ${email}.` });
  };

  const handleToggleImpersonation = (user: any) => {
    if (isImpersonating && impersonatedUser?.id === user.id) {
      stopImpersonation();
      toast.info('Impersonation Session Terminated');
    } else {
      startImpersonation(user);
      toast.warning(`Read-Only Impersonation Active`, { description: `Now simulating portal views for ${user.first_name}.` });
    }
  };

  return (
    <div className="space-y-6">
      {/* Impersonation Indicator Banner */}
      {isImpersonating && impersonatedUser && (
        <div className="flex items-center justify-between px-4 py-3 rounded-lg bg-amber-500/10 border border-amber-500/25 text-amber-500 animate-pulse">
          <div className="flex items-center gap-2.5 text-xs">
            <Eye className="h-5 w-5 shrink-0" />
            <span>
              Impersonation Active: Auditing interface as <strong>{impersonatedUser.first_name} {impersonatedUser.last_name}</strong> (Read-Only)
            </span>
          </div>
          <Button size="sm" variant="ghost" className="h-7 text-amber-500 hover:bg-amber-500/20" onClick={stopImpersonation}>
            Stop Impersonation
          </Button>
        </div>
      )}

      {/* 1. User Management Listing Table */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-bold flex items-center gap-1.5">
            <User className="h-4 w-4 text-primary" /> User Accounts Directory
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto scrollbar-thin">
          <Table>
            <TableHeader className="bg-muted/40">
              <TableRow>
                <TableHead className="font-semibold text-xs text-muted-foreground">User</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Status</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">MFA Enabled</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {displayUsers.map((u) => {
                const isActive = u.status === 'active';
                const isOwner = u.id === 'u-1';
                
                return (
                  <TableRow key={u.id} className="hover:bg-muted/30 transition-colors">
                    <TableCell className="font-semibold text-xs text-foreground">
                      <div>
                        <span>{u.first_name} {u.last_name}</span>
                        <div className="text-[9px] text-muted-foreground font-normal mt-0.5">{u.email}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={`text-[10px] scale-90 border font-semibold px-2 py-0.5 capitalize ${
                        isActive
                          ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/25'
                          : u.status === 'suspended'
                          ? 'bg-rose-500/10 text-rose-500 border-rose-500/25'
                          : 'bg-muted text-muted-foreground border-border'
                      }`}>
                        {u.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={(u as any).mfaEnabled ? 'default' : 'secondary'} className="text-[9px]">
                        {(u as any).mfaEnabled ? 'MFA Configured' : 'Disabled'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex gap-1 justify-end">
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-[10px] border-border text-foreground hover:bg-muted"
                          onClick={() => handleResetPassword(u.email)}
                        >
                          <Key className="h-3 w-3 mr-1" /> Reset Pass
                        </Button>

                        {!isOwner && (
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 text-[10px] border-border text-foreground hover:bg-muted"
                            onClick={() => handleToggleImpersonation(u)}
                          >
                            <Eye className="h-3 w-3 mr-1" />
                            {isImpersonating && impersonatedUser?.id === u.id ? 'Exit' : 'Impersonate'}
                          </Button>
                        )}

                        {!isOwner && (
                          <Button
                            size="sm"
                            variant="ghost"
                            className={`h-7 text-[10px] ${isActive ? 'text-rose-500 hover:bg-rose-500/10' : 'text-emerald-500 hover:bg-emerald-500/10'}`}
                            onClick={() => handleUpdateStatus(u.id, isActive ? 'suspended' : 'active')}
                          >
                            {isActive ? 'Suspend' : 'Activate'}
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 2. Session Management Dashboard */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-bold flex items-center gap-1.5">
            <Activity className="h-4 w-4 text-sky-500" /> Session Management Dashboard
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto scrollbar-thin">
          <Table>
            <TableHeader className="bg-muted/40">
              <TableRow>
                <TableHead className="font-semibold text-xs text-muted-foreground">User Session</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Device / OS</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">IP & Location</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Active Since</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {displaySessions.map((sess) => (
                <TableRow key={sess.id} className="hover:bg-muted/30 transition-colors">
                  <TableCell className="font-semibold text-xs text-foreground">{sess.userName}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{sess.device}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Globe className="h-3 w-3 text-muted-foreground" />
                      <span>{sess.ipAddress} • {sess.location}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono">{sess.activeSince}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-7 text-[10px] text-rose-500 hover:bg-rose-500/10"
                      onClick={() => {
                        revokeSession(sess.id);
                        toast.success('Session Revoked', { description: 'Login cookie terminated.' });
                      }}
                    >
                      <ShieldX className="h-3.5 w-3.5 mr-1" /> Revoke
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};
