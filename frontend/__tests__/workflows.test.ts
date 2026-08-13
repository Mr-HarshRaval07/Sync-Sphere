// ==========================================
// Module 12 — Visual Workflow Builder Tests
// ==========================================

// Mock structuredClone for JSDOM
if (typeof structuredClone === 'undefined') {
  (global as any).structuredClone = <T>(obj: T): T => JSON.parse(JSON.stringify(obj));
}

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value.toString(); },
    clear: () => { store = {}; },
    removeItem: (key: string) => { delete store[key]; },
  };
})();
Object.defineProperty(global, 'localStorage', { value: localStorageMock });

// Mock window/document
Object.defineProperty(global, 'window', {
  value: {
    document: {
      documentElement: {
        classList: { add: jest.fn(), remove: jest.fn() },
        style: { colorScheme: '' },
      },
    },
    localStorage: localStorageMock,
  },
  writable: true,
});

import {
  useWorkflowBuilderStore,
  wouldCreateCycle,
  topologicalSort,
  NodeConfig,
} from '../shared/stores/workflowBuilderStore';

import { validateWorkflow, hasErrors, getErrorCount, getWarningCount } from '../features/workflows/WorkflowValidation';
import { autoLayoutNodes } from '../features/workflows/AutoLayout';
import { simulateWorkflow, formatDuration, formatCost } from '../features/workflows/WorkflowSimulation';
import { WORKFLOW_TEMPLATES } from '../features/workflows/WorkflowTemplates';
import { KEYBOARD_SHORTCUTS } from '../features/workflows/KeyboardShortcuts';
import type { Node, Edge } from '@xyflow/react';

// ==========================================
// Helper: Create test nodes
// ==========================================
function makeNode(id: string, type: string, label: string, config: Record<string, any> = {}, status: string = 'idle'): Node<NodeConfig> {
  return {
    id,
    type,
    position: { x: 0, y: 0 },
    data: {
      label,
      nodeType: type,
      description: '',
      status: status as any,
      config,
    },
  };
}

function makeEdge(source: string, target: string, id?: string): Edge {
  return { id: id || `${source}-${target}`, source, target };
}

