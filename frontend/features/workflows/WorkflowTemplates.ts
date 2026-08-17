import { Node } from '@xyflow/react';
import { NodeConfig, WorkflowVersion } from '../../shared/stores/workflowBuilderStore';

// ==========================================
// Starter Workflow Templates
// ==========================================
export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  nodes: Node<NodeConfig>[];
  edges: { source: string; target: string }[];
}

function makeNode(id: string, type: string, label: string, x: number, y: number, config: Record<string, any> = {}): Node<NodeConfig> {
  return {
    id,
    type,
    position: { x, y },
    data: {
      label,
      nodeType: type,
      description: '',
      status: Object.keys(config).length > 0 ? 'configured' : 'idle',
      config,
    },
  };
}

export const WORKFLOW_TEMPLATES: WorkflowTemplate[] = [
  {
    id: 'tpl-bug-triage',
    name: 'Bug Triage Pipeline',
    description: 'Automated bug classification, severity assessment, and Jira ticket assignment.',
    category: 'Engineering',
    nodes: [
      makeNode('start_1', 'start', 'Webhook: Bug Report', 80, 150),
      makeNode('ai_1', 'ai', 'Classify Severity', 380, 80, { model_id: 'gpt-4o', prompt_template_id: 'classify_bug' }),
      makeNode('condition_1', 'condition', 'Is Critical?', 680, 150, { expression: '{{ai_1.output.severity}} == "critical"' }),
      makeNode('connector_1', 'connector', 'Create Sheets Row P0', 980, 60, { connector_id: 'google_sheets', tool_name: 'append_row' }),
      makeNode('connector_2', 'connector', 'Create Sheets Row P2', 980, 240, { connector_id: 'google_sheets', tool_name: 'append_row' }),
      makeNode('connector_3', 'connector', 'Slack Notify', 1280, 150, { connector_id: 'slack', tool_name: 'send_message' }),
      makeNode('end_1', 'end', 'Done', 1560, 150),
    ],
    edges: [
      { source: 'start_1', target: 'ai_1' },
      { source: 'ai_1', target: 'condition_1' },
      { source: 'condition_1', target: 'connector_1' },
      { source: 'condition_1', target: 'connector_2' },
      { source: 'connector_1', target: 'connector_3' },
      { source: 'connector_2', target: 'connector_3' },
      { source: 'connector_3', target: 'end_1' },
    ],
  },
  {
    id: 'tpl-incident-response',
    name: 'Incident Response',
    description: 'Multi-stage incident detection, escalation, and resolution workflow with human approval gates.',
    category: 'Operations',
    nodes: [
      makeNode('start_1', 'start', 'Alert Trigger', 80, 150),
      makeNode('ai_1', 'ai', 'Analyze Impact', 380, 150, { model_id: 'claude-3-5-sonnet', prompt_template_id: 'incident_analysis' }),
      makeNode('approval_1', 'approval', 'Manager Approval', 680, 150, { routing_strategy: 'Sequential' }),
      makeNode('connector_1', 'connector', 'PagerDuty Notify', 980, 80, { connector_id: 'pagerduty', tool_name: 'create_incident' }),
      makeNode('connector_2', 'connector', 'Slack War Room', 980, 230, { connector_id: 'slack', tool_name: 'create_channel' }),
      makeNode('end_1', 'end', 'Resolved', 1280, 150),
    ],
    edges: [
      { source: 'start_1', target: 'ai_1' },
      { source: 'ai_1', target: 'approval_1' },
      { source: 'approval_1', target: 'connector_1' },
      { source: 'approval_1', target: 'connector_2' },
      { source: 'connector_1', target: 'end_1' },
      { source: 'connector_2', target: 'end_1' },
    ],
  },
  {
    id: 'tpl-customer-support',
    name: 'Customer Support Agent',
    description: 'AI-powered customer query classification, knowledge base retrieval, and automated response generation.',
    category: 'Support',
    nodes: [
      makeNode('start_1', 'start', 'Customer Query', 80, 150),
      makeNode('ai_1', 'ai', 'Classify Intent', 380, 150, { model_id: 'gpt-4o', prompt_template_id: 'classify_intent' }),
      makeNode('http_1', 'http', 'Search KB', 680, 80, { url: '/v1/knowledge/search', method: 'POST' }),
      makeNode('ai_2', 'ai', 'Generate Reply', 680, 240, { model_id: 'gpt-4o', prompt_template_id: 'generate_response' }),
      makeNode('connector_1', 'connector', 'Send Email', 980, 150, { connector_id: 'email', tool_name: 'send_reply' }),
      makeNode('end_1', 'end', 'Completed', 1280, 150),
    ],
    edges: [
      { source: 'start_1', target: 'ai_1' },
      { source: 'ai_1', target: 'http_1' },
      { source: 'ai_1', target: 'ai_2' },
      { source: 'http_1', target: 'connector_1' },
      { source: 'ai_2', target: 'connector_1' },
      { source: 'connector_1', target: 'end_1' },
    ],
  },

  {
    id: 'tpl-daily-report',
    name: 'Daily Report Generator',
    description: 'Aggregate metrics from connectors, generate AI summary, and distribute via Slack and email.',
    category: 'Operations',
    nodes: [
      makeNode('start_1', 'start', 'Daily Schedule', 80, 150),
      makeNode('connector_1', 'connector', 'Fetch Calendar Events', 380, 80, { connector_id: 'google_calendar', tool_name: 'list_events' }),
      makeNode('connector_2', 'connector', 'Fetch Email Stats', 380, 240, { connector_id: 'gmail', tool_name: 'search_emails' }),
      makeNode('ai_1', 'ai', 'Generate Summary', 680, 150, { model_id: 'gpt-4o', prompt_template_id: 'daily_summary' }),
      makeNode('connector_3', 'connector', 'Post to Slack', 980, 80, { connector_id: 'slack', tool_name: 'send_message' }),
      makeNode('http_1', 'connector', 'Send Email', 980, 240, { connector_id: 'gmail', tool_name: 'send_email' }),
      makeNode('end_1', 'end', 'Report Sent', 1280, 150),
    ],
    edges: [
      { source: 'start_1', target: 'connector_1' },
      { source: 'start_1', target: 'connector_2' },
      { source: 'connector_1', target: 'ai_1' },
      { source: 'connector_2', target: 'ai_1' },
      { source: 'ai_1', target: 'connector_3' },
      { source: 'ai_1', target: 'http_1' },
      { source: 'connector_3', target: 'end_1' },
      { source: 'http_1', target: 'end_1' },
    ],
  },
];
