"use client";
import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { cn } from '../../lib/utils';
import { Play, ShieldAlert, CheckCircle2, AlertCircle, Clock, Search, FolderOpen, RefreshCw, ChevronRight, ChevronDown } from 'lucide-react';

// ==========================================
// 1. Metric Card Component
// ==========================================
interface MetricCardProps {
  title: string;
  value: React.ReactNode;
  description?: string;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  description,
  icon,
  trend,
  className,
}) => {
  return (
    <Card className={cn("overflow-hidden border-border bg-card shadow-sm hover:shadow-md transition-shadow duration-200", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold tracking-tight text-foreground">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
            {trend && (
              <span className={cn("font-medium", trend.isPositive ? "text-emerald-500" : "text-rose-500")}>
                {trend.isPositive ? "+" : ""}{trend.value}%
              </span>
            )}
            {description}
          </p>
        )}
      </CardContent>
    </Card>
  );
};

// ==========================================
// 2. Timeline Components
// ==========================================
interface TimelineProps {
  children: React.ReactNode;
  className?: string;
}

export const Timeline: React.FC<TimelineProps> = ({ children, className }) => {
  return (
    <div className={cn("relative border-l-2 border-border ml-3 pl-6 space-y-6", className)}>
      {children}
    </div>
  );
};

interface TimelineItemProps {
  title: string;
  time?: string;
  description?: string;
  status?: 'success' | 'running' | 'failed' | 'waiting' | 'error' | 'info';
  icon?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
}

export const TimelineItem: React.FC<TimelineItemProps> = ({
  title,
  time,
  description,
  status = 'waiting',
  icon,
  children,
  className,
}) => {
  const dotColor = {
    success: 'bg-emerald-500 ring-emerald-500/20',
    running: 'bg-sky-500 ring-sky-500/20 animate-pulse',
    failed: 'bg-rose-500 ring-rose-500/20',
    error: 'bg-rose-500 ring-rose-500/20',
    waiting: 'bg-muted ring-muted-foreground/10',
    info: 'bg-blue-500 ring-blue-500/20',
  }[status];

  return (
    <div className={cn("relative", className)}>
      <div className={cn("absolute -left-[31px] top-1.5 h-4 w-4 rounded-full border-2 border-background ring-4", dotColor)}>
        {icon && <div className="absolute inset-0 flex items-center justify-center text-[10px] text-white">{icon}</div>}
      </div>
      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between gap-4">
          <span className="font-semibold text-sm text-foreground">{title}</span>
          {time && <span className="text-xs text-muted-foreground">{time}</span>}
        </div>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
        {children}
      </div>
    </div>
  );
};

// ==========================================
// 3. DataGrid Component
// ==========================================
interface DataGridColumn<T> {
  header: string;
  accessor?: keyof T | ((row: T) => React.ReactNode);
  render?: (row: T) => React.ReactNode;
  className?: string;
}

interface DataGridProps<T> {
  columns: DataGridColumn<T>[];
  data: T[];
  searchPlaceholder?: string;
  searchKey?: keyof T;
  onRowClick?: (row: T) => void;
  className?: string;
}

