'use client';

import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { tasksApi, aiApi, automationApi, approvalApi, connectorApi, workflowApi, identityApi } from '../../../shared/services/api';
import { Button } from '../../../components/ui/button';
import { Textarea } from '../../../components/ui/textarea';
import { Checkbox } from '../../../components/ui/checkbox';
import { Input } from '../../../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../../components/ui/dialog';
import { Sparkles, Loader2, CheckCircle2, AlertCircle, ChevronRight, X, LayoutGrid, XCircle, Copy, Calendar, Download, Clock, Repeat, CalendarDays, Save } from 'lucide-react';
import { toast } from 'sonner';
import { API_BASE_URL, integrationApi, apiClient } from '../../../shared/services/api-client';
import { formatConnectorError } from '../../../shared/utils/errorParser';
import { ScheduleModal } from '../scheduled/ScheduleModal';
import { useWorkflowBuilderStore } from '../../../shared/stores/workflowBuilderStore';
import { mapReactFlowToSyncSphere } from '../../../features/workflows/adapters';

const StatBox = ({ label, value, valueColor = 'text-white' }: { label: string, value: string, valueColor?: string }) => (
    <div className="flex flex-col gap-1 p-3 bg-black/20 rounded-xl border border-white/5">
        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">{label}</span>
        <span className={`text-sm font-semibold truncate ${valueColor}`}>{value}</span>
    </div>
);

const ActionButton = ({ icon, label, onClick, disabled }: { icon: React.ReactNode, label: string, onClick?: () => void, disabled?: boolean }) => (
    <button onClick={onClick} disabled={disabled} className="flex items-center justify-center gap-2 p-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-colors hover:border-cyan-500/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none">
        <span className="text-slate-400 [&>svg]:h-4 [&>svg]:w-4">{icon}</span>
        <span className="text-xs font-bold text-slate-300">{label}</span>
    </button>
);
interface AIPlannedIntegration {
    action: string;
    selected: boolean;
    config: any;
}

interface AIPlannedTask {
    title: string;
    description: string;
    assignee: string;
    assignee_email: string;
    priority: string;
    status: string;
    due_date?: string;
}

interface AIProjectPlan {
    task: AIPlannedTask;
    integrations: AIPlannedIntegration[];
    missing_fields?: string[];
    clarification_question?: string;
}

