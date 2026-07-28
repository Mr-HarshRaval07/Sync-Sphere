'use client';

import React, { useState, useMemo, useCallback, DragEvent } from 'react';
import { NODE_TYPE_REGISTRY, NodeTypeInfo } from './CustomNodeRegistry';
import { useWorkflowBuilderStore, NodeTemplate } from '../../shared/stores/workflowBuilderStore';
import { Search, ChevronDown, ChevronRight, Star, Trash2, PanelLeftClose, PanelLeft } from 'lucide-react';

// ==========================================
// Category Definitions
// ==========================================
const CATEGORY_LABELS: Record<string, { label: string; order: number }> = {
  control:     { label: 'Control Flow', order: 0 },
  ai:          { label: 'AI & Intelligence', order: 1 },
  integration: { label: 'Integrations', order: 2 },
  logic:       { label: 'Logic Gates', order: 3 },
  utility:     { label: 'Utilities', order: 4 },
};

// ==========================================
// Draggable Node Item
// ==========================================
const DraggableNodeItem: React.FC<{ info: NodeTypeInfo }> = ({ info }) => {
  const onDragStart = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.dataTransfer.setData('application/syncsphere-node-type', info.type);
    event.dataTransfer.effectAllowed = 'move';
  }, [info.type]);

  return (
    <div
      draggable
      onDragStart={onDragStart}
      className="flex items-center gap-2.5 px-3 py-2 rounded-md cursor-grab active:cursor-grabbing
        border border-transparent hover:border-border hover:bg-accent/50
        transition-colors duration-100 group"
      title={info.description}
      role="button"
      aria-label={`Drag to add ${info.label} node`}
    >
      <span className={`${info.color} shrink-0 opacity-80 group-hover:opacity-100 transition-opacity`}>
        {info.icon}
      </span>
      <div className="flex-1 min-w-0">
        <div className="text-xs font-semibold text-foreground truncate">{info.label}</div>
        <div className="text-[10px] text-muted-foreground truncate">{info.description}</div>
      </div>
    </div>
  );
};

// ==========================================
// Node Template Item
// ==========================================
const NodeTemplateItem: React.FC<{ template: NodeTemplate }> = ({ template }) => {
  const { loadNodeTemplate, deleteNodeTemplate } = useWorkflowBuilderStore();
  const info = NODE_TYPE_REGISTRY.find((n) => n.type === template.nodeType);

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-accent/50 border border-transparent hover:border-border transition-colors group">
      <Star className="h-3.5 w-3.5 text-amber-500 shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="text-xs font-semibold text-foreground truncate">{template.name}</div>
        <div className="text-[10px] text-muted-foreground truncate">{info?.label || template.nodeType}</div>
      </div>
      <button
        onClick={() => loadNodeTemplate(template.id, { x: 300, y: 300 })}
        className="text-[10px] text-primary hover:text-primary/80 opacity-0 group-hover:opacity-100 transition-opacity"
        aria-label={`Insert ${template.name} template`}
      >
        Insert
      </button>
      <button
        onClick={() => deleteNodeTemplate(template.id)}
        className="text-muted-foreground hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity"
        aria-label={`Delete ${template.name} template`}
      >
        <Trash2 className="h-3 w-3" />
      </button>
    </div>
  );
};

