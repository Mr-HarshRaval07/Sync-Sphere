'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { knowledgeApi } from '../../../shared/services/api';
import { DataGrid, EmptyState, SkeletonLoader } from '../../../shared/components/DesignSystem';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Badge } from '../../../components/ui/badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../../components/ui/card';
import { Label } from '../../../components/ui/label';
import { Database, Plus, Search, HelpCircle, HardDrive, ShieldCheck, Info, Upload, Globe } from 'lucide-react';
import { toast } from 'sonner';

export default function KnowledgePage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);

  // Form states
  const [sourceName, setSourceName] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');

  // Query indexed sources
  const { data: sources = [], isLoading } = useQuery({
    queryKey: ['sources-list'],
    queryFn: () => knowledgeApi.listSources(),
  });

  // Import source mutation
  const importMutation = useMutation({
    mutationFn: (payload: any) => knowledgeApi.importSource(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources-list'] });
      setSourceName('');
      setSourceUrl('');
      toast.success('Source Imported', { description: 'Document indexing started in background task.' });
    },
  });

  // Semantic search mutation
  const searchMutation = useMutation({
    mutationFn: (query: string) => knowledgeApi.searchKnowledge(query),
    onSuccess: (data: any[]) => {
      setSearchResults(data);
      toast.success('Query Completed', { description: `Found ${data.length} relevant semantic chunks.` });
    },
  });

  const handleImportSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    importMutation.mutate({
      name: sourceName,
      source_type: 'url',
      config: { url: sourceUrl },
    });
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    searchMutation.mutate(searchQuery);
  };

  const sourceColumns = [
    { key: 'name', header: 'Document Name', render: (row: any) => <span className="font-semibold text-foreground">{row.name}</span> },
    { key: 'source_type', header: 'Type', render: (row: any) => <Badge variant="outline" className="capitalize border-border">{row.source_type}</Badge> },
    {
      key: 'status',
      header: 'Index status',
      render: (row: any) => (
        <Badge className="text-xs px-2 py-0.5 border bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
          {row.status || 'INDEXED'}
        </Badge>
      ),
    },
    { key: 'chunk_count', header: 'Chunks', render: (row: any) => <span>{row.chunk_count || 12} Chunks</span> },
    {
      key: 'created_at',
      header: 'Indexed date',
      render: (row: any) => (
        <span className="text-muted-foreground whitespace-nowrap text-xs">
          {row.created_at ? new Date(row.created_at).toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          }) : 'Just now'}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight">Knowledge Base</h2>
        <p className="text-xs text-muted-foreground mt-0.5 mb-4">
          Connect documents, project information and internal knowledge to give SyncSphere AI additional context.
        </p>
        <div className="bg-primary/10 border border-primary/20 text-primary/90 px-4 py-3 rounded-lg flex gap-3 text-sm items-start shadow-sm">
          <Info className="h-4 w-4 shrink-0 mt-0.5 text-primary" />
          <div className="flex flex-col gap-1">
            <span className="font-semibold text-primary">Prototype Mode:</span>
            <span className="opacity-90 leading-relaxed text-xs">
              This Knowledge Base currently contains demonstration documents for showcasing semantic search and AI context retrieval. In production, organizations can upload and index their own documents, websites, PDFs, API specifications, and internal knowledge.
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left pane: Index source list and Upload */}
        <div className="lg:col-span-2 space-y-6">
          {/* Index Source Form */}
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="text-base font-bold flex items-center gap-1.5">
                <Plus className="h-4 w-4 text-primary" /> Index Document Source
              </CardTitle>
              <CardDescription className="text-xs">Index websites, API specs, or guides into embeddings database.</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleImportSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label className="text-xs">Document Name</Label>
                  <Input
                    placeholder="SyncSphere Guide"
                    value={sourceName}
                    onChange={(e) => setSourceName(e.target.value)}
                    required
                    className="bg-card border-border placeholder-muted-foreground"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Documentation URL / Path</Label>
                  <Input
                    placeholder="https://docs.syncsphere.ai/intro"
                    value={sourceUrl}
                    onChange={(e) => setSourceUrl(e.target.value)}
                    required
                    className="bg-card border-border placeholder-muted-foreground"
                  />
                </div>
                <div className="sm:col-span-2 flex gap-3 mt-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => toast.info('Prototype Feature', { description: 'Document upload will be fully available in production.' })}
                    className="flex-1 border-dashed"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Upload Document
                  </Button>
                  <Button type="submit" disabled={importMutation.isPending} className="flex-1 bg-primary hover:bg-primary/95 text-primary-foreground shadow-sm">
                    <Globe className="w-4 h-4 mr-2" />
                    {importMutation.isPending ? 'Crawling...' : 'Index Website'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Sources List Grid */}
          <Card className="border-border bg-card">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold flex items-center gap-1.5">
                  <HardDrive className="h-4 w-4 text-primary" /> Vector Data Sources
                </CardTitle>
                <CardDescription className="text-xs">Document partitions indexed inside semantic cache.</CardDescription>
              </div>
              {sources.length === 0 && (
                <Badge variant="outline" className="text-amber-500 border-amber-500/20 bg-amber-500/10 gap-1.5 shadow-sm px-2.5 py-0.5">
                  <Info className="w-3 h-3" /> Demonstration Data
                </Badge>
              )}
            </CardHeader>
            <CardContent className="p-0">
              {isLoading ? (
                <div className="p-6"><SkeletonLoader rows={3} /></div>
              ) : (
                <DataGrid
                  columns={sourceColumns}
                  data={sources.length > 0 ? sources : [
                    { id: 'ex-1', name: 'Project Documentation', source_type: 'Documentation', status: 'READY', chunk_count: 24, created_at: new Date().toISOString() },
                    { id: 'ex-2', name: 'API Integration Guide', source_type: 'Reference', status: 'READY', chunk_count: 56, created_at: new Date().toISOString() },
                    { id: 'ex-3', name: 'Workflow Policies', source_type: 'Policy', status: 'READY', chunk_count: 12, created_at: new Date().toISOString() }
                  ]}
                  className="border-0 rounded-none border-t border-border/50 opacity-90 transition-opacity"
                />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right pane: Semantic Query Playground */}
        <div className="space-y-4">
          <Card className="border-border bg-card h-full flex flex-col">
            <CardHeader>
              <CardTitle className="text-base font-bold flex items-center gap-1.5">
                <Search className="h-4 w-4 text-primary" /> Semantic Query Sandbox
              </CardTitle>
              <CardDescription className="text-xs">Verify cosine vector similarity returns correct context chunks.</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col gap-4">
              <form onSubmit={handleSearchSubmit} className="flex gap-2">
                <Input
                  placeholder="Ask a question about the indexed documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  required
                  className="bg-card border-border placeholder-muted-foreground flex-1"
                />
                <Button type="submit" size="icon" disabled={searchMutation.isPending} className="bg-primary hover:bg-primary/95 text-primary-foreground shrink-0">
                  <Search className="h-4 w-4" />
                </Button>
              </form>

              <div className="flex-1 overflow-y-auto max-h-[350px] space-y-3">
                {searchMutation.isPending ? (
                  <SkeletonLoader rows={2} />
                ) : searchResults.length === 0 ? (
                  <div className="text-center py-12 text-xs text-muted-foreground flex flex-col items-center gap-2">
                    <HelpCircle className="h-8 w-8 text-muted-foreground/50" />
                    <span>Run similarity query to inspect results.</span>
                  </div>
                ) : (
                  searchResults.map((res, idx) => (
                    <div key={idx} className="border border-border bg-muted/20 p-3 rounded flex flex-col gap-1.5">
                      <div className="flex justify-between items-center text-[10px] text-muted-foreground">
                        <span>Chunk #{idx + 1}</span>
                        <Badge variant="outline" className="text-[9px] border-emerald-500/25 text-emerald-500 bg-emerald-500/5">
                          Score: {(res.score || 0.86).toFixed(2)}
                        </Badge>
                      </div>
                      <p className="text-[11px] text-foreground leading-normal whitespace-pre-wrap">{res.content || res.text}</p>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
