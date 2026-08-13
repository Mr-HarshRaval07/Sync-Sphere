'use client';

import React, { useState, useCallback, useRef, useMemo, useEffect, DragEvent } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowApi, runtimeApi, automationApi } from '../../../shared/services/api';
import { WorkflowCard, EmptyState, SkeletonLoader } from '../../../shared/components/DesignSystem';
import { GitFork, Plus, ChevronLeft, Save, Play, Upload, Undo2, Redo2, Zap, History, Layout, Keyboard } from 'lucide-react';
import { toast } from 'sonner';

// React Flow
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  ReactFlowProvider,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// Module 12 — Workflow Builder Components
import { customNodeTypes, NODE_TYPE_REGISTRY } from '../../../features/workflows/CustomNodeRegistry';
import { NodePalette } from '../../../features/workflows/NodePalette';
import { PropertyEditor } from '../../../features/workflows/PropertyEditor';
import { ExecutionPreview } from '../../../features/workflows/ExecutionPreview';
import { WorkflowVersionHistory } from '../../../features/workflows/WorkflowVersioning';
import { WorkflowCommandPalette } from '../../../features/workflows/WorkflowCommandPalette';
import { useWorkflowKeyboardShortcuts, KEYBOARD_SHORTCUTS } from '../../../features/workflows/KeyboardShortcuts';
import { autoLayoutNodes } from '../../../features/workflows/AutoLayout';
import { WORKFLOW_TEMPLATES, WorkflowTemplate } from '../../../features/workflows/WorkflowTemplates';
import { mapReactFlowToSyncSphere, mapSyncSphereToReactFlow, getReactFlowType } from '../../../features/workflows/adapters';
import {
  useWorkflowBuilderStore,
  NodeConfig,
} from '../../../shared/stores/workflowBuilderStore';

import type { Node, Edge, Connection } from '@xyflow/react';

// ==========================================
// Autosave Hook
// ==========================================
function useAutosave() {
  const { nodes, edges, workflowId, workflowName, workflowDescription, workflowState } = useWorkflowBuilderStore();

  useEffect(() => {
    if (!workflowId) return;
    const timer = setTimeout(() => {
      try {
        const key = `syncsphere_wf_autosave_${workflowId}`;
        const data = { nodes, edges, workflowName, workflowDescription, workflowState, savedAt: new Date().toISOString() };
        localStorage.setItem(key, JSON.stringify(data));
      } catch { /* quota exceeded or SSR */ }
    }, 2000);
    return () => clearTimeout(timer);
  }, [nodes, edges, workflowId, workflowName, workflowDescription, workflowState]);
}

function loadAutosave(workflowId: string) {
  try {
    const key = `syncsphere_wf_autosave_${workflowId}`;
    const raw = localStorage.getItem(key);
    if (raw) return JSON.parse(raw);
  } catch { /* noop */ }
  return null;
}

