'use client';

import React, { useState } from 'react';
import { DataGrid, EmptyState } from '../../../shared/components/DesignSystem';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { Input } from '../../../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../../../components/ui/dialog';
import { Label } from '../../../components/ui/label';
import { CheckSquare, UserPlus, CheckCircle, XCircle } from 'lucide-react';
import { toast } from 'sonner';

const PROTOTYPE_APPROVALS: any[] = [
  {
    id: "approv_9x8f7a6b",
    session_id: "exec_1a2b3c",
    node_id: "slack.send_message",
    title: "Send message to Slack",
    description: "Post a message or notification in a channel",
    status: "PENDING",
    created_at: new Date().toISOString(),
    context: { priority: "high", category: "Automation", approvers: "team-leads@acme.ai", instructions: "Verify that the notification does not contain PII." }
  },
  {
    id: "approv_5y4e3w2q",
    session_id: "exec_7x8y9z",
    title: "Create GitHub Issue",
    node_id: "github.create_issue",
    description: "Create an issue in a GitHub repository",
    status: "APPROVED",
    created_at: new Date(Date.now() - 3600000).toISOString(),
    context: { priority: "medium", category: "GitFlow", approvers: "devops@acme.ai", instructions: "Verify repository assignment." }
  },
  {
    id: "approv_pz93mal1",
    session_id: "exec_4m0p2s",
    title: "Create Meeting Notes",
    node_id: "notion.create_meeting_notes",
    description: "Create a new Notion page for meeting notes",
    status: "REJECTED",
    created_at: new Date(Date.now() - 86400000).toISOString(),
    context: { priority: "low", category: "Documentation", approvers: "managers@acme.ai" }
  }
];

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<any[]>(PROTOTYPE_APPROVALS);
  const [selectedApproval, setSelectedApproval] = useState<any>(null);
  const [notes, setNotes] = useState('');

  const [isDelegateOpen, setIsDelegateOpen] = useState(false);
  const [delegateTo, setDelegateTo] = useState('');
  const [isPending, setIsPending] = useState(false);

  const handleDecision = (approved: boolean) => {
    if (!selectedApproval) return;
    setIsPending(true);
    setTimeout(() => {
      setApprovals(prev => prev.map(app =>
        app.id === selectedApproval.id
          ? { ...app, status: approved ? 'APPROVED' : 'REJECTED' }
          : app
      ));
      setSelectedApproval(null);
      setNotes('');
      setIsPending(false);
      toast.success('Decision Registered', { description: 'Supervisor approval response logged (Prototype Mode).' });
    }, 500);
  };

  const handleDelegateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsDelegateOpen(false);
    setDelegateTo('');
    toast.success('Delegate Created', { description: 'Supervisor delegation rules updated (Prototype Mode).' });
  };

  const columns = [
    { key: 'id', header: 'Request ID', render: (row: any) => <span className="font-semibold text-xs font-mono">#{row.id.slice(-8)}</span> },
    { key: 'session_id', header: 'Execution ID', render: (row: any) => <span className="text-xs font-mono">#{(row.context?.log_id || row.context?.task_id || row.session_id || '').slice(-8)}</span> },
    { key: 'node_id', header: 'Trigger Step', render: (row: any) => <code className="text-[10px] bg-muted p-1 rounded font-mono truncate max-w-[120px] inline-block">{row.node_id || row.title}</code> },
    {
      key: 'context', header: 'Priority & Rule', render: (row: any) => (
        <div className="flex flex-col gap-1">
          <span className="text-[10px] font-semibold text-emerald-500 uppercase tracking-widest">{row.context?.priority || 'high'}</span>
          <span className="text-[10px] text-muted-foreground">{row.context?.category || 'Auto-generated'}</span>
        </div>
      )
    },
    {
      key: 'status',
      header: 'Status',
      render: (row: any) => {
        let variantStr = 'bg-amber-500/10 text-amber-500 border-amber-500/25';
        if (row.status === 'APPROVED') variantStr = 'bg-emerald-500/10 text-emerald-500 border-emerald-500/25';
        if (row.status === 'REJECTED') variantStr = 'bg-rose-500/10 text-rose-500 border-rose-500/25';
        return (
          <Badge variant="outline" className={`text-xs font-semibold px-2 py-0.5 border ${variantStr}`}>
            {row.status}
          </Badge>
        );
      }
    },
    { key: 'created_at', header: 'Timestamp', render: (row: any) => <span className="text-xs">{new Date(row.created_at).toLocaleString()}</span> },
    {
      key: 'actions',
      header: 'Actions',
      render: (row: any) => (
        <Button size="xs" variant="outline" className="border-border hover:bg-muted text-foreground" onClick={() => setSelectedApproval(row)} disabled={row.status !== 'PENDING'}>
          {row.status === 'PENDING' ? 'Respond' : 'View'}
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-amber-500/10 border border-amber-500/40 p-4 rounded-lg flex items-start gap-4 shadow-sm">
        <CheckSquare className="h-6 w-6 text-amber-500 mt-1 shrink-0" />
        <div>
          <h3 className="text-amber-500 font-bold text-sm tracking-tight mb-1">PROTOTYPE MODE - Human in the Loop (HITL)</h3>
          <p className="text-amber-500/80 text-xs leading-relaxed max-w-4xl">
            This module currently demonstrates how the Human Approval intervention component will function in future SyncSphere releases.
            The data populated below is static demo data to preview over-the-top intervention modals. Core production automation executes seamlessly without pauses.
          </p>
        </div>
      </div>
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

      <DataGrid
        columns={columns}
        data={approvals}
        onRowClick={(row) => setSelectedApproval(row)}
      />

      {/* Decision Respond Modal Dialog */}
      {selectedApproval && (
        <Dialog open={!!selectedApproval} onOpenChange={() => setSelectedApproval(null)}>
          <DialogContent className="max-w-md border-border bg-card shadow-2xl">
            <DialogHeader>
              <DialogTitle>Respond to Gate #{selectedApproval.id.slice(-8)}</DialogTitle>
              <DialogDescription>
                Provide supervisor override decisions. Rejecting will trigger rollback compensation handlers (Prototype Mode).
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="font-semibold text-muted-foreground block">Workflow Step</span>
                  <span className="font-mono text-foreground">{selectedApproval.node_id || selectedApproval.title}</span>
                </div>
                <div>
                  <span className="font-semibold text-muted-foreground block">Target Audience</span>
                  <span className="text-foreground">{selectedApproval.context?.approvers || 'Supervisors'}</span>
                </div>
              </div>

              <div className="bg-muted/30 p-3 rounded-md border border-border mt-2 mb-2">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {selectedApproval.context?.instructions || selectedApproval.description || 'Review the automated action taking place and determine if it complies with internal policies before confirming.'}
                </p>
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
                disabled={isPending}
              >
                <XCircle className="h-4 w-4" /> Reject
              </Button>
              <Button
                className="bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-1"
                onClick={() => handleDecision(true)}
                disabled={isPending}
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
