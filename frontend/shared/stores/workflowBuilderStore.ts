import { create } from 'zustand';
import { Node, Edge, NodeChange, EdgeChange, applyNodeChanges, applyEdgeChanges, Connection, addEdge } from '@xyflow/react';

// ==========================================
// Types
// ==========================================

export type NodeStatus = 'idle' | 'configured' | 'running' | 'success' | 'failed' | 'waiting' | 'approval_required' | 'disabled';

export type WorkflowState = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';

export interface NodeConfig {
  label: string;
  nodeType: string;
  description?: string;
  status: NodeStatus;
  config: Record<string, any>;
  parameterMappings?: Record<string, string>; // targetField -> sourceExpression (e.g. "{{nodes.slack_1.output.message}}")
  isTemplate?: boolean;
  templateName?: string;
  requires_approval?: boolean;
  [key: string]: any;
}

export interface WorkflowVersion {
  version: number;
  nodes: Node<NodeConfig>[];
  edges: Edge[];
  createdAt: string;
  label?: string;
  state: WorkflowState;
}

export interface SimulationResult {
  executionOrder: string[];
  nodeResults: Record<string, { output: any; latencyMs: number; status: string }>;
  totalLatencyMs: number;
  totalTokens: number;
  estimatedCost: number;
  requiredConnectors: string[];
  approvalGates: string[];
}

export interface ValidationMessage {
  nodeId?: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  code: string;
}

export interface NodeTemplate {
  id: string;
  name: string;
  nodeType: string;
  config: Record<string, any>;
  description: string;
  createdAt: string;
}

// ==========================================
// History State
// ==========================================
interface HistoryEntry {
  nodes: Node<NodeConfig>[];
  edges: Edge[];
}

// ==========================================
// Main Store Interface
// ==========================================
interface WorkflowBuilderState {
  // Canvas state
  nodes: Node<NodeConfig>[];
  edges: Edge[];
  selectedNodeId: string | null;

  // Workflow metadata
  workflowId: string | null;
  workflowName: string;
  workflowDescription: string;
  workflowState: WorkflowState;

  // Versioning
  versions: WorkflowVersion[];
  activeVersion: number;

  // Execution Mode Context
  builderMode: 'create' | 'edit';

  // History (undo/redo)
  historyStack: HistoryEntry[];
  historyIndex: number;
  maxHistory: number;

  // Clipboard
  copyBuffer: Node<NodeConfig> | null;

  // Node templates
  nodeTemplates: NodeTemplate[];

  // Simulation
  simulationResult: SimulationResult | null;
  isSimulating: boolean;

  // Validation
  validationMessages: ValidationMessage[];

  // UI state
  isPaletteOpen: boolean;
  isPropertyEditorOpen: boolean;
  isPreviewOpen: boolean;
  isVersionHistoryOpen: boolean;

  // Actions - Canvas
  initBuilder: (workflowId: string, name: string, description: string, nodes: Node<NodeConfig>[], edges: Edge[], state: WorkflowState, mode?: 'create' | 'edit') => void;
  resetBuilder: () => void;
  addNode: (node: Node<NodeConfig>) => void;
  updateNodeConfig: (nodeId: string, config: Partial<NodeConfig>) => void;
  updateNodeStatus: (nodeId: string, status: NodeStatus) => void;
  deleteNode: (nodeId: string) => void;
  selectNode: (nodeId: string | null) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => boolean;
  setNodes: (nodes: Node<NodeConfig>[]) => void;
  setEdges: (edges: Edge[]) => void;

  // Actions - History
  saveSnapshot: () => void;
  undo: () => void;
  redo: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;

  // Actions - Clipboard
  copyNode: (nodeId: string) => void;
  pasteNode: () => void;
  duplicateNode: (nodeId: string) => void;

  // Actions - Versioning
  saveDraft: () => void;
  publishWorkflow: () => void;
  rollbackToVersion: (version: number) => void;
  addVersion: (v: WorkflowVersion) => void;
  setVersions: (versions: WorkflowVersion[]) => void;
  setActiveVersion: (v: number) => void;

