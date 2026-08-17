'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tasksApi } from '../../../shared/services/api';
import { API_BASE_URL } from '../../../shared/services/api-client';
import { Task, TaskPriority, TaskStatus } from '../../../shared/types';
import { toast } from 'sonner';
import { format, isValid, parseISO } from 'date-fns';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Badge } from '../../../components/ui/badge';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '../../../components/ui/dialog';

import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '../../../components/ui/select';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '../../../components/ui/table';
import {
    Plus,
    Search,
    Pencil,
    Trash2,
    CheckCircle2,
    Circle,
    Timer,
    Flag,
    User,
    Calendar,
    Bot,
    Send,
    Loader2,
    X,
    ClipboardList,
    ChevronDown,
    ChevronUp,
    Eye,
    Sparkles,
} from 'lucide-react';
import { cn } from '../../../lib/utils';
import { PlanWithAIModal } from './PlanWithAIModal';
import { TaskCreationModal, TaskCreationData } from './TaskCreationModal';
import { useWorkflowBuilderStore } from '../../../shared/stores/workflowBuilderStore';

// ─────────────────────────────────────────
//  Types
// ─────────────────────────────────────────
type WizardStep =
    | 'title'
    | 'description'
    | 'assignee'
    | 'priority'
    | 'status'
    | 'due_date'
    | 'confirm';

interface WizardMessage {
    role: 'bot' | 'user';
    text: string;
}

interface WizardData {
    title: string;
    description: string;
    assigned_to: string;
    priority: TaskPriority | '';
    status: TaskStatus | '';
    due_date: string;
}

// ─────────────────────────────────────────
//  Helpers
// ─────────────────────────────────────────
function priorityColor(p: TaskPriority) {
    switch (p) {
        case 'High': return 'bg-red-500/15 text-red-400 border-red-500/30';
        case 'Medium': return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
        case 'Low': return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
        default: return 'bg-muted text-muted-foreground';
    }
}

function statusIcon(s: TaskStatus) {
    switch (s) {
        case 'Completed': return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />;
        case 'In Progress': return <Timer className="h-3.5 w-3.5 text-blue-400" />;
        default: return <Circle className="h-3.5 w-3.5 text-muted-foreground" />;
    }
}

function statusColor(s: TaskStatus) {
    switch (s) {
        case 'Completed': return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
        case 'In Progress': return 'bg-blue-500/15 text-blue-400 border-blue-500/30';
        default: return 'bg-muted/60 text-muted-foreground border-border';
    }
}

function formatDate(d: string | null) {
    if (!d) return '—';
    const parsed = parseISO(d);
    return isValid(parsed) ? format(parsed, 'MMM d, yyyy') : d;
}

// ─────────────────────────────────────────
//  Wizard bot prompts per step
// ─────────────────────────────────────────
const STEP_PROMPTS: Record<WizardStep, string> = {
    title: "What's the task title?",
    description: 'Give it a brief description (or skip — press Enter to skip).',
    assignee: "Who should this be assigned to? (Enter a name, or skip.)",
    priority: 'Choose a priority — High, Medium, or Low.',
    status: "What's the initial status — Pending, In Progress, or Completed?",
    due_date: 'When is it due? (YYYY-MM-DD format, or skip.)',
    confirm: '',   // handled dynamically
};

const STEP_ORDER: WizardStep[] = ['title', 'description', 'assignee', 'priority', 'status', 'due_date', 'confirm'];

