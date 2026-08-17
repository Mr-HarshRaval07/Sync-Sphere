'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { approvalApi } from '../../../shared/services/api';
import { DataGrid, EmptyState, SkeletonLoader } from '../../../shared/components/DesignSystem';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { Input } from '../../../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../../../components/ui/dialog';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../../components/ui/card';
import { Label } from '../../../components/ui/label';
import { CheckSquare, UserPlus, CheckCircle, XCircle, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';
import { ApprovalRequest, ApprovalDelegate } from '../../../shared/types';

export default function ApprovalsPage() {
  const queryClient = useQueryClient();
  const [selectedApproval, setSelectedApproval] = useState<ApprovalRequest | null>(null);
  const [notes, setNotes] = useState('');

  // Form states for delegate
  const [isDelegateOpen, setIsDelegateOpen] = useState(false);
  const [delegateTo, setDelegateTo] = useState('');

  // Query pending approvals
  const { data: approvals = [], isLoading } = useQuery({
    queryKey: ['approvals-list'],
    queryFn: () => approvalApi.listPendingApprovals(),
  });

  // Query delegates
  const { data: delegates = [], isLoading: delegatesLoading } = useQuery({
    queryKey: ['delegates-list'],
    queryFn: () => approvalApi.listDelegates(),
  });

  // Decision mutation
  const decisionMutation = useMutation({
    mutationFn: (payload: { id: string; approved: boolean; notes: string }) =>
      approvalApi.submitDecision(payload.id, payload.approved, payload.notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals-list'] });
      setSelectedApproval(null);
      setNotes('');
      toast.success('Decision Registered', { description: 'Supervisor approval response logged.' });
    },
    onError: (err: any) => {
      toast.error('Submission Failed', { description: err.response?.data?.error?.message || 'Failed to submit decision.' });
    },
  });

  // Create delegate mutation
  const delegateMutation = useMutation({
    mutationFn: (payload: any) => approvalApi.createDelegate(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['delegates-list'] });
      setIsDelegateOpen(false);
      setDelegateTo('');
      toast.success('Delegate Created', { description: 'Supervisor delegation rules updated.' });
    },
  });

  const handleDecision = (approved: boolean) => {
    if (!selectedApproval) return;
    decisionMutation.mutate({
      id: selectedApproval.id,
      approved,
      notes,
    });
  };

  const handleDelegateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    delegateMutation.mutate({
      to_user_id: delegateTo,
      is_active: true,
    });
  };

  const columns = [
    { key: 'id', header: 'Request ID', render: (row: ApprovalRequest) => <span className="font-semibold text-xs font-mono">#{row.id.slice(-8)}</span> },
    { key: 'session_id', header: 'Execution ID', render: (row: ApprovalRequest) => <span className="text-xs font-mono">#{row.session_id.slice(-8)}</span> },
    { key: 'node_id', header: 'Trigger Step', render: (row: ApprovalRequest) => <code className="text-xs bg-muted p-1 rounded font-mono">{row.node_id}</code> },
    { key: 'routing_strategy', header: 'Routing Rule' },
    {
      key: 'status',
      header: 'Status',
      render: (row: ApprovalRequest) => (
        <Badge variant="outline" className="text-xs font-semibold px-2 py-0.5 border border-amber-500/25 text-amber-500 bg-amber-500/10">
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row: ApprovalRequest) => (
        <Button size="xs" variant="outline" className="border-border hover:bg-muted text-foreground" onClick={() => setSelectedApproval(row)}>
          Respond
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight">Human Approvals</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Audit and verify pending execution decisions or configure supervisor delegates.
          </p>
        </div>
        <Button onClick={() => setIsDelegateOpen(true)} className="bg-primary hover:bg-primary/95 text-primary-foreground flex items-center gap-1.5">
          <UserPlus className="h-4 w-4" /> Delegate Access
        </Button>
      </div>

      {isLoading ? (
        <SkeletonLoader rows={4} />
      ) : approvals.length === 0 ? (
        <EmptyState
          title="No Approvals Pending"
          description="Supervisor checkpoint gates will appear here when triggered by executions."
          icon={<CheckSquare className="h-10 w-10 text-muted-foreground" />}
        />
      ) : (
        <DataGrid
          columns={columns}
          data={approvals}
          onRowClick={(row) => setSelectedApproval(row)}
        />
      )}

      {/* Decision Respond Modal Dialog */}
      {selectedApproval && (
        <Dialog open={!!selectedApproval} onOpenChange={() => setSelectedApproval(null)}>
          <DialogContent className="max-w-md border-border bg-card shadow-2xl">
            <DialogHeader>
              <DialogTitle>Respond to Gate #{selectedApproval.id.slice(-8)}</DialogTitle>
              <DialogDescription>
                Provide supervisor override decisions. Rejecting will trigger rollback compensation handlers.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="font-semibold text-muted-foreground block">Workflow Step</span>
                  <span className="font-mono text-foreground">{selectedApproval.node_id}</span>
                </div>
                <div>
                  <span className="font-semibold text-muted-foreground block">Routing Rule</span>
                  <span className="text-foreground">{selectedApproval.routing_strategy}</span>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs text-foreground">Decision Notes</Label>
                <textarea
                  className="flex min-h-[80px] w-full rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus-visible:outline-none"
                  placeholder="Provide context or instructions for this override..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  required
                />
              </div>
            </div>
            <DialogFooter className="flex gap-2">
              <Button variant="ghost" onClick={() => setSelectedApproval(null)} className="hover:bg-muted text-foreground">
                Cancel
              </Button>
              <Button
                variant="outline"
                className="border-rose-500/20 hover:bg-rose-500/5 text-rose-500 flex items-center gap-1"
                onClick={() => handleDecision(false)}
                disabled={decisionMutation.isPending}
              >
                <XCircle className="h-4 w-4" /> Reject
              </Button>
              <Button
                className="bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-1"
                onClick={() => handleDecision(true)}
                disabled={decisionMutation.isPending}
              >
                <CheckCircle className="h-4 w-4" /> Approve
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Delegate Modal Dialog */}
      <Dialog open={isDelegateOpen} onOpenChange={setIsDelegateOpen}>
        <DialogContent className="max-w-md border-border bg-card shadow-2xl">
          <DialogHeader>
            <DialogTitle>Configure Supervisor Delegate</DialogTitle>
            <DialogDescription>Redirect approvals when you are offline.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleDelegateSubmit} className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label className="text-xs">Delegate Supervisor Email</Label>
              <Input
                placeholder="supervisor-b@acme.ai"
                value={delegateTo}
                onChange={(e) => setDelegateTo(e.target.value)}
                required
                className="bg-card border-border placeholder-muted-foreground"
              />
            </div>
            <DialogFooter className="pt-2">
              <Button type="button" variant="ghost" onClick={() => setIsDelegateOpen(false)} className="hover:bg-muted text-foreground">
                Cancel
              </Button>
              <Button type="submit" className="bg-primary hover:bg-primary/95 text-primary-foreground">
                Active Rule
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