export function DataGrid<T>({
  columns,
  data,
  searchPlaceholder = "Search records...",
  searchKey,
  onRowClick,
  className,
}: DataGridProps<T>) {
  const [query, setQuery] = useState('');

  const filteredData = searchKey && query
    ? data.filter((row) => {
      const value = row[searchKey];
      return String(value).toLowerCase().includes(query.toLowerCase());
    })
    : data;

  return (
    <div className={cn("space-y-4", className)}>
      {searchKey && (
        <div className="relative max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={searchPlaceholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      )}
      <div className="rounded-md border border-border bg-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((col, idx) => (
                <TableHead key={idx} className={col.className}>
                  {col.header}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredData.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="text-center h-24 text-muted-foreground">
                  No records found.
                </TableCell>
              </TableRow>
            ) : (
              filteredData.map((row, rowIdx) => (
                <TableRow
                  key={rowIdx}
                  className={cn(onRowClick && "cursor-pointer hover:bg-muted/30")}
                  onClick={() => onRowClick && onRowClick(row)}
                >
                  {columns.map((col, colIdx) => (
                    <TableCell key={colIdx} className={col.className}>
                      {col.render
                        ? col.render(row)
                        : col.accessor
                          ? typeof col.accessor === 'function'
                            ? col.accessor(row)
                            : (row[col.accessor] as React.ReactNode)
                          : null}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

// ==========================================
// 4. Tree View Components
// ==========================================
export interface TreeItem {
  id: string;
  label: React.ReactNode;
  subLabel?: React.ReactNode;
  children?: TreeItem[];
  icon?: React.ReactNode;
}

interface TreeViewProps {
  items?: TreeItem[];
  children?: React.ReactNode;
  className?: string;
}

export const TreeView: React.FC<TreeViewProps> = ({ items, children, className }) => {
  const renderItem = (item: TreeItem) => {
    return (
      <TreeItem
        key={item.id}
        label={
          <div className="flex items-center gap-2">
            {item.icon}
            <div className="flex flex-col">
              <span className="text-sm">{item.label}</span>
              {item.subLabel && <span className="text-[10px] text-muted-foreground">{item.subLabel}</span>}
            </div>
          </div>
        }
      >
        {item.children && item.children.map(renderItem)}
      </TreeItem>
    );
  };

  return (
    <div className={cn("space-y-1.5 pl-2", className)}>
      {items ? items.map(renderItem) : children}
    </div>
  );
};

interface TreeItemProps {
  label: React.ReactNode;
  children?: React.ReactNode;
  defaultExpanded?: boolean;
  className?: string;
}

export const TreeItem: React.FC<TreeItemProps> = ({
  label,
  children,
  defaultExpanded = false,
  className,
}) => {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const hasChildren = !!children;

  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <div
        className="flex items-center gap-2 cursor-pointer py-1 px-2 rounded-md hover:bg-muted/50 transition-colors"
        onClick={() => hasChildren && setExpanded(!expanded)}
      >
        {hasChildren ? (
          expanded ? <ChevronDown className="h-4 w-4 text-muted-foreground" /> : <ChevronRight className="h-4 w-4 text-muted-foreground" />
        ) : (
          <div className="w-4" />
        )}
        <div className="text-sm font-medium flex-1">{label}</div>
      </div>
      {hasChildren && expanded && (
        <div className="pl-6 border-l border-border/60 ml-3 space-y-1">
          {children}
        </div>
      )}
    </div>
  );
};

// ==========================================
// 5. Search Bar Component
// ==========================================
interface SearchBarProps {
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = "Search...",
  value,
  onChange,
  className,
}) => {
  return (
    <div className={cn("relative w-full", className)}>
      <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
      <Input
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="pl-9"
      />
    </div>
  );
};

// ==========================================
// 6. Empty State Component
// ==========================================
interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon = <FolderOpen className="h-10 w-10 text-muted-foreground" />,
  actionLabel,
  onAction,
  className,
}) => {
  return (
    <div className={cn("flex flex-col items-center justify-center p-8 text-center rounded-lg border border-dashed border-border bg-card/50 min-h-[300px]", className)}>
      <div className="p-3 bg-muted rounded-full mb-4">{icon}</div>
      <h3 className="font-semibold text-lg text-foreground mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground max-w-sm mb-6">{description}</p>
      {actionLabel && onAction && (
        <Button onClick={onAction} className="shadow-sm">
          {actionLabel}
        </Button>
      )}
    </div>
  );
};

// ==========================================
// 7. Error State Component
// ==========================================
interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "An Error Occurred",
  message,
  onRetry,
  className,
}) => {
  return (
    <div className={cn("flex flex-col items-center justify-center p-8 text-center rounded-lg border border-rose-500/20 bg-rose-500/5 min-h-[250px]", className)}>
      <div className="p-3 bg-rose-500/10 text-rose-500 rounded-full mb-4">
        <ShieldAlert className="h-10 w-10" />
      </div>
      <h3 className="font-semibold text-lg text-rose-500 mb-1">{title}</h3>
      <p className="text-sm text-rose-500/85 max-w-sm mb-6">{message}</p>
      {onRetry && (
        <Button variant="outline" onClick={onRetry} className="border-rose-500/25 hover:bg-rose-500/10 text-rose-500">
          <RefreshCw className="h-4 w-4 mr-2" /> Retry
        </Button>
      )}
    </div>
  );
};

// ==========================================
// 8. Skeleton Loader Component
// ==========================================
interface SkeletonLoaderProps {
  rows?: number;
  className?: string;
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  rows = 3,
  className,
}) => {
  return (
    <div className={cn("space-y-4 w-full animate-pulse", className)}>
      {Array.from({ length: rows }).map((_, idx) => (
        <div key={idx} className="flex flex-col gap-2 p-4 rounded-lg border border-border bg-card/60">
          <div className="h-4 w-1/3 bg-muted rounded" />
          <div className="h-3 w-2/3 bg-muted rounded" />
          <div className="h-3 w-1/2 bg-muted rounded" />
        </div>
      ))}
    </div>
  );
};

// ==========================================
// 9. Workflow Card Component
// ==========================================
interface WorkflowCardProps {
  workflow: {
    id: string;
    name: string;
    description?: string;
    version: number;
    state: 'DRAFT' | 'PUBLISHED';
    updated_at: string;
  };
  onSelect: (id: string) => void;
  onRun?: (id: string) => void;
  className?: string;
}

export const WorkflowCard: React.FC<WorkflowCardProps> = ({
  workflow,
  onSelect,
  onRun,
  className,
}) => {
  return (
    <Card className={cn("border-border bg-card shadow-sm hover:shadow-md hover:border-primary/20 transition-all duration-200 cursor-pointer flex flex-col justify-between min-h-[160px]", className)}
      onClick={() => onSelect(workflow.id)}>
      <CardHeader className="p-4 pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-col gap-0.5">
            <span className="font-semibold text-sm text-foreground line-clamp-1">{workflow.name}</span>
            <span className="text-xs text-muted-foreground">Version {workflow.version}</span>
          </div>
          <Badge variant={workflow.state === 'PUBLISHED' ? 'default' : 'secondary'} className="text-[10px] font-semibold px-2 py-0.5">
            {workflow.state}
          </Badge>
        </div>
        {workflow.description && (
          <CardDescription className="text-xs text-muted-foreground line-clamp-2 mt-1">
            {workflow.description}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="p-4 pt-2 flex items-center justify-between border-t border-border/40 bg-muted/10">
        <span className="text-[10px] text-muted-foreground">
          Updated: {new Date(workflow.updated_at).toLocaleDateString()}
        </span>
        {workflow.state === 'PUBLISHED' && onRun && (
          <Button
            size="sm"
            variant="ghost"
            className="h-7 px-2 hover:bg-emerald-500/10 hover:text-emerald-500 text-muted-foreground"
            onClick={(e) => {
              e.stopPropagation();
              onRun(workflow.id);
            }}
          >
            <Play className="h-3.5 w-3.5 mr-1" /> Run
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

// ==========================================
// 10. Execution Card Component
// ==========================================
interface ExecutionCardProps {
  execution: {
    id: string;
    workflow_id: string;
    workflow_name?: string;
    status: 'running' | 'completed' | 'success' | 'failed' | 'paused' | 'partial' | 'cancelled';
    created_at?: string;
    started_at?: string;
  };
  onSelect?: (id: string) => void;
  className?: string;
}

export const ExecutionCard: React.FC<ExecutionCardProps> = ({
  execution,
  onSelect,
  className,
}) => {
  const statusConfigs = {
    running: { label: 'Running', color: 'text-sky-500 bg-sky-500/10 border-sky-500/25', icon: <RefreshCw className="h-3 w-3 animate-spin" /> },
    completed: { label: 'Completed', color: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/25', icon: <CheckCircle2 className="h-3 w-3" /> },
    success: { label: 'Success', color: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/25', icon: <CheckCircle2 className="h-3 w-3" /> },
    failed: { label: 'Failed', color: 'text-rose-500 bg-rose-500/10 border-rose-500/25', icon: <AlertCircle className="h-3 w-3" /> },
    paused: { label: 'Paused', color: 'text-amber-500 bg-amber-500/10 border-amber-500/25', icon: <Clock className="h-3 w-3" /> },
    partial: { label: 'Partial', color: 'text-amber-500 bg-amber-500/10 border-amber-500/25', icon: <CheckCircle2 className="h-3 w-3" /> },
    cancelled: { label: 'Cancelled', color: 'text-muted-foreground bg-muted/10 border-border', icon: <AlertCircle className="h-3 w-3" /> },
  };

  const currentStatus = statusConfigs[execution.status] || statusConfigs.cancelled;

  return (
    <Card className={cn("border-border bg-card shadow-sm hover:shadow-md hover:border-primary/20 transition-all duration-200 cursor-pointer", className)}
      onClick={() => onSelect && onSelect(execution.id)}>
      <CardContent className="p-4 flex items-center justify-between">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm text-foreground">Run #{execution.id.slice(-6)}</span>
            <Badge className={cn("text-xs font-semibold px-2 py-0.5 border flex items-center gap-1", currentStatus.color)}>
              {currentStatus.icon} {currentStatus.label}
            </Badge>
          </div>
          <span className="text-xs text-muted-foreground">Workflow: {execution.workflow_name || execution.workflow_id}</span>
        </div>
        <span className="text-xs text-muted-foreground">{execution.started_at ? new Date(execution.started_at).toLocaleString() : execution.created_at ? new Date(execution.created_at).toLocaleString() : ''}</span>
      </CardContent>
    </Card>
  );
};