// ==========================================
// 1. Workflow Builder Store Tests
// ==========================================
describe('WorkflowBuilderStore', () => {
  beforeEach(() => {
    useWorkflowBuilderStore.getState().resetBuilder();
  });

  test('initializes with default values', () => {
    const state = useWorkflowBuilderStore.getState();
    expect(state.nodes).toEqual([]);
    expect(state.edges).toEqual([]);
    expect(state.selectedNodeId).toBeNull();
    expect(state.workflowName).toBe('Untitled Workflow');
    expect(state.workflowState).toBe('DRAFT');
    expect(state.versions).toEqual([]);
  });

  test('initBuilder sets workflow state', () => {
    const nodes = [makeNode('s1', 'start', 'Start')];
    const edges: Edge[] = [];
    useWorkflowBuilderStore.getState().initBuilder('wf-1', 'Test Flow', 'A test', nodes, edges, 'DRAFT');

    const state = useWorkflowBuilderStore.getState();
    expect(state.workflowId).toBe('wf-1');
    expect(state.workflowName).toBe('Test Flow');
    expect(state.nodes).toHaveLength(1);
    expect(state.historyStack).toHaveLength(1);
    expect(state.historyIndex).toBe(0);
  });

  test('addNode appends a node and records history', () => {
    const store = useWorkflowBuilderStore.getState();
    store.initBuilder('wf-1', 'Test', '', [], [], 'DRAFT');

    store.addNode(makeNode('s1', 'start', 'Start'));
    expect(useWorkflowBuilderStore.getState().nodes).toHaveLength(1);

    store.addNode(makeNode('e1', 'end', 'End'));
    expect(useWorkflowBuilderStore.getState().nodes).toHaveLength(2);
  });

  test('deleteNode removes node and connected edges', () => {
    const store = useWorkflowBuilderStore.getState();
    const nodes = [makeNode('s1', 'start', 'Start'), makeNode('a1', 'ai', 'AI'), makeNode('e1', 'end', 'End')];
    const edges = [makeEdge('s1', 'a1'), makeEdge('a1', 'e1')];
    store.initBuilder('wf-1', 'Test', '', nodes, edges, 'DRAFT');

    store.deleteNode('a1');
    const state = useWorkflowBuilderStore.getState();
    expect(state.nodes).toHaveLength(2);
    expect(state.edges).toHaveLength(0); // Both edges connected to a1 should be removed
  });

  test('selectNode updates selection', () => {
    const store = useWorkflowBuilderStore.getState();
    store.initBuilder('wf-1', 'Test', '', [makeNode('s1', 'start', 'Start')], [], 'DRAFT');

    store.selectNode('s1');
    expect(useWorkflowBuilderStore.getState().selectedNodeId).toBe('s1');

    store.selectNode(null);
    expect(useWorkflowBuilderStore.getState().selectedNodeId).toBeNull();
  });

  test('updateNodeConfig updates node data', () => {
    const store = useWorkflowBuilderStore.getState();
    store.initBuilder('wf-1', 'Test', '', [makeNode('a1', 'ai', 'AI')], [], 'DRAFT');

    store.updateNodeConfig('a1', { label: 'Updated AI' } as any);
    const node = useWorkflowBuilderStore.getState().nodes.find((n) => n.id === 'a1');
    expect(node?.data.label).toBe('Updated AI');
  });

  test('updateNodeStatus changes node status', () => {
    const store = useWorkflowBuilderStore.getState();
    store.initBuilder('wf-1', 'Test', '', [makeNode('a1', 'ai', 'AI')], [], 'DRAFT');

    store.updateNodeStatus('a1', 'running');
    const node = useWorkflowBuilderStore.getState().nodes.find((n) => n.id === 'a1');
    expect(node?.data.status).toBe('running');
  });

  // --- Undo/Redo ---
  test('undo restores previous state', () => {
    const store = useWorkflowBuilderStore.getState();
    store.initBuilder('wf-1', 'Test', '', [makeNode('s1', 'start', 'Start')], [], 'DRAFT');

    store.addNode(makeNode('a1', 'ai', 'AI'));
    expect(useWorkflowBuilderStore.getState().nodes).toHaveLength(2);

    store.undo();
    expect(useWorkflowBuilderStore.getState().nodes).toHaveLength(1);
  });

  test('redo restores undone state', () => {
    const store = useWorkflowBuilderStore.getState();
    store.initBuilder('wf-1', 'Test', '', [makeNode('s1', 'start', 'Start')], [], 'DRAFT');

    // addNode calls saveSnapshot (pre-state) then adds node
    store.addNode(makeNode('a1', 'ai', 'AI'));
    // Manually snapshot *after* add so redo has a target
    useWorkflowBuilderStore.getState().saveSnapshot();
    expect(useWorkflowBuilderStore.getState().nodes).toHaveLength(2);

    useWorkflowBuilderStore.getState().undo();
    expect(useWorkflowBuilderStore.getState().nodes).toHaveLength(1);

    useWorkflowBuilderStore.getState().redo();
    expect(useWorkflowBuilderStore.getState().nodes).toHaveLength(2);
  });

  test('canUndo and canRedo reflect stack position', () => {
    const store = useWorkflowBuilderStore.getState();
    store.initBuilder('wf-1', 'Test', '', [], [], 'DRAFT');

    expect(store.canUndo()).toBe(false);
    expect(store.canRedo()).toBe(false);

    store.addNode(makeNode('s1', 'start', 'Start'));
    expect(useWorkflowBuilderStore.getState().canUndo()).toBe(true);
    expect(useWorkflowBuilderStore.getState().canRedo()).toBe(false);

    useWorkflowBuilderStore.getState().undo();
    expect(useWorkflowBuilderStore.getState().canRedo()).toBe(true);
  });

  // --- Clipboard ---
  test('copyNode and pasteNode duplicates a node with offset', () => {
    const store = useWorkflowBuilderStore.getState();
    const node = makeNode('a1', 'ai', 'AI', { model_id: 'gpt-4o' });
    node.position = { x: 100, y: 200 };
    store.initBuilder('wf-1', 'Test', '', [node], [], 'DRAFT');

    store.copyNode('a1');
    expect(useWorkflowBuilderStore.getState().copyBuffer).not.toBeNull();

    store.pasteNode();
    const nodes = useWorkflowBuilderStore.getState().nodes;
    expect(nodes).toHaveLength(2);
    expect(nodes[1].position.x).toBe(140); // +40 offset
    expect(nodes[1].position.y).toBe(240); // +40 offset
    expect(nodes[1].data.config.model_id).toBe('gpt-4o');
  });

  test('duplicateNode creates a copy of the selected node', () => {
    const store = useWorkflowBuilderStore.getState();
    store.initBuilder('wf-1', 'Test', '', [makeNode('a1', 'ai', 'AI')], [], 'DRAFT');

    store.duplicateNode('a1');
    expect(useWorkflowBuilderStore.getState().nodes).toHaveLength(2);
  });

  // --- Versioning ---
  test('saveDraft creates a new version', () => {
    const store = useWorkflowBuilderStore.getState();
    store.initBuilder('wf-1', 'Test', '', [makeNode('s1', 'start', 'Start')], [], 'DRAFT');

    store.saveDraft();
    const state = useWorkflowBuilderStore.getState();
    expect(state.versions).toHaveLength(1);
    expect(state.versions[0].state).toBe('DRAFT');
    expect(state.activeVersion).toBe(1);
  });

  test('publishWorkflow creates a PUBLISHED version', () => {
    const store = useWorkflowBuilderStore.getState();
    store.initBuilder('wf-1', 'Test', '', [makeNode('s1', 'start', 'Start')], [], 'DRAFT');

    store.publishWorkflow();
    const state = useWorkflowBuilderStore.getState();
    expect(state.versions).toHaveLength(1);
    expect(state.versions[0].state).toBe('PUBLISHED');
    expect(state.workflowState).toBe('PUBLISHED');
  });

  test('rollbackToVersion restores a previous version', () => {
    const store = useWorkflowBuilderStore.getState();
    store.initBuilder('wf-1', 'Test', '', [makeNode('s1', 'start', 'Start')], [], 'DRAFT');

    // Save v1
    store.saveDraft();
    // Add node and save v2
    store.addNode(makeNode('a1', 'ai', 'AI'));
    store.saveDraft();
    expect(useWorkflowBuilderStore.getState().nodes).toHaveLength(2);

    // Rollback to v1
    store.rollbackToVersion(1);
    expect(useWorkflowBuilderStore.getState().nodes).toHaveLength(1);
    expect(useWorkflowBuilderStore.getState().workflowState).toBe('DRAFT');
  });

  // --- Node Templates ---
  test('saveNodeAsTemplate and loadNodeTemplate', () => {
    const store = useWorkflowBuilderStore.getState();
    const node = makeNode('a1', 'ai', 'My AI Node', { model_id: 'gpt-4o', temperature: 0.7 });
    store.initBuilder('wf-1', 'Test', '', [node], [], 'DRAFT');

    store.saveNodeAsTemplate('a1', 'GPT-4o Template');
    expect(useWorkflowBuilderStore.getState().nodeTemplates).toHaveLength(1);

    const tpl = useWorkflowBuilderStore.getState().nodeTemplates[0];
    store.loadNodeTemplate(tpl.id, { x: 500, y: 300 });
    expect(useWorkflowBuilderStore.getState().nodes).toHaveLength(2);
    const loaded = useWorkflowBuilderStore.getState().nodes[1];
    expect(loaded.data.config.model_id).toBe('gpt-4o');
    expect(loaded.data.isTemplate).toBe(true);
  });

  test('deleteNodeTemplate removes template', () => {
    useWorkflowBuilderStore.getState().initBuilder('wf-1', 'Test', '', [makeNode('a1', 'ai', 'AI')], [], 'DRAFT');
    useWorkflowBuilderStore.getState().saveNodeAsTemplate('a1', 'Template 1');
    expect(useWorkflowBuilderStore.getState().nodeTemplates).toHaveLength(1);
    const tplId = useWorkflowBuilderStore.getState().nodeTemplates[0].id;
    useWorkflowBuilderStore.getState().deleteNodeTemplate(tplId);
    expect(useWorkflowBuilderStore.getState().nodeTemplates).toHaveLength(0);
  });

  // --- UI Toggles ---
  test('togglePalette/togglePropertyEditor/togglePreview/toggleVersionHistory', () => {
    const store = useWorkflowBuilderStore.getState();
    expect(store.isPaletteOpen).toBe(true);
    store.togglePalette();
    expect(useWorkflowBuilderStore.getState().isPaletteOpen).toBe(false);

    expect(useWorkflowBuilderStore.getState().isPropertyEditorOpen).toBe(true);
    useWorkflowBuilderStore.getState().togglePropertyEditor();
    expect(useWorkflowBuilderStore.getState().isPropertyEditorOpen).toBe(false);

    expect(useWorkflowBuilderStore.getState().isPreviewOpen).toBe(false);
    useWorkflowBuilderStore.getState().togglePreview();
    expect(useWorkflowBuilderStore.getState().isPreviewOpen).toBe(true);

    expect(useWorkflowBuilderStore.getState().isVersionHistoryOpen).toBe(false);
    useWorkflowBuilderStore.getState().toggleVersionHistory();
    expect(useWorkflowBuilderStore.getState().isVersionHistoryOpen).toBe(true);
  });
});

