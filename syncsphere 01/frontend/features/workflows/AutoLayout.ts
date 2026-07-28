import { Node, Edge } from '@xyflow/react';
import { NodeConfig, topologicalSort } from '../../shared/stores/workflowBuilderStore';

// ==========================================
// Auto-Layout Algorithm (Hierarchical BFS)
// ==========================================
const HORIZONTAL_SPACING = 280;
const VERTICAL_SPACING = 120;

export function autoLayoutNodes(
  nodes: Node<NodeConfig>[],
  edges: Edge[],
  direction: 'LR' | 'TB' = 'LR'
): Node<NodeConfig>[] {
  if (nodes.length === 0) return nodes;

  // Build adjacency and reverse adjacency
  const adj: Record<string, string[]> = {};
  const inDegree: Record<string, number> = {};
  for (const node of nodes) {
    adj[node.id] = [];
    inDegree[node.id] = 0;
  }
  for (const edge of edges) {
    if (adj[edge.source]) adj[edge.source].push(edge.target);
    inDegree[edge.target] = (inDegree[edge.target] || 0) + 1;
  }

  // Assign layers using BFS (Kahn's algorithm)
  const layers: string[][] = [];
  const nodeLayer: Record<string, number> = {};
  const queue: string[] = [];

  for (const node of nodes) {
    if (inDegree[node.id] === 0) queue.push(node.id);
  }

  const visited = new Set<string>();
  let layerIdx = 0;

  while (queue.length > 0) {
    const currentBatch = [...queue];
    queue.length = 0;
    layers.push(currentBatch);

    for (const nodeId of currentBatch) {
      nodeLayer[nodeId] = layerIdx;
      visited.add(nodeId);
      for (const neighbor of (adj[nodeId] || [])) {
        inDegree[neighbor]--;
        if (inDegree[neighbor] === 0 && !visited.has(neighbor)) {
          queue.push(neighbor);
        }
      }
    }
    layerIdx++;
  }

  // Handle disconnected nodes (not reached by BFS)
  const disconnected = nodes.filter((n) => !visited.has(n.id));
  if (disconnected.length > 0) {
    layers.push(disconnected.map((n) => n.id));
    for (const dn of disconnected) {
      nodeLayer[dn.id] = layerIdx;
    }
  }

  // Assign positions based on layer and position within layer
  const positionMap: Record<string, { x: number; y: number }> = {};
  for (let i = 0; i < layers.length; i++) {
    const layer = layers[i];
    for (let j = 0; j < layer.length; j++) {
      if (direction === 'LR') {
        positionMap[layer[j]] = {
          x: 80 + i * HORIZONTAL_SPACING,
          y: 80 + j * VERTICAL_SPACING,
        };
      } else {
        positionMap[layer[j]] = {
          x: 80 + j * HORIZONTAL_SPACING,
          y: 80 + i * VERTICAL_SPACING,
        };
      }
    }
  }

  // Return new nodes with updated positions
  return nodes.map((node) => ({
    ...node,
    position: positionMap[node.id] || node.position,
  }));
}
