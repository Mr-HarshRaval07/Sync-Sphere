'use client';

import React from 'react';
import { AdminSecret } from '../stores/adminStore';
import { useAdminStore as useStore } from '../stores/adminStore';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/table';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { Key, ShieldCheck, RefreshCw, AlertTriangle, Cpu } from 'lucide-react';
import { toast } from 'sonner';

export const SecretsManager: React.FC = () => {
  const { secrets, setSecrets, rotateSecret } = useStore();

  const defaultSecrets: AdminSecret[] = [
    { id: 'sec-1', name: 'OpenAI API Token', provider: 'OpenAI', status: 'valid', lastRotated: '12 days ago', encryptionStatus: 'AES-256-GCM' },
    { id: 'sec-2', name: 'Anthropic SDK Key', provider: 'Anthropic', status: 'expired', lastRotated: '94 days ago', encryptionStatus: 'AES-256-GCM' },
    { id: 'sec-3', name: 'Slack Bot Credentials', provider: 'Slack', status: 'valid', lastRotated: '4 days ago', encryptionStatus: 'AES-256-GCM' },
    { id: 'sec-4', name: 'GitHub Integration Token', provider: 'GitHub', status: 'valid', lastRotated: '32 days ago', encryptionStatus: 'AES-256-GCM' },
  ];

  const displaySecrets = secrets.length > 0 ? secrets : defaultSecrets;

  const handleRotate = (id: string, name: string) => {
    rotateSecret(id);
    toast.success('Credentials Rotated', { description: `Securely rotated API tokens for ${name}.` });
  };

  return (
    <div className="space-y-6">
      {/* 1. Secrets Rotation Dashboard */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-xs font-bold flex items-center gap-1.5">
            <Key className="h-4 w-4 text-primary" /> Key Vault & Secrets Rotation Dashboard
          </CardTitle>
          <CardDescription className="text-[10px]">Verify cryptographic key cycles and encryption status</CardDescription>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto scrollbar-thin">
          <Table>
            <TableHeader className="bg-muted/40">
              <TableRow>
                <TableHead className="font-semibold text-xs text-muted-foreground">Secret Name</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Provider</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Status</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Last Rotated</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground">Encryption</TableHead>
                <TableHead className="font-semibold text-xs text-muted-foreground text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {displaySecrets.map((s) => {
                const isValid = s.status === 'valid' || s.status === 'rotated';
                
                return (
                  <TableRow key={s.id} className="hover:bg-muted/30 transition-colors">
                    <TableCell className="font-semibold text-xs text-foreground flex items-center gap-2">
                      <Key className="h-3.5 w-3.5 text-amber-500" />
                      {s.name}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{s.provider}</TableCell>
                    <TableCell>
                      <Badge className={`text-[10px] scale-90 border font-semibold px-2 py-0.5 capitalize ${
                        isValid
                          ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/25'
                          : 'bg-rose-500/10 text-rose-500 border-rose-500/25 animate-pulse'
                      }`}>
                        {s.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground font-mono">{s.lastRotated}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-[10px] text-emerald-500">
                        <ShieldCheck className="h-3.5 w-3.5" />
                        <span>{s.encryptionStatus}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 text-[10px] border-border text-foreground hover:bg-muted"
                        onClick={() => handleRotate(s.id, s.name)}
                      >
                        <RefreshCw className="h-3 w-3 mr-1" /> Rotate
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 2. Vault Security Compliance Check */}
      {displaySecrets.some((s) => s.status === 'expired') && (
        <Card className="border-rose-500/25 bg-rose-500/5 text-rose-500">
          <CardContent className="p-4 flex items-start gap-3 text-xs">
            <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5 animate-bounce" />
            <div>
              <span className="font-bold">Cryptographic Policy Violation:</span> System detected API credentials exceeding the 90-day rotation compliance cycle limit. Rotate the affected keys above.
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
