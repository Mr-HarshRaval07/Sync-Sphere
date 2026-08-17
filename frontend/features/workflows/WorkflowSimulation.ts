import { Node, Edge } from '@xyflow/react';
import { NodeConfig, SimulationResult, topologicalSort } from '../../shared/stores/workflowBuilderStore';

// ==========================================
// Node Type Cost & Latency Estimates
// ==========================================
const NODE_LATENCY_ESTIMATES: Record<string, number> = {
  start: 5,
  end: 5,
  planner: 3500,
  ai: 2200,
  connector: 800,
  approval: 0, // Human dependent, not estimated
  condition: 10,
  loop: 15,
  delay: 0, // Uses configured duration
  http: 1200,
  webhook: 50,
};

const NODE_TOKEN_ESTIMATES: Record<string, number> = {
  planner: 4500,
  ai: 2000,
};

const COST_PER_1K_TOKENS = 0.008; // Average blended cost

// ==========================================
// Simulation Engine
// ==========================================
export function simulateWorkflow(
  nodes: Node<NodeConfig>[],
  edges: Edge[]
): SimulationResult {
  // 1. Compute execution order via topological sort
  const executionOrder = topologicalSort(nodes, edges);
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));

  // 2. Simulate each node in order
  const nodeResults: Record<string, { output: any; latencyMs: number; status: string }> = {};
  let totalLatencyMs = 0;
  let totalTokens = 0;
  const requiredConnectors: string[] = [];
  const approvalGates: string[] = [];

  for (const nodeId of executionOrder) {
    const node = nodeMap.get(nodeId);
    if (!node) continue;
    const nodeType = node.data.nodeType;

    // Calculate latency
    let latency = NODE_LATENCY_ESTIMATES[nodeType] || 100;
    if (nodeType === 'delay') {
      latency = (node.data.config?.duration_seconds || 0) * 1000;
    }

    // Calculate tokens
    const tokens = NODE_TOKEN_ESTIMATES[nodeType] || 0;
    totalTokens += tokens;
    totalLatencyMs += latency;

    // Track connectors
    if ((nodeType === 'connector' || nodeType.includes('.')) && node.data.config?.connector_id) {
      const connName = node.data.config.connector_id;
      if (!requiredConnectors.includes(connName)) {
        requiredConnectors.push(connName);
      }
    }

    // Track approval gates
    if (nodeType === 'approval') {
      approvalGates.push(node.data.label || node.id);
    }

    // Generate simulated output
    const simulatedOutput = generateSimulatedOutput(nodeType, node.data);

    nodeResults[nodeId] = {
      output: simulatedOutput,
      latencyMs: latency,
      status: node.data.status === 'disabled' ? 'skipped' : 'success',
    };
  }

  const estimatedCost = (totalTokens / 1000) * COST_PER_1K_TOKENS;

  return {
    executionOrder,
    nodeResults,
    totalLatencyMs,
    totalTokens,
    estimatedCost,
    requiredConnectors,
    approvalGates,
  };
}

// ==========================================
// Simulated Output Generator
// ==========================================
function generateSimulatedOutput(nodeType: string, data: NodeConfig): any {
  switch (nodeType) {
    case 'start':
      return { triggered: true, timestamp: new Date().toISOString() };
    case 'end':
      return { completed: true, timestamp: new Date().toISOString() };
    case 'planner':
      return {
        plan: {
          steps: ['Analyze input', 'Select tools', 'Execute actions', 'Compile results'],
          strategy: data.config?.strategy || 'chain_of_thought',
        },
      };
    case 'ai':
      return {
        completion: 'Simulated AI response based on prompt template.',
        tokens_used: 2000,
        model: data.config?.model_id || 'gpt-4o',
      };
    case nodeType !== 'connector' && nodeType.includes('.') ? nodeType : 'connector':
      return {
        tool_result: {
          is_error: false,
          content: `Simulated response from connector "${data.config?.connector_id || 'unknown'}" tool "${data.config?.tool_name || nodeType}"`,
        },
      };
    case 'approval':
      return {
        decision: 'approved',
        supervisor: 'sim-user@syncsphere.ai',
        notes: 'Auto-approved in simulation mode.',
      };
    case 'condition':
      return {
        evaluated: true,
        branch: 'true',
        expression: data.config?.expression || 'true',
      };
    case 'loop':
      return {
        iterations: 3,
        collection: data.config?.collection_variable || '[]',
        completed: true,
      };
    case 'delay':
      return {
        waited_seconds: data.config?.duration_seconds || 0,
        resumed: true,
      };
    case 'http':
      return {
        status_code: 200,
        body: { message: 'Simulated HTTP response' },
        url: data.config?.url || 'https://api.example.com',
      };
    case 'webhook':
      return {
        received: true,
        path: data.config?.path || '/webhook',
        payload: { event: 'simulated_trigger' },
      };
    default:
      return { status: 'executed' };
  }
}

// ==========================================
// Execution Summary Helpers
// ==========================================
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

export function formatCost(cost: number): string {
  return `$${cost.toFixed(4)}`;
}