// ==========================================
// Inner Builder Canvas (needs ReactFlow context)
// ==========================================
const WorkflowCanvas: React.FC = () => {
  const reactFlow = useReactFlow();
  const {
    nodes, edges, onNodesChange, onEdgesChange, onConnect, selectNode,
    addNode, setNodes, setEdges, saveSnapshot,
    isPaletteOpen, isPropertyEditorOpen, isPreviewOpen,
  } = useWorkflowBuilderStore();

  // Drop handler for palette drag-and-drop
  const onDragOver = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: DragEvent) => {
      event.preventDefault();
      const nodeType = event.dataTransfer.getData('application/syncsphere-node-type');
      if (!nodeType) return;

      const position = reactFlow.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const id = `${nodeType.replace('.', '_')}_${Date.now()}`;

      const configObj: any = {};
      if (nodeType.includes('.')) {
        configObj.connector_id = nodeType.split('.')[0];
        configObj.tool_name = nodeType;
        configObj.arguments_map = {};
      }

      const reg = NODE_TYPE_REGISTRY.find(n => n.type === nodeType);
      const label = reg ? reg.label : nodeType.charAt(0).toUpperCase() + nodeType.slice(1);
      const description = reg ? reg.description : '';

      const newNode: Node<NodeConfig> = {
        id,
        type: getReactFlowType(nodeType),
        position,
        data: {
          label,
          nodeType,
          description,
          status: 'idle',
          config: configObj,
        },
      };
      addNode(newNode);
    },
    [reactFlow, addNode]
  );

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      selectNode(node.id);
    },
    [selectNode]
  );

  const handlePaneClick = useCallback(() => {
    selectNode(null);
  }, [selectNode]);

  const handleConnect = useCallback(
    (connection: Connection) => {
      const success = onConnect(connection);
      if (!success) {
        toast.error('Invalid Connection', { description: 'This connection would create a cycle in the workflow graph.' });
      }
    },
    [onConnect]
  );

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={handleConnect}
      onNodeClick={handleNodeClick}
      onPaneClick={handlePaneClick}
      onDragOver={onDragOver}
      onDrop={onDrop}
      nodeTypes={customNodeTypes}
      fitView
      snapToGrid
      snapGrid={[16, 16]}
      colorMode="dark"
      defaultEdgeOptions={{
        animated: true,
        style: { strokeWidth: 2, stroke: 'var(--border)' },
      }}
      proOptions={{ hideAttribution: true }}
    >
      <Controls className="bg-card border border-border text-foreground [&>button]:border-border hover:[&>button]:bg-muted" />
      <MiniMap
        className="bg-card border border-border rounded shadow-lg [&>svg]:bg-card"
        nodeColor={(n) => {
          const data = n.data as NodeConfig;
          if (data?.status === 'running') return '#f59e0b';
          if (data?.status === 'success') return '#10b981';
          if (data?.status === 'failed') return '#f43f5e';
          return 'var(--muted-foreground)';
        }}
      />
      <Background color="var(--border)" gap={16} size={1} />

      {/* Active Prompt Overlay */}
      {useWorkflowBuilderStore.getState().activePromptContext && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-card/80 backdrop-blur border border-indigo-500/50 shadow-2xl shadow-indigo-500/10 p-4 rounded-xl z-50 w-full max-w-xl pointer-events-auto">
          <div className="flex justify-between items-center mb-1">
            <h4 className="text-xs font-black uppercase text-indigo-500 tracking-wider">Active Planner Prompt</h4>
            <button onClick={() => useWorkflowBuilderStore.getState().setActivePromptContext(null)} className="text-muted-foreground hover:text-foreground"><span className="text-[10px]">CLEAR</span></button>
          </div>
          <div className="text-sm italic font-serif text-foreground line-clamp-2">
            "{useWorkflowBuilderStore.getState().activePromptContext?.prompt}"
          </div>
        </div>
      )}
    </ReactFlow>
  );
};

// ==========================================
// Builder View (Full Workflow Builder)
// ==========================================
interface BuilderViewProps {
  workflowId: string;
  workflowName: string;
  onBack: () => void;
}

