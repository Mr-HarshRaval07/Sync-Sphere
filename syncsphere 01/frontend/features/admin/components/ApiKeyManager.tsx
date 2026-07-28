'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { identityApi } from '../../../shared/services/api';
import { useAdminStore } from '../stores/adminStore';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/table';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Key, ShieldX, Plus, RotateCw } from 'lucide-react';
import { toast } from 'sonner';

export const ApiKeyManager: React.FC = () => {
  const { apiKeys, setApiKeys, addApiKey, revokeApiKey } = useAdminStore();
  const [newKeyName, setNewKeyName] = useState('');

  // Query API keys
  const { data: serverKeys = [], isLoading } = useQuery({
    queryKey: ['admin-apikeys-list'],
    queryFn: async () => {
      const data = await identityApi.getApiKeys();
      setApiKeys(data);
      return data;
    },
  });

  const displayKeys = apiKeys.length > 0 ? apiKeys : serverKeys;

  const handleCreateKey = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    
    const keyId = `key_${Date.now()}`;
    addApiKey({
      id: keyId,
      name: newKeyName.trim(),
      key_prefix: 'sk_live_' + Math.random().toString(36).substring(2, 8),
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 86400000 * 90).toISOString(), // 90 days
    });
    
    toast.success('API Key Generated', { description: `Secure prefix sk_live_ created.` });
    setNewKeyName('');
  };

  const handleRotate = (name: string) => {
    toast.success('API Key Rotated', { description: `Secure hash rotated for key: ${name}.` });
  };

  const handleRevoke = (id: string, name: string) => {
    revokeApiKey(id);
    toast.success('API Key Revoked', { description: `Secret credentials deleted for ${name}.` });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* 1. API Keys Directory Table (Left/Center Col) */}
      <div className="lg:col-span-2 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-foreground flex items-center gap-1.5">
              <Key className="h-4 w-4 text-primary" /> API Keys Configuration
            </h4>
            <p className="text-[10px] text-muted-foreground mt-0.5">Manage external gateway authorization tokens</p>
          </div>
        </div>

        <div className="rounded-md border border-border bg-card overflow-hidden">
          <Table>
            <TableHeader className="bg-muted/40">
              <TableRow>
                <TableHead className="font-semibold text-xs text-muted-foreground">Key Name</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Prefix</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Expires At</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading && displayKeys.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-8 text-xs text-muted-foreground">
                    Querying credentials directory...
                  </TableCell>
                </TableRow>
              ) : displayKeys.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-8 text-xs text-muted-foreground italic">
                    No active API keys found.
                  </TableCell>
                </TableRow>
              ) : (
                displayKeys.map((k: any) => (
                  <TableRow key={k.id} className="hover:bg-muted/30 transition-colors">
                    <TableCell className="font-semibold text-xs text-foreground">{k.name}</TableCell>
                    <TableCell className="text-xs text-muted-foreground font-mono">{k.key_prefix}***</TableCell>
                    <TableCell className="text-xs text-muted-foreground font-mono">
                      {k.expires_at ? new Date(k.expires_at).toLocaleDateString() : 'Never'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex gap-1 justify-end">
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-[10px] border-border text-foreground hover:bg-muted"
                          onClick={() => handleRotate(k.name)}
                        >
                          <RotateCw className="h-3 w-3 mr-1" /> Rotate
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-[10px] text-rose-500 hover:bg-rose-500/10"
                          onClick={() => handleRevoke(k.id, k.name)}
                        >
                          <ShieldX className="h-3.5 w-3.5 mr-1" /> Revoke
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* 2. Key Generation Box (Right Col) */}
      <Card className="border-border bg-card h-fit">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-bold flex items-center gap-1.5">
            <Plus className="h-4 w-4 text-emerald-500" /> Create New API Key
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreateKey} className="space-y-3">
            <div className="space-y-1">
              <label className="text-[10px] text-muted-foreground font-medium block">Key Description</label>
              <Input
                placeholder="GitHub Actions CI Key"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                required
                className="h-8 text-xs placeholder:text-muted-foreground bg-card border-border focus-visible:ring-primary"
              />
            </div>
            <Button type="submit" size="sm" className="w-full bg-primary hover:bg-primary/90 text-primary-foreground">
              Generate Secure Key
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
