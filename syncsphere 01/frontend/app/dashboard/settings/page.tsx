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
import { Settings, Key, Plus, Trash2, Globe, Shield } from 'lucide-react';
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

  // Create API key mutation
  const createKeyMutation = useMutation({
    mutationFn: (payload: { name: string }) => identityApi.createApiKey(payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['api-keys-list'] });
      setKeyName('');
      setNewKeyGenerated(data.key); // Display full secret key once
      toast.success('API Key Generated', { description: 'Make sure to copy the key now as it won\'t be visible again.' });
    },
  });

  const handleCreateKey = (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyName.trim()) return;
    createKeyMutation.mutate({ name: keyName.trim() });
  };

  const keyColumns = [
    { key: 'name', header: 'Key Name', render: (row: ApiKey) => <span className="font-semibold text-foreground">{row.name}</span> },
    { key: 'key_prefix', header: 'Key Prefix', render: (row: ApiKey) => <code className="text-xs bg-muted p-1 rounded font-mono">{row.key_prefix}*********</code> },
    { key: 'created_at', header: 'Created At', render: (row: ApiKey) => new Date(row.created_at).toLocaleDateString() },
    { key: 'expires_at', header: 'Expires At', render: (row: ApiKey) => row.expires_at ? new Date(row.expires_at).toLocaleDateString() : 'Never' },
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
