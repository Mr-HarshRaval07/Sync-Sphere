'use client';

import React, { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { useWorkflowBuilderStore } from '../../shared/stores/workflowBuilderStore';
import { NODE_TYPE_REGISTRY } from './CustomNodeRegistry';
import { WORKFLOW_TEMPLATES } from './WorkflowTemplates';
import { KEYBOARD_SHORTCUTS } from './KeyboardShortcuts';
import {
  Search, Command, ArrowRight, Keyboard,
  Play, FileText, Zap, Settings,
} from 'lucide-react';

// ==========================================
// Command Palette Entry Types
// ==========================================
interface CommandEntry {
  id: string;
  label: string;
  description: string;
  category: 'node' | 'template' | 'action' | 'shortcut';
  icon: React.ReactNode;
  onSelect: () => void;
}

// ==========================================
// Workflow Command Palette
// ==========================================
export const WorkflowCommandPalette: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    addNode, saveDraft, publishWorkflow, undo, redo,
    togglePreview, togglePalette, togglePropertyEditor, toggleVersionHistory,
  } = useWorkflowBuilderStore();

  // Toggle with Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
        setSearch('');
        setSelectedIndex(0);
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Build command entries
  const allCommands: CommandEntry[] = useMemo(() => {
    const commands: CommandEntry[] = [];

    // Node creation commands
    NODE_TYPE_REGISTRY.forEach((info) => {
      commands.push({
        id: `add-node-${info.type}`,
        label: `Add ${info.label} Node`,
        description: info.description,
        category: 'node',
        icon: info.icon,
        onSelect: () => {
          const id = `${info.type}_${Date.now()}`;
          addNode({
            id,
            type: info.type,
            position: { x: 300 + Math.random() * 200, y: 200 + Math.random() * 200 },
            data: {
              label: info.label,
              nodeType: info.type,
              description: info.description,
              status: 'idle',
              config: {},
            },
          });
          setIsOpen(false);
        },
      });
    });

    // Template commands
    WORKFLOW_TEMPLATES.forEach((tpl) => {
      commands.push({
        id: `load-template-${tpl.id}`,
        label: `Load: ${tpl.name}`,
        description: tpl.description,
        category: 'template',
        icon: <FileText className="h-4 w-4 text-violet-500" />,
        onSelect: () => {
          // Apply template by adding all nodes and edges
          tpl.nodes.forEach((n) => addNode({ ...n, id: `${n.id}_${Date.now()}` }));
          setIsOpen(false);
        },
      });
    });

    // Action commands
    commands.push(
      { id: 'save-draft', label: 'Save Draft', description: 'Save current workflow as draft', category: 'action', icon: <Settings className="h-4 w-4 text-sky-500" />, onSelect: () => { saveDraft(); setIsOpen(false); } },
      { id: 'publish', label: 'Publish Workflow', description: 'Publish workflow for execution', category: 'action', icon: <Play className="h-4 w-4 text-emerald-500" />, onSelect: () => { publishWorkflow(); setIsOpen(false); } },
      { id: 'undo', label: 'Undo', description: 'Undo last change', category: 'action', icon: <ArrowRight className="h-4 w-4 text-muted-foreground rotate-180" />, onSelect: () => { undo(); setIsOpen(false); } },
      { id: 'redo', label: 'Redo', description: 'Redo last undone change', category: 'action', icon: <ArrowRight className="h-4 w-4 text-muted-foreground" />, onSelect: () => { redo(); setIsOpen(false); } },
      { id: 'preview', label: 'Toggle Execution Preview', description: 'Show/hide simulation panel', category: 'action', icon: <Zap className="h-4 w-4 text-amber-500" />, onSelect: () => { togglePreview(); setIsOpen(false); } },
      { id: 'palette', label: 'Toggle Node Palette', description: 'Show/hide node palette', category: 'action', icon: <Settings className="h-4 w-4 text-sky-500" />, onSelect: () => { togglePalette(); setIsOpen(false); } },
      { id: 'property-editor', label: 'Toggle Property Editor', description: 'Show/hide property panel', category: 'action', icon: <Settings className="h-4 w-4 text-amber-500" />, onSelect: () => { togglePropertyEditor(); setIsOpen(false); } },
      { id: 'version-history', label: 'Toggle Version History', description: 'Show/hide versions', category: 'action', icon: <Settings className="h-4 w-4 text-violet-500" />, onSelect: () => { toggleVersionHistory(); setIsOpen(false); } },
    );

    // Shortcut reference commands
    KEYBOARD_SHORTCUTS.forEach((s) => {
      commands.push({
        id: `shortcut-${s.keys}`,
        label: s.keys,
        description: s.description,
        category: 'shortcut',
        icon: <Keyboard className="h-4 w-4 text-muted-foreground" />,
        onSelect: () => {},
      });
    });

    return commands;
  }, [addNode, saveDraft, publishWorkflow, undo, redo, togglePreview, togglePalette, togglePropertyEditor, toggleVersionHistory]);

  // Filtered commands
  const filteredCommands = useMemo(() => {
    if (!search) return allCommands;
    const lower = search.toLowerCase();
    return allCommands.filter(
      (c) =>
        c.label.toLowerCase().includes(lower) ||
        c.description.toLowerCase().includes(lower) ||
        c.category.toLowerCase().includes(lower)
    );
  }, [search, allCommands]);

  // Keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, filteredCommands.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      filteredCommands[selectedIndex]?.onSelect();
    }
  }, [filteredCommands, selectedIndex]);

  // Reset selection when search changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [search]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]" role="dialog" aria-label="Command palette">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setIsOpen(false)} />

      {/* Palette */}
      <div className="relative w-full max-w-[520px] bg-card rounded-xl border border-border shadow-2xl overflow-hidden" onKeyDown={handleKeyDown}>
        {/* Search Input */}
        <div className="flex items-center gap-3 px-4 border-b border-border">
          <Command className="h-4 w-4 text-muted-foreground shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search nodes, templates, actions..."
            className="flex-1 h-12 bg-transparent text-sm text-foreground placeholder:text-muted-foreground
              focus:outline-none"
            aria-label="Command search"
          />
          <kbd className="hidden sm:inline-block px-1.5 py-0.5 rounded bg-muted text-[10px] text-muted-foreground font-mono">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-[320px] overflow-y-auto py-2 scrollbar-thin">
          {filteredCommands.length === 0 && (
            <div className="px-4 py-6 text-center">
              <Search className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">No results for &ldquo;{search}&rdquo;</p>
            </div>
          )}

          {/* Grouped by category */}
          {['node', 'template', 'action', 'shortcut'].map((cat) => {
            const items = filteredCommands.filter((c) => c.category === cat);
            if (items.length === 0) return null;
            return (
              <div key={cat}>
                <div className="px-4 py-1 text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                  {cat === 'node' ? 'Nodes' : cat === 'template' ? 'Templates' : cat === 'action' ? 'Actions' : 'Shortcuts'}
                </div>
                {items.map((cmd) => {
                  const globalIndex = filteredCommands.indexOf(cmd);
                  return (
                    <button
                      key={cmd.id}
                      onClick={cmd.onSelect}
                      className={`w-full flex items-center gap-3 px-4 py-2 text-left transition-colors
                        ${globalIndex === selectedIndex ? 'bg-accent' : 'hover:bg-accent/50'}
                      `}
                      onMouseEnter={() => setSelectedIndex(globalIndex)}
                      aria-selected={globalIndex === selectedIndex}
                    >
                      <span className="shrink-0 opacity-70">{cmd.icon}</span>
                      <div className="flex-1 min-w-0">
                        <span className="text-xs font-medium text-foreground">{cmd.label}</span>
                        <span className="text-[10px] text-muted-foreground ml-2">{cmd.description}</span>
                      </div>
                      {cmd.category === 'shortcut' && (
                        <kbd className="px-1.5 py-0.5 rounded bg-muted text-[10px] text-muted-foreground font-mono">{cmd.label}</kbd>
                      )}
                      {globalIndex === selectedIndex && (
                        <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
                      )}
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2 border-t border-border text-[10px] text-muted-foreground">
          <span>↑↓ Navigate</span>
          <span>↵ Select</span>
          <span>ESC Close</span>
        </div>
      </div>
    </div>
  );
};