// ==========================================
// 2. Cycle Detection Tests
// ==========================================
describe('Cycle Detection (DFS)', () => {
  test('detects self-loop', () => {
    const nodes = [makeNode('a', 'ai', 'A')];
    const edges: Edge[] = [];
    expect(wouldCreateCycle(nodes, edges, { source: 'a', target: 'a', sourceHandle: null, targetHandle: null })).toBe(true);
  });

  test('detects simple cycle: A→B→A', () => {
    const nodes = [makeNode('a', 'ai', 'A'), makeNode('b', 'ai', 'B')];
    const edges = [makeEdge('a', 'b')];
    expect(wouldCreateCycle(nodes, edges, { source: 'b', target: 'a', sourceHandle: null, targetHandle: null })).toBe(true);
  });

  test('detects transitive cycle: A→B→C→A', () => {
    const nodes = [makeNode('a', 'ai', 'A'), makeNode('b', 'ai', 'B'), makeNode('c', 'ai', 'C')];
    const edges = [makeEdge('a', 'b'), makeEdge('b', 'c')];
    expect(wouldCreateCycle(nodes, edges, { source: 'c', target: 'a', sourceHandle: null, targetHandle: null })).toBe(true);
  });

  test('allows valid DAG connections', () => {
    const nodes = [makeNode('a', 'ai', 'A'), makeNode('b', 'ai', 'B'), makeNode('c', 'ai', 'C')];
    const edges = [makeEdge('a', 'b')];
    expect(wouldCreateCycle(nodes, edges, { source: 'b', target: 'c', sourceHandle: null, targetHandle: null })).toBe(false);
  });

  test('allows convergent DAG (diamond pattern)', () => {
    const nodes = [
      makeNode('a', 'start', 'A'),
      makeNode('b', 'ai', 'B'),
      makeNode('c', 'ai', 'C'),
      makeNode('d', 'end', 'D'),
    ];
    const edges = [makeEdge('a', 'b'), makeEdge('a', 'c'), makeEdge('b', 'd')];
    // C→D should be fine (diamond pattern)
    expect(wouldCreateCycle(nodes, edges, { source: 'c', target: 'd', sourceHandle: null, targetHandle: null })).toBe(false);
  });
});