const BuilderView: React.FC<BuilderViewProps> = ({ workflowId, workflowName, onBack }) => {
  const {
    nodes, edges, workflowState, saveDraft, publishWorkflow,
    undo, redo, canUndo, canRedo, setNodes, setEdges,
    togglePreview, toggleVersionHistory,
    isPreviewOpen, isVersionHistoryOpen,
    setWorkflowName, setWorkflowDescription,
    setVersions,
  } = useWorkflowBuilderStore();

  const queryClient = useQueryClient();
  const [showShortcuts, setShowShortcuts] = useState(false);

  // Load versions
  const { data: versionsData } = useQuery({
    queryKey: ['workflow-versions', workflowId],
    queryFn: () => workflowApi.getWorkflowVersions(workflowId),
    enabled: !!workflowId && !workflowId.startsWith('temp_') && !workflowId.startsWith('local_'),
  });

  useEffect(() => {
    if (versionsData) {
      const mapped = versionsData.map((v: any) => ({
        version: v.version,
        state: v.state || 'DRAFT',
        createdAt: v.created_at || new Date().toISOString(),
        label: v.description || `v${v.version}`,
        nodes: v.nodes ? Object.values(v.nodes) : [],
        edges: v.edges || []
      }));
      setVersions(mapped);
    }
  }, [versionsData, setVersions]);

  // Keyboard shortcuts
  useWorkflowKeyboardShortcuts();

  // Autosave
  useAutosave();

  // Auto-layout
  const handleAutoLayout = useCallback(() => {
    const layouted = autoLayoutNodes(nodes, edges, 'LR');
    setNodes(layouted);
    toast.success('Auto Layout', { description: 'Nodes have been rearranged.' });
  }, [nodes, edges, setNodes]);

  // Save to API (Direct DAG Persistence)
  const saveMutation = useMutation({
    mutationFn: () => {
      const state = useWorkflowBuilderStore.getState();
      const mapped = mapReactFlowToSyncSphere(state.nodes, state.edges);
      const isDraft = state.workflowId?.startsWith('local_') || state.workflowId?.startsWith('draft_') || state.workflowId?.startsWith('wf_') || state.workflowId?.startsWith('temp_');

      if (isDraft) {
        return workflowApi.createWorkflow({
          name: state.workflowName,
          description: state.workflowDescription,
          nodes: mapped.nodes,
          edges: mapped.edges
        });
      }

      return workflowApi.updateWorkflow(state.workflowId!, {
        name: state.workflowName,
        nodes: mapped.nodes,
        edges: mapped.edges
      });
    },
    onSuccess: (data: any) => {
      saveDraft();
      if (data && data.id) {
        useWorkflowBuilderStore.setState({ workflowId: data.id });
        window.history.pushState(null, '', `?id=${data.id}`);
      }
      queryClient.invalidateQueries({ queryKey: ['workflow-versions', useWorkflowBuilderStore.getState().workflowId] });
      toast.success('Workflow Draft Saved', { description: 'Draft snapshot created successfully.' });
    },
    onError: (err: any) => {
      saveDraft();
      toast.info('Saved Locally', { description: err.response?.data?.error?.message || 'API sync failed.' });
    },
  });

  const publishMutation = useMutation({
    mutationFn: () => {
      const state = useWorkflowBuilderStore.getState();
      return workflowApi.publishWorkflow(state.workflowId!, { version_description: `Published version` });
    },
    onSuccess: () => {
      publishWorkflow();
      queryClient.invalidateQueries({ queryKey: ['workflow-versions', workflowId] });
      toast.success('Workflow Published', { description: 'A new published snapshot was created.' });
    },
    onError: (err: any) => {
      toast.error('Publish Failed', { description: err.response?.data?.error?.message || 'API sync failed.' });
    },
  });

  const handlePublish = useCallback(() => {
    publishMutation.mutate();
  }, [publishMutation]);

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)] bg-card border border-border rounded-lg overflow-hidden relative select-none">
      {/* Toolbar */}
      <div className="flex h-12 items-center justify-between border-b border-border bg-muted/30 px-3 shrink-0 gap-2">
        {/* Left: Navigation */}
        <div className="flex items-center gap-2 min-w-0">
          <button onClick={onBack} className="p-1.5 rounded-md hover:bg-muted transition-colors" aria-label="Back to list">
            <ChevronLeft className="h-4 w-4 text-muted-foreground" />
          </button>
          <div className="flex flex-col min-w-0">
            <input
              type="text"
              value={useWorkflowBuilderStore.getState().workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="font-bold text-sm text-foreground bg-transparent border-none outline-none truncate max-w-[200px]"
              aria-label="Workflow name"
            />
            <span className="text-[9px] text-muted-foreground">
              {workflowState} • {nodes.length} nodes • {edges.length} edges
            </span>
          </div>
        </div>

        {/* Center: Quick actions */}
        <div className="flex items-center gap-1">
          <button onClick={undo} disabled={!canUndo()} className="p-1.5 rounded-md hover:bg-muted disabled:opacity-30 transition-colors" title="Undo (Ctrl+Z)" aria-label="Undo">
            <Undo2 className="h-3.5 w-3.5 text-muted-foreground" />
          </button>
          <button onClick={redo} disabled={!canRedo()} className="p-1.5 rounded-md hover:bg-muted disabled:opacity-30 transition-colors" title="Redo (Ctrl+Shift+Z)" aria-label="Redo">
            <Redo2 className="h-3.5 w-3.5 text-muted-foreground" />
          </button>
          <div className="w-px h-5 bg-border mx-1" />
          <button onClick={handleAutoLayout} className="p-1.5 rounded-md hover:bg-muted transition-colors" title="Auto Layout" aria-label="Auto layout">
            <Layout className="h-3.5 w-3.5 text-muted-foreground" />
          </button>
          <button onClick={togglePreview} className={`p-1.5 rounded-md transition-colors ${isPreviewOpen ? 'bg-primary/10 text-primary' : 'hover:bg-muted text-muted-foreground'}`} title="Execution Preview (Ctrl+K)" aria-label="Toggle preview">
            <Zap className="h-3.5 w-3.5" />
          </button>
          <button onClick={toggleVersionHistory} className={`p-1.5 rounded-md transition-colors ${isVersionHistoryOpen ? 'bg-primary/10 text-primary' : 'hover:bg-muted text-muted-foreground'}`} title="Version History (Ctrl+H)" aria-label="Toggle version history">
            <History className="h-3.5 w-3.5" />
          </button>
          <button onClick={() => setShowShortcuts(!showShortcuts)} className="p-1.5 rounded-md hover:bg-muted transition-colors" title="Keyboard Shortcuts" aria-label="Show shortcuts">
            <Keyboard className="h-3.5 w-3.5 text-muted-foreground" />
          </button>
        </div>

        {/* Right: Save/Publish */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending}
            className="flex items-center gap-1.5 h-7 px-3 rounded-md text-xs font-medium border border-border hover:bg-muted text-foreground transition-colors disabled:opacity-50"
            aria-label="Save draft"
          >
            <Save className="h-3.5 w-3.5" />
            {saveMutation.isPending ? 'Saving...' : 'Save'}
          </button>
          <button
            onClick={() => publishMutation.mutate()}
            disabled={publishMutation.isPending}
            className="flex items-center gap-1.5 h-7 px-3 rounded-md text-xs font-bold bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
            aria-label="Publish workflow"
          >
            <Upload className="h-3.5 w-3.5" />
            {publishMutation.isPending ? 'Publishing...' : 'Publish'}
          </button>
        </div>
      </div>

      {/* Keyboard Shortcuts Tooltip */}
      {showShortcuts && (
        <div className="absolute right-3 top-14 z-30 bg-popover border border-border rounded-lg shadow-xl p-3 w-52">
          <h4 className="text-xs font-bold text-foreground mb-2">Keyboard Shortcuts</h4>
          <div className="space-y-1">
            {KEYBOARD_SHORTCUTS.map((s) => (
              <div key={s.keys} className="flex justify-between text-[10px]">
                <span className="text-muted-foreground">{s.description}</span>
                <kbd className="px-1 py-0.5 rounded bg-muted text-muted-foreground font-mono">{s.keys}</kbd>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left: Node Palette */}
        <NodePalette />

        {/* Center: React Flow Canvas */}
        <div className="flex-1 relative bg-muted/10">
          <ReactFlowProvider>
            <WorkflowCanvas />
          </ReactFlowProvider>

          {/* Overlays */}
          <ExecutionPreview />
          <WorkflowVersionHistory />
        </div>

        {/* Right: Property Editor */}
        <PropertyEditor />
      </div>

      {/* Command Palette (Ctrl+K) */}
      <WorkflowCommandPalette />
    </div>
  );
};

// ==========================================
// Template Selection Modal
// ==========================================
const TemplateSelector: React.FC<{
  templates: WorkflowTemplate[];
  onSelect: (template: WorkflowTemplate) => void;
  onClose: () => void;
}> = ({ templates, onSelect, onClose }) => {
  const [search, setSearch] = useState('');
  const filtered = useMemo(() => {
    if (!search) return templates;
    const lower = search.toLowerCase();
    return templates.filter(
      (t) => t.name.toLowerCase().includes(lower) || t.description.toLowerCase().includes(lower) || t.category.toLowerCase().includes(lower)
    );
  }, [search, templates]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-label="Select a template">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-card border border-border rounded-xl shadow-2xl w-full max-w-2xl max-h-[70vh] flex flex-col overflow-hidden">
        <div className="px-5 pt-4 pb-3 border-b border-border">
          <h2 className="text-lg font-bold text-foreground">Start from Template</h2>
          <p className="text-xs text-muted-foreground mt-0.5">Choose a pre-built workflow or start from scratch.</p>
          <div className="mt-3 relative">
            <input
              type="text"
              placeholder="Search templates..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full h-9 pl-9 pr-3 rounded-md border border-border bg-background text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <GitFork className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-4 grid grid-cols-1 sm:grid-cols-2 gap-3 scrollbar-thin">
          {/* Blank workflow */}
          <button
            onClick={() => onSelect({ id: 'blank', name: 'Untitled Workflow', description: 'Start from scratch with an empty canvas.', category: 'General', nodes: [], edges: [] })}
            className="text-left p-4 rounded-lg border-2 border-dashed border-border hover:border-primary/40 hover:bg-primary/5 transition-all"
          >
            <Plus className="h-6 w-6 text-muted-foreground mb-2" />
            <h3 className="text-sm font-bold text-foreground">Blank Workflow</h3>
            <p className="text-xs text-muted-foreground mt-1">Start with an empty canvas.</p>
          </button>

          {filtered.map((tpl) => (
            <button
              key={tpl.id}
              onClick={() => onSelect(tpl)}
              className="text-left p-4 rounded-lg border border-border hover:border-primary/40 hover:bg-primary/5 transition-all"
            >
              <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">{tpl.category}</span>
              <h3 className="text-sm font-bold text-foreground mt-1">{tpl.name}</h3>
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{tpl.description}</p>
              <span className="text-[10px] text-primary font-medium mt-2 inline-block">{tpl.nodes.length} nodes</span>
            </button>
          ))}
        </div>
        <div className="px-5 py-3 border-t border-border flex justify-end">
          <button onClick={onClose} className="h-8 px-4 rounded-md text-xs font-medium border border-border hover:bg-muted text-foreground transition-colors">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

import { useSearchParams, useRouter } from 'next/navigation';

// ==========================================
// Main Page Export
// ==========================================
export default function WorkflowsPage() {
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const router = useRouter();
  const [activeWorkflowId, setActiveWorkflowId] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isTemplateOpen, setIsTemplateOpen] = useState(false);

  const { initBuilder, resetBuilder } = useWorkflowBuilderStore();

  // Query workflows list
  const { data: workflows = [], isLoading } = useQuery({
    queryKey: ['workflows-list'],
    queryFn: () => workflowApi.listWorkflows(),
  });

  // Create workflow mutation
  const createMutation = useMutation({
    mutationFn: (payload: any) => workflowApi.createWorkflow({
      name: payload.name || 'New Workflow',
      description: payload.description || '',
      variables: []
    }),
    onSuccess: (data: any, variables: any) => {
      queryClient.invalidateQueries({ queryKey: ['workflows-list'] });
      toast.success('Workflow Created', { description: 'Opening workflow builder...' });
      const n = variables.nodes || [];
      const e = variables.edges || [];
      handleOpenBuilder(data.id || `local_${Date.now()}`, data.name || variables.name || 'New Workflow', variables.description || '', n, e, 'create');
    },
    onError: (err: any, variables: any) => {
      toast.error('Workflow Creation Failed', { description: err.response?.data?.error?.message || err?.message || 'Server error while generating workflow.' });
    },
  });

  // Execute workflow mutation (fallback placeholder since runtime execution needs distinct logic)
  const runMutation = useMutation({
    mutationFn: (workflowId: string) => runtimeApi.startExecution(workflowId, {}),
    onSuccess: (data) => {
      toast.success('Execution Started', {
        description: `Workflow test triggered successfully.`,
      });
    },
    onError: (err: any) => {
      toast.error('Execution Failed', { description: err.response?.data?.error?.message || 'Failed.' });
    },
  });

  const handleOpenBuilder = useCallback((id: string, name: string, description: string, nodes: Node<NodeConfig>[], edges: Edge[], mode: 'create' | 'edit' = 'edit') => {
    // Check for autosave first
    const autosaved = loadAutosave(id);
    if (autosaved && autosaved.nodes?.length > 0) {
      initBuilder(id, autosaved.workflowName || name, autosaved.workflowDescription || description, autosaved.nodes, autosaved.edges, autosaved.workflowState || 'DRAFT', mode);
      toast.info('Autosave Restored', { description: 'Loaded from your last session.' });
    } else {
      initBuilder(id, name, description, nodes, edges, 'DRAFT', mode);
    }
    setActiveWorkflowId(id);
  }, [initBuilder]);

  const handleSelectWorkflow = useCallback((workflowId: string) => {
    const wf = workflows.find((w: any) => w.id === workflowId);
    if (!wf) return;

    const mapped = mapSyncSphereToReactFlow(wf.nodes || {}, wf.edges || []);
    handleOpenBuilder(wf.id, wf.name, wf.description || '', mapped.nodes, mapped.edges, 'edit');
  }, [workflows, handleOpenBuilder]);

  // Handle ?import=true parameter
  useEffect(() => {
    const isImport = searchParams.get('import');
    const existingId = searchParams.get('id');

    if (existingId && !activeWorkflowId) {
      // Just immediately trigger the normal selection
      setTimeout(() => handleSelectWorkflow(existingId), 50);
      router.replace('/dashboard/workflows');
      return;
    }

    if (isImport === 'true' && !activeWorkflowId) {
      const raw = localStorage.getItem('syncsphere_wf_import');
      if (raw) {
        try {
          const wfData = JSON.parse(raw);
          // Set as active workflow locally without backend mutation
          const tempId = `draft_${Date.now()}`;
          handleOpenBuilder(
            tempId,
            wfData.workflowName || 'Imported Workflow',
            wfData.workflowDescription || '',
            wfData.nodes || [],
            wfData.edges || [],
            'create'
          );
          toast.info('Draft Loaded', { description: 'Review your duplicate before saving.' });
        } catch (e) {
          console.error("Failed to parse import", e);
        }
        localStorage.removeItem('syncsphere_wf_import');
      }
      // Clean up URL
      router.replace('/dashboard/workflows');
    }
  }, [searchParams, activeWorkflowId, router, handleOpenBuilder, handleSelectWorkflow]);

  const handleTemplateSelect = useCallback((template: WorkflowTemplate) => {
    setIsTemplateOpen(false);
    const tempId = `wf_${Date.now()}`;
    const templateNodes = template.nodes.map((n) => ({
      ...n,
      id: `${n.id}_${Date.now()}`,
    }));
    const templateEdges = template.edges.map((e, idx) => ({
      id: `te-${idx}`,
      source: `${e.source}_${Date.now()}`,
      target: `${e.target}_${Date.now()}`,
      animated: true,
      style: { strokeWidth: 2 },
    }));
    resetBuilder();

    // For template, ensure deep cloning to prevent mutating the global template arrays in memory
    const nodes = structuredClone(template.nodes) as Node<NodeConfig>[];
    const edges = structuredClone(template.edges).map((e: any, idx: number) => ({
      ...e,
      id: `te-${idx}-${Date.now()}`,
      animated: true,
      style: { strokeWidth: 2 },
    }));

    // Trigger API creation and let onSuccess mount the builder (prevents dual-mounting race condition)
    createMutation.mutate({ name: template.name, description: template.description, nodes, edges });
  }, [createMutation]);

  const handleBack = useCallback(() => {
    setActiveWorkflowId(null);
    resetBuilder();
  }, [resetBuilder]);

  // --- Builder Viewport ---
  if (activeWorkflowId) {
    return (
      <BuilderView
        workflowId={activeWorkflowId}
        workflowName={useWorkflowBuilderStore.getState().workflowName}
        onBack={handleBack}
      />
    );
  }

  // --- List Viewport ---
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight">Workflows</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Design and monitor multi-agent DAG pipelines orchestrating connected tools.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setIsTemplateOpen(true)}
            className="flex items-center gap-1.5 h-9 px-4 rounded-md text-xs font-medium border border-border hover:bg-muted text-foreground transition-colors"
          >
            <GitFork className="h-4 w-4" />
            From Template
          </button>
          <button
            onClick={() => {
              resetBuilder();
              createMutation.mutate({ name: 'Untitled Workflow', description: '', nodes: [], edges: [] });
            }}
            className="flex items-center gap-1.5 h-9 px-4 rounded-md text-xs font-bold bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            New Workflow
          </button>
        </div>
      </div>

      {isLoading ? (
        <SkeletonLoader rows={4} />
      ) : workflows.length === 0 ? (
        <EmptyState
          title="No Workflows Found"
          description="Create customized workflow channels containing parallel execution steps and AI nodes."
          icon={<GitFork className="h-10 w-10 text-muted-foreground" />}
          actionLabel="Build First Workflow"
          onAction={() => {
            resetBuilder();
            createMutation.mutate({ name: 'Untitled Workflow', description: '', nodes: [], edges: [] });
          }}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {workflows.map((wf: any) => (
            <WorkflowCard
              key={wf.id}
              workflow={wf}
              onSelect={handleSelectWorkflow}
              onRun={(id: string) => runMutation.mutate(id)}
            />
          ))}
        </div>
      )}

      {/* Template Selection Modal */}
      {isTemplateOpen && (
        <TemplateSelector
          templates={WORKFLOW_TEMPLATES}
          onSelect={handleTemplateSelect}
          onClose={() => setIsTemplateOpen(false)}
        />
      )}
    </div>
  );
}
