import { useEffect, useCallback } from 'react';
import { useWorkflowBuilderStore } from '../../shared/stores/workflowBuilderStore';

// ==========================================
// Keyboard Shortcuts Hook
// ==========================================
export function useWorkflowKeyboardShortcuts() {
  const {
    selectedNodeId, copyNode, pasteNode, duplicateNode, deleteNode,
    undo, redo, saveDraft, canUndo, canRedo,
    togglePreview, togglePalette, togglePropertyEditor, toggleVersionHistory,
  } = useWorkflowBuilderStore();

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    const target = e.target as HTMLElement;
    // Don't intercept when typing in inputs
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT' || target.isContentEditable) {
      return;
    }

    const ctrl = e.ctrlKey || e.metaKey;

    // Ctrl+Z — Undo
    if (ctrl && !e.shiftKey && e.key === 'z') {
      e.preventDefault();
      undo();
      return;
    }

    // Ctrl+Shift+Z — Redo
    if (ctrl && e.shiftKey && e.key === 'Z') {
      e.preventDefault();
      redo();
      return;
    }

    // Ctrl+Y — Redo (alternative)
    if (ctrl && e.key === 'y') {
      e.preventDefault();
      redo();
      return;
    }

    // Ctrl+C — Copy selected node
    if (ctrl && e.key === 'c' && selectedNodeId) {
      e.preventDefault();
      copyNode(selectedNodeId);
      return;
    }

    // Ctrl+V — Paste node
    if (ctrl && e.key === 'v') {
      e.preventDefault();
      pasteNode();
      return;
    }

    // Ctrl+D — Duplicate selected node
    if (ctrl && e.key === 'd' && selectedNodeId) {
      e.preventDefault();
      duplicateNode(selectedNodeId);
      return;
    }

    // Ctrl+S — Save draft
    if (ctrl && e.key === 's') {
      e.preventDefault();
      saveDraft();
      return;
    }

    // Delete or Backspace — Delete selected node
    if ((e.key === 'Delete' || e.key === 'Backspace') && selectedNodeId) {
      e.preventDefault();
      deleteNode(selectedNodeId);
      return;
    }

    // Ctrl+K — Toggle command palette (preview as placeholder)
    if (ctrl && e.key === 'k') {
      e.preventDefault();
      togglePreview();
      return;
    }

    // Ctrl+B — Toggle palette
    if (ctrl && e.key === 'b') {
      e.preventDefault();
      togglePalette();
      return;
    }

    // Ctrl+E — Toggle property editor
    if (ctrl && e.key === 'e') {
      e.preventDefault();
      togglePropertyEditor();
      return;
    }

    // Ctrl+H — Toggle version history
    if (ctrl && e.key === 'h') {
      e.preventDefault();
      toggleVersionHistory();
      return;
    }
  }, [selectedNodeId, copyNode, pasteNode, duplicateNode, deleteNode, undo, redo, saveDraft, canUndo, canRedo, togglePreview, togglePalette, togglePropertyEditor, toggleVersionHistory]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

// ==========================================
// Shortcut Reference
// ==========================================
export const KEYBOARD_SHORTCUTS = [
  { keys: 'Ctrl+Z', description: 'Undo' },
  { keys: 'Ctrl+Shift+Z', description: 'Redo' },
  { keys: 'Ctrl+C', description: 'Copy node' },
  { keys: 'Ctrl+V', description: 'Paste node' },
  { keys: 'Ctrl+D', description: 'Duplicate node' },
  { keys: 'Ctrl+S', description: 'Save draft' },
  { keys: 'Delete', description: 'Delete node' },
  { keys: 'Ctrl+K', description: 'Execution preview' },
  { keys: 'Ctrl+B', description: 'Toggle palette' },
  { keys: 'Ctrl+E', description: 'Toggle property editor' },
  { keys: 'Ctrl+H', description: 'Version history' },
];