// ==========================================
// Main Node Palette Component
// ==========================================
export const NodePalette: React.FC = () => {
  const [search, setSearch] = useState('');
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const { isPaletteOpen, togglePalette, nodeTemplates } = useWorkflowBuilderStore();

  // Filtered and grouped nodes
  const filteredGroups = useMemo(() => {
    const lowerSearch = search.toLowerCase();
    const filtered = NODE_TYPE_REGISTRY.filter(
      (n) =>
        n.label.toLowerCase().includes(lowerSearch) ||
        n.description.toLowerCase().includes(lowerSearch) ||
        n.type.toLowerCase().includes(lowerSearch)
    );

    const groups: Record<string, NodeTypeInfo[]> = {};
    for (const node of filtered) {
      if (!groups[node.category]) groups[node.category] = [];
      groups[node.category].push(node);
    }

    return Object.entries(groups)
      .map(([cat, nodes]) => ({
        category: cat,
        label: CATEGORY_LABELS[cat]?.label || cat,
        order: CATEGORY_LABELS[cat]?.order ?? 99,
        nodes,
      }))
      .sort((a, b) => a.order - b.order);
  }, [search]);

  // Filtered templates
  const filteredTemplates = useMemo(() => {
    if (!search) return nodeTemplates;
    const lower = search.toLowerCase();
    return nodeTemplates.filter(
      (t) => t.name.toLowerCase().includes(lower) || t.nodeType.toLowerCase().includes(lower)
    );
  }, [search, nodeTemplates]);

  const toggleCategory = (cat: string) => {
    setCollapsed((prev) => ({ ...prev, [cat]: !prev[cat] }));
  };

  if (!isPaletteOpen) {
    return (
      <button
        onClick={togglePalette}
        className="absolute left-2 top-2 z-10 p-2 rounded-md bg-card border border-border shadow-sm hover:bg-accent transition-colors"
        aria-label="Open node palette"
      >
        <PanelLeft className="h-4 w-4 text-muted-foreground" />
      </button>
    );
  }

  return (
    <div className="w-[260px] h-full bg-card border-r border-border flex flex-col shrink-0 overflow-hidden" role="complementary" aria-label="Node palette">
      {/* Header */}
      <div className="flex items-center justify-between px-3 pt-3 pb-2">
        <h3 className="text-sm font-bold text-foreground">Nodes</h3>
        <button onClick={togglePalette} className="p-1 rounded hover:bg-accent transition-colors" aria-label="Close palette">
          <PanelLeftClose className="h-4 w-4 text-muted-foreground" />
        </button>
      </div>

      {/* Search */}
      <div className="px-3 pb-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search nodes..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-8 pl-8 pr-3 rounded-md border border-border bg-background text-xs text-foreground
              placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            aria-label="Search nodes"
          />
        </div>
      </div>

      {/* Scrollable Node List */}
      <div className="flex-1 overflow-y-auto px-1.5 pb-3 scrollbar-thin">
        {filteredGroups.map((group) => (
          <div key={group.category} className="mb-1">
            <button
              onClick={() => toggleCategory(group.category)}
              className="flex items-center gap-1.5 w-full px-2 py-1.5 text-[10px] font-bold text-muted-foreground uppercase tracking-wider hover:text-foreground transition-colors"
              aria-expanded={!collapsed[group.category]}
            >
              {collapsed[group.category] ? <ChevronRight className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              {group.label}
              <span className="ml-auto text-[9px] font-normal">{group.nodes.length}</span>
            </button>
            {!collapsed[group.category] && (
              <div className="space-y-0.5 pl-1">
                {group.nodes.map((info) => (
                  <DraggableNodeItem key={info.type} info={info} />
                ))}
              </div>
            )}
          </div>
        ))}

        {/* Node Templates Section */}
        {filteredTemplates.length > 0 && (
          <div className="mt-3 pt-3 border-t border-border">
            <div className="flex items-center gap-1.5 px-2 py-1.5 text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
              <Star className="h-3 w-3 text-amber-500" />
              Saved Templates
              <span className="ml-auto text-[9px] font-normal">{filteredTemplates.length}</span>
            </div>
            <div className="space-y-0.5 pl-1">
              {filteredTemplates.map((tpl) => (
                <NodeTemplateItem key={tpl.id} template={tpl} />
              ))}
            </div>
          </div>
        )}

        {/* Empty state */}
        {filteredGroups.length === 0 && filteredTemplates.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Search className="h-8 w-8 text-muted-foreground/40 mb-2" />
            <p className="text-xs text-muted-foreground">No nodes found for &ldquo;{search}&rdquo;</p>
          </div>
        )}
      </div>
    </div>
  );
};