// ==========================================
// 3. Topological Sort Tests
// ==========================================
describe('Topological Sort', () => {
  test('sorts linear chain', () => {
    const nodes = [makeNode('a', 'start', 'A'), makeNode('b', 'ai', 'B'), makeNode('c', 'end', 'C')];
    const edges = [makeEdge('a', 'b'), makeEdge('b', 'c')];
    const order = topologicalSort(nodes, edges);
    expect(order).toEqual(['a', 'b', 'c']);
  });

  test('handles diamond DAG', () => {
    const nodes = [
      makeNode('a', 'start', 'A'),
      makeNode('b', 'ai', 'B'),
      makeNode('c', 'ai', 'C'),
      makeNode('d', 'end', 'D'),
    ];
    const edges = [makeEdge('a', 'b'), makeEdge('a', 'c'), makeEdge('b', 'd'), makeEdge('c', 'd')];
    const order = topologicalSort(nodes, edges);
    expect(order[0]).toBe('a');
    expect(order[order.length - 1]).toBe('d');
    expect(order).toHaveLength(4);
  });

  test('handles disconnected nodes', () => {
    const nodes = [makeNode('a', 'start', 'A'), makeNode('b', 'ai', 'B')];
    const edges: Edge[] = [];
    const order = topologicalSort(nodes, edges);
    expect(order).toHaveLength(2);
  });
});

