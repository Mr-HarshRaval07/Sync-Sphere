'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { aiApi } from '../../../shared/services/api';
import { DataGrid, EmptyState, SkeletonLoader } from '../../../shared/components/DesignSystem';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Badge } from '../../../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../../../components/ui/dialog';
import { Label } from '../../../components/ui/label';
import { FileCode, Plus, History, Tag, Edit3 } from 'lucide-react';
import { toast } from 'sonner';
import { PromptTemplate } from '../../../shared/types';

export default function PromptsPage() {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState<PromptTemplate | null>(null);

  // Form states
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [systemTemplate, setSystemTemplate] = useState('');
  const [userTemplate, setUserTemplate] = useState('');

  // Query prompt templates
  const { data: prompts = [], isLoading } = useQuery({
    queryKey: ['prompts-list'],
    queryFn: () => aiApi.listPrompts(),
  });

  // Create prompt mutation
  const createMutation = useMutation({
    mutationFn: (payload: any) => aiApi.createPrompt(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts-list'] });
      setIsCreateOpen(false);
      setName('');
      setDescription('');
      setSystemTemplate('');
      setUserTemplate('');
      toast.success('Prompt Created', { description: 'New versioned prompt template added successfully.' });
    },
    onError: (err: any) => {
      toast.error('Creation Failed', { description: err.response?.data?.error?.message || 'Failed to create prompt.' });
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      name: name.toLowerCase().trim().replace(/\s+/g, '_'),
      description,
      system_template: systemTemplate,
      user_template: userTemplate,
      variables: [], // Simple dynamic extraction could be done, but list default empty
    });
  };

  const columns = [
    { key: 'name', header: 'Template Name', render: (row: PromptTemplate) => <span className="font-semibold font-mono text-xs text-foreground">{row.name}</span> },
    { key: 'description', header: 'Description' },
    { key: 'active_version', header: 'Active Version', render: (row: PromptTemplate) => <Badge variant="outline" className="border-border">v{row.active_version}</Badge> },
    {
      key: 'actions',
      header: 'Actions',
      render: (row: PromptTemplate) => (
        <div className="flex gap-2">
          <Button size="xs" variant="outline" className="border-border hover:bg-muted text-foreground flex items-center gap-1" onClick={(e) => { e.stopPropagation(); setSelectedPrompt(row); }}>
            <Edit3 className="h-3 w-3" /> View & Edit
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight">Prompt Templates</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Manage sandboxed Jinja prompt templates and version history snapshots.
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} className="bg-primary hover:bg-primary/95 text-primary-foreground flex items-center gap-1.5">
          <Plus className="h-4 w-4" /> New Template
        </Button>
      </div>

      {isLoading ? (
        <SkeletonLoader rows={4} />
      ) : prompts.length === 0 ? (
        <EmptyState
          title="No Prompts Found"
          description="Create structured prompt layouts, specifying system guidelines and variable injection tokens."
          icon={<FileCode className="h-10 w-10 text-muted-foreground" />}
          actionLabel="Add Prompt Template"
          onAction={() => setIsCreateOpen(true)}
        />
      ) : (
        <DataGrid
          columns={columns}
          data={prompts}
          onRowClick={(row) => setSelectedPrompt(row)}
        />
      )}

      {/* Create Prompt Modal */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="max-w-xl border-border bg-card shadow-2xl overflow-y-auto max-h-[85vh]">
          <DialogHeader>
            <DialogTitle>Create Prompt Template</DialogTitle>
            <DialogDescription>Define system instructions and user request formats.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label className="text-xs">Template Identifier</Label>
              <Input
                placeholder="customer_welcome_email"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="bg-card border-border placeholder-muted-foreground"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Description</Label>
              <Input
                placeholder="Template used in workflow triggers to greet new workspace admins."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="bg-card border-border placeholder-muted-foreground"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">System Prompt Template</Label>
              <textarea
                className="flex min-h-[90px] w-full rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus-visible:outline-none"
                placeholder="You are a professional assistant. Help the customer with the request..."
                value={systemTemplate}
                onChange={(e) => setSystemTemplate(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">User Prompt Template (Jinja compatible)</Label>
              <textarea
                className="flex min-h-[90px] w-full rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus-visible:outline-none"
                placeholder="Hello {{customer_name}}, thank you for choosing our platform..."
                value={userTemplate}
                onChange={(e) => setUserTemplate(e.target.value)}
                required
              />
            </div>
            <DialogFooter className="pt-2">
              <Button type="button" variant="ghost" onClick={() => setIsCreateOpen(false)} className="hover:bg-muted text-foreground">
                Cancel
              </Button>
              <Button type="submit" disabled={createMutation.isPending} className="bg-primary hover:bg-primary/95 text-primary-foreground">
                {createMutation.isPending ? 'Saving...' : 'Create Template'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit/View Prompt Details Modal */}
      {selectedPrompt && (
        <Dialog open={!!selectedPrompt} onOpenChange={() => setSelectedPrompt(null)}>
          <DialogContent className="max-w-2xl border-border bg-card shadow-2xl overflow-y-auto max-h-[85vh]">
            <DialogHeader>
              <DialogTitle className="font-mono text-base">{selectedPrompt.name}</DialogTitle>
              <DialogDescription>Review prompt configurations and variables mapping.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-3 text-xs leading-relaxed">
              <div>
                <span className="font-semibold text-muted-foreground block mb-1">System Template</span>
                <pre className="bg-muted/30 border border-border p-3 rounded font-mono text-foreground whitespace-pre-wrap leading-normal">
                  {selectedPrompt.system_template}
                </pre>
              </div>

              <div>
                <span className="font-semibold text-muted-foreground block mb-1">User Template</span>
                <pre className="bg-muted/30 border border-border p-3 rounded font-mono text-foreground whitespace-pre-wrap leading-normal">
                  {selectedPrompt.user_template}
                </pre>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="border border-border bg-muted/10 p-3 rounded flex flex-col gap-1.5">
                  <span className="font-semibold text-muted-foreground flex items-center gap-1.5">
                    <History className="h-3.5 w-3.5" /> Template Version
                  </span>
                  <span className="text-sm font-bold text-foreground">v{selectedPrompt.active_version}</span>
                </div>
                <div className="border border-border bg-muted/10 p-3 rounded flex flex-col gap-1.5">
                  <span className="font-semibold text-muted-foreground flex items-center gap-1.5">
                    <Tag className="h-3.5 w-3.5" /> Variables Checked
                  </span>
                  <span className="text-sm font-bold text-foreground">
                    {selectedPrompt.variables?.length || 0} variables
                  </span>
                </div>
              </div>
            </div>
            <DialogFooter className="border-t border-border/50 pt-4">
              <Button onClick={() => setSelectedPrompt(null)} className="bg-primary hover:bg-primary/95 text-primary-foreground">
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