  // Actions - Templates
  saveNodeAsTemplate: (nodeId: string, templateName: string) => void;
  loadNodeTemplate: (templateId: string, position: { x: number; y: number }) => void;
  deleteNodeTemplate: (templateId: string) => void;

  // Actions - Simulation
  setSimulationResult: (result: SimulationResult | null) => void;
  setIsSimulating: (v: boolean) => void;

  // Actions - Validation
  setValidationMessages: (msgs: ValidationMessage[]) => void;

  // Actions - UI
  togglePalette: () => void;
  togglePropertyEditor: () => void;
  togglePreview: () => void;
  toggleVersionHistory: () => void;
  setWorkflowName: (name: string) => void;
  setWorkflowDescription: (desc: string) => void;

  // Global Prompt Context
  activePromptContext: any;
  setActivePromptContext: (prompt: any) => void;
}

// ==========================================
// Store Implementation
// ==========================================
export const useWorkflowBuilderStore = create<WorkflowBuilderState>((set, get) => ({
  // Initial state
  nodes: [],
  edges: [],
  selectedNodeId: null,
  workflowId: null,
  workflowName: 'Untitled Workflow',
  workflowDescription: '',
  workflowState: 'DRAFT',
  builderMode: 'create' as const,
  versions: [],
  activeVersion: 0,
  historyStack: [],
  historyIndex: -1,
  maxHistory: 50,
  copyBuffer: null,
  nodeTemplates: [],
  simulationResult: null,
  isSimulating: false,
  validationMessages: [],
  isPaletteOpen: true,
  isPropertyEditorOpen: true,
  isPreviewOpen: false,
  isVersionHistoryOpen: false,
  activePromptContext: null,

  // --- Canvas Actions ---
  initBuilder: (workflowId, name, description, nodes, edges, state, mode = 'edit') => {
    set({
      workflowId,
      workflowName: name,
      workflowDescription: description,
      builderMode: mode,
      nodes,
      edges,
      workflowState: state,
      selectedNodeId: null,
      historyStack: [{ nodes: structuredClone(nodes), edges: structuredClone(edges) }],
      historyIndex: 0,
      simulationResult: null,
      validationMessages: [],
    });
  },

  resetBuilder: () => {
    set({
      nodes: [],
      edges: [],
      selectedNodeId: null,
      workflowId: null,
      workflowName: 'Untitled Workflow',
      workflowDescription: '',
      workflowState: 'DRAFT',
      builderMode: 'create',
      versions: [],
      activeVersion: 0,
      historyStack: [],
      historyIndex: -1,
      copyBuffer: null,
      nodeTemplates: [],
      simulationResult: null,
      validationMessages: [],
    });
  },

  addNode: (node) => {
    get().saveSnapshot();
    set((s) => ({ nodes: [...s.nodes, node] }));
  },

  updateNodeConfig: (nodeId, config) => {
    get().saveSnapshot();
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === nodeId ? { ...n, data: { ...n.data, ...config } } : n
      ),
    }));
  },

  updateNodeStatus: (nodeId, status) => {
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === nodeId ? { ...n, data: { ...n.data, status } } : n
      ),
    }));
  },

  deleteNode: (nodeId) => {
    get().saveSnapshot();
    set((s) => ({
      nodes: s.nodes.filter((n) => n.id !== nodeId),
      edges: s.edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
      selectedNodeId: s.selectedNodeId === nodeId ? null : s.selectedNodeId,
    }));
  },

  selectNode: (nodeId) => set({ selectedNodeId: nodeId }),

  onNodesChange: (changes) => {
    set((s) => ({ nodes: applyNodeChanges(changes, s.nodes) as Node<NodeConfig>[] }));
  },

  onEdgesChange: (changes) => {
    set((s) => ({ edges: applyEdgeChanges(changes, s.edges) }));
  },

  onConnect: (connection) => {
    const state = get();
    // Cycle detection before adding edge
    if (wouldCreateCycle(state.nodes, state.edges, connection)) {
      return false;
    }
    get().saveSnapshot();
    set((s) => ({
      edges: addEdge({ ...connection, animated: true, style: { strokeWidth: 2 } }, s.edges),
    }));
    return true;
  },

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  // --- History Actions ---
  saveSnapshot: () => {
    const { nodes, edges, historyStack, historyIndex, maxHistory } = get();
    const entry: HistoryEntry = {
      nodes: structuredClone(nodes),
      edges: structuredClone(edges),
    };
    // Truncate future states when we branch
    const truncated = historyStack.slice(0, historyIndex + 1);
    const newStack = [...truncated, entry].slice(-maxHistory);
    set({
      historyStack: newStack,
      historyIndex: newStack.length - 1,
    });
  },

  undo: () => {
    const { historyIndex, historyStack } = get();
    if (historyIndex <= 0) return;
    const newIndex = historyIndex - 1;
    const entry = historyStack[newIndex];
    set({
      nodes: structuredClone(entry.nodes),
      edges: structuredClone(entry.edges),
      historyIndex: newIndex,
    });
  },

  redo: () => {
    const { historyIndex, historyStack } = get();
    if (historyIndex >= historyStack.length - 1) return;
    const newIndex = historyIndex + 1;
    const entry = historyStack[newIndex];
    set({
      nodes: structuredClone(entry.nodes),
      edges: structuredClone(entry.edges),
      historyIndex: newIndex,
    });
  },

  canUndo: () => get().historyIndex > 0,
  canRedo: () => get().historyIndex < get().historyStack.length - 1,

  // --- Clipboard Actions ---
  copyNode: (nodeId) => {
    const node = get().nodes.find((n) => n.id === nodeId);
    if (node) set({ copyBuffer: structuredClone(node) });
  },

  pasteNode: () => {
    const { copyBuffer } = get();
    if (!copyBuffer) return;
    const id = `${copyBuffer.data.nodeType}_${Date.now()}`;
    const newNode: Node<NodeConfig> = {
      ...structuredClone(copyBuffer),
      id,
      position: {
        x: copyBuffer.position.x + 40,
        y: copyBuffer.position.y + 40,
      },
    };
    get().addNode(newNode);
  },

  duplicateNode: (nodeId) => {
    get().copyNode(nodeId);
    get().pasteNode();
  },

  // --- Versioning Actions ---
  saveDraft: () => {
    const s = get();
    const nextVerNum = (s.versions.length > 0 ? Math.max(...s.versions.map((v) => v.version)) : 0) + 1;
    const newVer: WorkflowVersion = {
      version: nextVerNum,
      nodes: structuredClone(s.nodes),
      edges: structuredClone(s.edges),
      createdAt: new Date().toISOString(),
      label: `Draft v${nextVerNum}`,
      state: 'DRAFT',
    };
    set({
      workflowState: 'DRAFT',
      versions: [...s.versions, newVer],
      activeVersion: nextVerNum,
    });
  },

  publishWorkflow: () => {
    const s = get();
    const nextVerNum = (s.versions.length > 0 ? Math.max(...s.versions.map((v) => v.version)) : 0) + 1;
    const newVer: WorkflowVersion = {
      version: nextVerNum,
      nodes: structuredClone(s.nodes),
      edges: structuredClone(s.edges),
      createdAt: new Date().toISOString(),
      label: `Published v${nextVerNum}`,
      state: 'PUBLISHED',
    };
    set({
      workflowState: 'PUBLISHED',
      versions: [...s.versions, newVer],
      activeVersion: nextVerNum,
    });
  },

  rollbackToVersion: (version) => {
    const v = get().versions.find((ver) => ver.version === version);
    if (!v) return;
    get().saveSnapshot();
    set({
      nodes: structuredClone(v.nodes),
      edges: structuredClone(v.edges),
      workflowState: 'DRAFT', // Rollback always returns to draft
    });
  },

  addVersion: (v) => set((s) => ({ versions: [...s.versions, v] })),
  setVersions: (versions) => set({ versions, activeVersion: versions.length > 0 ? Math.max(...versions.map(v => v.version)) : 0 }),
  setActiveVersion: (activeVersion) => set({ activeVersion }),

  // --- Template Actions ---
  saveNodeAsTemplate: (nodeId, templateName) => {
    const node = get().nodes.find((n) => n.id === nodeId);
    if (!node) return;
    const tpl: NodeTemplate = {
      id: `tpl_${Date.now()}`,
      name: templateName,
      nodeType: node.data.nodeType,
      config: structuredClone(node.data.config),
      description: node.data.description || '',
      createdAt: new Date().toISOString(),
    };
    set((s) => ({ nodeTemplates: [...s.nodeTemplates, tpl] }));
  },

  loadNodeTemplate: (templateId, position) => {
    const tpl = get().nodeTemplates.find((t) => t.id === templateId);
    if (!tpl) return;
    const id = `${tpl.nodeType}_${Date.now()}`;
    const node: Node<NodeConfig> = {
      id,
      type: tpl.nodeType,
      position,
      data: {
        label: tpl.name,
        nodeType: tpl.nodeType,
        description: tpl.description,
        status: 'configured' as NodeStatus,
        config: structuredClone(tpl.config),
        isTemplate: true,
        templateName: tpl.name,
      },
    };
    get().addNode(node);
  },

  deleteNodeTemplate: (templateId) => {
    set((s) => ({ nodeTemplates: s.nodeTemplates.filter((t) => t.id !== templateId) }));
  },

  // --- Simulation Actions ---
  setSimulationResult: (result) => set({ simulationResult: result }),
  setIsSimulating: (v) => set({ isSimulating: v }),

  // --- Validation Actions ---
  setValidationMessages: (msgs) => set({ validationMessages: msgs }),

  // --- UI Actions ---
  togglePalette: () => set((s) => ({ isPaletteOpen: !s.isPaletteOpen })),
  togglePropertyEditor: () => set((s) => ({ isPropertyEditorOpen: !s.isPropertyEditorOpen })),
  togglePreview: () => set((s) => ({ isPreviewOpen: !s.isPreviewOpen })),
  toggleVersionHistory: () => set((s) => ({ isVersionHistoryOpen: !s.isVersionHistoryOpen })),
  setWorkflowName: (name) => set({ workflowName: name }),
  setWorkflowDescription: (desc) => set({ workflowDescription: desc }),
  setActivePromptContext: (prompt) => set({ activePromptContext: prompt }),
}));