// ─────────────────────────────────────────
//  Conversational Wizard Modal
// ─────────────────────────────────────────
function TaskWizard({
    open,
    onClose,
    onCreate,
    isCreating,
}: {
    open: boolean;
    onClose: () => void;
    onCreate: (data: Omit<WizardData, ''>) => void;
    isCreating: boolean;
}) {
    const [step, setStep] = useState<WizardStep>('title');
    const [messages, setMessages] = useState<WizardMessage[]>([]);
    const [input, setInput] = useState('');
    const [data, setData] = useState<WizardData>({
        title: '', description: '', assigned_to: '', priority: '', status: '', due_date: '',
    });
    const bottomRef = useRef<HTMLDivElement>(null);

    // Reset when dialog opens
    useEffect(() => {
        if (open) {
            setStep('title');
            setData({ title: '', description: '', assigned_to: '', priority: '', status: '', due_date: '' });
            setInput('');
            setMessages([{ role: 'bot', text: STEP_PROMPTS.title }]);
        }
    }, [open]);

    // Scroll to bottom of chat on new messages
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const pushBot = (text: string) =>
        setMessages(prev => [...prev, { role: 'bot', text }]);

    const handleSelect = (value: string) => {
        setInput(value);
    };

    const advance = (userInput: string) => {
        const trimmed = userInput.trim();
        setMessages(prev => [...prev, { role: 'user', text: trimmed || '(skipped)' }]);
        setInput('');

        const next = (nextStep: WizardStep, updatedData?: Partial<WizardData>) => {
            const newData = { ...data, ...updatedData };
            setData(newData);
            setStep(nextStep);
            if (nextStep === 'confirm') {
                pushBot(
                    `Great! Here's your task summary:\n\n` +
                    `📌 **Title:** ${newData.title}\n` +
                    `📝 **Description:** ${newData.description || '—'}\n` +
                    `👤 **Assignee:** ${newData.assigned_to || '—'}\n` +
                    `🚦 **Priority:** ${newData.priority || 'Medium'}\n` +
                    `⏳ **Status:** ${newData.status || 'Pending'}\n` +
                    `📅 **Due Date:** ${newData.due_date || '—'}\n\n` +
                    `Shall I create this task? Click **Create Task** or type "edit" to start over.`
                );
            } else {
                pushBot(STEP_PROMPTS[nextStep]);
            }
        };

        switch (step) {
            case 'title':
                if (!trimmed) { pushBot("A title is required! What should the task be called?"); return; }
                next('description', { title: trimmed });
                break;
            case 'description':
                next('assignee', { description: trimmed });
                break;
            case 'assignee':
                next('priority', { assigned_to: trimmed });
                break;
            case 'priority': {
                const p = ['High', 'Medium', 'Low'].find(x => x.toLowerCase() === trimmed.toLowerCase()) as TaskPriority | undefined;
                if (!p && trimmed) { pushBot("Please choose: High, Medium, or Low."); return; }
                next('status', { priority: p || 'Medium' });
                break;
            }
            case 'status': {
                const s = ['Pending', 'In Progress', 'Completed'].find(
                    x => x.toLowerCase() === trimmed.toLowerCase()
                ) as TaskStatus | undefined;
                if (!s && trimmed) { pushBot("Please choose: Pending, In Progress, or Completed."); return; }
                next('due_date', { status: s || 'Pending' });
                break;
            }
            case 'due_date':
                next('confirm', { due_date: trimmed });
                break;
            case 'confirm':
                if (trimmed.toLowerCase() === 'edit') {
                    setStep('title');
                    setData({ title: '', description: '', assigned_to: '', priority: '', status: '', due_date: '' });
                    pushBot("No problem! Let's start over.\n\n" + STEP_PROMPTS.title);
                } else {
                    onCreate(data);
                }
                break;
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') advance(input);
    };

    // Quick select chips for priority/status steps
    const quickOptions: Record<string, string[]> = {
        priority: ['High', 'Medium', 'Low'],
        status: ['Pending', 'In Progress', 'Completed'],
    };

    return (
        <Dialog open={open} onOpenChange={v => !v && onClose()}>
            <DialogContent className="sm:max-w-[520px] p-0 overflow-hidden flex flex-col gap-0 max-h-[90vh]">
                {/* Header */}
                <DialogHeader className="flex flex-row items-center justify-between px-5 py-4 border-b border-border shrink-0">
                    <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                            <Bot className="h-4 w-4 text-primary" />
                        </div>
                        <DialogTitle className="text-base font-semibold">New Task — AI Assistant</DialogTitle>
                    </div>
                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}>
                        <X className="h-4 w-4" />
                    </Button>
                </DialogHeader>

                {/* Progress dots */}
                <div className="flex items-center gap-1.5 px-5 py-2.5 bg-muted/40 border-b border-border shrink-0">
                    {STEP_ORDER.filter(s => s !== 'confirm').map((s, i) => (
                        <div
                            key={s}
                            className={cn(
                                "h-1.5 rounded-full transition-all duration-300",
                                STEP_ORDER.indexOf(step) > i ? "w-6 bg-primary" :
                                    STEP_ORDER.indexOf(step) === i ? "w-4 bg-primary/60" : "w-2 bg-muted-foreground/30"
                            )}
                        />
                    ))}
                    <span className="ml-auto text-[11px] text-muted-foreground">
                        {step === 'confirm' ? 'Review' : `Step ${STEP_ORDER.indexOf(step) + 1} / 6`}
                    </span>
                </div>

                {/* Chat thread */}
                <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3 min-h-0">
                    {messages.map((msg, i) => (
                        <div
                            key={i}
                            className={cn(
                                "flex gap-2",
                                msg.role === 'user' ? "justify-end" : "justify-start"
                            )}
                        >
                            {msg.role === 'bot' && (
                                <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 mt-0.5">
                                    <Bot className="h-3 w-3 text-primary" />
                                </div>
                            )}
                            <div
                                className={cn(
                                    "rounded-2xl px-3.5 py-2 text-sm max-w-[80%] whitespace-pre-wrap leading-relaxed",
                                    msg.role === 'bot'
                                        ? "bg-muted text-foreground rounded-tl-sm"
                                        : "bg-primary text-primary-foreground rounded-tr-sm"
                                )}
                            >
                                {msg.text}
                            </div>
                        </div>
                    ))}
                    <div ref={bottomRef} />
                </div>

                {/* Quick-select chips */}
                {quickOptions[step] && (
                    <div className="flex flex-wrap gap-2 px-5 pb-2 shrink-0">
                        {quickOptions[step].map(opt => (
                            <button
                                key={opt}
                                onClick={() => advance(opt)}
                                className="px-3 py-1 text-xs rounded-full border border-border hover:bg-muted transition-colors"
                            >
                                {opt}
                            </button>
                        ))}
                    </div>
                )}

                {/* Input area */}
                <div className="px-5 py-3 border-t border-border shrink-0">
                    {step === 'confirm' ? (
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                className="flex-1"
                                onClick={() => { setStep('title'); setData({ title: '', description: '', assigned_to: '', priority: '', status: '', due_date: '' }); pushBot("No problem! Let's start over.\n\n" + STEP_PROMPTS.title); }}
                            >
                                Start Over
                            </Button>
                            <Button
                                className="flex-1"
                                onClick={() => onCreate(data)}
                                disabled={isCreating}
                            >
                                {isCreating ? <><Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" /> Creating…</> : 'Create Task'}
                            </Button>
                        </div>
                    ) : (
                        <div className="flex items-center gap-2">
                            <Input
                                value={input}
                                onChange={e => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Type your answer…"
                                className="flex-1 h-9 text-sm"
                                autoFocus
                            />
                            <Button size="icon" className="h-9 w-9 shrink-0" onClick={() => advance(input)}>
                                <Send className="h-3.5 w-3.5" />
                            </Button>
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
}

// ─────────────────────────────────────────
//  Edit Modal
// ─────────────────────────────────────────
function EditTaskModal({ task, onClose, onSave }: { task: Task; onClose: () => void; onSave: (id: string, data: Partial<Task>) => void }) {
    const [form, setForm] = useState({
        title: task.title,
        description: task.description,
        assigned_to: task.assigned_to,
        priority: task.priority,
        status: task.status,
        due_date: task.due_date || '',
    });

    return (
        <Dialog open onOpenChange={v => !v && onClose()}>
            <DialogContent className="sm:max-w-[460px]">
                <DialogHeader>
                    <DialogTitle>Edit Task</DialogTitle>
                </DialogHeader>
                <div className="space-y-3 mt-2">
                    <div>
                        <label className="text-xs text-muted-foreground mb-1 block">Title</label>
                        <Input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
                    </div>
                    <div>
                        <label className="text-xs text-muted-foreground mb-1 block">Description</label>
                        <Input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
                    </div>
                    <div>
                        <label className="text-xs text-muted-foreground mb-1 block">Assigned To</label>
                        <Input value={form.assigned_to} onChange={e => setForm({ ...form, assigned_to: e.target.value })} />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="text-xs text-muted-foreground mb-1 block">Priority</label>
                            <Select value={form.priority} onValueChange={v => setForm({ ...form, priority: v as TaskPriority })}>
                                <SelectTrigger className="h-8 text-xs"><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="High">High</SelectItem>
                                    <SelectItem value="Medium">Medium</SelectItem>
                                    <SelectItem value="Low">Low</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div>
                            <label className="text-xs text-muted-foreground mb-1 block">Status</label>
                            <Select value={form.status} onValueChange={v => setForm({ ...form, status: v as TaskStatus })}>
                                <SelectTrigger className="h-8 text-xs"><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Pending">Pending</SelectItem>
                                    <SelectItem value="In Progress">In Progress</SelectItem>
                                    <SelectItem value="Completed">Completed</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <div>
                        <label className="text-xs text-muted-foreground mb-1 block">Due Date (YYYY-MM-DD)</label>
                        <Input value={form.due_date} onChange={e => setForm({ ...form, due_date: e.target.value })} placeholder="2026-08-15" />
                    </div>
                </div>
                <div className="flex gap-2 mt-4">
                    <Button variant="outline" className="flex-1" onClick={onClose}>Cancel</Button>
                    <Button className="flex-1" onClick={() => onSave(task.id, form)}>Save Changes</Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}

// ─────────────────────────────────────────
//  Delete Action Modal
// ─────────────────────────────────────────
function DeleteTaskModal({ task, onClose, onConfirm, isDeleting }: { task: Task; onClose: () => void; onConfirm: (id: string) => void; isDeleting: boolean }) {
    return (
        <Dialog open onOpenChange={v => !v && onClose()}>
            <DialogContent className="sm:max-w-[400px]">
                <DialogHeader>
                    <DialogTitle>Delete Task?</DialogTitle>
                </DialogHeader>
                <div className="space-y-3 mt-2 text-sm text-muted-foreground">
                    <p>Are you sure you want to delete <span className="font-semibold text-foreground">"{task.title}"</span>?</p>
                    <p>This action cannot be undone.</p>
                </div>
                <div className="flex gap-2 mt-4">
                    <Button variant="outline" className="flex-1" onClick={onClose} disabled={isDeleting}>Cancel</Button>
                    <Button className="flex-1" variant="destructive" onClick={() => onConfirm(task.id)} disabled={isDeleting}>
                        {isDeleting ? <><Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" /> Deleting...</> : 'Delete Task'}
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}


// ─────────────────────────────────────────
//  Detail Drawer / Sheet
// ─────────────────────────────────────────
function TaskDetailPanel({ task, onClose }: { task: Task; onClose: () => void }) {
    return (
        <div className="fixed inset-y-0 right-0 z-50 w-full max-w-sm shadow-2xl bg-card border-l border-border flex flex-col">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
                <span className="font-semibold text-sm">Task Details</span>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}><X className="h-4 w-4" /></Button>
            </div>
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
                <div>
                    <h2 className="font-semibold text-base">{task.title}</h2>
                    <p className="text-sm text-muted-foreground mt-1">{task.description || 'No description.'}</p>
                </div>
                <div className="flex gap-2 flex-wrap">
                    <Badge variant="outline" className={cn("text-xs border", priorityColor(task.priority))}>
                        <Flag className="h-3 w-3 mr-1" /> {task.priority}
                    </Badge>
                    <Badge variant="outline" className={cn("text-xs border flex items-center gap-1", statusColor(task.status))}>
                        {statusIcon(task.status)} {task.status}
                    </Badge>
                </div>
                <div className="rounded-lg border border-border p-3 space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                        <User className="h-3.5 w-3.5" />
                        <span className="text-xs">Assignee</span>
                        <span className="ml-auto font-medium text-foreground">{task.assigned_to || '—'}</span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                        <Calendar className="h-3.5 w-3.5" />
                        <span className="text-xs">Due Date</span>
                        <span className="ml-auto font-medium text-foreground">{formatDate(task.due_date)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                        <Calendar className="h-3.5 w-3.5" />
                        <span className="text-xs">Created</span>
                        <span className="ml-auto font-medium text-foreground">{formatDate(task.created_at)}</span>
                    </div>
                </div>
                {task.automations && task.automations.length > 0 && (
                    <div className="mt-6 border-t border-border pt-4">
                        <h3 className="font-semibold text-sm mb-3">Automation Integrations</h3>
                        <div className="space-y-3">
                            {task.automations.map((a, i) => (
                                <div key={i} className="rounded-md border border-border p-3 bg-muted/20 text-xs">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="font-semibold capitalize text-foreground">{a.action.replace('_', ' ').replace('.', ' — ')}</span>
                                        {a.status === 'blocked' ? (
                                            <Badge variant="secondary" className="bg-amber-500/10 text-amber-600 border-none uppercase text-[10px] font-bold">
                                                AUTHORIZATION REQUIRED
                                            </Badge>
                                        ) : (
                                            <Badge variant="secondary" className={cn(
                                                "capitalize",
                                                a.status === 'success' ? 'bg-emerald-500/10 text-emerald-500 border-none' :
                                                    a.status === 'failed' ? 'bg-red-500/10 text-red-500 border-none' :
                                                        a.status === 'executing' ? 'bg-blue-500/10 text-blue-500 border-none' : 'bg-muted text-muted-foreground border-none'
                                            )}>{a.status}</Badge>
                                        )}
                                    </div>
                                    <p className="text-muted-foreground text-[10px] truncate max-w-full font-mono">{JSON.stringify(a.config)}</p>

                                    {a.error && (
                                        <div className="mt-3">
                                            <p className="text-amber-800 text-xs font-medium bg-amber-500/10 p-2.5 rounded whitespace-pre-wrap">{a.error}</p>
                                            {a.status === 'blocked' && (
                                                <Button
                                                    size="sm"
                                                    className="mt-2 text-xs h-7 w-full border-amber-500/30 bg-card hover:bg-amber-500/10 text-amber-600"
                                                    variant="outline"
                                                    onClick={() => {
                                                        const pKey = a.action.startsWith('slack') ? 'slack' : 'google';
                                                        let reqAcctStr = pKey;
                                                        if (a.config?.google_email && pKey === 'google') reqAcctStr = `google:${a.config.google_email}`;
                                                        if (a.config?.slack_workspace && pKey === 'slack') reqAcctStr = `slack:${a.config.slack_workspace}`;
                                                        try {
                                                            const eObj = JSON.parse(String(a.error));
                                                            if (eObj.account) reqAcctStr = `${pKey}:${eObj.account}`;
                                                        } catch { }

                                                        const requestedAccount = reqAcctStr.includes(':') ? reqAcctStr.split(':')[1] : undefined;
                                                        import('../../../shared/services/api-client').then(({ integrationApi, API_BASE_URL }) => {
                                                            if (pKey === 'google') integrationApi.connectGoogle(requestedAccount);
                                                            else if (pKey === 'slack') integrationApi.connectSlack(requestedAccount);
                                                            else window.location.href = `${API_BASE_URL}/v1/connect/${pKey}`;
                                                        });
                                                    }}
                                                >
                                                    Connect {
                                                        (() => {
                                                            let reqAcctStr = a.action.startsWith('slack') ? 'slack' : 'google';
                                                            if (a.config?.google_email && reqAcctStr === 'google') reqAcctStr = `google:${a.config.google_email}`;
                                                            try { const eo = JSON.parse(String(a.error)); if (eo.account) reqAcctStr = `${reqAcctStr}:${eo.account}`; } catch { }
                                                            return reqAcctStr.includes(':') ? reqAcctStr.split(':')[1] : reqAcctStr.charAt(0).toUpperCase() + reqAcctStr.slice(1);
                                                        })()
                                                    }
                                                </Button>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

// ─────────────────────────────────────────
//  Main Tasks Page
// ─────────────────────────────────────────
export default function TasksPage() {
    const qc = useQueryClient();

    const { data: oauthStatus } = useQuery({
        queryKey: ['connector-status'],
        queryFn: async () => {
            const res = await fetch(`${API_BASE_URL}/v1/connect/status`, { credentials: 'include' });
            if (res.status !== 200) return { google: { connected: false }, slack: { connected: false } };
            return res.json();
        },
        refetchOnWindowFocus: true,
        refetchOnMount: true,
    });

    const [search, setSearch] = useState('');
    const [filterPriority, setFilterPriority] = useState<string>('all');
    const [filterStatus, setFilterStatus] = useState<string>('all');
    const [sortField, setSortField] = useState<keyof Task>('created_at');
    const [sortAsc, setSortAsc] = useState(false);
    const [showWizard, setShowWizard] = useState(false);
    const [showPlanAI, setShowPlanAI] = useState(false);

    const { activePromptContext } = useWorkflowBuilderStore();

    useEffect(() => {
        if (typeof window !== 'undefined' && sessionStorage.getItem('pending_ai_plan')) {
            setShowPlanAI(true);
        }
    }, []);

    useEffect(() => {
        if (activePromptContext && !showPlanAI) {
            setShowPlanAI(true);
        }
    }, [activePromptContext, showPlanAI]);

    const [editTask, setEditTask] = useState<Task | null>(null);
    const [detailTask, setDetailTask] = useState<Task | null>(null);
    const [deleteTask, setDeleteTask] = useState<Task | null>(null);

    const { data: tasks = [], isLoading, error } = useQuery({
        queryKey: ['tasks'],
        queryFn: () => tasksApi.listTasks(),
    });

    const createMutation = useMutation({
        mutationFn: (payload: Parameters<typeof tasksApi.createTask>[0]) => tasksApi.createTask(payload),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['tasks'] });
            toast.success('Task created', { description: 'Automations have been started' });
            setShowWizard(false);
        },
        onError: (e: any) => toast.error('Failed to create task', { description: e?.message }),
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<Task> }) => tasksApi.updateTask(id, data),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['tasks'] });
            toast.success('Task updated');
            setEditTask(null);
        },
        onError: (e: any) => toast.error('Failed to update task', { description: e?.message }),
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => tasksApi.deleteTask(id),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['tasks'] });
            toast.success('Task deleted');
            setDeleteTask(null);
        },
        onError: (e: any) => toast.error('Failed to delete task', { description: e?.message }),
    });

    const handleCreate = (data: TaskCreationData) => {
        createMutation.mutate({
            title: data.title,
            description: data.description || undefined,
            assigned_to: data.assigned_to || undefined,
            priority: data.priority,
            status: data.status,
            due_date: data.due_date || null,
            automations: data.automations,
        });
    };

    const handleSortToggle = (field: keyof Task) => {
        if (sortField === field) setSortAsc(prev => !prev);
        else { setSortField(field); setSortAsc(true); }
    };

    // Filter + sort
    const filtered = [...tasks]
        .filter(t => {
            const matchesSearch = t.title.toLowerCase().includes(search.toLowerCase()) ||
                (t.assigned_to?.toLowerCase().includes(search.toLowerCase()) ?? false);
            const matchesPriority = filterPriority === 'all' || t.priority === filterPriority;
            const matchesStatus = filterStatus === 'all' || t.status === filterStatus;
            return matchesSearch && matchesPriority && matchesStatus;
        })
        .sort((a, b) => {
            const av = a[sortField] ?? '';
            const bv = b[sortField] ?? '';
            return sortAsc ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
        });

    // Stats
    const stats = {
        total: tasks.length,
        pending: tasks.filter(t => t.status === 'Pending').length,
        inProgress: tasks.filter(t => t.status === 'In Progress').length,
        completed: tasks.filter(t => t.status === 'Completed').length,
    };

    const SortIcon = ({ field }: { field: keyof Task }) => (
        sortField === field
            ? sortAsc ? <ChevronUp className="h-3 w-3 ml-1 text-primary" /> : <ChevronDown className="h-3 w-3 ml-1 text-primary" />
            : <ChevronDown className="h-3 w-3 ml-1 opacity-30" />
    );

    return (
        <div className="relative flex-1 flex flex-col overflow-hidden bg-background">
            {/* Side detail panel overlay */}
            {detailTask && (
                <>
                    <div className="fixed inset-0 z-40 bg-black/40 backdrop-blur-[2px]" onClick={() => setDetailTask(null)} />
                    <TaskDetailPanel task={detailTask} onClose={() => setDetailTask(null)} />
                </>
            )}

            {/* Edit modal */}
            {editTask && (
                <EditTaskModal
                    task={editTask}
                    onClose={() => setEditTask(null)}
                    onSave={(id, data) => updateMutation.mutate({ id, data })}
                />
            )}

            {/* Delete modal */}
            {deleteTask && (
                <DeleteTaskModal
                    task={deleteTask}
                    onClose={() => setDeleteTask(null)}
                    onConfirm={(id) => deleteMutation.mutate(id)}
                    isDeleting={deleteMutation.isPending}
                />
            )}

            {/* Creation wizard (now explicitly TaskCreationModal) */}
            <TaskCreationModal
                open={showWizard}
                onClose={() => setShowWizard(false)}
                onCreate={handleCreate}
                isCreating={createMutation.isPending}
                oauthStatus={oauthStatus}
            />

            {/* Plan with AI Modal */}
            <PlanWithAIModal
                open={showPlanAI}
                onClose={() => setShowPlanAI(false)}
            />

            <div className="flex flex-col gap-6 p-6 overflow-y-auto flex-1">
                {/* ── Page header ── */}
                <div className="flex items-start justify-between gap-4">
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <ClipboardList className="h-5 w-5 text-primary" />
                            <h1 className="text-2xl font-bold tracking-tight">Task Management</h1>
                        </div>
                        <p className="text-sm text-muted-foreground">
                            Create, track, and manage tasks. New tasks trigger Slack notifications automatically.
                        </p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                        <Button
                            className="gap-2 shrink-0"
                            onClick={() => setShowPlanAI(true)}
                        >
                            <Sparkles className="h-4 w-4" /> New Task
                        </Button>
                    </div>
                </div>

                {/* ── Stats cards ── */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {[
                        { label: 'Total', value: stats.total, color: 'text-foreground', bg: 'bg-muted/50' },
                        { label: 'Pending', value: stats.pending, color: 'text-muted-foreground', bg: 'bg-muted/30' },
                        { label: 'In Progress', value: stats.inProgress, color: 'text-blue-400', bg: 'bg-blue-500/10' },
                        { label: 'Completed', value: stats.completed, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
                    ].map(stat => (
                        <div key={stat.label} className={cn("rounded-xl p-4 border border-border/50", stat.bg)}>
                            <p className="text-xs text-muted-foreground mb-1">{stat.label}</p>
                            <p className={cn("text-2xl font-bold", stat.color)}>{stat.value}</p>
                        </div>
                    ))}
                </div>

                {/* ── Filters bar ── */}
                <div className="flex flex-wrap items-center gap-3">
                    <div className="relative flex-1 min-w-[200px] max-w-sm">
                        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                        <Input
                            placeholder="Search tasks or assignees…"
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            className="pl-8 h-8 text-xs"
                        />
                    </div>
                    <Select
                        value={filterPriority}
                        onValueChange={(value) => {
                            setFilterPriority(value ?? "all");
                        }}
                    >
                        <SelectTrigger className="h-8 text-xs w-[130px]">
                            <Flag className="h-3 w-3 mr-1.5 text-muted-foreground" />
                            <SelectValue placeholder="Priority" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">All Priorities</SelectItem>
                            <SelectItem value="High">High</SelectItem>
                            <SelectItem value="Medium">Medium</SelectItem>
                            <SelectItem value="Low">Low</SelectItem>
                        </SelectContent>
                    </Select>
                    <Select
                        value={filterStatus}
                        onValueChange={(value) => {
                            setFilterStatus(value ?? "all");
                        }}
                    >
                        <SelectTrigger className="h-8 text-xs w-[130px]">
                            <Circle className="h-3 w-3 mr-1.5 text-muted-foreground" />
                            <SelectValue placeholder="Status" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">All Statuses</SelectItem>
                            <SelectItem value="Pending">Pending</SelectItem>
                            <SelectItem value="In Progress">In Progress</SelectItem>
                            <SelectItem value="Completed">Completed</SelectItem>
                        </SelectContent>
                    </Select>
                    {(filterPriority !== 'all' || filterStatus !== 'all' || search) && (
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 text-xs text-muted-foreground"
                            onClick={() => { setSearch(''); setFilterPriority('all'); setFilterStatus('all'); }}
                        >
                            <X className="h-3 w-3 mr-1" /> Clear
                        </Button>
                    )}
                    <span className="ml-auto text-xs text-muted-foreground">
                        {filtered.length} task{filtered.length !== 1 ? 's' : ''}
                    </span>
                </div>

                {/* ── Table ── */}
                <div className="rounded-xl border border-border overflow-hidden bg-card flex-1">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-20">
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        </div>
                    ) : error ? (
                        <div className="flex flex-col items-center justify-center py-20 gap-3">
                            <p className="text-sm text-destructive">Failed to load tasks</p>
                            <Button variant="outline" size="sm" onClick={() => qc.invalidateQueries({ queryKey: ['tasks'] })}>Retry</Button>
                        </div>
                    ) : filtered.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-20 gap-3">
                            <ClipboardList className="h-10 w-10 text-muted-foreground/40" />
                            <p className="text-sm text-muted-foreground">
                                {tasks.length === 0 ? 'No tasks yet. Click "+ New Task" to get started.' : 'No tasks match your filters.'}
                            </p>
                        </div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow className="hover:bg-transparent border-b border-border">
                                    {[
                                        { label: 'Title', field: 'title' as keyof Task },
                                        { label: 'Assignee', field: 'assigned_to' as keyof Task },
                                        { label: 'Priority', field: 'priority' as keyof Task },
                                        { label: 'Status', field: 'status' as keyof Task },
                                        { label: 'Due Date', field: 'due_date' as keyof Task },
                                        { label: 'Created', field: 'created_at' as keyof Task },
                                    ].map(col => (
                                        <TableHead
                                            key={col.field}
                                            className="text-xs font-medium text-muted-foreground cursor-pointer select-none h-10"
                                            onClick={() => handleSortToggle(col.field)}
                                        >
                                            <span className="flex items-center">
                                                {col.label} <SortIcon field={col.field} />
                                            </span>
                                        </TableHead>
                                    ))}
                                    <TableHead className="w-10" />
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filtered.map(task => (
                                    <TableRow
                                        key={task.id}
                                        className="group cursor-pointer hover:bg-muted/30 transition-colors"
                                        onClick={() => setDetailTask(task)}
                                    >
                                        <TableCell className="font-medium text-sm max-w-[220px] truncate">
                                            <span className="truncate block">{task.title}</span>
                                        </TableCell>
                                        <TableCell className="text-xs text-muted-foreground">
                                            <div className="flex items-center gap-1.5">
                                                {task.assigned_to ? (
                                                    <>
                                                        <div className="h-5 w-5 rounded-full bg-primary/20 flex items-center justify-center text-[10px] font-semibold text-primary shrink-0">
                                                            {task.assigned_to[0]?.toUpperCase()}
                                                        </div>
                                                        <span className="truncate max-w-[100px]">{task.assigned_to}</span>
                                                    </>
                                                ) : '—'}
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant="outline" className={cn("text-[11px] border px-2 py-0.5", priorityColor(task.priority))}>
                                                {task.priority}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant="outline" className={cn("text-[11px] border px-2 py-0.5 flex items-center gap-1 w-fit", statusColor(task.status))}>
                                                {statusIcon(task.status)} {task.status}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-xs text-muted-foreground">{formatDate(task.due_date)}</TableCell>
                                        <TableCell className="text-xs text-muted-foreground">{formatDate(task.created_at)}</TableCell>
                                        <TableCell onClick={e => e.stopPropagation()}>
                                            <div className="flex items-center gap-1">
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-7 w-7"
                                                    onClick={() => setDetailTask(task)}
                                                >
                                                    <Eye className="h-4 w-4" />
                                                </Button>

                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-7 w-7"
                                                    onClick={() => setEditTask(task)}
                                                >
                                                    <Pencil className="h-4 w-4" />
                                                </Button>

                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-7 w-7"
                                                    onClick={() => setDeleteTask(task)}
                                                >
                                                    <Trash2 className="h-4 w-4 text-red-500" />
                                                </Button>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </div>
            </div>
        </div>
    );
}