// ==========================================
// 4. Validation Engine Tests
// ==========================================
describe('Workflow Validation Engine', () => {
  test('returns EMPTY_WORKFLOW for empty graph', () => {
    const messages = validateWorkflow([], []);
    expect(hasErrors(messages)).toBe(true);
    expect(messages[0].code).toBe('EMPTY_WORKFLOW');
  });

  test('detects MISSING_START', () => {
    const nodes = [makeNode('e1', 'end', 'End')];
    const messages = validateWorkflow(nodes, []);
    expect(messages.some((m) => m.code === 'MISSING_START')).toBe(true);
  });

  test('detects MISSING_END', () => {
    const nodes = [makeNode('s1', 'start', 'Start')];
    const messages = validateWorkflow(nodes, []);
    expect(messages.some((m) => m.code === 'MISSING_END')).toBe(true);
  });

  test('detects DUPLICATE_START', () => {
    const nodes = [
      makeNode('s1', 'start', 'Start'),
      makeNode('s2', 'start', 'Start 2'),
      makeNode('e1', 'end', 'End'),
    ];
    const messages = validateWorkflow(nodes, []);
    expect(messages.some((m) => m.code === 'DUPLICATE_START')).toBe(true);
  });

  test('detects DISCONNECTED_NODE', () => {
    const nodes = [
      makeNode('s1', 'start', 'Start'),
      makeNode('a1', 'ai', 'AI'),
      makeNode('e1', 'end', 'End'),
    ];
    const edges = [makeEdge('s1', 'e1')];
    const messages = validateWorkflow(nodes, edges);
    expect(messages.some((m) => m.code === 'DISCONNECTED_NODE' && m.nodeId === 'a1')).toBe(true);
  });

  test('detects MISSING_CONFIG for AI node', () => {
    const nodes = [
      makeNode('s1', 'start', 'Start'),
      makeNode('a1', 'ai', 'AI', {}),
      makeNode('e1', 'end', 'End'),
    ];
    const edges = [makeEdge('s1', 'a1'), makeEdge('a1', 'e1')];
    const messages = validateWorkflow(nodes, edges);
    expect(messages.some((m) => m.code === 'MISSING_CONFIG' && m.nodeId === 'a1')).toBe(true);
  });

  test('detects CONNECTOR_UNAVAILABLE', () => {
    const nodes = [
      makeNode('s1', 'start', 'Start'),
      makeNode('c1', 'connector', 'Connector', {}),
      makeNode('e1', 'end', 'End'),
    ];
    const edges = [makeEdge('s1', 'c1'), makeEdge('c1', 'e1')];
    const messages = validateWorkflow(nodes, edges);
    expect(messages.some((m) => m.code === 'CONNECTOR_UNAVAILABLE')).toBe(true);
  });

  test('detects CONDITION_INCOMPLETE (less than 2 outgoing edges)', () => {
    const nodes = [
      makeNode('s1', 'start', 'Start'),
      makeNode('cond1', 'condition', 'Condition', { expression: 'x > 5' }),
      makeNode('e1', 'end', 'End'),
    ];
    const edges = [makeEdge('s1', 'cond1'), makeEdge('cond1', 'e1')];
    const messages = validateWorkflow(nodes, edges);
    expect(messages.some((m) => m.code === 'CONDITION_INCOMPLETE')).toBe(true);
  });

  test('reports NODE_DISABLED info messages', () => {
    const nodes = [
      makeNode('s1', 'start', 'Start'),
      makeNode('a1', 'ai', 'AI', { model_id: 'gpt-4o', prompt_template_id: 'p1' }, 'disabled'),
      makeNode('e1', 'end', 'End'),
    ];
    const edges = [makeEdge('s1', 'a1'), makeEdge('a1', 'e1')];
    const messages = validateWorkflow(nodes, edges);
    expect(messages.some((m) => m.code === 'NODE_DISABLED')).toBe(true);
  });

  test('passes validation for valid workflow', () => {
    const nodes = [
      makeNode('s1', 'start', 'Start'),
      makeNode('a1', 'ai', 'AI', { model_id: 'gpt-4o', prompt_template_id: 'p1' }),
      makeNode('e1', 'end', 'End'),
    ];
    const edges = [makeEdge('s1', 'a1'), makeEdge('a1', 'e1')];
    const messages = validateWorkflow(nodes, edges);
    expect(getErrorCount(messages)).toBe(0);
  });

  test('getErrorCount and getWarningCount return correct counts', () => {
    const nodes = [
      makeNode('s1', 'start', 'Start'),
      makeNode('a1', 'ai', 'AI', {}), // missing config
      makeNode('a2', 'ai', 'AI2', { model_id: 'x', prompt_template_id: 'y' }),
      makeNode('e1', 'end', 'End'),
    ];
    const edges = [makeEdge('s1', 'a1'), makeEdge('a1', 'e1')]; // a2 disconnected
    const messages = validateWorkflow(nodes, edges);
    expect(getErrorCount(messages)).toBeGreaterThan(0);
    expect(getWarningCount(messages)).toBeGreaterThan(0);
  });
});