// ==========================================
// Cycle Detection (DFS)
// ==========================================
export function wouldCreateCycle(
  nodes: Node[],
  edges: Edge[],
  newConnection: Connection
): boolean {
  if (!newConnection.source || !newConnection.target) return false;
  if (newConnection.source === newConnection.target) return true;

  // Build adjacency list including the proposed edge
  const adj: Record<string, string[]> = {};
  for (const node of nodes) {
    adj[node.id] = [];
  }
  for (const edge of edges) {
    if (!adj[edge.source]) adj[edge.source] = [];
    adj[edge.source].push(edge.target);
  }
  if (!adj[newConnection.source]) adj[newConnection.source] = [];
  adj[newConnection.source].push(newConnection.target);

  // DFS from target to see if we can reach source
  const visited = new Set<string>();
  const stack = [newConnection.target];
  while (stack.length > 0) {
    const current = stack.pop()!;
    if (current === newConnection.source) return true;
    if (visited.has(current)) continue;
    visited.add(current);
    for (const neighbor of (adj[current] || [])) {
      stack.push(neighbor);
    }
  }
  return false;
}

// ==========================================
// Topological Sort (Kahn's Algorithm)
// ==========================================
export function topologicalSort(nodes: Node[], edges: Edge[]): string[] {
  const inDegree: Record<string, number> = {};
  const adj: Record<string, string[]> = {};

  for (const node of nodes) {
    inDegree[node.id] = 0;
    adj[node.id] = [];
  }
  for (const edge of edges) {
    adj[edge.source].push(edge.target);
    inDegree[edge.target] = (inDegree[edge.target] || 0) + 1;
  }

  const queue: string[] = [];
  for (const id of Object.keys(inDegree)) {
    if (inDegree[id] === 0) queue.push(id);
  }

  const order: string[] = [];
  while (queue.length > 0) {
    const current = queue.shift()!;
    order.push(current);
    for (const neighbor of adj[current]) {
      inDegree[neighbor]--;
      if (inDegree[neighbor] === 0) queue.push(neighbor);
    }
  }
  return order;
}
