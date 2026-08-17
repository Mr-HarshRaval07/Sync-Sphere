'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { NodeConfig, NodeStatus } from '../../shared/stores/workflowBuilderStore';
import {
  Play, Square, BrainCircuit, Sparkles, Radio, ShieldCheck, GitFork,
  Repeat, Clock, Globe, Webhook, Database, HelpCircle, Hourglass, Terminal
} from 'lucide-react';

// ==========================================
// Node Status Colors & Styling
// ==========================================
const STATUS_STYLES: Record<NodeStatus, { border: string; bg: string; dot: string; label: string }> = {
  idle: { border: 'border-border', bg: 'bg-card', dot: 'bg-muted-foreground', label: 'Idle' },
  configured: { border: 'border-sky-500/40', bg: 'bg-sky-500/5', dot: 'bg-sky-500', label: 'Configured' },
  running: { border: 'border-amber-500/60', bg: 'bg-amber-500/5', dot: 'bg-amber-500 animate-pulse', label: 'Running' },
  success: { border: 'border-emerald-500/60', bg: 'bg-emerald-500/5', dot: 'bg-emerald-500', label: 'Success' },
  failed: { border: 'border-rose-500/60', bg: 'bg-rose-500/5', dot: 'bg-rose-500', label: 'Failed' },
  waiting: { border: 'border-violet-500/40', bg: 'bg-violet-500/5', dot: 'bg-violet-500 animate-pulse', label: 'Waiting' },
  approval_required: { border: 'border-orange-500/60', bg: 'bg-orange-500/5', dot: 'bg-orange-500 animate-pulse', label: 'Approval Req.' },
  disabled: { border: 'border-border opacity-50', bg: 'bg-muted/30', dot: 'bg-muted-foreground', label: 'Disabled' },
};

// ==========================================
// Node Type Metadata
// ==========================================
export interface NodeTypeInfo {
  type: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  color: string;       // accent color class
  category: 'control' | 'ai' | 'integration' | 'logic' | 'utility';
  hasMultipleOutputs?: boolean;
}

export const NODE_TYPE_REGISTRY: NodeTypeInfo[] = [
  { type: 'start', label: 'Start', description: 'Workflow entry point', icon: <Play className="h-4 w-4" />, color: 'text-emerald-500', category: 'control' },
  { type: 'end', label: 'End', description: 'Workflow exit point', icon: <Square className="h-4 w-4" />, color: 'text-rose-500', category: 'control' },
  { type: 'planner', label: 'Planner', description: 'AI agentic planner node', icon: <BrainCircuit className="h-4 w-4" />, color: 'text-violet-500', category: 'ai' },
  { type: 'ai', label: 'AI Model', description: 'LLM completion node', icon: <Sparkles className="h-4 w-4" />, color: 'text-amber-500', category: 'ai' },

  // Real Integration Actions map directly to Connector Node type, but are visually distinguishable 
  { type: 'slack.send_message', label: 'Slack', description: 'Send Message', icon: <Radio className="h-4 w-4" />, color: 'text-sky-500', category: 'integration' },
  { type: 'gmail.send_email', label: 'Gmail', description: 'Send Email', icon: <Globe className="h-4 w-4" />, color: 'text-rose-500', category: 'integration' },
  { type: 'google_sheets.append_row', label: 'Google Sheets', description: 'Append Row', icon: <Database className="h-4 w-4" />, color: 'text-emerald-500', category: 'integration' },
  { type: 'google_calendar.create_event', label: 'Google Calendar', description: 'Create Event', icon: <Clock className="h-4 w-4" />, color: 'text-sky-500', category: 'integration' },
  { type: 'notion.create_page', label: 'Notion', description: 'Create Docs or Log Meeting', icon: <Database className="h-4 w-4" />, color: 'text-slate-800', category: 'integration' },
  { type: 'github.create_issue', label: 'GitHub', description: 'Create Issue', icon: <Terminal className="h-4 w-4" />, color: 'text-slate-500', category: 'integration' },
  { type: 'jira.create_issue', label: 'Jira', description: 'Create Ticket', icon: <Radio className="h-4 w-4" />, color: 'text-sky-500', category: 'integration' },

  { type: 'approval', label: 'Human Approval', description: 'Wait for human gate decision', icon: <Hourglass className="h-4 w-4" />, color: 'text-yellow-500', category: 'integration' },
  { type: 'knowledge', label: 'Knowledge', description: 'RAG vector search', icon: <Database className="h-4 w-4" />, color: 'text-teal-500', category: 'ai' },
  { type: 'condition', label: 'Condition', description: 'Branching logic gate', icon: <GitFork className="h-4 w-4" />, color: 'text-purple-500', category: 'logic', hasMultipleOutputs: true },
  { type: 'loop', label: 'Loop', description: 'Iterate over collection', icon: <Repeat className="h-4 w-4" />, color: 'text-cyan-500', category: 'logic' },
  { type: 'delay', label: 'Delay', description: 'Wait for duration', icon: <Clock className="h-4 w-4" />, color: 'text-slate-400', category: 'utility' },
  { type: 'http', label: 'HTTP', description: 'External HTTP request', icon: <Globe className="h-4 w-4" />, color: 'text-blue-500', category: 'integration' },
  { type: 'webhook', label: 'Webhook', description: 'Inbound webhook trigger', icon: <Webhook className="h-4 w-4" />, color: 'text-pink-500', category: 'utility' },
];