// ==========================================
// 5. Auto Layout Tests
// ==========================================
describe('Auto Layout Algorithm', () => {
  test('positions nodes in hierarchical layers', () => {
    const nodes = [
      makeNode('s1', 'start', 'Start'),
      makeNode('a1', 'ai', 'AI'),
      makeNode('e1', 'end', 'End'),
    ];
    const edges = [makeEdge('s1', 'a1'), makeEdge('a1', 'e1')];
    const result = autoLayoutNodes(nodes, edges, 'LR');
    expect(result).toHaveLength(3);
    // Start should be leftmost
    expect(result.find((n) => n.id === 's1')!.position.x).toBeLessThan(
      result.find((n) => n.id === 'a1')!.position.x
    );
    // AI should be before End
    expect(result.find((n) => n.id === 'a1')!.position.x).toBeLessThan(
      result.find((n) => n.id === 'e1')!.position.x
    );
  });

  test('handles empty graph', () => {
    expect(autoLayoutNodes([], [])).toEqual([]);
  });

  test('handles disconnected nodes', () => {
    const nodes = [makeNode('a', 'ai', 'A'), makeNode('b', 'ai', 'B')];
    const result = autoLayoutNodes(nodes, []);
    expect(result).toHaveLength(2);
  });

  test('supports TB direction', () => {
    const nodes = [makeNode('s1', 'start', 'Start'), makeNode('e1', 'end', 'End')];
    const edges = [makeEdge('s1', 'e1')];
    const result = autoLayoutNodes(nodes, edges, 'TB');
    expect(result.find((n) => n.id === 's1')!.position.y).toBeLessThan(
      result.find((n) => n.id === 'e1')!.position.y
    );
  });
});

// ==========================================
// 6. Simulation Engine Tests
// ==========================================
describe('Workflow Simulation Engine', () => {
  test('simulates a simple workflow', () => {
    const nodes = [
      makeNode('s1', 'start', 'Start'),
      makeNode('a1', 'ai', 'AI', { model_id: 'gpt-4o' }),
      makeNode('e1', 'end', 'End'),
    ];
    const edges = [makeEdge('s1', 'a1'), makeEdge('a1', 'e1')];
    const result = simulateWorkflow(nodes, edges);

    expect(result.executionOrder).toEqual(['s1', 'a1', 'e1']);
    expect(result.totalLatencyMs).toBeGreaterThan(0);
    expect(result.totalTokens).toBeGreaterThan(0);
    expect(result.estimatedCost).toBeGreaterThan(0);
    expect(result.nodeResults['s1'].status).toBe('success');
    expect(result.nodeResults['a1'].output.model).toBe('gpt-4o');
  });

  test('tracks required connectors', () => {
    const nodes = [
      makeNode('s1', 'start', 'Start'),
      makeNode('c1', 'connector', 'Slack', { connector_id: 'slack', tool_name: 'post' }),
      makeNode('e1', 'end', 'End'),
    ];
    const edges = [makeEdge('s1', 'c1'), makeEdge('c1', 'e1')];
    const result = simulateWorkflow(nodes, edges);
    expect(result.requiredConnectors).toContain('slack');
  });

  test('tracks approval gates', () => {
    const nodes = [
      makeNode('s1', 'start', 'Start'),
      makeNode('ap1', 'approval', 'Manager Approval', { routing_strategy: 'Sequential' }),
      makeNode('e1', 'end', 'End'),
    ];
    const edges = [makeEdge('s1', 'ap1'), makeEdge('ap1', 'e1')];
    const result = simulateWorkflow(nodes, edges);
    expect(result.approvalGates).toContain('Manager Approval');
  });

  test('handles delay node with configured duration', () => {
    const nodes = [
      makeNode('s1', 'start', 'Start'),
      makeNode('d1', 'delay', 'Wait', { duration_seconds: 30 }),
      makeNode('e1', 'end', 'End'),
    ];
    const edges = [makeEdge('s1', 'd1'), makeEdge('d1', 'e1')];
    const result = simulateWorkflow(nodes, edges);
    expect(result.nodeResults['d1'].latencyMs).toBe(30000);
  });

  test('marks disabled nodes as skipped', () => {
    const nodes = [
      makeNode('s1', 'start', 'Start'),
      makeNode('a1', 'ai', 'AI', {}, 'disabled'),
      makeNode('e1', 'end', 'End'),
    ];
    const edges = [makeEdge('s1', 'a1'), makeEdge('a1', 'e1')];
    const result = simulateWorkflow(nodes, edges);
    expect(result.nodeResults['a1'].status).toBe('skipped');
  });
});

