'use client';

import React, { useMemo } from 'react';
import { useWorkflowBuilderStore, NodeConfig, NodeStatus } from '../../shared/stores/workflowBuilderStore';
import { getNodeTypeInfo } from './CustomNodeRegistry';
import {
  X, Settings, Tag, FileText, Link2, Trash2, Copy, Star,
  ToggleLeft, ToggleRight, ChevronDown, Variable, Shield,
} from 'lucide-react';

// ==========================================
// Config Field Definitions per Node Type
// ==========================================
interface FieldDef {
  key: string;
  label: string;
  type: 'text' | 'textarea' | 'select' | 'number' | 'toggle';
  placeholder?: string;
  options?: { value: string; label: string }[];
}

const NODE_CONFIG_FIELDS: Record<string, FieldDef[]> = {
  start: [
    {
      key: 'trigger_type', label: 'Trigger Type', type: 'select', options: [
        { value: 'manual', label: 'Manual' },
        { value: 'webhook', label: 'Webhook' },
        { value: 'schedule', label: 'Schedule' },
        { value: 'event', label: 'Event' },
      ]
    },
  ],
  end: [
    { key: 'output_variable', label: 'Output Variable', type: 'text', placeholder: 'e.g. result' },
  ],
  planner: [
    { key: 'prompt', label: 'Planning Prompt', type: 'textarea', placeholder: 'Describe the task the planner should accomplish...' },
    {
      key: 'strategy', label: 'Strategy', type: 'select', options: [
        { value: 'chain_of_thought', label: 'Chain of Thought' },
        { value: 'react', label: 'ReAct' },
        { value: 'tree_of_thought', label: 'Tree of Thought' },
        { value: 'plan_and_execute', label: 'Plan & Execute' },
      ]
    },
    { key: 'max_iterations', label: 'Max Iterations', type: 'number', placeholder: '10' },
  ],
  ai: [
    {
      key: 'model_id', label: 'Model', type: 'select', options: [
        { value: 'gpt-4o', label: 'GPT-4o' },
        { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
        { value: 'claude-3-5-sonnet', label: 'Claude 3.5 Sonnet' },
        { value: 'claude-3-opus', label: 'Claude 3 Opus' },
        { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
      ]
    },
    { key: 'prompt_template_id', label: 'Prompt Template', type: 'text', placeholder: 'Template ID' },
    { key: 'temperature', label: 'Temperature', type: 'number', placeholder: '0.7' },
    { key: 'max_tokens', label: 'Max Tokens', type: 'number', placeholder: '4096' },
  ],
  connector: [
    {
      key: 'app', label: 'App', type: 'select', options: [
        { value: 'slack', label: 'Slack' },
        { value: 'gmail', label: 'Gmail' },
        { value: 'google_calendar', label: 'Google Calendar' },
        { value: 'google_sheets', label: 'Google Sheets' },
      ]
    },
    {
      key: 'action', label: 'Action', type: 'select', options: [
        { value: 'send_message', label: 'Send Message' },
        { value: 'send_email', label: 'Send Email' },
        { value: 'create_event', label: 'Create Event' },
        { value: 'append_row', label: 'Append Row' },
        { value: 'create_issue', label: 'Create Issue' },
      ]
    },
    { key: 'channel', label: 'Slack: Channel', type: 'text', placeholder: 'e.g. general' },
    { key: 'message', label: 'Slack: Message', type: 'textarea', placeholder: 'Hello world' },
    { key: 'to', label: 'Gmail: To', type: 'text', placeholder: 'user@example.com' },
    { key: 'subject', label: 'Gmail/Calendar: Subject/Summary', type: 'text', placeholder: 'Subject' },
    { key: 'body', label: 'Gmail/GitHub: Body/Description', type: 'textarea', placeholder: 'Content body...' },
    { key: 'start_time_iso', label: 'Calendar: Start Time (ISO)', type: 'text', placeholder: '2026-07-30T10:00:00Z' },
    { key: 'end_time_iso', label: 'Calendar: End Time (ISO)', type: 'text', placeholder: '2026-07-30T11:00:00Z' },
    { key: 'spreadsheet_id', label: 'Sheets: Spreadsheet ID', type: 'text', placeholder: 'abc123xyz' },
    { key: 'range_', label: 'Sheets: Range', type: 'text', placeholder: 'Sheet1!A:B' },
    { key: 'values', label: 'Sheets: Values (JSON)', type: 'text', placeholder: '["Row", "Val"]' },
    { key: 'repo_name', label: 'GitHub: Repo Name', type: 'text', placeholder: 'owner/repo' },
    { key: 'title', label: 'GitHub: Issue Title', type: 'text', placeholder: 'Bug title' },
  ],
  approval: [
    { key: 'title', label: 'Approval Title', type: 'text', placeholder: 'Security Review' },
    { key: 'description', label: 'Description', type: 'textarea', placeholder: 'Summarize the request...' },
    { key: 'instructions', label: 'Instructions', type: 'textarea', placeholder: 'Detailed steps for approver...' },
    { key: 'approvers', label: 'Approver(s) Emails', type: 'text', placeholder: 'user@acme.com, admin@acme.com' },
    { key: 'timeout_hours', label: 'Timeout (hours)', type: 'number', placeholder: '24' },
    { key: 'auto_approve', label: 'Auto Approve on Timeout', type: 'toggle' },
    { key: 'auto_reject', label: 'Auto Reject on Timeout', type: 'toggle' },
    { key: 'require_comment', label: 'Require Comment', type: 'toggle' },
    {
      key: 'priority', label: 'Priority', type: 'select', options: [
        { value: 'low', label: 'Low' },
        { value: 'medium', label: 'Medium' },
        { value: 'high', label: 'High' },
        { value: 'critical', label: 'Critical' },
      ]
    },
    { key: 'category', label: 'Category', type: 'text', placeholder: 'Financial' },
    {
      key: 'notification_channel', label: 'Notification Channel', type: 'select', options: [
        { value: 'dashboard', label: 'Dashboard Only' },
        { value: 'email', label: 'Email' },
        { value: 'slack', label: 'Slack' },
      ]
    },
  ],
  knowledge: [
    { key: 'collection_id', label: 'Collection', type: 'text', placeholder: 'Knowledge collection ID' },
    { key: 'query_variable', label: 'Query Variable', type: 'text', placeholder: '{{input.query}}' },
    { key: 'top_k', label: 'Top K Results', type: 'number', placeholder: '5' },
    { key: 'similarity_threshold', label: 'Similarity Threshold', type: 'number', placeholder: '0.75' },
  ],
  condition: [
    { key: 'expression', label: 'Condition Expression', type: 'textarea', placeholder: '{{ai_1.output.severity}} == "critical"' },
  ],
  loop: [
    { key: 'collection_variable', label: 'Collection Variable', type: 'text', placeholder: '{{connector_1.output.items}}' },
    { key: 'iterator_variable', label: 'Iterator Variable', type: 'text', placeholder: 'item' },
    { key: 'max_iterations', label: 'Max Iterations', type: 'number', placeholder: '100' },
  ],
  delay: [
    { key: 'duration_seconds', label: 'Duration (seconds)', type: 'number', placeholder: '60' },
  ],
  http: [
    { key: 'url', label: 'URL', type: 'text', placeholder: 'https://api.example.com/endpoint' },
    {
      key: 'method', label: 'Method', type: 'select', options: [
        { value: 'GET', label: 'GET' },
        { value: 'POST', label: 'POST' },
        { value: 'PUT', label: 'PUT' },
        { value: 'PATCH', label: 'PATCH' },
        { value: 'DELETE', label: 'DELETE' },
      ]
    },
    { key: 'headers', label: 'Headers (JSON)', type: 'textarea', placeholder: '{"Authorization": "Bearer {{token}}"}' },
    { key: 'body', label: 'Body (JSON)', type: 'textarea', placeholder: '{"key": "value"}' },
  ],
  webhook: [
    { key: 'path', label: 'Webhook Path', type: 'text', placeholder: '/webhooks/my-hook' },
    { key: 'secret', label: 'Validation Secret', type: 'text', placeholder: 'whsec_...' },
  ],
};

// ==========================================
// Parameter Mapping Section
// ==========================================
const ParameterMappingSection: React.FC<{ nodeId: string; data: NodeConfig }> = ({ nodeId, data }) => {
  const { updateNodeConfig, nodes, edges } = useWorkflowBuilderStore();
  const mappings = data.parameterMappings || {};

  // Find upstream nodes that could provide outputs
  const upstreamNodes = useMemo(() => {
    const incoming = new Set<string>();
    const visited = new Set<string>();
    const queue = [nodeId];
    while (queue.length > 0) {
      const current = queue.shift()!;
      if (visited.has(current)) continue;
      visited.add(current);
      for (const edge of edges) {
        if (edge.target === current && !visited.has(edge.source)) {
          incoming.add(edge.source);
          queue.push(edge.source);
        }
      }
    }
    return nodes.filter((n) => incoming.has(n.id));
  }, [nodeId, nodes, edges]);

  const addMapping = () => {
    const newKey = `param_${Object.keys(mappings).length + 1}`;
    updateNodeConfig(nodeId, {
      parameterMappings: { ...mappings, [newKey]: '' },
    } as any);
  };

  const updateMapping = (key: string, value: string) => {
    updateNodeConfig(nodeId, {
      parameterMappings: { ...mappings, [key]: value },
    } as any);
  };

  const removeMapping = (key: string) => {
    const { [key]: _, ...rest } = mappings;
    updateNodeConfig(nodeId, { parameterMappings: rest } as any);
  };

  const renameMapping = (oldKey: string, newKey: string) => {
    if (oldKey === newKey || !newKey.trim()) return;
    const val = mappings[oldKey];
    const { [oldKey]: _, ...rest } = mappings;
    updateNodeConfig(nodeId, { parameterMappings: { ...rest, [newKey]: val } } as any);
  };

  return (
    <div className="border-t border-border pt-3 mt-3">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-xs font-bold text-foreground flex items-center gap-1.5">
          <Variable className="h-3.5 w-3.5 text-violet-500" />
          Parameter Mapping
        </h4>
        <button
          onClick={addMapping}
          className="text-[10px] text-primary hover:text-primary/80 font-medium"
          aria-label="Add parameter mapping"
        >
          + Add
        </button>
      </div>

      {Object.entries(mappings).length === 0 && (
        <p className="text-[10px] text-muted-foreground italic">No parameter mappings configured.</p>
      )}

      {Object.entries(mappings).map(([key, expr]) => (
        <div key={key} className="flex items-start gap-1.5 mb-2">
          <input
            type="text"
            value={key}
            onChange={(e) => renameMapping(key, e.target.value)}
            className="w-24 h-7 px-2 rounded border border-border bg-background text-[11px] text-foreground
              focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="field"
            aria-label="Parameter name"
          />
          <span className="text-[10px] text-muted-foreground mt-1.5">←</span>
          <div className="flex-1 relative">
            <input
              type="text"
              value={expr}
              onChange={(e) => updateMapping(key, e.target.value)}
              className="w-full h-7 px-2 rounded border border-border bg-background text-[11px] text-foreground
                focus:outline-none focus:ring-1 focus:ring-primary"
              placeholder="{{node.output.field}}"
              aria-label="Source expression"
            />
            {/* Variable suggestions dropdown trigger */}
            {upstreamNodes.length > 0 && (
              <div className="absolute right-1 top-1">
                <details className="relative">
                  <summary className="cursor-pointer p-0.5 hover:bg-accent rounded" aria-label="Show available variables">
                    <ChevronDown className="h-3 w-3 text-muted-foreground" />
                  </summary>
                  <div className="absolute right-0 top-6 w-52 bg-popover border border-border rounded-md shadow-lg z-50 max-h-40 overflow-y-auto">
                    {upstreamNodes.map((n) => (
                      <button
                        key={n.id}
                        onClick={() => updateMapping(key, `{{${n.id}.output}}`)}
                        className="w-full text-left px-3 py-1.5 text-[10px] hover:bg-accent transition-colors"
                      >
                        <span className="font-medium text-foreground">{n.data.label}</span>
                        <span className="text-muted-foreground ml-1">({n.id})</span>
                      </button>
                    ))}
                  </div>
                </details>
              </div>
            )}
          </div>
          <button
            onClick={() => removeMapping(key)}
            className="p-1 mt-0.5 text-muted-foreground hover:text-rose-500 transition-colors"
            aria-label={`Remove ${key} mapping`}
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      ))}
    </div>
  );
};

// ==========================================
// Main Property Editor Component
// ==========================================
export const PropertyEditor: React.FC = () => {
  const {
    selectedNodeId, nodes, isPropertyEditorOpen, togglePropertyEditor,
    updateNodeConfig, deleteNode, copyNode, updateNodeStatus, saveNodeAsTemplate,
  } = useWorkflowBuilderStore();

  const selectedNode = useMemo(
    () => nodes.find((n) => n.id === selectedNodeId),
    [selectedNodeId, nodes]
  );

  if (!isPropertyEditorOpen || !selectedNode) {
    return null;
  }

  const data = selectedNode.data as NodeConfig;
  const nodeInfo = getNodeTypeInfo(data.nodeType);
  const fields = NODE_CONFIG_FIELDS[data.nodeType] || [];

  const handleConfigChange = (key: string, value: any) => {
    updateNodeConfig(selectedNode.id, {
      config: { ...data.config, [key]: value },
    } as any);
  };

  const handleLabelChange = (label: string) => {
    updateNodeConfig(selectedNode.id, { label } as any);
  };

  const handleDescriptionChange = (description: string) => {
    updateNodeConfig(selectedNode.id, { description } as any);
  };

  const handleToggleDisabled = () => {
    updateNodeStatus(selectedNode.id, data.status === 'disabled' ? 'idle' : 'disabled');
  };

  const handleSaveTemplate = () => {
    const name = data.label || `${data.nodeType} template`;
    saveNodeAsTemplate(selectedNode.id, name);
  };

  return (
    <div className="w-[300px] h-full bg-card border-l border-border flex flex-col shrink-0 overflow-hidden" role="complementary" aria-label="Property editor">
      {/* Header */}
      <div className="flex items-center justify-between px-3 pt-3 pb-2 border-b border-border">
        <div className="flex items-center gap-2 min-w-0">
          <span className={nodeInfo?.color || 'text-muted-foreground'}>
            {nodeInfo?.icon}
          </span>
          <h3 className="text-sm font-bold text-foreground truncate">{data.label}</h3>
        </div>
        <button onClick={togglePropertyEditor} className="p-1 rounded hover:bg-accent transition-colors" aria-label="Close property editor">
          <X className="h-4 w-4 text-muted-foreground" />
        </button>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-4 scrollbar-thin">
        {/* Identity Section */}
        <div>
          <h4 className="text-xs font-bold text-foreground mb-2 flex items-center gap-1.5">
            <Tag className="h-3.5 w-3.5 text-sky-500" />
            Identity
          </h4>
          <div className="space-y-2">
            <div>
              <label className="text-[10px] text-muted-foreground font-medium block mb-1">Label</label>
              <input
                type="text"
                value={data.label}
                onChange={(e) => handleLabelChange(e.target.value)}
                className="w-full h-8 px-2.5 rounded-md border border-border bg-background text-xs text-foreground
                  focus:outline-none focus:ring-1 focus:ring-primary"
                aria-label="Node label"
              />
            </div>
            <div>
              <label className="text-[10px] text-muted-foreground font-medium block mb-1">Description</label>
              <textarea
                value={data.description || ''}
                onChange={(e) => handleDescriptionChange(e.target.value)}
                className="w-full h-14 px-2.5 py-1.5 rounded-md border border-border bg-background text-xs text-foreground
                  resize-none focus:outline-none focus:ring-1 focus:ring-primary"
                placeholder="Optional description..."
                aria-label="Node description"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-muted-foreground font-medium">Node ID</span>
              <code className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">{selectedNode.id}</code>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-muted-foreground font-medium">Type</span>
              <code className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">{data.nodeType}</code>
            </div>
            {/* Require Approval Toggle - Show for all non-system action nodes */}
            {!['start', 'end', 'condition', 'delay', 'loop', 'approval'].includes(data.nodeType) && (
              <div className="flex items-center justify-between pt-2 border-t border-border mt-2">
                <span className="text-[10px] text-muted-foreground font-medium flex items-center gap-1.5">
                  <Shield className="h-3 w-3 text-indigo-500" />
                  Require Human Approval
                </span>
                <button
                  type="button"
                  onClick={() => updateNodeConfig(selectedNode.id, { requires_approval: !data.requires_approval } as any)}
                  className={`w-9 h-5 rounded-full relative transition-colors ${data.requires_approval ? 'bg-indigo-500' : 'bg-muted-foreground/30'}`}
                  aria-label="Toggle human approval"
                >
                  <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${data.requires_approval ? 'translate-x-4' : 'translate-x-0'}`} />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Configuration Section */}
        {fields.length > 0 && (
          <div className="border-t border-border pt-3">
            <h4 className="text-xs font-bold text-foreground mb-2 flex items-center gap-1.5">
              <Settings className="h-3.5 w-3.5 text-amber-500" />
              Configuration
            </h4>
            <div className="space-y-2.5">
              {fields.map((field) => (
                <div key={field.key}>
                  <label className="text-[10px] text-muted-foreground font-medium block mb-1">{field.label}</label>
                  {field.type === 'text' && (
                    <input
                      type="text"
                      value={data.config?.[field.key] || ''}
                      onChange={(e) => handleConfigChange(field.key, e.target.value)}
                      placeholder={field.placeholder}
                      className="w-full h-8 px-2.5 rounded-md border border-border bg-background text-xs text-foreground
                        focus:outline-none focus:ring-1 focus:ring-primary"
                      aria-label={field.label}
                    />
                  )}
                  {field.type === 'textarea' && (
                    <textarea
                      value={data.config?.[field.key] || ''}
                      onChange={(e) => handleConfigChange(field.key, e.target.value)}
                      placeholder={field.placeholder}
                      className="w-full h-16 px-2.5 py-1.5 rounded-md border border-border bg-background text-xs text-foreground
                        resize-none focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                      aria-label={field.label}
                    />
                  )}
                  {field.type === 'select' && (
                    <select
                      value={data.config?.[field.key] || ''}
                      onChange={(e) => handleConfigChange(field.key, e.target.value)}
                      className="w-full h-8 px-2.5 rounded-md border border-border bg-background text-xs text-foreground
                        focus:outline-none focus:ring-1 focus:ring-primary"
                      aria-label={field.label}
                    >
                      <option value="">Select...</option>
                      {field.options?.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  )}
                  {field.type === 'number' && (
                    <input
                      type="number"
                      value={data.config?.[field.key] || ''}
                      onChange={(e) => handleConfigChange(field.key, parseFloat(e.target.value) || 0)}
                      placeholder={field.placeholder}
                      className="w-full h-8 px-2.5 rounded-md border border-border bg-background text-xs text-foreground
                        focus:outline-none focus:ring-1 focus:ring-primary"
                      aria-label={field.label}
                    />
                  )}
                  {field.type === 'toggle' && (
                    <div className="mt-1 flex items-center justify-between px-2">
                      <span className="text-xs text-foreground">{field.label}</span>
                      <button
                        type="button"
                        onClick={() => handleConfigChange(field.key, !data.config?.[field.key])}
                        className={`w-9 h-5 rounded-full relative transition-colors ${data.config?.[field.key] ? 'bg-emerald-500' : 'bg-muted-foreground/30'}`}
                      >
                        <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${data.config?.[field.key] ? 'translate-x-4' : 'translate-x-0'}`} />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Parameter Mapping */}
        <ParameterMappingSection nodeId={selectedNode.id} data={data} />

        {/* Actions */}
        <div className="border-t border-border pt-3">
          <h4 className="text-xs font-bold text-foreground mb-2 flex items-center gap-1.5">
            <FileText className="h-3.5 w-3.5 text-emerald-500" />
            Actions
          </h4>
          <div className="space-y-1.5">
            <button
              onClick={handleToggleDisabled}
              className="flex items-center gap-2 w-full px-2.5 py-1.5 rounded-md text-xs hover:bg-accent transition-colors text-left"
              aria-label={data.status === 'disabled' ? 'Enable node' : 'Disable node'}
            >
              {data.status === 'disabled' ? <ToggleLeft className="h-3.5 w-3.5 text-muted-foreground" /> : <ToggleRight className="h-3.5 w-3.5 text-emerald-500" />}
              <span>{data.status === 'disabled' ? 'Enable Node' : 'Disable Node'}</span>
            </button>
            <button
              onClick={() => copyNode(selectedNode.id)}
              className="flex items-center gap-2 w-full px-2.5 py-1.5 rounded-md text-xs hover:bg-accent transition-colors text-left"
              aria-label="Copy node"
            >
              <Copy className="h-3.5 w-3.5 text-sky-500" />
              Copy Node
            </button>
            <button
              onClick={handleSaveTemplate}
              className="flex items-center gap-2 w-full px-2.5 py-1.5 rounded-md text-xs hover:bg-accent transition-colors text-left"
              aria-label="Save as template"
            >
              <Star className="h-3.5 w-3.5 text-amber-500" />
              Save as Template
            </button>
            <button
              onClick={() => deleteNode(selectedNode.id)}
              className="flex items-center gap-2 w-full px-2.5 py-1.5 rounded-md text-xs text-rose-500 hover:bg-rose-500/10 transition-colors text-left"
              aria-label="Delete node"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Delete Node
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
