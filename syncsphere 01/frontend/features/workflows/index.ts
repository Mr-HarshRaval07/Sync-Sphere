// ==========================================
// Module 12 — Visual Workflow Builder Barrel
// ==========================================

// Core Store
export { useWorkflowBuilderStore, wouldCreateCycle, topologicalSort } from '../../shared/stores/workflowBuilderStore';
export type { NodeConfig, NodeStatus, WorkflowVersion, SimulationResult, ValidationMessage, NodeTemplate, WorkflowState } from '../../shared/stores/workflowBuilderStore';

// Custom Node Registry
export { customNodeTypes, NODE_TYPE_REGISTRY, getNodeTypeInfo } from './CustomNodeRegistry';
export type { NodeTypeInfo } from './CustomNodeRegistry';

// Validation Engine
export { validateWorkflow, hasErrors, getErrorCount, getWarningCount } from './WorkflowValidation';

// Auto Layout
export { autoLayoutNodes } from './AutoLayout';

// Simulation Engine
export { simulateWorkflow, formatDuration, formatCost } from './WorkflowSimulation';

// Workflow Templates
export { WORKFLOW_TEMPLATES } from './WorkflowTemplates';
export type { WorkflowTemplate } from './WorkflowTemplates';

// Keyboard Shortcuts
export { useWorkflowKeyboardShortcuts, KEYBOARD_SHORTCUTS } from './KeyboardShortcuts';

// UI Components (lazy-loaded in page, but available for import)
export { NodePalette } from './NodePalette';
export { PropertyEditor } from './PropertyEditor';
export { ExecutionPreview } from './ExecutionPreview';
export { WorkflowVersionHistory } from './WorkflowVersioning';
export { WorkflowCommandPalette } from './WorkflowCommandPalette';
