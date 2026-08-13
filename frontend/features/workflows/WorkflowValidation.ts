import { Node, Edge } from '@xyflow/react';
import { NodeConfig, ValidationMessage, topologicalSort } from '../../shared/stores/workflowBuilderStore';

// ==========================================
// Node Type Definitions & Required Fields
// ==========================================
const NODE_REQUIRED_FIELDS: Record<string, string[]> = {
  start: [],
  end: [],
  planner: ['prompt', 'strategy'],
  ai: ['model_id', 'prompt_template_id'],
  connector: ['connector_id', 'tool_name'],
  approval: ['routing_strategy'],
  condition: ['expression'],
  loop: ['collection_variable', 'iterator_variable'],
  delay: ['duration_seconds'],
  http: ['url', 'method'],
  webhook: ['path'],
};

// ==========================================
// Validation Engine
// ==========================================
export function validateWorkflow(
  nodes: Node<NodeConfig>[],
  edges: Edge[]
): ValidationMessage[] {
  const messages: ValidationMessage[] = [];

  // 1. Check empty workflow
  if (nodes.length === 0) {
    messages.push({
      severity: 'error',
      message: 'Workflow is empty. Add at least a Start and End node.',
      code: 'EMPTY_WORKFLOW',
    });
    return messages;
  }

  // 2. Check for Start node
  const startNodes = nodes.filter((n) => n.data.nodeType === 'start');
  if (startNodes.length === 0) {
    messages.push({
      severity: 'error',
      message: 'Missing Start node. Every workflow must have exactly one Start node.',
      code: 'MISSING_START',
    });
  } else if (startNodes.length > 1) {
    messages.push({
      severity: 'error',
      message: `Found ${startNodes.length} Start nodes. Only one Start node is allowed.`,
      code: 'DUPLICATE_START',
    });
  }

  // 3. Check for End node
  const endNodes = nodes.filter((n) => n.data.nodeType === 'end');
  if (endNodes.length === 0) {
    messages.push({
      severity: 'error',
      message: 'Missing End node. Every workflow must have at least one End node.',
      code: 'MISSING_END',
    });
  }

  // 4. Check for duplicate node IDs
  const idSet = new Set<string>();
  for (const node of nodes) {
    if (idSet.has(node.id)) {
      messages.push({
        nodeId: node.id,
        severity: 'error',
        message: `Duplicate node ID detected: "${node.id}".`,
        code: 'DUPLICATE_ID',
      });
    }
    idSet.add(node.id);
  }

  // 5. Check for disconnected nodes
  const connectedIds = new Set<string>();
  for (const edge of edges) {
    connectedIds.add(edge.source);
    connectedIds.add(edge.target);
  }
  for (const node of nodes) {
    if (!connectedIds.has(node.id) && nodes.length > 1) {
      messages.push({
        nodeId: node.id,
        severity: 'warning',
        message: `Node "${node.data.label}" is disconnected from the workflow graph.`,
        code: 'DISCONNECTED_NODE',
      });
    }
  }

  // 6. Check for missing required configuration
  for (const node of nodes) {
    const requiredFields = NODE_REQUIRED_FIELDS[node.data.nodeType] || [];
    for (const field of requiredFields) {
      const value = node.data.config?.[field];
      if (value === undefined || value === null || value === '') {
        messages.push({
          nodeId: node.id,
          severity: 'error',
          message: `Node "${node.data.label}" is missing required field: "${field}".`,
          code: 'MISSING_CONFIG',
        });
      }
    }
  }

  // 7. Cycle detection (excluding explicit Loop nodes)
  const nonLoopEdges = edges.filter((e) => {
    const sourceNode = nodes.find((n) => n.id === e.source);
    return sourceNode?.data.nodeType !== 'loop';
  });
  const sortResult = topologicalSort(nodes, nonLoopEdges);
  if (sortResult.length < nodes.length) {
    messages.push({
      severity: 'error',
      message: 'Invalid cycle detected in the workflow graph (excluding loop constructs).',
      code: 'INVALID_CYCLE',
    });
  }

  // 8. Check connector availability
  const connectorNodes = nodes.filter((n) => n.data.nodeType === 'connector' || n.data.nodeType.includes('.'));
  for (const cn of connectorNodes) {
    if (!cn.data.config?.connector_id) {
      messages.push({
        nodeId: cn.id,
        severity: 'error',
        message: `Connector node "${cn.data.label}" has no connector assigned.`,
        code: 'CONNECTOR_UNAVAILABLE',
      });
    }
  }

  // 9. Check AI model availability
  const aiNodes = nodes.filter((n) => n.data.nodeType === 'ai');
  for (const ai of aiNodes) {
    if (!ai.data.config?.model_id) {
      messages.push({
        nodeId: ai.id,
        severity: 'error',
        message: `AI node "${ai.data.label}" has no model assigned.`,
        code: 'MODEL_UNAVAILABLE',
      });
    }
  }

  // 10. Check approval policy availability
  const approvalNodes = nodes.filter((n) => n.data.nodeType === 'approval');
  for (const ap of approvalNodes) {
    if (!ap.data.config?.routing_strategy) {
      messages.push({
        nodeId: ap.id,
        severity: 'error',
        message: `Approval node "${ap.data.label}" has no routing strategy configured.`,
        code: 'APPROVAL_POLICY_MISSING',
      });
    }
  }

  // 11. Condition node must have at least two outgoing edges
  const conditionNodes = nodes.filter((n) => n.data.nodeType === 'condition');
  for (const cond of conditionNodes) {
    const outgoing = edges.filter((e) => e.source === cond.id);
    if (outgoing.length < 2) {
      messages.push({
        nodeId: cond.id,
        severity: 'warning',
        message: `Condition node "${cond.data.label}" should have at least 2 outgoing paths (true/false).`,
        code: 'CONDITION_INCOMPLETE',
      });
    }
  }

  // 12. Start node should have no incoming edges
  for (const start of startNodes) {
    const incoming = edges.filter((e) => e.target === start.id);
    if (incoming.length > 0) {
      messages.push({
        nodeId: start.id,
        severity: 'warning',
        message: 'Start node should not have incoming connections.',
        code: 'START_HAS_INCOMING',
      });
    }
  }

  // 13. End node should have no outgoing edges
  for (const end of endNodes) {
    const outgoing = edges.filter((e) => e.source === end.id);
    if (outgoing.length > 0) {
      messages.push({
        nodeId: end.id,
        severity: 'warning',
        message: 'End node should not have outgoing connections.',
        code: 'END_HAS_OUTGOING',
      });
    }
  }

  // 14. Disabled node warning
  const disabledNodes = nodes.filter((n) => n.data.status === 'disabled');
  for (const dn of disabledNodes) {
    messages.push({
      nodeId: dn.id,
      severity: 'info',
      message: `Node "${dn.data.label}" is disabled and will be skipped during execution.`,
      code: 'NODE_DISABLED',
    });
  }

  return messages;
}

// ==========================================
// Validation Summary Helpers
// ==========================================
export function hasErrors(messages: ValidationMessage[]): boolean {
  return messages.some((m) => m.severity === 'error');
}

export function getErrorCount(messages: ValidationMessage[]): number {
  return messages.filter((m) => m.severity === 'error').length;
}

export function getWarningCount(messages: ValidationMessage[]): number {
  return messages.filter((m) => m.severity === 'warning').length;
}