export function getNodeTypeInfo(type: string): NodeTypeInfo | undefined {
  return NODE_TYPE_REGISTRY.find((n) => n.type === type);
}

// ==========================================
// Base Custom Node Component
// ==========================================
const BaseNode: React.FC<NodeProps & { data: NodeConfig }> = ({ data, selected, id }) => {
  const info = getNodeTypeInfo(data.nodeType) || {
    type: data.nodeType, label: data.nodeType, description: '', icon: <HelpCircle className="h-4 w-4" />, color: 'text-muted-foreground', category: 'utility' as const,
  };
  const statusStyle = STATUS_STYLES[data.status] || STATUS_STYLES.idle;
  const isCondition = data.nodeType === 'condition';
  const isStart = data.nodeType === 'start';
  const isEnd = data.nodeType === 'end';

  return (
    <div
      className={`
        relative min-w-[180px] max-w-[220px] rounded-lg border-2 shadow-sm
        ${statusStyle.border} ${statusStyle.bg}
        ${selected ? 'ring-2 ring-primary ring-offset-1 ring-offset-background shadow-lg' : ''}
        ${data.status === 'disabled' ? 'opacity-50' : ''}
        transition-all duration-150 group
      `}
      role="button"
      tabIndex={0}
      aria-label={`${data.label} node, status: ${statusStyle.label}`}
    >
      {/* Input Handle */}
      {!isStart && (
        <Handle
          type="target"
          position={Position.Left}
          className="!w-3 !h-3 !bg-muted-foreground !border-2 !border-background hover:!bg-primary transition-colors"
          aria-label="Input connection point"
        />
      )}

      {/* Node Header */}
      <div className="flex items-center gap-2 px-3 pt-2.5 pb-1">
        <span className={`${info.color} shrink-0`}>{info.icon}</span>
        <span className="text-xs font-bold text-foreground truncate">{data.label}</span>
      </div>

      {/* Node Body */}
      <div className="px-3 pb-2.5">
        <span className="text-[10px] text-muted-foreground leading-tight block truncate">
          {data.description || info.description}
        </span>
        {/* Status indicator */}
        <div className="flex items-center gap-1.5 mt-1.5">
          <span className={`h-1.5 w-1.5 rounded-full ${statusStyle.dot}`} />
          <span className="text-[9px] text-muted-foreground font-medium">{statusStyle.label}</span>
        </div>
      </div>

      {/* Output Handle(s) */}
      {!isEnd && !isCondition && (
        <Handle
          type="source"
          position={Position.Right}
          className="!w-3 !h-3 !bg-muted-foreground !border-2 !border-background hover:!bg-primary transition-colors"
          aria-label="Output connection point"
        />
      )}

      {/* Condition node: two output handles (True / False) */}
      {isCondition && (
        <>
          <Handle
            type="source"
            position={Position.Right}
            id="true"
            className="!w-3 !h-3 !bg-emerald-500 !border-2 !border-background hover:!bg-emerald-400 transition-colors"
            style={{ top: '35%' }}
            aria-label="True branch output"
          />
          <Handle
            type="source"
            position={Position.Right}
            id="false"
            className="!w-3 !h-3 !bg-rose-500 !border-2 !border-background hover:!bg-rose-400 transition-colors"
            style={{ top: '65%' }}
            aria-label="False branch output"
          />
          <span className="absolute right-5 text-[8px] text-emerald-500 font-bold" style={{ top: '28%' }}>T</span>
          <span className="absolute right-5 text-[8px] text-rose-500 font-bold" style={{ top: '60%' }}>F</span>
        </>
      )}
    </div>
  );
};

