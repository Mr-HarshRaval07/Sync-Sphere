'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { identityApi } from '../../../shared/services/api';
import { DataGrid, SkeletonLoader } from '../../../shared/components/DesignSystem';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Badge } from '../../../components/ui/badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../../components/ui/card';
import { Label } from '../../../components/ui/label';
import { Settings, Key, Plus, Trash2, Globe, Shield, Save } from 'lucide-react';
import { toast } from 'sonner';
import { ApiKey } from '../../../shared/types';

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [keyName, setKeyName] = useState('');
  const [newKeyGenerated, setNewKeyGenerated] = useState<string | null>(null);

  // Query API keys
  const { data: keys = [], isLoading: keysLoading } = useQuery({
    queryKey: ['api-keys-list'],
    queryFn: () => identityApi.getApiKeys(),
  });

  // Query User Profile
  const { data: user } = useQuery({
    queryKey: ['user-profile'],
    queryFn: () => identityApi.getMe(),
  });

  const [localPreferences, setLocalPreferences] = useState({
    default_google_sheets_id: '',
    default_notion_db_id: ''
  });

  React.useEffect(() => {
    if (user && user.preferences) {
      setLocalPreferences({
        default_google_sheets_id: user.preferences.default_google_sheets_id || '',
        default_notion_db_id: user.preferences.default_notion_db_id || ''
      });
    }
  }, [user]);

  const updateProfileMutation = useMutation({
    mutationFn: (payload: any) => identityApi.updateProfile(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
      toast.success('Preferences saved successfully');
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail?.message || 'Failed to update preferences');
    }
  });

  const handleSavePreferences = () => {
    updateProfileMutation.mutate({ preferences: localPreferences });
  };

  // Query Organization
  const { data: org } = useQuery({
    queryKey: ['user-org'],
    queryFn: () => identityApi.getOrgs(),
  });

  const createKeyMutation = useMutation({
    mutationFn: (payload: { name: string }) => identityApi.createApiKey(payload),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['api-keys-list'] });
      setKeyName('');
      setNewKeyGenerated(data.key); // Display full secret key once
      toast.success('API Key Generated', { description: 'Make sure to copy the key now as it won\'t be visible again.' });
    },
  });

  // Delete API key mutation
  const deleteKeyMutation = useMutation({
    mutationFn: (id: string) => identityApi.deleteApiKey(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys-list'] });
      toast.success('API Key Revoked');
    },
  });

  const handleCreateKey = (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyName.trim()) return;
    createKeyMutation.mutate({ name: keyName.trim() });
  };

  const keyColumns = [
    { key: 'name', header: 'Key Name', render: (row: any) => <span className="font-semibold text-foreground">{row.name}</span> },
    { key: 'key_prefix', header: 'Key Prefix', render: (row: any) => <code className="text-xs bg-muted p-1 rounded font-mono">{row.key_prefix}****</code> },
    { key: 'created_at', header: 'Created At', render: (row: any) => new Date(row.created_at).toLocaleDateString() },
    { key: 'last_used_at', header: 'Last Used', render: (row: any) => row.last_used_at ? new Date(row.last_used_at).toLocaleDateString() : 'Never' },
    {
      key: 'status', header: 'Status', render: (row: any) => (
        <Badge variant={row.status === 'ACTIVE' ? 'default' : 'destructive'} className="text-[10px]">
          {row.status}
        </Badge>
      )
    },
    {
      key: 'actions', header: '', render: (row: any) => (
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 text-muted-foreground hover:text-destructive"
          onClick={() => { if (confirm('Are you sure you want to revoke this key?')) deleteKeyMutation.mutate(row.id); }}
          disabled={row.status !== 'ACTIVE' || deleteKeyMutation.isPending}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      )
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight">Workspace Settings</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Configure security credentials, organization workspaces, and API credentials.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left pane: API credentials */}
        <div className="lg:col-span-2 space-y-6">
          {/* Key generation form */}
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="text-base font-bold flex items-center gap-1.5">
                <Key className="h-4 w-4 text-primary" /> API Developer Credentials
              </CardTitle>
              <CardDescription className="text-xs">Generate secrets to allow programmatic integrations via SDKs.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={handleCreateKey} className="flex gap-2">
                <Input
                  placeholder="Local test script Key"
                  value={keyName}
                  onChange={(e) => setKeyName(e.target.value)}
                  required
                  className="bg-card border-border placeholder-muted-foreground flex-1"
                />
                <Button type="submit" disabled={createKeyMutation.isPending} className="bg-primary hover:bg-primary/95 text-primary-foreground flex items-center gap-1 shrink-0">
                  <Plus className="h-4 w-4" /> Create Key
                </Button>
              </form>

              {/* Show newly generated API key box */}
              {newKeyGenerated && (
                <div className="border border-emerald-500/25 bg-emerald-500/5 p-3 rounded flex flex-col gap-1.5 text-xs text-foreground">
                  <span className="font-semibold text-emerald-500">Copy Secret Key (Visible Once)</span>
                  <div className="flex gap-2">
                    <code className="bg-card border border-border p-2 rounded block font-mono flex-1 select-all overflow-x-auto">
                      {newKeyGenerated}
                    </code>
                    <Button size="sm" variant="outline" className="border-border text-foreground hover:bg-muted shrink-0" onClick={() => { navigator.clipboard.writeText(newKeyGenerated); toast.info('Copied key to clipboard!'); }}>
                      Copy
                    </Button>
                  </div>
                </div>
              )}

              {/* Keys DataGrid */}
              <div className="border-t border-border/50 pt-4">
                {keysLoading ? (
                  <SkeletonLoader rows={3} />
                ) : keys.length === 0 ? (
                  <span className="text-xs text-muted-foreground block py-4">No active developer keys found. Generate one above.</span>
                ) : (
                  <DataGrid
                    columns={keyColumns}
                    data={keys}
                    className="border border-border"
                  />
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="text-base font-bold flex items-center gap-1.5">
                <Settings className="h-4 w-4 text-primary" /> Workflow Default Overrides
              </CardTitle>
              <CardDescription className="text-xs">Automatically inject fallback IDs when AI misses them.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2">
                <Label className="text-xs font-semibold">Default Google Sheets Spreadsheet ID</Label>
                <Input
                  placeholder="e.g. 17KafHEhIdy1ZbgPY0An-NfC5RzmUMJnSoK8bViymES8"
                  value={localPreferences.default_google_sheets_id}
                  onChange={(e) => setLocalPreferences(prev => ({ ...prev, default_google_sheets_id: e.target.value }))}
                  className="bg-card border-border placeholder-muted-foreground"
                />
              </div>
              <div className="grid gap-2">
                <Label className="text-xs font-semibold">Default Notion Database ID or Page ID</Label>
                <Input
                  placeholder="e.g. 3b1a773bfdcf81199d64f4066e8e8111"
                  value={localPreferences.default_notion_db_id}
                  onChange={(e) => setLocalPreferences(prev => ({ ...prev, default_notion_db_id: e.target.value }))}
                  className="bg-card border-border placeholder-muted-foreground"
                />
              </div>
              <Button onClick={handleSavePreferences} disabled={updateProfileMutation.isPending} className="w-full bg-primary hover:bg-primary/95 text-primary-foreground flex items-center gap-1">
                <Save className="h-4 w-4" /> Save Default IDs
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Right pane: Org metadata info */}
        <div className="space-y-4">
          <Card className="border-border bg-card h-full flex flex-col">
            <CardHeader>
              <CardTitle className="text-base font-bold flex items-center gap-1.5">
                <Globe className="h-4 w-4 text-primary" /> Tenant Workspace
              </CardTitle>
              <CardDescription className="text-xs">Details about current tenant domain parameters.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div className="border border-border bg-muted/10 p-3 rounded flex flex-col gap-1">
                <span className="font-semibold text-muted-foreground">Tenant Name</span>
                <span className="font-bold text-foreground">{org?.name || 'SyncSphere Enterprise'}</span>
                {org?.workspace_id && <span className="text-[10px] text-muted-foreground break-all">ID: {org.workspace_id}</span>}
              </div>

              <div className="border border-border bg-muted/10 p-3 rounded flex flex-col gap-1">
                <span className="font-semibold text-muted-foreground">User Details</span>
                <span className="font-bold text-foreground">{user?.name || user?.email || 'Admin'}</span>
                <span className="text-[10px] text-muted-foreground break-all">{user?.email || ''}</span>
              </div>

              <div className="border border-border bg-muted/10 p-3 rounded flex flex-col gap-1">
                <span className="font-semibold text-muted-foreground">Compliance SLA</span>
                <span className="font-bold text-foreground">Enterprise Multi-Tenant Node</span>
              </div>

              <div className="border border-border bg-muted/10 p-3 rounded flex flex-col gap-1">
                <span className="font-semibold text-muted-foreground">Security Shield</span>
                <span className="font-bold text-foreground flex items-center gap-1 text-emerald-500">
                  <Shield className="h-4 w-4 shrink-0 text-emerald-500" /> Fully Isolated Partition
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
