'use client';

import React from 'react';
import { useWorkflowBuilderStore, WorkflowVersion } from '../../shared/stores/workflowBuilderStore';
import {
  X, History, RotateCcw, GitBranch, Eye, CheckCircle,
  FileText, Clock, ArrowRight,
} from 'lucide-react';

// ==========================================
// Version History Panel
// ==========================================
export const WorkflowVersionHistory: React.FC = () => {
  const {
    versions, activeVersion, isVersionHistoryOpen, toggleVersionHistory,
    rollbackToVersion, workflowState,
  } = useWorkflowBuilderStore();

  if (!isVersionHistoryOpen) return null;

  const sortedVersions = [...versions].sort((a, b) => b.version - a.version);

  return (
    <div className="absolute left-0 top-0 w-[340px] h-full bg-card border-r border-border flex flex-col z-20 shadow-xl overflow-hidden" role="dialog" aria-label="Version history">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-3 pb-2 border-b border-border">
        <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
          <History className="h-4 w-4 text-violet-500" />
          Version History
        </h3>
        <button onClick={toggleVersionHistory} className="p-1 rounded hover:bg-accent transition-colors" aria-label="Close version history">
          <X className="h-4 w-4 text-muted-foreground" />
        </button>
      </div>

      {/* Current State */}
      <div className="px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2 mb-1">
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
            workflowState === 'PUBLISHED'
              ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20'
              : workflowState === 'ARCHIVED'
              ? 'bg-muted text-muted-foreground border border-border'
              : 'bg-amber-500/10 text-amber-600 border border-amber-500/20'
          }`}>
            {workflowState}
          </span>
          <span className="text-xs text-muted-foreground">Current: v{activeVersion}</span>
        </div>
      </div>

      {/* Version List */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1.5 scrollbar-thin">
        {sortedVersions.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <GitBranch className="h-10 w-10 text-muted-foreground/30 mb-3" />
            <p className="text-sm text-muted-foreground font-medium">No versions saved yet</p>
            <p className="text-xs text-muted-foreground mt-1">Save a draft or publish to create a version.</p>
          </div>
        )}

        {sortedVersions.map((version) => (
          <VersionCard
            key={version.version}
            version={version}
            isActive={version.version === activeVersion}
            onRollback={() => rollbackToVersion(version.version)}
          />
        ))}
      </div>
    </div>
  );
};

// ==========================================
// Version Card
// ==========================================
const VersionCard: React.FC<{
  version: WorkflowVersion;
  isActive: boolean;
  onRollback: () => void;
}> = ({ version, isActive, onRollback }) => {
  const dateStr = new Date(version.createdAt).toLocaleString();
  const nodeCount = version.nodes.length;
  const edgeCount = version.edges.length;

  return (
    <div
      className={`
        rounded-lg border p-3 transition-all
        ${isActive
          ? 'border-primary/40 bg-primary/5 ring-1 ring-primary/20'
          : 'border-border bg-background hover:border-border hover:bg-accent/30'
        }
      `}
    >
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-foreground">v{version.version}</span>
          <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
            version.state === 'PUBLISHED'
              ? 'bg-emerald-500/10 text-emerald-600'
              : 'bg-amber-500/10 text-amber-600'
          }`}>
            {version.state}
          </span>
          {isActive && (
            <span className="flex items-center gap-0.5 text-[9px] text-primary font-bold">
              <CheckCircle className="h-3 w-3" /> Active
            </span>
          )}
        </div>
      </div>

      {version.label && (
        <p className="text-xs text-foreground mb-1">{version.label}</p>
      )}

      <div className="flex items-center gap-3 text-[10px] text-muted-foreground mb-2">
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {dateStr}
        </span>
      </div>

      <div className="flex items-center gap-3 text-[10px] text-muted-foreground mb-2">
        <span>{nodeCount} nodes</span>
        <span>•</span>
        <span>{edgeCount} edges</span>
      </div>

      {!isActive && (
        <button
          onClick={onRollback}
          className="flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 font-medium transition-colors"
          aria-label={`Rollback to version ${version.version}`}
        >
          <RotateCcw className="h-3 w-3" />
          Rollback to this version
        </button>
      )}
    </div>
  );
};