// ==========================================
// 7. Format Helpers Tests
// ==========================================
describe('Format Helpers', () => {
  test('formatDuration handles ms, seconds, minutes', () => {
    expect(formatDuration(500)).toBe('500ms');
    expect(formatDuration(2500)).toBe('2.5s');
    expect(formatDuration(90000)).toBe('1.5m');
  });

  test('formatCost formats to 4 decimal places', () => {
    expect(formatCost(0.0123)).toBe('$0.0123');
    expect(formatCost(0)).toBe('$0.0000');
  });
});

// ==========================================
// 8. Workflow Templates Tests
// ==========================================
describe('Workflow Templates', () => {
  test('provides starter templates', () => {
    expect(WORKFLOW_TEMPLATES.length).toBeGreaterThanOrEqual(4);
  });

  test('each template has required fields', () => {
    for (const tpl of WORKFLOW_TEMPLATES) {
      expect(tpl.id).toBeTruthy();
      expect(tpl.name).toBeTruthy();
      expect(tpl.description).toBeTruthy();
      expect(tpl.category).toBeTruthy();
      expect(tpl.nodes.length).toBeGreaterThan(0);
      expect(tpl.edges.length).toBeGreaterThan(0);
    }
  });

  test('Bug Triage template has correct structure', () => {
    const bugTriage = WORKFLOW_TEMPLATES.find((t) => t.id === 'tpl-bug-triage');
    expect(bugTriage).toBeDefined();
    expect(bugTriage!.nodes.some((n) => n.data.nodeType === 'start')).toBe(true);
    expect(bugTriage!.nodes.some((n) => n.data.nodeType === 'end')).toBe(true);
    expect(bugTriage!.nodes.some((n) => n.data.nodeType === 'ai')).toBe(true);
    expect(bugTriage!.nodes.some((n) => n.data.nodeType === 'condition')).toBe(true);
  });

  test('Incident Response template has approval gate', () => {
    const incident = WORKFLOW_TEMPLATES.find((t) => t.id === 'tpl-incident-response');
    expect(incident).toBeDefined();
    expect(incident!.nodes.some((n) => n.data.nodeType === 'approval')).toBe(true);
  });
});

// ==========================================
// 9. Keyboard Shortcuts Tests
// ==========================================
describe('Keyboard Shortcuts Reference', () => {
  test('defines all required shortcuts', () => {
    const keys = KEYBOARD_SHORTCUTS.map((s) => s.keys);
    expect(keys).toContain('Ctrl+Z');
    expect(keys).toContain('Ctrl+Shift+Z');
    expect(keys).toContain('Ctrl+C');
    expect(keys).toContain('Ctrl+V');
    expect(keys).toContain('Ctrl+D');
    expect(keys).toContain('Ctrl+S');
    expect(keys).toContain('Delete');
  });
});
