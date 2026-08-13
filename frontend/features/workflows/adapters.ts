import { Node, Edge } from '@xyflow/react';
import { NodeConfig, NodeStatus } from '../../shared/stores/workflowBuilderStore';
import { WorkflowNode, WorkflowEdge, ApprovalRequest } from '../../shared/types';

// ==========================================
// ReactFlow to SyncSphere Mapping
// ==========================================

export function mapReactFlowToSyncSphere(nodes: Node<NodeConfig>[], edges: Edge[]): { nodes: Record<string, any>, edges: any[] } {
    const backendNodes: Record<string, any> = {};

    for (const node of nodes) {
        const config = node.data.config || {};

        const backendNode: any = {
            id: node.id,
            name: node.data.label || node.data.nodeType,
            type: mapFrontendTypeToBackend(node.data.nodeType),

            position: node.position,
            data: node.data,

            retry_policy: config.retry_policy || { max_attempts: 3, backoff_factor: 2.0, initial_interval_seconds: 2 },
            timeout_policy: config.timeout_policy || { timeout_seconds: 300 },
            compensation_policy: config.compensation_policy || { compensation_node_id: null, parameters_mapping: {} },

            input_bindings: config.input_bindings || [],
            output_bindings: config.output_bindings || [],
        };

        // Domain Specific Mapping
        if (backendNode.type === 'tool_call') {
            backendNode.tool_invocation = {
                connector_binding: {
                    connector_id: config.connector_id || 'unknown',
                    scopes_override: config.scopes_override || []
                },
                tool_name: config.tool_name || node.data.nodeType,
                arguments_map: config.arguments_map || {}
            };
        } else if (backendNode.type === 'condition') {
            backendNode.condition = {
                left_operand: config.left_operand || "",
                operator: config.operator || "EQUAL",
                right_operand: config.right_operand ?? ""
            };
        } else if (backendNode.type === 'approval') {
            backendNode.approval_gate = {
                title: config.title || "Human Approval Required",
                description: config.description || "",
                instructions: config.instructions || "Please review carefully before proceeding.",
                approvers: config.approvers || ["admin@acme.ai"],
                timeout_hours: parseInt(config.timeout_hours || "24", 10) || 24,
                auto_approve: config.auto_approve === 'true' || config.auto_approve === true,
                auto_reject: config.auto_reject === undefined || config.auto_reject === 'true' || config.auto_reject === true,
                require_comment: config.require_comment === 'true' || config.require_comment === true,
                priority: config.priority || "high",
                category: config.category || "Auto-Generated",
                notification_channel: config.notification_channel || "dashboard"
            };
        } else if (backendNode.type === 'delay') {
            backendNode.delay_seconds = parseInt(config.duration_seconds || "0", 10) || 0;
        }

        backendNodes[node.id] = backendNode;
    }

    const backendEdges = edges.map((e) => ({
        id: e.id,
        source_node_id: e.source,
        target_node_id: e.target,
        source: e.source,
        target: e.target,
        type: e.type,
        sourceHandle: e.sourceHandle,
        animated: e.animated,
        condition_expression: e.sourceHandle === 'true' ? 'true' : e.sourceHandle === 'false' ? 'false' : null
    }));

    // But we need to save the visual geometry (x, y) so it loads back properly!
    // We can stuff it inside the `nodes` object somehow if the backend accepts extra fields,
    // or we leverage local storage / separate metadata field. 
    // Let's inject a UI_metadata block inside each node's output_bindings or just directly if backend is loose,
    // but Wait, Pydantic will drop EXTRA fields unless configured `extra = "allow"`.
    // Wait! The user just said: the python schema `WorkflowNode` does not have display x/y!
    // I will add a dictionary field `ui_metadata: dict = {}` to WorkflowNode if it's missing, let's just send it inside `config` or safely omit.
    // Wait! Actually, syncsphere/workflow/domain/value_objects.py does not have ui_metadata.

    return { nodes: backendNodes, edges: backendEdges };
}


// ==========================================
// SyncSphere to ReactFlow Mapping
// ==========================================

export function mapSyncSphereToReactFlow(backendNodes: Record<string, any> = {}, backendEdges: any[] = []): { nodes: Node<NodeConfig>[], edges: Edge[] } {
    const nodes: Node<NodeConfig>[] = [];

    let i = 0;
    for (const [id, bkNode] of Object.entries(backendNodes)) {
        // Generate some fallback positions since backend might not store them cleanly
        const x = 100 + (i * 200);
        const y = 200 + ((i % 3) * 100);
        i++;

        const config: Record<string, any> = {
            retry_policy: bkNode.retry_policy,
            timeout_policy: bkNode.timeout_policy,
            compensation_policy: bkNode.compensation_policy,
            input_bindings: bkNode.input_bindings,
            output_bindings: bkNode.output_bindings,
        };

        let logicalType = bkNode.type;

        if (bkNode.type === 'tool_call' && bkNode.tool_invocation) {
            logicalType = bkNode.tool_invocation.tool_name;
            config.connector_id = bkNode.tool_invocation.connector_binding?.connector_id;
            config.tool_name = bkNode.tool_invocation.tool_name;
            config.arguments_map = bkNode.tool_invocation.arguments_map;
        } else if (bkNode.type === 'condition' && bkNode.condition) {
            logicalType = 'condition';
            config.left_operand = bkNode.condition.left_operand;
            config.operator = bkNode.condition.operator;
            config.right_operand = bkNode.condition.right_operand;
        } else if (bkNode.type === 'approval' && bkNode.approval_gate) {
            logicalType = 'approval';
            Object.assign(config, bkNode.approval_gate);
        } else if (bkNode.type === 'delay') {
            logicalType = 'delay';
            config.duration_seconds = bkNode.delay_seconds;
        }

        nodes.push({
            id: id,
            type: getReactFlowType(logicalType),
            position: bkNode.position || { x, y },
            data: bkNode.data || {
                label: bkNode.name || id,
                nodeType: logicalType,
                status: 'idle',
                config: config
            }
        });
    }

    const edges: Edge[] = backendEdges.map((e, idx) => {
        const edge: Edge = {
            id: `e-${e.source_node_id}-${e.target_node_id}-${idx}`,
            source: e.source_node_id,
            target: e.target_node_id,
            animated: true,
            style: { strokeWidth: 2 }
        };
        if (e.condition_expression === 'true') edge.sourceHandle = 'true';
        if (e.condition_expression === 'false') edge.sourceHandle = 'false';
        return edge;
    });

    return { nodes, edges };
}

function mapFrontendTypeToBackend(nodeType: string): string {
    if (nodeType === 'condition') return 'condition';
    if (nodeType === 'approval') return 'approval';
    if (nodeType === 'delay') return 'delay';
    if (nodeType === 'transform') return 'transform';
    if (nodeType === 'start' || nodeType === 'end') return 'transform';
    return 'tool_call'; // e.g. slack.send_message
}

export function getReactFlowType(logicalType: string): string {
    const coreTypes = ['start', 'end', 'condition', 'approval', 'delay', 'webhook', 'http'];
    if (coreTypes.includes(logicalType)) return logicalType;
    if (logicalType.includes('.')) return 'connector'; // Maps to ReactFlow ConnectorNode component!
    return 'connector';
}