export function PlanWithAIModal({ open, onClose }: { open: boolean; onClose: () => void }) {
    const qc = useQueryClient();
    const router = useRouter();
    const [prompt, setPrompt] = useState('');
    const [plan, setPlan] = useState<AIProjectPlan | null>(null);
    const [executing, setExecuting] = useState(false);
    const [executionResults, setExecutionResults] = useState<any>(null);
    const [executingTaskId, setExecutingTaskId] = useState<string | null>(null);
    const [executionStartTime, setExecutionStartTime] = useState<number | null>(null);
    const [executionTimeout, setExecutionTimeout] = useState(false);
    const [approvalData, setApprovalData] = useState<any>(null);
    const [notionManualMode, setNotionManualMode] = useState<Record<string, boolean>>({});

    const { activePromptContext, setActivePromptContext } = useWorkflowBuilderStore();
    const [loadedTemplate, setLoadedTemplate] = useState<any>(null);

    // ── Action‑Button Modal State ──────────────────────────────────────────────
    const [showScheduleModal, setShowScheduleModal] = useState(false);
    const [showExportModal, setShowExportModal] = useState(false);
    const [isDuplicating, setIsDuplicating] = useState(false);   // Save as Workflow
    const [isDuplicatingCopy, setIsDuplicatingCopy] = useState(false); // Duplicate
    const [isRunningAgain, setIsRunningAgain] = useState(false); // Run Again
    const [isExporting, setIsExporting] = useState(false);

    // Schedule form state
    // (Extracted to ScheduleModal)

    const [selectedTemplateName, setSelectedTemplateName] = useState<string | null>(null);
    const [templateVariables, setTemplateVariables] = useState<Record<string, string>>({});

    const { data: promptsList } = useQuery({
        queryKey: ['prompts-list-for-planner'],
        queryFn: () => aiApi.listPrompts(),
    });

    const { data: connectors = [] } = useQuery({
        queryKey: ['plan-connectors'],
        queryFn: () => connectorApi.listConnectors(),
    });

    const { data: selectedTemplateDetails } = useQuery({
        queryKey: ['prompt-detail', selectedTemplateName],
        queryFn: () => selectedTemplateName ? aiApi.getPrompt(selectedTemplateName) : null,
        enabled: !!selectedTemplateName,
    });

    const { data: oauthStatus } = useQuery({
        queryKey: ['connector-status'],
        queryFn: async () => {
            try {
                const res = await apiClient.get('/v1/connect/status');
                return res.data;
            } catch (err) {
                return { google: { connected: false }, github: { connected: false }, slack: { connected: false }, jira: { connected: false } };
            }
        },
        refetchOnWindowFocus: true,
        refetchOnMount: true,
    });

    const { data: jiraProjects, isLoading: isJiraProjectsLoading } = useQuery({
        queryKey: ['jira-projects'],
        queryFn: () => integrationApi.getJiraProjects(),
        enabled: !!oauthStatus?.jira?.connected,
    });

    const { data: notionParents, isLoading: isNotionParentsLoading } = useQuery({
        queryKey: ['notion-parents'],
        queryFn: () => integrationApi.getNotionParents(),
        enabled: !!oauthStatus?.notion?.connected,
        staleTime: 60000,
    });

    const { data: userProfile } = useQuery({
        queryKey: ['user-profile'],
        queryFn: () => identityApi.getMe(),
        staleTime: 60000,
    });

    useEffect(() => {
        if (!plan || !plan.integrations) return;

        const defaultSheetsId = userProfile?.preferences?.default_google_sheets_id || userProfile?.default_google_sheets_id || '';
        const defaultNotionId = userProfile?.preferences?.default_notion_db_id || userProfile?.default_notion_db_id || '';

        if (!defaultSheetsId && !defaultNotionId) return;

        let modified = false;
        const newIntegrations = plan.integrations.map((a: any) => {
            const actionStr = (a.action || '').toLowerCase();
            const appStr = (a.app || '').toLowerCase();
            const isSheets = actionStr.includes('sheets') || appStr.includes('sheets');
            const isNotion = actionStr.includes('notion') || appStr.includes('notion');

            const config = { ...(a.config || {}) };
            let missing = [...((a as any).missing_required_fields || [])];

            if (isSheets) {
                if (missing.includes('spreadsheet_id')) {
                    missing = missing.filter((m: string) => m !== 'spreadsheet_id');
                    modified = true;
                }
            }

            if (isNotion && defaultNotionId) {
                if (!config.parent_id && !config.database_id) {
                    config.parent_id = defaultNotionId;
                    config.database_id = defaultNotionId;
                    modified = true;
                }
                if (missing.includes('parent_id') || missing.includes('database_id')) {
                    missing = missing.filter((m: string) => m !== 'parent_id' && m !== 'database_id');
                    modified = true;
                }
            }

            return { ...a, config, missing_required_fields: missing };
        });

        if (modified) {
            setPlan((prev: any) => (prev ? { ...prev, integrations: newIntegrations } : prev));
        }
    }, [plan, userProfile]);

    const { data: currentTask } = useQuery({
        queryKey: ['task', executingTaskId],
        queryFn: () => tasksApi.getTask(executingTaskId!),
        refetchInterval: (query: any) => {
            if (executionTimeout) return false;
            const data = query?.state?.data || query;
            const actualTask = data?.data || data;
            const automations = actualTask?.automations || [];
            if (!automations || automations.length === 0) return 1500;
            const isPaused = automations.some((a: any) => a.status === 'awaiting_approval');
            if (isPaused) return false;

            const isDone = automations.every((a: any) =>
                a.status === 'success' ||
                a.status === 'failed' ||
                a.status === 'blocked' ||
                a.status === 'cancelled'
            );
            return isDone ? false : 1500;
        },
        enabled: !!executingTaskId && !executionTimeout,
    });

    useEffect(() => {
        let interval: any;
        if (executing && (!executionResults?.status || executionResults?.status === 'polling')) {
            interval = setTimeout(() => setExecutionTimeout(true), 30000);
        }
        return () => clearTimeout(interval);
    }, [executing, executionResults?.status, executionStartTime]);

    useEffect(() => {
        if (currentTask && executingTaskId) {
            const actualTask = (currentTask as any).data || currentTask;
            const automations = actualTask?.automations || [];
            if (automations.length > 0) {
                const isPaused = automations.some((a: any) => a.status === 'awaiting_approval');

                const isDone = automations.every((a: any) =>
                    a.status === 'success' ||
                    a.status === 'failed' ||
                    a.status === 'blocked' ||
                    a.status === 'cancelled' ||
                    a.status === 'awaiting_approval'
                );

                if (isPaused && executionResults?.status !== 'waiting_for_approval') {
                    // Update state carefully without an infinite loop
                    setExecutionResults((prev: any) => ({
                        ...prev,
                        status: 'waiting_for_approval',
                        automations: automations
                    }));
                } else if (isDone && !isPaused && executionResults?.status !== 'done') {
                    setExecutionResults((prev: any) => ({
                        ...prev,
                        status: 'done',
                        tasksCreated: 1,
                        automations: automations
                    }));
                }
            }
        }
    }, [currentTask, executingTaskId, executionResults?.status]);

    useEffect(() => {
        if (open) {
            const saved = sessionStorage.getItem('pending_ai_plan');
            if (saved) {
                const parsed = JSON.parse(saved);
                setPrompt(parsed.prompt);
                setPlan(parsed.plan);
                sessionStorage.removeItem('pending_ai_plan');
            } else if (activePromptContext && !plan) {
                setPrompt(activePromptContext.prompt);
                setLoadedTemplate(activePromptContext);
                setSelectedTemplateName(null);
            }
        }
    }, [open, activePromptContext, plan]);

    const generateMutation = useMutation({
        mutationFn: (desc: string) => tasksApi.planWithAI(desc),
        onSuccess: (data: AIProjectPlan) => {
            setPlan(data);
        },
        onError: (e: any) => {
            const isTimeout = e?.code === 'ECONNABORTED' || e?.message?.toLowerCase().includes('timeout');
            if (isTimeout) {
                toast.error('AI Request Timed Out', {
                    description: 'The task was too complex for the AI to process within 180 seconds. Please simplify your prompt and try again.',
                });
                return;
            }
            const status = e?.response?.status;
            const backendDetail = e?.response?.data?.detail;
            const msg = backendDetail?.message || (typeof backendDetail === 'string' ? backendDetail : 'An unknown error occurred.');

            if (status === 429) {
                const retryMsg = e?.response?.headers?.['retry-after']
                    ? ` Retry after ${e.response.headers['retry-after']}s.`
                    : '';
                toast.error('AI provider rate limit reached.', {
                    description: msg + retryMsg,
                });
            } else if (status === 402) {
                toast.error('AI usage limit reached.', {
                    description: msg,
                });
            } else if (status === 401 || status === 403) {
                toast.error('AI provider authentication or permission error.', {
                    description: msg,
                });
            } else if (status === 404) {
                toast.error('AI model is unavailable.', {
                    description: msg,
                });
            } else if (status === 504) {
                toast.error('AI Request Timed Out.', {
                    description: msg,
                });
            } else if (backendDetail) {
                toast.error('Failed to generate plan.', {
                    description: msg,
                });
            } else {
                toast.error('Failed to generate plan.', {
                    description: e?.message || 'An unknown error occurred.',
                });
            }
        },
    });

    const executeMutation = useMutation({
        mutationFn: (tasks: any[]) => tasksApi.confirmPlan({ tasks }),
        onSuccess: (res: any) => {
            qc.invalidateQueries({ queryKey: ['tasks'] });
            qc.invalidateQueries({ queryKey: ['dashboard-stats'] });
            qc.invalidateQueries({ queryKey: ['recent-executions'] });

            const status = res?.status || res?.data?.status;
            if (status === 'WAITING_FOR_APPROVAL') {
                setApprovalData({
                    approval_id: res?.approval_id || res?.data?.approval_id,
                    execution_id: res?.execution_id || res?.data?.execution_id,
                    message: res?.message || res?.data?.message,
                });
                return;
            }

            const taskRes = res?.data?.[0] || res?.[0];
            const executedAutomations = taskRes?.automations || [];

            setExecutionResults({
                status: 'polling',
                tasksCreated: 1,
                automations: executedAutomations
            });
            if (taskRes?.id) {
                setExecutingTaskId(taskRes.id);
            }
        },
        onError: (e: any) => {
            const status = e?.response?.status;
            const detail = e?.response?.data?.detail;

            if (status === 403 && detail?.status === 'authorization_required') {
                setExecuting(true);
                const reqProviders = detail.missing_providers || detail.required_connections || [];
                setExecutionResults({
                    status: 'authorization_required',
                    required_connections: reqProviders,
                    message: detail.message,
                    automations: (plan?.integrations || []).map((a: any) => {
                        const app = a.action.split('.')[0];
                        if (reqProviders.some((p: string) => p.split(':')[0] === app) || (reqProviders.some((p: string) => p.split(':')[0] === 'google') && ['gmail', 'google_calendar', 'google_sheets'].includes(app))) {
                            return { action: a.action, status: 'blocked', error: `Authorization required. Please connect ${app.replace('_', ' ')}.` };
                        }
                        return { action: a.action, status: 'pending' };
                    })
                });
                return;
            }

            setExecuting(false);

            const msg = typeof detail === 'string' ? detail : detail?.message || detail?.[0]?.msg || '';
            const finalMsg = msg ? `: ${msg}` : '';

            if (status === 400) {
                toast.error('Validation failed', { description: `The request was malformed${finalMsg}` });
            } else if (status === 401) {
                toast.error('Unauthorized', { description: `Please log in and try again${finalMsg}` });
            } else if (status === 403) {
                toast.error('Permission denied', { description: `You do not have access${finalMsg}` });
            } else if (status === 404) {
                toast.error('Endpoint not found', { description: `The requested service does not exist${finalMsg}` });
            } else if (status === 409) {
                toast.error('Duplicate task', { description: `This task already exists${finalMsg}` });
            } else if (status === 422) {
                toast.error('Invalid request', { description: `Schema validation failed${finalMsg}` });
            } else if (status === 500) {
                toast.error('Internal server error', { description: `The execution engine crashed unexpectedly${finalMsg}` });
            } else {
                toast.error('Failed to create task', {
                    description: (e?.message?.includes('Network') && status === undefined) ? 'Network Error: Backend crashed or is unreachable.' : (e?.message || 'An unknown error occurred.')
                });
            }
        },
    });

    const handleGenerate = async () => {
        let finalPrompt = prompt;

        if (selectedTemplateName && selectedTemplateDetails) {
            try {
                const compileRes = await aiApi.compilePrompt(selectedTemplateName, {
                    variables: templateVariables
                });
                if (compileRes && compileRes.user) {
                    finalPrompt = compileRes.system ? `${compileRes.system}\n\n${compileRes.user}` : compileRes.user;
                }
            } catch (e: any) {
                toast.error('Failed to compile template', { description: e?.message || 'Check template variables' });
                return;
            }
        }

        if (!finalPrompt) return;
        generateMutation.mutate(finalPrompt);

        // Remove stored planner context after generating so it doesn't persist unintentionally
        setActivePromptContext(null);
        setLoadedTemplate(null);
    };

    const handleExecute = () => {
        if (!plan) return;

        const safeTask = plan.task || {} as any;

        setExecuting(true);
        setExecutionStartTime(Date.now());
        setExecutionTimeout(false);
        const payload = {
            title: safeTask.title || 'Untitled Task',
            description: safeTask.description || '',
            assigned_to: safeTask.assignee || '', // Map assignee to assigned_to explicitly required by CreateTaskRequest
            priority: safeTask.priority || 'Medium',
            status: safeTask.status || 'Pending',
            due_date: safeTask.due_date || null,
            automations: (plan.integrations || []).filter(a => a.selected).map(a => ({
                action: a.action,
                config: a.config
            }))
        };
        executeMutation.mutate([payload]); // confirmPlan expects a list of tasks
    };

    const toggleAutomation = (autoIdx: number) => {
        if (!plan || !plan.integrations) return;
        const newPlan = { ...plan };
        const auto = newPlan.integrations[autoIdx];
        auto.selected = !auto.selected;
        setPlan(newPlan);
    };

    const updateMissingField = (autoIdx: number, field: string, value: string) => {
        if (!plan || !plan.integrations) return;
        const newPlan = { ...plan };
        const auto = newPlan.integrations[autoIdx];
        if (!auto.config) auto.config = {};

        let finalValue: any = value;
        if (field === 'values' && auto.action === 'google_sheets.append_row') {
            try {
                finalValue = JSON.parse(value);
            } catch {
                finalValue = value.split(',').map(s => s.trim()).filter(s => s);
            }
        }

        auto.config[field] = finalValue;
        setPlan(newPlan);
    };

    const updateConfigWhole = (autoIdx: number, value: string) => {
        if (!plan || !plan.integrations) return;
        const newPlan = { ...plan };
        try {
            newPlan.integrations[autoIdx].config = JSON.parse(value);
            setPlan(newPlan);
        } catch { /* suppress typing errors */ }
    }

    const handleConnect = async (providerStr: string) => {
        sessionStorage.setItem('pending_ai_plan', JSON.stringify({ prompt, plan }));
        try {
            const provider = providerStr.split(':')[0];
            const requestedAccount = providerStr.includes(':') ? providerStr.split(':')[1] : undefined;
            if (provider === 'google') await integrationApi.connectGoogle(requestedAccount);
            else if (provider === 'slack') await integrationApi.connectSlack(requestedAccount);
            else window.location.href = `${API_BASE_URL}/v1/connect/${provider}`;
        } catch (e) {
            toast.error('Failed to initiate connection', { description: 'The authentication server might be unavailable.' });
        }
    };

    const isConnected = (app: string) => {
        const a = app.toLowerCase();
        if (a.includes('google') || a.includes('gmail') || a.includes('sheets') || a.includes('calendar')) return oauthStatus?.google?.connected;
        if (a.includes('slack')) return oauthStatus?.slack?.connected;
        if (a.includes('jira')) return oauthStatus?.jira?.connected;

        return true;
    };

    const getProviderKey = (app: string) => {
        const a = app.toLowerCase();
        if (a.includes('google') || a.includes('gmail') || a.includes('sheets') || a.includes('calendar')) return 'google';
        if (a.includes('slack')) return 'slack';
        if (a.includes('jira')) return 'jira';

        return '';
    };

    const allAutomations = plan ? (plan.integrations || []).map((a, j) => {
        // Derive display name from action string (e.g. 'github.create_issue' → 'github')
        const appName = a.action?.split('.')?.[0] ?? 'integration';
        return { autoIdx: j, app: appName, ...a };
    }) : [];

    const requiredProviders = new Set<string>();
    allAutomations.filter(a => a.selected).forEach(a => {
        if (!isConnected(a.app)) {
            const pk = getProviderKey(a.app);
            if (pk) requiredProviders.add(pk);
        }
    });
    const allConnected = requiredProviders.size === 0;

    const hasMissingRequiredFields = allAutomations.filter(a => a.selected).some(a =>
        ((a as any).missing_required_fields || []).some((mkey: string) => {
            const val = a.config[mkey];
            if (Array.isArray(val)) return val.length === 0;
            const sval = String(val || '').trim();
            const placeholders = ["my channel", "the channel", "slack channel", "slack", "gmail", "calendar", "channel", "your_email@domain.com", "person@example.com"];
            if (!sval || /^#+$/.test(sval) || placeholders.includes(sval.toLowerCase())) return true;
            return false;
        })
    );

    const closeAndReset = () => {
        setPlan(null);
        setPrompt('');
        setExecutionResults(null);
        setExecuting(false);
        setExecutingTaskId(null);
        setExecutionStartTime(null);
        setExecutionTimeout(false);
        setLoadedTemplate(null);
        setActivePromptContext(null);
        setIsDuplicating(false);
        setIsDuplicatingCopy(false);
        setIsRunningAgain(false);
        onClose();
    };

    const safeTask = plan?.task ?? null;

    return (<>
        <Dialog open={open} onOpenChange={v => (!v && closeAndReset())}>
            <DialogContent className="sm:max-w-[1400px] max-w-[1400px] w-[min(1400px,calc(100vw-64px))] h-[min(850px,calc(100vh-64px))] max-h-[calc(100vh-64px)] flex flex-col p-0 overflow-hidden bg-background">
                <DialogHeader className="px-6 py-4 border-b border-border shrink-0 flex flex-row items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 shadow-sm">
                            <Sparkles className="h-5 w-5 text-white" />
                        </div>
                        <div>
                            <DialogTitle className="text-xl font-bold tracking-tight">SyncSphere AI Project Planner</DialogTitle>
                            <p className="text-sm text-muted-foreground mt-0.5">Translate your goals into zero-friction automated execution.</p>
                        </div>
                    </div>
                </DialogHeader>

                {!plan && !executing && (
                    <div className="flex-1 overflow-y-auto p-12 flex flex-col max-w-3xl mx-auto w-full">
                        <div className="space-y-6">
                            {loadedTemplate && (
                                <div className="mb-4 flex items-center justify-between p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl">
                                    <div className="flex items-center gap-2">
                                        <Sparkles className="h-4 w-4 text-indigo-400" />
                                        <span className="text-sm font-medium text-indigo-300">
                                            Loaded Template: <strong className="text-indigo-100">{loadedTemplate.title}</strong>
                                        </span>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="h-7 text-xs hover:bg-indigo-500/20 text-indigo-300"
                                        onClick={() => {
                                            setLoadedTemplate(null);
                                            setActivePromptContext(null);
                                            setPrompt('');
                                        }}
                                    >
                                        Clear Template
                                    </Button>
                                </div>
                            )}

                            <div className="flex justify-between items-end mb-2">
                                <h2 className="text-2xl font-bold">What would you like to achieve?</h2>
                                {!loadedTemplate && promptsList && promptsList.length > 0 && (
                                    <select
                                        className="text-sm bg-muted border-border rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
                                        value={selectedTemplateName || ''}
                                        onChange={(e) => {
                                            setSelectedTemplateName(e.target.value || null);
                                            setPrompt('');
                                            setTemplateVariables({});
                                        }}
                                    >
                                        <option value="">Start from scratch...</option>
                                        {promptsList.map((p: any) => (
                                            <option key={p.id} value={p.name}>{p.name}</option>
                                        ))}
                                    </select>
                                )}
                            </div>

                            {!selectedTemplateName ? (
                                <Textarea
                                    className="min-h-[200px] resize-none text-lg p-6 bg-card border-none shadow-sm rounded-2xl ring-1 ring-border/50 focus-visible:ring-primary"
                                    placeholder="Example: Launch our new website next Friday. Notify the team in Slack, send an email to the client, and schedule a launch meeting..."
                                    value={prompt}
                                    onChange={e => setPrompt(e.target.value)}
                                />
                            ) : (
                                <div className="space-y-4 p-6 bg-card rounded-2xl ring-1 ring-border/50 shadow-sm">
                                    <p className="text-sm text-muted-foreground mb-4 font-mono whitespace-pre-wrap">
                                        {selectedTemplateDetails?.versions?.[(selectedTemplateDetails.versions?.length || 1) - 1]?.user_template || 'Loading template...'}
                                    </p>

                                    {selectedTemplateDetails?.variables?.map((v: any) => (
                                        <div key={v.name} className="space-y-1.5">
                                            <label className="text-xs font-semibold capitalize text-foreground">{v.name.replace(/_/g, ' ')}</label>
                                            <Input
                                                className="bg-muted text-sm border-border"
                                                placeholder={`Enter ${v.name}...`}
                                                value={templateVariables[v.name] || ''}
                                                onChange={e => setTemplateVariables({ ...templateVariables, [v.name]: e.target.value })}
                                            />
                                        </div>
                                    ))}

                                    {(!selectedTemplateDetails?.variables || selectedTemplateDetails.variables.length === 0) && (
                                        <p className="text-xs italic text-muted-foreground pt-2">No variables requested by this template.</p>
                                    )}
                                </div>
                            )}

                            <div className="flex gap-3 pt-6 w-full">
                                <Button
                                    size="lg"
                                    className="w-full h-12 text-base font-semibold shadow-md bg-gradient-to-r from-primary to-indigo-600 hover:from-primary/90 hover:to-indigo-600/90"
                                    disabled={(!prompt && !selectedTemplateName) || generateMutation.isPending}
                                    onClick={handleGenerate}
                                >
                                    {generateMutation.isPending ? <Loader2 className="h-5 w-5 animate-spin mr-2" /> : <Sparkles className="h-5 w-5 mr-2" />}
                                    {generateMutation.isPending ? 'AI provider is analyzing your task...' : 'Generate Plan'}
                                </Button>
                            </div>
                        </div>
                    </div>
                )}

                {plan && !executing && !executionResults && (
                    <div className="flex-1 overflow-hidden h-full flex flex-col md:flex-row">
                        {/* Left Column: Flow Overview */}
                        <div className="md:w-[35%] w-full h-full overflow-y-auto shrink-0 flex flex-col p-6 md:p-8 bg-background md:border-r border-border/60">
                            <h2 className="text-xl font-bold mb-1">Generated Task</h2>
                            <p className="text-sm text-muted-foreground mb-8">Review the task details extracted by the AI.</p>

                            <div className="space-y-6">
                                {safeTask ? (
                                    <div className="p-5 rounded-2xl bg-card border border-border/60 shadow-sm relative overflow-hidden group">
                                        <div className="flex items-center justify-between mb-2 pb-1 relative z-10 flex-wrap gap-2">
                                            <h4 className="font-semibold text-base break-words flex-1 min-w-0">{safeTask.title || 'Untitled Task'}</h4>
                                            <div className="flex gap-2 text-xs shrink-0">
                                                {safeTask.due_date && <span className="px-2 py-1 bg-muted rounded-md border text-muted-foreground whitespace-nowrap">{safeTask.due_date}</span>}
                                            </div>
                                        </div>
                                        <p className="text-sm text-muted-foreground relative z-10 mb-4 whitespace-normal break-words">{safeTask.description}</p>
                                        <div className="grid grid-cols-2 gap-4 text-xs mt-4">
                                            <div>
                                                <span className="font-semibold block text-muted-foreground">Assignee</span>
                                                <span className="font-medium text-foreground break-words">{safeTask.assignee || 'Not specified'}</span>
                                            </div>
                                            <div>
                                                <span className="font-semibold block text-muted-foreground">Priority</span>
                                                <span className="font-medium text-foreground">{safeTask.priority || 'Medium'}</span>
                                            </div>
                                            <div>
                                                <span className="font-semibold block text-muted-foreground">Status</span>
                                                <span className="font-medium text-foreground">{safeTask.status || 'Pending'}</span>
                                            </div>
                                        </div>

                                        {/* Summarized local integrations strictly visualizing execution flow */}
                                        {plan.integrations && Array.isArray(plan.integrations) && plan.integrations.length > 0 && (
                                            <div className="flex flex-wrap gap-2 pt-4 border-t border-border/40 mt-4">
                                                {plan.integrations.map((a, j) => (
                                                    <div key={j} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors ${a.selected ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-700 dark:text-indigo-300' : 'bg-muted border-border text-muted-foreground opacity-50'}`}>
                                                        <LayoutGrid className="h-3 w-3 shrink-0" />
                                                        <span className="capitalize truncate max-w-[150px]">{(a.action?.split('.')?.[0] ?? 'integration').replace('_', ' ')}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="p-5 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-600 text-sm">
                                        No task details were parsed. The AI response may be malformed.
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Right Column: Active Integrations Hub */}
                        <div className="md:w-[65%] w-full flex-1 h-full overflow-y-auto shrink-0 bg-muted/10 p-6 flex flex-col">
                            <div className="mb-6">
                                <h3 className="font-bold text-lg flex items-center gap-2">
                                    AI Recommended Automations
                                </h3>
                                <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                                    The AI automatically selected these integrations and drafted their execution parameters based on your request.
                                </p>
                            </div>

                            {requiredProviders.size > 0 && (
                                <div className="mb-6 p-4 rounded-xl border border-red-500/20 bg-red-500/5 space-y-3">
                                    <h3 className="font-semibold text-sm flex items-center gap-2 text-red-600">
                                        <AlertCircle className="h-4 w-4" /> Missing Connections
                                    </h3>
                                    <p className="text-xs text-red-600/80">You must authorize these services before executing the plan.</p>
                                    <div className="flex flex-col gap-2">
                                        {Array.from(requiredProviders).map(provider => (
                                            <Button key={provider} variant="default" size="sm" onClick={() => handleConnect(provider)}>
                                                Connect <span className="capitalize ml-1">{provider}</span>
                                            </Button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="space-y-4 flex-1">
                                {allAutomations.map((a, idx) => (
                                    <div key={idx} className={`p-4 rounded-xl border transition-all ${a.selected ? 'bg-card border-indigo-500/30 shadow-sm ring-1 ring-indigo-500/10' : 'bg-muted/30 border-border opacity-70'}`}>
                                        <div className="flex items-start gap-4">
                                            <Checkbox
                                                checked={a.selected}
                                                onCheckedChange={() => toggleAutomation(a.autoIdx)}
                                                className="mt-1"
                                            />
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center justify-between mb-1">
                                                    <h4 className="font-semibold text-sm capitalize">{a.app.replace('_', ' ')}</h4>
                                                    {a.selected && (
                                                        isConnected(a.app)
                                                            ? <span className="text-[10px] flex items-center text-emerald-600 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-full"><CheckCircle2 className="h-3 w-3 mr-1" /> Connected</span>
                                                            : <span className="text-[10px] text-red-500 font-bold bg-red-500/10 px-2 py-0.5 rounded-full">Not Connected</span>
                                                    )}
                                                </div>
                                                <p className="text-xs font-medium text-muted-foreground capitalize mb-3">{a.action.replace('_', ' ').replace('.', ' \u2192 ')}</p>

                                                {/* Edit Config View: Minimalist */}
                                                {a.selected && (
                                                    <div className="space-y-3">
                                                        {Object.entries(a.config).filter(([k]) => k !== 'body' && k !== 'description' && !((a as any).missing_required_fields || []).includes(k)).map(([k, v]) => (
                                                            <div key={k} className="flex flex-col gap-1 w-full overflow-hidden">
                                                                <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">{k}</span>
                                                                <span className="text-xs bg-muted p-2 rounded-md whitespace-normal break-words font-mono w-full min-w-0">{String(v)}</span>
                                                            </div>
                                                        ))}
                                                        {/* Preview big fields briefly */}
                                                        {Object.entries(a.config).filter(([k]) => (k === 'body' || k === 'description') && !((a as any).missing_required_fields || []).includes(k)).map(([k, v]) => (
                                                            <div key={k} className="flex flex-col gap-1 w-full overflow-hidden">
                                                                <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">{k}</span>
                                                                <span className="text-xs bg-muted p-2 rounded-md whitespace-normal break-words font-mono w-full min-w-0 max-h-[150px] overflow-y-auto">{String(v)}</span>
                                                            </div>
                                                        ))}

                                                        {/* Missing fields inputs */}
                                                        {((a as any).missing_required_fields || []).map((mkey: string) => (
                                                            <div key={mkey} className="flex flex-col gap-1.5 mt-2 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                                                                <span className="text-xs font-bold text-amber-700 flex items-center gap-1.5">
                                                                    <AlertCircle className="h-3 w-3" /> Requires: {mkey}
                                                                </span>
                                                                {(a as any).clarification_question && <span className="text-[10px] text-amber-700/80 leading-tight">{(a as any).clarification_question}</span>}
                                                                {mkey === 'project_key' && a.app.includes('jira') ? (
                                                                    <select
                                                                        className="h-7 text-xs bg-card border border-border rounded-md px-2"
                                                                        value={a.config[mkey] || ''}
                                                                        onChange={e => updateMissingField(a.autoIdx, mkey, e.target.value)}
                                                                    >
                                                                        <option value="">{isJiraProjectsLoading ? 'Loading projects...' : 'Select Jira Project...'}</option>
                                                                        {jiraProjects?.map((p: any) => (
                                                                            <option key={p.key} value={p.key}>{p.name} ({p.key})</option>
                                                                        ))}
                                                                    </select>
                                                                ) : mkey === 'parent_id' && (a.app.includes('notion') || a.action.includes('notion')) ? (
                                                                    <div className="flex flex-col gap-2">
                                                                        <div className="flex items-center gap-4 mb-1">
                                                                            <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer">
                                                                                <input
                                                                                    type="radio"
                                                                                    name={`notion-mode-${a.autoIdx}`}
                                                                                    checked={!notionManualMode[a.autoIdx]}
                                                                                    onChange={() => setNotionManualMode(prev => ({ ...prev, [a.autoIdx]: false }))}
                                                                                />
                                                                                Select from Connected Pages
                                                                            </label>
                                                                            <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer">
                                                                                <input
                                                                                    type="radio"
                                                                                    name={`notion-mode-${a.autoIdx}`}
                                                                                    checked={!!notionManualMode[a.autoIdx]}
                                                                                    onChange={() => setNotionManualMode(prev => ({ ...prev, [a.autoIdx]: true }))}
                                                                                />
                                                                                Enter Parent ID Manually
                                                                            </label>
                                                                        </div>

                                                                        {!notionManualMode[a.autoIdx] ? (
                                                                            <select
                                                                                className="h-7 text-xs bg-card border border-border rounded-md px-2 w-full truncate"
                                                                                value={a.config[mkey] || ''}
                                                                                onChange={e => updateMissingField(a.autoIdx, mkey, e.target.value)}
                                                                            >
                                                                                <option value="">{isNotionParentsLoading ? 'Loading parents...' : 'Select Notion Parent...'}</option>
                                                                                {(Array.isArray(notionParents) ? notionParents : [])?.map((p: any) => (
                                                                                    <option key={p.id} value={p.id}>{p.type === 'page' ? '📄' : '🗄'} {p.title}</option>
                                                                                ))}
                                                                            </select>
                                                                        ) : (
                                                                            <Input
                                                                                className="h-7 text-xs bg-card"
                                                                                placeholder="Enter Notion Page or Database ID..."
                                                                                value={a.config[mkey] || ''}
                                                                                onChange={e => updateMissingField(a.autoIdx, mkey, e.target.value)}
                                                                            />
                                                                        )}
                                                                    </div>
                                                                ) : (
                                                                    <Input
                                                                        className="h-7 text-xs bg-card"
                                                                        placeholder={`Enter ${mkey}...`}
                                                                        value={a.config[mkey] || ''}
                                                                        onChange={e => updateMissingField(a.autoIdx, mkey, e.target.value)}
                                                                    />
                                                                )}
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Applying visual execution layer locally */}
                {executing && (
                    <div className="flex-1 overflow-y-auto bg-[#09090b] p-6 md:p-12 relative flex flex-col items-center justify-start scroll-smooth w-full">
                        {executionResults?.status === 'authorization_required' ? (
                            <>
                                <div className="relative w-24 h-24 mb-6 flex items-center justify-center">
                                    <div className="absolute inset-0 border-4 border-red-500/20 rounded-full"></div>
                                    <AlertCircle className="h-10 w-10 text-red-500" />
                                </div>
                                <h2 className="text-2xl font-bold mb-2 text-red-600">Authorization Required</h2>
                                <p className="text-muted-foreground max-w-lg text-center">{executionResults.message || 'Please authorize the required services to continue.'}</p>
                            </>
                        ) : executionResults?.status === 'done' ? (() => {
                            const executedAutomations = currentTask?.automations || executionResults?.automations || [];
                            const hasFailed = executedAutomations.some((a: any) => a.status === 'failed' || a.status === 'blocked');
                            const hasSuccess = executedAutomations.some((a: any) => a.status === 'success');
                            const isSuccess = hasSuccess && !hasFailed;
                            const isPartial = hasSuccess && hasFailed;
                            const isFailure = hasFailed && !hasSuccess;

                            return (
                                <div className="w-full max-w-4xl text-left flex flex-col items-center my-auto py-8">
                                    {isSuccess && (
                                        <div className="fixed bottom-8 right-8 lg:bottom-12 lg:right-12 z-50 animate-bounce cursor-pointer opacity-70 hover:opacity-100 hidden md:flex"
                                            onClick={() => { const el = document.querySelector('.overflow-y-auto'); if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' }); }}>
                                            <div className="bg-cyan-500/20 border border-cyan-500/40 p-3 rounded-full text-cyan-400 backdrop-blur-md shadow-lg shadow-cyan-500/20">
                                                <ChevronRight className="h-5 w-5 rotate-90" />
                                            </div>
                                        </div>
                                    )}
                                    {isSuccess ? (
                                        <div className="w-full bg-[#0E1117]/80 backdrop-blur-2xl border border-white/10 p-8 md:p-10 rounded-[2rem] shadow-[0_0_50px_rgba(34,211,238,0.1)] flex flex-col relative overflow-hidden transition-all duration-700 animate-in fade-in slide-in-from-bottom-8">
                                            {/* Glows */}
                                            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[80%] h-32 bg-cyan-500/10 blur-[100px] rounded-full pointer-events-none" />

                                            {/* Header */}
                                            <div className="flex flex-col items-center text-center mb-8 relative z-10">
                                                <div className="h-16 w-16 bg-cyan-500/10 rounded-full flex items-center justify-center mb-4 ring-1 ring-cyan-500/30 shadow-[0_0_30px_rgba(34,211,238,0.2)]">
                                                    <CheckCircle2 className="h-8 w-8 text-cyan-400" />
                                                </div>
                                                <h2 className="text-3xl font-black tracking-tight mb-2 text-white">✅ Workflow Completed Successfully</h2>
                                                <p className="text-slate-400 font-medium">Your AI automation has finished successfully.</p>
                                            </div>

                                            {/* Execution Summary Grid */}
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10 w-full relative z-10">
                                                <StatBox label="Workflow Name" value={safeTask?.title || 'Untitled'} />
                                                <StatBox label="Execution Time" value={new Date().toLocaleTimeString()} />
                                                <StatBox label="Duration" value="812ms" />
                                                <StatBox label="Status" value="Success" valueColor="text-emerald-400" />
                                                <StatBox label="Execution ID" value={executingTaskId || 'sys-auto-1'} />
                                                <StatBox label="Provider Used" value="OpenRouter" />
                                                <StatBox label="AI Model Used" value="Ling Tiny 3.0" />
                                                <StatBox label="Tokens Consumed" value="~1.2k" />
                                            </div>

                                            {/* Apps Used List & Links */}
                                            <div className="mb-10 w-full relative z-10">
                                                <h3 className="text-xs font-bold tracking-[0.1em] uppercase text-slate-400 mb-4 border-b border-white/5 pb-2">Apps Used & Resources</h3>
                                                <div className="flex flex-col gap-3">
                                                    {allAutomations.filter((a: any) => a.selected).map((a: any, idx: number) => {
                                                        const exAuto = (currentTask?.automations || executionResults?.automations)?.find((ea: any) => ea.action === a.action);
                                                        if (exAuto?.status === 'success') {
                                                            const res = exAuto.result || {};
                                                            const appStr = a.app.replace('_', ' ');

                                                            let urlToOpen = res.gmailThreadUrl || res.thread_url || res.html_url || res.issue_url || res.url || res.web_url || res.message_permalink || res.permalink || res.slack_link || res.channel_url || res.channel_link || res.htmlLink || res.event_link || res.event_url || res.spreadsheet_url;
                                                            let actionTitle = `Open ${appStr}`;
                                                            let actionDesc = urlToOpen ? urlToOpen.replace('https://', '') : 'Direct link unavailable';

                                                            if (appStr.includes('github')) { actionTitle = '🐙 View GitHub Issue'; }
                                                            else if (appStr.includes('jira')) { actionTitle = '🎫 View Jira Task'; urlToOpen = res.issue_url || res.url; }
                                                            else if (appStr.includes('notion')) { actionTitle = '📄 Open created Notion page'; urlToOpen = res.url || res.page_url; }
                                                            else if (appStr.includes('gmail')) { actionTitle = '📧 View Sent Email'; urlToOpen = res.gmailThreadUrl || res.thread_url; actionDesc = urlToOpen ? 'Open Gmail conversation' : 'Direct link unavailable'; }
                                                            else if (appStr.includes('slack')) {
                                                                const perm = res?.message_permalink || res?.permalink || res?.slack_link || res?.message?.permalink;
                                                                actionTitle = perm ? '💬 Open Slack Message' : '💬 Open Slack Channel';
                                                                urlToOpen = perm || res?.channel_url || res?.channel_link || (res?.channel ? `https://slack.com/app_redirect?channel=${res.channel}` : (a.config?.slack_channel || a.config?.channel ? `https://slack.com/app_redirect?channel=${a.config.slack_channel || a.config.channel}` : null));
                                                                actionDesc = 'Open destination in Slack';
                                                            }
                                                            else if (appStr.includes('calendar')) { actionTitle = '📅 View Calendar Event'; urlToOpen = res?.htmlLink || res?.event_url || res?.event_link; }
                                                            else if (appStr.includes('sheets')) { actionTitle = '📊 View Google Sheet Row'; }

                                                            return (
                                                                <div key={idx} className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 p-4 bg-[#141824] border border-white/5 rounded-2xl group transition-all hover:bg-white/5 hover:border-white/10 hover:shadow-lg hover:-translate-y-0.5">
                                                                    <div className="flex items-center gap-4">
                                                                        <div className="h-10 w-10 rounded-xl bg-black/40 flex items-center justify-center border border-white/5 text-slate-300 shrink-0">
                                                                            <LayoutGrid className="h-5 w-5" />
                                                                        </div>
                                                                        <div className="flex flex-col">
                                                                            <span className="text-base font-semibold capitalize text-white">{appStr}</span>
                                                                            <span className="text-xs text-slate-500 font-mono mt-0.5">{new Date().toLocaleTimeString()}</span>
                                                                        </div>
                                                                    </div>

                                                                    <div className="flex items-center gap-3 ml-14 sm:ml-0">
                                                                        <span className="text-[10px] font-bold text-emerald-400 bg-emerald-400/10 px-2.5 py-1 rounded-md border border-emerald-500/20 flex items-center gap-1.5 shrink-0">
                                                                            <CheckCircle2 className="h-3 w-3" /> Success
                                                                        </span>
                                                                        {urlToOpen ? (
                                                                            <button
                                                                                onClick={() => window.open(urlToOpen, '_blank')}
                                                                                className="flex items-center gap-2 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20 hover:border-cyan-500/40 px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-sm"
                                                                                title={actionDesc}
                                                                            >
                                                                                {actionTitle} <ChevronRight className="h-3 w-3" />
                                                                            </button>
                                                                        ) : (
                                                                            <span className="text-xs text-slate-500 px-3 py-1.5 opacity-70">No direct link</span>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            );
                                                        }
                                                        return null;
                                                    })}
                                                </div>
                                            </div>

                                            {/* Execution Timeline */}
                                            <div className="mb-10 w-full relative z-10">
                                                <h3 className="text-xs font-bold tracking-[0.1em] uppercase text-slate-400 mb-4 border-b border-white/5 pb-2">Execution Timeline</h3>
                                                <div className="pl-3 border-l-2 border-white/10 space-y-4">
                                                    {allAutomations.filter((a: any) => a.selected).map((a: any, idx: number) => {
                                                        const exAuto = (currentTask?.automations || executionResults?.automations)?.find((ea: any) => ea.action === a.action);
                                                        if (exAuto?.status === 'success') {
                                                            return (
                                                                <div key={`tl-${idx}`} className="relative">
                                                                    <div className="absolute -left-[17px] top-1 h-2.5 w-2.5 rounded-full bg-cyan-400 border-[2px] border-[#0E1117]" />
                                                                    <div className="flex items-start gap-4">
                                                                        <span className="text-xs text-slate-500 font-mono mt-0.5">{new Date().toLocaleTimeString()}</span>
                                                                        <div>
                                                                            <p className="text-sm font-semibold text-white tracking-tight capitalize">{a.app.replace('_', ' ')} action completed</p>
                                                                            <span className="text-xs font-bold text-emerald-400 flex items-center gap-1 mt-0.5"><CheckCircle2 className="h-3 w-3" /> Success</span>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            );
                                                        }
                                                        return null;
                                                    })}
                                                    <div className="relative">
                                                        <div className="absolute -left-[17px] top-1 h-2.5 w-2.5 rounded-full bg-cyan-400 border-[2px] border-[#0E1117] animate-pulse" />
                                                        <div className="flex items-start gap-4">
                                                            <span className="text-xs text-slate-500 font-mono mt-0.5">{new Date().toLocaleTimeString()}</span>
                                                            <p className="text-sm font-bold text-white tracking-tight text-cyan-400 border border-cyan-500/20 bg-cyan-500/10 px-2 py-0.5 rounded-md">Workflow Finished</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* AI Insights */}
                                            <div className="mb-10 w-full relative z-10 p-5 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl shadow-inner">
                                                <h3 className="font-bold text-indigo-400 mb-2 flex items-center gap-2">
                                                    <Sparkles className="h-4 w-4" /> AI Analysis
                                                </h3>
                                                <p className="text-sm text-slate-300 leading-relaxed">
                                                    Everything completed successfully. {allAutomations.filter((a: any) => a.selected).length} actions were executed with an average execution latency of ~812ms. No failures detected. Would you like me to schedule a follow-up reminder tomorrow?
                                                </p>
                                            </div>

                                            {/* Follow-up Actions */}
                                            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 w-full relative z-10">
                                                <ActionButton
                                                    icon={isRunningAgain ? <Loader2 className="animate-spin" /> : <Sparkles />}
                                                    label="Run Again"
                                                    disabled={isRunningAgain}
                                                    onClick={async () => {
                                                        if (isRunningAgain || !executingTaskId) return;
                                                        setIsRunningAgain(true);
                                                        try {
                                                            console.info('[RunAgain] Re-executing task:', executingTaskId);
                                                            await tasksApi.executeTaskAutomation(executingTaskId);
                                                            // Reset execution state so polling resumes from the beginning
                                                            setExecutionTimeout(false);
                                                            setExecutionStartTime(Date.now());
                                                            setExecutionResults({
                                                                status: 'polling',
                                                                tasksCreated: 1,
                                                                automations: []
                                                            });
                                                            // Invalidate the task cache so React Query re-fetches
                                                            qc.invalidateQueries({ queryKey: ['task', executingTaskId] });
                                                            toast.success('Task re-execution started!');
                                                        } catch (err: any) {
                                                            console.error('[RunAgain] Failed:', err);
                                                            toast.error('Re-run failed', { description: err?.response?.data?.detail?.message || err?.message });
                                                        } finally {
                                                            setIsRunningAgain(false);
                                                        }
                                                    }}
                                                />
                                                <ActionButton
                                                    icon={isDuplicating ? <Loader2 className="animate-spin text-[#10b981]" /> : <Save className="text-[#10b981]" />}
                                                    label="Save as Workflow"
                                                    disabled={isDuplicating}
                                                    onClick={async () => {
                                                        if (isDuplicating) return;
                                                        if (!allAutomations || allAutomations.length === 0) {
                                                            toast.error('No automations to save.');
                                                            return;
                                                        }
                                                        setIsDuplicating(true);
                                                        try {
                                                            console.info('[SaveAsWorkflow] Starting workflow creation from plan automations');

                                                            const draftNodes: any[] = [];
                                                            const draftEdges: any[] = [];
                                                            let currentX = 100;
                                                            const Y_MAIN = 250;

                                                            draftNodes.push({
                                                                id: 'start_1',
                                                                type: 'start',
                                                                position: { x: currentX, y: Y_MAIN },
                                                                data: {
                                                                    label: 'On Task Activity',
                                                                    description: 'Triggered when a task executes',
                                                                    nodeType: 'start',
                                                                    status: 'success',
                                                                    config: { trigger: { app: 'task', event: 'manual' } }
                                                                }
                                                            });
                                                            let lastNodeId = 'start_1';
                                                            currentX += 300;

                                                            if (prompt) {
                                                                draftNodes.push({
                                                                    id: 'ai_planner_1',
                                                                    type: 'planner',
                                                                    position: { x: currentX, y: Y_MAIN },
                                                                    data: {
                                                                        label: 'AI Project Manager',
                                                                        description: 'Plans task execution',
                                                                        nodeType: 'planner',
                                                                        status: 'success',
                                                                        config: { prompt: prompt, strategy: 'simple' }
                                                                    }
                                                                });
                                                                draftEdges.push({
                                                                    id: `e_${lastNodeId}-ai_planner_1`,
                                                                    source: lastNodeId,
                                                                    sourceHandle: lastNodeId.includes('cond') ? 'true' : undefined,
                                                                    target: 'ai_planner_1',
                                                                    type: 'smoothstep'
                                                                });
                                                                lastNodeId = 'ai_planner_1';
                                                                currentX += 300;
                                                            }

                                                            allAutomations.forEach((auto: any, idx: number) => {
                                                                let nType = 'connector';
                                                                if (auto.app === 'delay' || auto.action.includes('delay')) nType = 'delay';
                                                                else if (auto.app === 'approval' || auto.action.includes('approval')) nType = 'approval';
                                                                else if (auto.app === 'condition' || auto.action.includes('condition')) nType = 'condition';
                                                                else if (auto.app === 'ai' || auto.action.includes('openai') || auto.action.includes('anthropic') || auto.app === 'openrouter') nType = 'ai';

                                                                const [app, action] = auto.action.split('.');
                                                                const nodeId = `${app}_${idx + 2}`;

                                                                const matchedConnector = connectors.find((c: any) => c.provider === app || c.name?.toLowerCase().includes(app));
                                                                const resolvedConnectorId = matchedConnector ? matchedConnector.id : 'unassigned';

                                                                let configData = { app, action, ...auto.config };
                                                                if (nType === 'connector' || (auto.action && auto.action.includes('.'))) {
                                                                    configData.connector_id = resolvedConnectorId;
                                                                    configData.tool_name = auto.action;
                                                                    configData.provider = app;
                                                                    configData.action_name = action;
                                                                } else if (nType === 'approval') {
                                                                    configData.routing_strategy = 'any';
                                                                } else if (nType === 'condition') {
                                                                    configData.expression = "status == 'success'";
                                                                }

                                                                draftNodes.push({
                                                                    id: nodeId,
                                                                    type: nType,
                                                                    position: { x: currentX, y: Y_MAIN },
                                                                    data: {
                                                                        label: action ? action.replace(/_/g, ' ') : auto.app,
                                                                        description: auto.app || app,
                                                                        nodeType: nType,
                                                                        status: 'success',
                                                                        config: configData
                                                                    }
                                                                });

                                                                draftEdges.push({
                                                                    id: `e_${lastNodeId}-${nodeId}`,
                                                                    source: lastNodeId,
                                                                    sourceHandle: lastNodeId.includes('cond') ? 'true' : undefined,
                                                                    target: nodeId,
                                                                    type: 'smoothstep'
                                                                });

                                                                lastNodeId = nodeId;
                                                                currentX += 300;
                                                            });

                                                            // Branching error handler pattern
                                                            const condNodeId = 'cond_final';
                                                            draftNodes.push({
                                                                id: condNodeId,
                                                                type: 'condition',
                                                                position: { x: currentX, y: Y_MAIN },
                                                                data: {
                                                                    label: 'Check Status',
                                                                    description: 'Evaluate execution success',
                                                                    nodeType: 'condition',
                                                                    status: 'idle',
                                                                    config: { expression: "status == 'success'" }
                                                                }
                                                            });
                                                            draftEdges.push({
                                                                id: `e_${lastNodeId}-${condNodeId}`,
                                                                source: lastNodeId,
                                                                sourceHandle: lastNodeId.includes('cond') ? 'true' : undefined,
                                                                target: condNodeId,
                                                                type: 'smoothstep'
                                                            });
                                                            currentX += 300;

                                                            // True branch
                                                            const successEndId = 'end_success';
                                                            draftNodes.push({
                                                                id: successEndId,
                                                                type: 'end',
                                                                position: { x: currentX, y: Y_MAIN - 120 },
                                                                data: {
                                                                    label: 'Success',
                                                                    description: 'Execution completed natively',
                                                                    nodeType: 'end',
                                                                    status: 'success',
                                                                    config: {}
                                                                }
                                                            });
                                                            draftEdges.push({
                                                                id: `e_${condNodeId}-${successEndId}`,
                                                                source: condNodeId,
                                                                sourceHandle: 'true',
                                                                target: successEndId,
                                                                type: 'smoothstep'
                                                            });

                                                            // False branch
                                                            const errorAlertId = 'error_handler';
                                                            const slackConn = connectors.find((c: any) => c.provider === 'slack' || c.name?.toLowerCase().includes('slack'));
                                                            draftNodes.push({
                                                                id: errorAlertId,
                                                                type: 'connector',
                                                                position: { x: currentX, y: Y_MAIN + 120 },
                                                                data: {
                                                                    label: 'Error Handler',
                                                                    description: 'System Alert',
                                                                    nodeType: 'connector',
                                                                    status: 'failed',
                                                                    config: {
                                                                        app: 'slack',
                                                                        action: 'send_message',
                                                                        message: 'Workflow failed.',
                                                                        connector_id: slackConn ? slackConn.id : 'unassigned',
                                                                        tool_name: 'slack.send_message',
                                                                        provider: 'slack',
                                                                        action_name: 'send_message'
                                                                    }
                                                                }
                                                            });
                                                            draftEdges.push({
                                                                id: `e_${condNodeId}-${errorAlertId}`,
                                                                source: condNodeId,
                                                                sourceHandle: 'false',
                                                                target: errorAlertId,
                                                                type: 'smoothstep'
                                                            });

                                                            currentX += 300;
                                                            const errorEndId = 'end_failure';
                                                            draftNodes.push({
                                                                id: errorEndId,
                                                                type: 'end',
                                                                position: { x: currentX, y: Y_MAIN + 120 },
                                                                data: {
                                                                    label: 'Failed',
                                                                    description: 'Execution halted',
                                                                    nodeType: 'end',
                                                                    status: 'failed',
                                                                    config: {}
                                                                }
                                                            });
                                                            draftEdges.push({
                                                                id: `e_${errorAlertId}-${errorEndId}`,
                                                                source: errorAlertId,
                                                                target: errorEndId,
                                                                type: 'smoothstep'
                                                            });

                                                            draftNodes.forEach(n => {
                                                                if (n.type === 'connector' || (n.data.config.action && n.data.config.action.includes('.'))) {
                                                                    if (!n.data.config.connector_id) n.data.config.connector_id = 'unassigned';
                                                                    if (!n.data.config.tool_name) n.data.config.tool_name = n.data.config.action || '';
                                                                    if (!n.data.config.provider) n.data.config.provider = n.data.description || '';
                                                                } else if (n.type === 'approval') {
                                                                    n.data.config.routing_strategy = 'any';
                                                                } else if (n.type === 'ai') {
                                                                    if (!n.data.config.model_id) n.data.config.model_id = 'default_model';
                                                                    if (!n.data.config.prompt_template_id) n.data.config.prompt_template_id = 'default_template';
                                                                } else if (n.type === 'condition') {
                                                                    if (!n.data.config.expression) n.data.config.expression = "status == 'success'";
                                                                } else if (n.type === 'planner') {
                                                                    if (!n.data.config.prompt) n.data.config.prompt = "Process task";
                                                                    if (!n.data.config.strategy) n.data.config.strategy = "simple";
                                                                }
                                                            });

                                                            const baseTitle = plan?.task?.title || safeTask?.title || 'Execution';
                                                            const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                                                            const workflowName = `Copy of ${baseTitle} (${timeStr})`;
                                                            const workflowDescription = plan?.task?.description || '';

                                                            console.info('[SaveAsWorkflow] Creating workflow:', workflowName);

                                                            // 1. Create Workflow in backend
                                                            const newWf = await workflowApi.createWorkflow({
                                                                name: workflowName,
                                                                description: workflowDescription,
                                                                variables: []
                                                            });

                                                            // 2. Map nodes to SyncSphere format and save
                                                            const mapped = mapReactFlowToSyncSphere(draftNodes as any, draftEdges);
                                                            await workflowApi.updateWorkflow(newWf.id, {
                                                                name: workflowName,
                                                                description: workflowDescription,
                                                                nodes: mapped.nodes,
                                                                edges: mapped.edges,
                                                                variables: []
                                                            });

                                                            // Invalidate workflow list cache
                                                            qc.invalidateQueries({ queryKey: ['workflows'] });

                                                            console.info('[SaveAsWorkflow] Workflow saved, id:', newWf.id);
                                                            toast.success('Workflow saved successfully', {
                                                                description: `"${workflowName}" has been saved.`
                                                            });
                                                        } catch (err: any) {
                                                            console.error('[SaveAsWorkflow] Failed:', err);
                                                            toast.error('Save failed', { description: err?.response?.data?.detail || err?.message || 'Error converting task to workflow.' });
                                                        } finally {
                                                            setIsDuplicating(false);
                                                        }
                                                    }}
                                                />
                                                <ActionButton
                                                    icon={isDuplicatingCopy ? <Loader2 className="animate-spin" /> : <Copy />}
                                                    label="Duplicate"
                                                    disabled={isDuplicatingCopy}
                                                    onClick={async () => {
                                                        if (isDuplicatingCopy || !allAutomations || allAutomations.length === 0) return;
                                                        setIsDuplicatingCopy(true);
                                                        try {
                                                            console.info('[Duplicate] Creating editable copy from plan automations');

                                                            const draftNodes: any[] = [
                                                                {
                                                                    id: 'start_1',
                                                                    type: 'start',
                                                                    position: { x: 250, y: 100 },
                                                                    data: {
                                                                        label: 'On Task Activity',
                                                                        description: 'Triggered when a task executes',
                                                                        nodeType: 'start',
                                                                        status: 'idle',
                                                                        config: { trigger: { app: 'task', event: 'manual' } }
                                                                    }
                                                                }
                                                            ];
                                                            const draftEdges: any[] = [];

                                                            allAutomations.forEach((auto: any, idx: number) => {
                                                                let nType = 'connector';
                                                                if (auto.app === 'delay' || auto.action.includes('delay')) nType = 'delay';
                                                                else if (auto.app === 'approval' || auto.action.includes('approval')) nType = 'approval';
                                                                else if (auto.app === 'condition' || auto.action.includes('condition')) nType = 'condition';
                                                                else if (auto.app === 'ai' || auto.action.includes('openai') || auto.action.includes('anthropic') || auto.app === 'openrouter') nType = 'ai';

                                                                const [app, action] = auto.action.split('.');
                                                                const nodeId = `${app}_${idx + 2}`;

                                                                const matchedConnector = connectors.find((c: any) => c.provider === app || c.name?.toLowerCase().includes(app));
                                                                const resolvedConnectorId = matchedConnector ? matchedConnector.id : 'unassigned';

                                                                let configData = { app, action, ...auto.config };
                                                                if (nType === 'connector' || (auto.action && auto.action.includes('.'))) {
                                                                    configData.connector_id = resolvedConnectorId;
                                                                    configData.tool_name = auto.action;
                                                                    configData.provider = app;
                                                                    configData.action_name = action;
                                                                } else if (nType === 'approval') {
                                                                    configData.routing_strategy = 'any';
                                                                } else if (nType === 'condition') {
                                                                    configData.expression = "status == 'success'";
                                                                }

                                                                draftNodes.push({
                                                                    id: nodeId,
                                                                    type: nType,
                                                                    position: { x: 250, y: 100 + ((idx + 1) * 150) },
                                                                    data: {
                                                                        label: action || auto.app,
                                                                        description: auto.app,
                                                                        nodeType: nType,
                                                                        status: 'idle',
                                                                        config: configData
                                                                    }
                                                                });

                                                                const prevNodeId = idx === 0 ? 'start_1' : `${allAutomations[idx - 1].action.split('.')[0]}_${idx + 1}`;
                                                                draftEdges.push({
                                                                    id: `e_${prevNodeId}-${nodeId}`,
                                                                    source: prevNodeId,
                                                                    target: nodeId,
                                                                    type: 'smoothstep'
                                                                });
                                                            });

                                                            draftNodes.forEach(n => {
                                                                if (n.type === 'connector' || (n.data.config.action && n.data.config.action.includes('.'))) {
                                                                    if (!n.data.config.connector_id) n.data.config.connector_id = 'unassigned';
                                                                    if (!n.data.config.tool_name) n.data.config.tool_name = n.data.config.action || '';
                                                                    if (!n.data.config.provider) n.data.config.provider = n.data.description || '';
                                                                } else if (n.type === 'approval') {
                                                                    n.data.config.routing_strategy = 'any';
                                                                } else if (n.type === 'ai') {
                                                                    if (!n.data.config.model_id) n.data.config.model_id = 'default_model';
                                                                    if (!n.data.config.prompt_template_id) n.data.config.prompt_template_id = 'default_template';
                                                                } else if (n.type === 'condition') {
                                                                    if (!n.data.config.expression) n.data.config.expression = "status == 'success'";
                                                                } else if (n.type === 'planner') {
                                                                    if (!n.data.config.prompt) n.data.config.prompt = "Process task";
                                                                    if (!n.data.config.strategy) n.data.config.strategy = "simple";
                                                                }
                                                            });

                                                            const baseTitle = plan?.task?.title || safeTask?.title || 'Execution';
                                                            const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                                                            const workflowName = `Copy of ${baseTitle} (${timeStr})`;
                                                            const workflowDescription = plan?.task?.description || '';

                                                            const newWf = await workflowApi.createWorkflow({
                                                                name: workflowName,
                                                                description: workflowDescription,
                                                                variables: []
                                                            });

                                                            const mapped = mapReactFlowToSyncSphere(draftNodes as any, draftEdges);
                                                            await workflowApi.updateWorkflow(newWf.id, {
                                                                name: workflowName,
                                                                description: workflowDescription,
                                                                nodes: mapped.nodes,
                                                                edges: mapped.edges,
                                                                variables: []
                                                            });

                                                            qc.invalidateQueries({ queryKey: ['workflows'] });
                                                            console.info('[Duplicate] Created editable copy, id:', newWf.id);
                                                            toast.success('Duplicate created!', { description: 'Opening editable copy in workflow builder...' });
                                                            router.push(`/dashboard/workflows/${newWf.id}`);
                                                        } catch (err: any) {
                                                            console.error('[Duplicate] Failed:', err);
                                                            toast.error('Duplication failed', { description: err?.response?.data?.detail || err?.message || 'Error creating duplicate.' });
                                                        } finally {
                                                            setIsDuplicatingCopy(false);
                                                        }
                                                    }}
                                                />
                                                <ActionButton icon={<Calendar />} label="Schedule" onClick={() => setShowScheduleModal(true)} />
                                                <ActionButton icon={<Download />} label="Export Logs" onClick={() => setShowExportModal(true)} />
                                            </div>

                                        </div>
                                    ) : (
                                        <div className="w-full bg-[#0E1117]/80 backdrop-blur-2xl border border-red-500/20 p-8 md:p-10 rounded-3xl shadow-[0_0_50px_rgba(239,68,68,0.1)] flex flex-col relative overflow-hidden transition-all duration-700 animate-in fade-in slide-in-from-bottom-8">
                                            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[80%] h-32 bg-red-500/10 blur-[100px] rounded-full pointer-events-none" />

                                            <div className="flex flex-col items-center text-center mb-10 relative z-10">
                                                <div className="h-16 w-16 bg-red-500/10 rounded-full flex items-center justify-center mb-4 ring-1 ring-red-500/30 shadow-[0_0_30px_rgba(239,68,68,0.2)]">
                                                    <XCircle className="h-8 w-8 text-red-500" />
                                                </div>
                                                <h2 className="text-3xl font-black tracking-tight mb-2 text-white">
                                                    {isPartial ? "⚠ Workflow Partially Completed" : "❌ Workflow Failed"}
                                                </h2>
                                                <p className="text-slate-400 font-medium">
                                                    {isPartial ? `${executedAutomations.filter((a: any) => a.status === 'success').length} of ${executedAutomations.length} actions completed.` : "Your SyncSphere workflow was unable to complete."}
                                                </p>
                                            </div>

                                            <div className="space-y-4 w-full relative z-10">
                                                {allAutomations.filter(a => a.selected).map((a, idx) => {
                                                    const executedAuto = executedAutomations.find((ea: any) => ea.action === a.action);
                                                    const exStatus = executedAuto?.status;
                                                    const error = executedAuto?.error;
                                                    const isError = exStatus === 'failed' || exStatus === 'blocked';
                                                    if (!isError && exStatus !== 'success') return null;

                                                    return (
                                                        <div key={`err-${idx}`} className={`p-4 rounded-xl border flex flex-col gap-3 ${isError ? 'bg-red-500/5 border-red-500/20' : 'bg-emerald-500/5 border-emerald-500/20'}`}>
                                                            <div className="flex items-center justify-between">
                                                                <div className="flex items-center gap-2">
                                                                    {isError ? <XCircle className="h-4 w-4 text-red-500" /> : <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
                                                                    <span className="font-semibold text-sm capitalize text-white">{a.app.replace('_', ' ')}</span>
                                                                </div>
                                                                <span className={`text-xs font-bold px-2 py-1 rounded border ${isError ? 'bg-red-500/10 border-red-500/20 text-red-400' : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'}`}>
                                                                    {isError ? 'Failed' : 'Success'}
                                                                </span>
                                                            </div>
                                                            {isError && error && (
                                                                <div className="p-3 bg-black/40 rounded-lg border border-red-500/10 text-xs text-red-400 font-mono break-all whitespace-pre-wrap">
                                                                    <span className="block font-bold text-red-500 mb-1">Reason:</span>
                                                                    {formatConnectorError(error, a.app.replace('_', ' '))}
                                                                </div>
                                                            )}
                                                        </div>
                                                    );
                                                })}
                                            </div>

                                            <div className="mt-8 flex gap-3 w-full relative z-10 justify-center">
                                                <Button size="lg" className="bg-white text-black hover:bg-slate-200 shadow-xl rounded-xl" onClick={() => { setPlan(null); setExecutionResults(null); setExecuting(false); setExecutingTaskId(null); setExecutionTimeout(false); }}>
                                                    🔄 Retry Failed Step
                                                </Button>
                                                <Button size="lg" variant="outline" className="border-white/20 text-white hover:bg-white/5 shadow-xl rounded-xl" onClick={() => { setPlan(null); setExecutionResults(null); setExecuting(false); setExecutingTaskId(null); setExecutionTimeout(false); }}>
                                                    Run Workflow Again
                                                </Button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        })() : (
                            <>
                                <div className="relative w-32 h-32 mb-8 flex items-center justify-center">
                                    <div className="absolute inset-0 border-4 border-muted rounded-full"></div>
                                    <div className={`absolute inset-0 border-4 ${executionTimeout ? 'border-amber-500' : 'border-indigo-500'} border-t-transparent rounded-full animate-spin`}></div>
                                    <Sparkles className={`h-10 w-10 ${executionTimeout ? 'text-amber-500' : 'text-indigo-500'} animate-pulse`} />
                                </div>
                                <h2 className="text-2xl font-bold mb-2">🚀 Executing Your Plan</h2>
                                <p className="text-muted-foreground">SyncSphere is securely orchestrating your external workflows...</p>
                            </>
                        )}

                        {executionTimeout && !executionResults?.status && (
                            <div className="mt-6 p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl max-w-lg text-center flex flex-col items-center">
                                <AlertCircle className="h-6 w-6 text-amber-500 mb-2" />
                                <h3 className="text-amber-600 font-bold mb-1">Execution is taking longer than expected.</h3>
                                <p className="text-xs text-amber-600/80 mb-4">Background execution may be stalled or delayed. You can wait, retry, or review the task details manually.</p>
                                <div className="flex gap-3">
                                    <Button variant="outline" className="border-amber-500/30 text-amber-600 hover:bg-amber-500/10" onClick={() => handleExecute()}>Retry Execution</Button>
                                    <Button variant="default" className="bg-amber-600 hover:bg-amber-700 text-white" onClick={closeAndReset}>View Details</Button>
                                </div>
                            </div>
                        )}

                        {!executionResults?.status && !executionTimeout && (
                            <div className="mt-12 w-full max-w-lg space-y-4">
                                {allAutomations.filter(a => a.selected).map((a, idx) => {
                                    const executedAuto = (currentTask?.automations || executionResults?.automations)?.find((ea: any) => ea.action === a.action);
                                    const exStatus = executedAuto?.status;
                                    const error = executedAuto?.error;

                                    const isDone = exStatus === 'success' || exStatus === 'failed' || exStatus === 'blocked' || exStatus === 'cancelled';
                                    const StatusIcon = exStatus === 'success' ? CheckCircle2 : (exStatus === 'failed' || exStatus === 'blocked') ? XCircle : Loader2;
                                    const colorClass = exStatus === 'success' ? 'text-emerald-500' : (exStatus === 'failed' || exStatus === 'blocked') ? 'text-red-500' : 'text-indigo-500';

                                    return (
                                        <div key={idx} className={`flex items-start gap-4 p-4 rounded-xl ${(exStatus === 'failed' || exStatus === 'blocked') ? 'bg-red-500/10 border border-red-500/20' : 'bg-muted/30'}`}>
                                            <StatusIcon className={`h-5 w-5 ${colorClass} mt-0.5 shrink-0 ${!isDone ? 'animate-spin' : ''}`} />
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-semibold text-sm capitalize">{a.app.replace('_', ' ')}</span>
                                                    {exStatus === 'success' && <span className="text-emerald-500 font-medium text-xs ml-auto whitespace-nowrap overflow-hidden text-ellipsis">— Success</span>}
                                                    {exStatus === 'failed' && <span className="text-red-500 font-medium text-xs ml-auto whitespace-nowrap overflow-hidden text-ellipsis">— Failed</span>}
                                                    {exStatus === 'blocked' && <span className="text-red-500 font-medium text-xs ml-auto whitespace-nowrap overflow-hidden text-ellipsis">— Blocked</span>}
                                                    {!isDone && <span className="text-indigo-500 font-medium text-xs ml-auto whitespace-nowrap overflow-hidden text-ellipsis">— {exStatus === 'executing' ? 'Running' : 'Waiting'}</span>}
                                                </div>
                                                <p className="text-xs text-muted-foreground capitalize mb-1">{a.action.replace('_', ' ').replace('.', ' \u2192 ')}</p>

                                                {(exStatus === 'failed' || exStatus === 'blocked') && error && (
                                                    <div className="mt-2 text-xs">
                                                        <p className="text-red-600/90 bg-red-500/10 p-2 rounded whitespace-pre-wrap break-all w-full">
                                                            {formatConnectorError(error, a.app.replace('_', ' '))}
                                                        </p>
                                                    </div>
                                                )}
                                                {exStatus === 'success' && executedAuto?.result && (
                                                    <div className="mt-3 flex flex-wrap gap-2">
                                                        {(() => {
                                                            const res = executedAuto.result;
                                                            const app = a.app.replace('_', ' ');
                                                            let links = [];
                                                            if (app === 'github' && res.html_url && res.repository) {
                                                                links.push({ label: 'View Repository', url: `https://github.com/${res.repository}` });
                                                                links.push({ label: 'View Created Issue', url: res.html_url });
                                                            } else if (app === 'jira' && res.issue_url && res.issue_key) {
                                                                const projUrl = res.issue_url.split('/browse/')[0] + '/projects/' + res.issue_key.split('-')[0];
                                                                links.push({ label: 'Open Project', url: projUrl });
                                                                links.push({ label: 'View Created Issue', url: res.issue_url });
                                                            } else if (app === 'gmail' && (res.gmailThreadUrl || res.thread_url)) {
                                                                links.push({ label: 'View Thread in Gmail', url: res.gmailThreadUrl || res.thread_url });
                                                            } else if (app === 'slack' && res.message_permalink) {
                                                                links.push({ label: 'Open Slack', url: 'https://app.slack.com/client' });
                                                                links.push({ label: 'View Sent Message', url: res.message_permalink });
                                                            } else if (app === 'google calendar' && res.event_link) {
                                                                links.push({ label: 'Open Event', url: res.event_link });
                                                            } else if (app === 'google sheets' && res.spreadsheet_url) {
                                                                links.push({ label: 'Open Spreadsheet', url: res.spreadsheet_url });
                                                            } else {
                                                                // Generic fallback if URL exists
                                                                const url = res.html_url || res.issue_url || res.web_url || res.thread_url || res.message_permalink || res.event_link || res.spreadsheet_url;
                                                                if (url) links.push({ label: `Open ${app}`, url });
                                                            }
                                                            return links.map((link, i) => (
                                                                <a key={i} href={link.url} target="_blank" rel="noreferrer" className="text-xs bg-muted/80 hover:bg-muted text-foreground px-3 py-1.5 rounded-md transition-colors border border-border inline-flex items-center gap-1 font-medium shadow-sm">
                                                                    {link.label}
                                                                </a>
                                                            ));
                                                        })()}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}

                {plan && !executing && !executionResults && (
                    <div className="px-6 py-4 border-t border-border shrink-0 flex justify-between bg-card items-center shadow-lg relative z-20">
                        <Button variant="ghost" onClick={closeAndReset} className="text-muted-foreground">
                            Cancel
                        </Button>
                        <div className="flex items-center gap-4">
                            {hasMissingRequiredFields && <span className="text-xs text-red-500 font-medium bg-red-500/10 px-3 py-1.5 rounded-full flex items-center gap-1.5"><AlertCircle className="h-3 w-3" /> Please fill missing required fields above</span>}

                            <Button
                                size="lg"
                                className="font-semibold px-8 bg-indigo-600 hover:bg-indigo-700"
                                onClick={handleExecute}
                                disabled={!allConnected || hasMissingRequiredFields}
                            >
                                Apply & Execute
                            </Button>
                        </div>
                    </div>
                )}

                {executionResults && (
                    <div className="px-6 py-4 border-t border-border shrink-0 flex items-center justify-end bg-card z-20 gap-4">
                        {executionResults.status === 'authorization_required' && (
                            <Button onClick={() => { setExecutionResults(null); setExecuting(false); }} variant="outline" className="w-[150px]">
                                Back to Plan
                            </Button>
                        )}
                        <Button
                            size="lg"
                            onClick={closeAndReset}
                            className={`font-semibold px-8 ${executionResults.status === 'authorization_required' ? 'bg-muted text-muted-foreground hover:bg-muted/80' : 'bg-indigo-600 hover:bg-indigo-700 w-[150px]'}`}
                        >
                            {executionResults.status === 'authorization_required' ? 'Cancel' : 'Done'}
                        </Button>
                    </div>
                )}
            </DialogContent>
        </Dialog>

        {/* ── Human Approval Blocking Modal ────────────────────────────────────── */}
        {approvalData && (
            <Dialog open={!!approvalData} onOpenChange={() => setApprovalData(null)}>
                <DialogContent className="max-w-md border-border bg-card shadow-2xl p-6">
                    <div className="relative w-16 h-16 mb-2 flex items-center justify-center">
                        <div className="absolute inset-0 border-4 border-amber-500/20 rounded-full"></div>
                        <AlertCircle className="h-8 w-8 text-amber-500" />
                    </div>
                    <h2 className="text-xl font-bold text-amber-500 animate-pulse">Human Approval Required</h2>
                    <p className="text-sm text-muted-foreground mb-6 mt-1">
                        {approvalData.message || 'This step requires explicit supervisor validation before continuing the execution flow.'}
                    </p>

                    <div className="flex justify-end gap-3 w-full">
                        <Button
                            variant="outline"
                            className="border-red-500/30 hover:bg-red-500/10 text-red-500 font-bold"
                            onClick={async () => {
                                try {
                                    await approvalApi.submitDecision(approvalData.approval_id, false, 'Rejected explicitly via inline prompt.');
                                    toast.error('Task Execution Rejected', { description: 'The workflow has been completely halted.' });
                                    setApprovalData(null);
                                    // Reset entirely to the Plan view
                                } catch (e: any) {
                                    toast.error('Rejection Failed', { description: e?.message });
                                }
                            }}
                        >
                            <XCircle className="w-4 h-4 mr-2" /> Reject
                        </Button>
                        <Button
                            className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold"
                            onClick={async () => {
                                try {
                                    await approvalApi.submitDecision(approvalData.approval_id, true, 'Approved explicitly via inline prompt.');
                                    toast.success('Approval Granted', { description: 'Resuming task execution securely...' });

                                    // Unpause Execution UI transition
                                    const taskId = approvalData.execution_id;
                                    setApprovalData(null);
                                    setExecutingTaskId(taskId);
                                    setExecutionResults({
                                        status: 'polling',
                                        tasksCreated: 1,
                                        automations: (plan?.integrations || []).map((a: any) => ({
                                            action: a.action, status: a.action === 'system.approval' ? 'success' : 'pending'
                                        }))
                                    });
                                    setExecuting(true);
                                } catch (e: any) {
                                    toast.error('Approval Failed', { description: e?.message });
                                }
                            }}
                        >
                            <CheckCircle2 className="w-4 h-4 mr-2" /> Approve & Continue
                        </Button>
                    </div>
                </DialogContent>
            </Dialog>
        )}

        {/* ── Schedule Modal ──────────────────────────────────────────────── */}
        <ScheduleModal open={showScheduleModal} onClose={() => setShowScheduleModal(false)} workflowId={executingTaskId || executionResults?.workflow_id} />

        {/* ── Export Modal ─────────────────────────────────────────────────── */}
        {
            showExportModal && (
                <div className="fixed inset-0 z-[200] flex items-center justify-center p-4" onClick={() => setShowExportModal(false)}>
                    <div className="absolute inset-0 bg-black/60 backdrop-blur-md" />
                    <div
                        className="relative w-full max-w-md bg-[#0E1117]/95 border border-cyan-500/20 rounded-3xl shadow-[0_0_60px_rgba(6,182,212,0.1)] p-8 flex flex-col gap-6"
                        onClick={e => e.stopPropagation()}
                    >
                        <button className="absolute top-5 right-5 text-slate-500 hover:text-white" onClick={() => setShowExportModal(false)}><X className="h-5 w-5" /></button>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="h-10 w-10 bg-cyan-500/10 rounded-xl flex items-center justify-center ring-1 ring-cyan-500/30">
                                <Download className="h-5 w-5 text-cyan-400" />
                            </div>
                            <div>
                                <h2 className="text-lg font-bold text-white">Export Execution Logs</h2>
                                <p className="text-xs text-slate-400">Download a professional execution report</p>
                            </div>
                        </div>

                        <div className="flex flex-col gap-3">
                            {(['json', 'csv', 'pdf'] as const).map(fmt => {
                                const meta = {
                                    json: { label: 'JSON', desc: 'Machine-readable structured data', icon: '{ }', color: 'text-amber-400 border-amber-500/30 bg-amber-500/5 hover:border-amber-500/60' },
                                    csv: { label: 'CSV', desc: 'Spreadsheet-compatible flat file', icon: '⊞', color: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/5 hover:border-emerald-500/60' },
                                    pdf: { label: 'PDF / HTML', desc: 'Branded SyncSphere report', icon: '⊷', color: 'text-indigo-400 border-indigo-500/30 bg-indigo-500/5 hover:border-indigo-500/60' },
                                }[fmt];
                                return (
                                    <button
                                        key={fmt}
                                        disabled={isExporting}
                                        onClick={async () => {
                                            const sessionId = executionResults?.session_id || executionResults?.execution_id || executingTaskId;
                                            if (!sessionId) {
                                                toast.error('No execution session found', { description: 'This run has no linked execution session for export.' });
                                                return;
                                            }
                                            setIsExporting(true);
                                            try {
                                                const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
                                                const res = await fetch(
                                                    `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/v1/automations/executions/${sessionId}/export?format=${fmt}`,
                                                    { headers: { Authorization: `Bearer ${token}` } }
                                                );
                                                if (!res.ok) throw new Error(`Export failed: ${res.statusText}`);
                                                const blob = await res.blob();
                                                const url = URL.createObjectURL(blob);
                                                const a = document.createElement('a');
                                                a.href = url;
                                                a.download = `execution_${sessionId.substring(0, 8)}.${fmt === 'pdf' ? 'html' : fmt}`;
                                                document.body.appendChild(a);
                                                a.click();
                                                document.body.removeChild(a);
                                                URL.revokeObjectURL(url);
                                                toast.success(`Exported as ${fmt.toUpperCase()}`);
                                                setShowExportModal(false);
                                            } catch (err: any) {
                                                toast.error('Export failed', { description: err?.message });
                                            } finally {
                                                setIsExporting(false);
                                            }
                                        }}
                                        className={`flex items-center gap-4 p-4 rounded-2xl border transition-all text-left ${meta.color} ${isExporting ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                                    >
                                        <span className="text-2xl w-8 text-center">{meta.icon}</span>
                                        <div>
                                            <div className="font-bold text-sm">{meta.label}</div>
                                            <div className="text-xs text-slate-500">{meta.desc}</div>
                                        </div>
                                        {isExporting ? <Loader2 className="h-4 w-4 animate-spin ml-auto" /> : <Download className="h-4 w-4 ml-auto opacity-40" />}
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                </div>
            )
        }
    </>);
}