// ==========================================
// Memoized Node Components (Performance)
// ==========================================
export const StartNode = memo((props: NodeProps) => <BaseNode {...props} data={props.data as NodeConfig} />);
StartNode.displayName = 'StartNode';

export const EndNode = memo((props: NodeProps) => <BaseNode {...props} data={props.data as NodeConfig} />);
EndNode.displayName = 'EndNode';

export const PlannerNode = memo((props: NodeProps) => <BaseNode {...props} data={props.data as NodeConfig} />);
PlannerNode.displayName = 'PlannerNode';

export const AINode = memo((props: NodeProps) => <BaseNode {...props} data={props.data as NodeConfig} />);
AINode.displayName = 'AINode';

export const ConnectorNode = memo((props: NodeProps) => <BaseNode {...props} data={props.data as NodeConfig} />);
ConnectorNode.displayName = 'ConnectorNode';

export const ApprovalNode = memo((props: NodeProps) => <BaseNode {...props} data={props.data as NodeConfig} />);
ApprovalNode.displayName = 'ApprovalNode';

export const KnowledgeNode = memo((props: NodeProps) => <BaseNode {...props} data={props.data as NodeConfig} />);
KnowledgeNode.displayName = 'KnowledgeNode';

export const ConditionNode = memo((props: NodeProps) => <BaseNode {...props} data={props.data as NodeConfig} />);
ConditionNode.displayName = 'ConditionNode';

export const LoopNode = memo((props: NodeProps) => <BaseNode {...props} data={props.data as NodeConfig} />);
LoopNode.displayName = 'LoopNode';

export const DelayNode = memo((props: NodeProps) => <BaseNode {...props} data={props.data as NodeConfig} />);
DelayNode.displayName = 'DelayNode';

export const HTTPNode = memo((props: NodeProps) => <BaseNode {...props} data={props.data as NodeConfig} />);
HTTPNode.displayName = 'HTTPNode';

export const WebhookNode = memo((props: NodeProps) => <BaseNode {...props} data={props.data as NodeConfig} />);
WebhookNode.displayName = 'WebhookNode';

// ==========================================
// Node Type Map (for React Flow registration)
// ==========================================
export const customNodeTypes = {
  start: StartNode,
  end: EndNode,
  planner: PlannerNode,
  ai: AINode,
  connector: ConnectorNode,
  approval: ApprovalNode,
  knowledge: KnowledgeNode,
  condition: ConditionNode,
  loop: LoopNode,
  delay: DelayNode,
  http: HTTPNode,
  webhook: WebhookNode,
};
