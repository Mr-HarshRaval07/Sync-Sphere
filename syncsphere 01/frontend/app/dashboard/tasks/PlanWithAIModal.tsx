'use client';

import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { tasksApi } from '../../../shared/services/api';
import { Button } from '../../../components/ui/button';
import { Textarea } from '../../../components/ui/textarea';
import { Checkbox } from '../../../components/ui/checkbox';
import { Input } from '../../../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../../components/ui/dialog';
import { Sparkles, Loader2, CheckCircle2, AlertCircle, ChevronRight, X, LayoutGrid, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import { API_BASE_URL, integrationApi, apiClient } from '../../../shared/services/api-client';
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
    const [prompt, setPrompt] = useState('');
    const [plan, setPlan] = useState<AIProjectPlan | null>(null);
    const [executing, setExecuting] = useState(false);
    const [executionResults, setExecutionResults] = useState<any>(null);
    const [executingTaskId, setExecutingTaskId] = useState<string | null>(null);
    const [executionStartTime, setExecutionStartTime] = useState<number | null>(null);
    const [executionTimeout, setExecutionTimeout] = useState(false);

    const { data: oauthStatus } = useQuery({
        queryKey: ['connector-status'],
        queryFn: async () => {
            try {
                const res = await apiClient.get('/v1/connect/status');
                return res.data;
            } catch (err) {
                return { google: { connected: false }, github: { connected: false }, slack: { connected: false } };
            }
        },
        refetchOnWindowFocus: true,
        refetchOnMount: true,
    });

    const { data: currentTask } = useQuery({
        queryKey: ['task', executingTaskId],
        queryFn: () => tasksApi.getTask(executingTaskId!),
        refetchInterval: (query: any) => {
            if (executionTimeout) return false;
            const data = query?.state?.data || query;
            const actualTask = data?.data || data;
            const automations = actualTask?.automations || [];
            if (!automations || automations.length === 0) return 1500;
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
        if (executing && !executionResults && executionStartTime) {
            interval = setInterval(() => {
                if (Date.now() - executionStartTime > 60000) {
                    setExecutionTimeout(true);
                }
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [executing, executionResults, executionStartTime]);

    useEffect(() => {
        if (currentTask && executingTaskId) {
            const actualTask = (currentTask as any).data || currentTask;
            const automations = actualTask?.automations || [];
            if (automations.length > 0) {
                const isDone = automations.every((a: any) =>
                    a.status === 'success' ||
                    a.status === 'failed' ||
                    a.status === 'blocked' ||
                    a.status === 'cancelled'
                );

                setExecutionResults((prev: any) => ({
                    ...prev,
                    status: isDone ? 'done' : 'polling',
                    tasksCreated: 1,
                    automations: automations
                }));
            }
        }
    }, [currentTask, executingTaskId]);

    useEffect(() => {
        if (open) {
            const saved = sessionStorage.getItem('pending_ai_plan');
            if (saved) {
                const parsed = JSON.parse(saved);
                setPrompt(parsed.prompt);
                setPlan(parsed.plan);
                sessionStorage.removeItem('pending_ai_plan');
            }
        }
    }, [open]);

    const generateMutation = useMutation({
        mutationFn: (desc: string) => tasksApi.planWithAI(desc),
        onSuccess: (data: AIProjectPlan) => {
            setPlan(data);
        },
        onError: (e: any) => {
            const isTimeout = e?.code === 'ECONNABORTED' || e?.message?.toLowerCase().includes('timeout');
            if (isTimeout) {
                toast.error('AI Request Timed Out', {
                    description: 'The task was too complex for the AI to process within 60 seconds. Please simplify your prompt and try again.',
                });
                return;
            }
            const status = e?.response?.status;
            const backendDetail = e?.response?.data?.detail;

            if (status === 429) {
                const retryMsg = e?.response?.headers?.['retry-after']
                    ? ` Retry after ${e.response.headers['retry-after']}s.`
                    : '';
                toast.error('AI provider rate limit reached.', {
                    description: (backendDetail || 'Please wait and try again.') + retryMsg,
                });
            } else if (status === 401 || status === 403) {
                toast.error('AI provider authentication or permission error.', {
                    description: backendDetail || 'Check your API key.',
                });
            } else if (status === 404) {
                toast.error('AI model is unavailable.', {
                    description: backendDetail || 'Check the configured model name.',
                });
            } else if (backendDetail) {
                toast.error('Failed to generate plan.', {
                    description: backendDetail,
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
                        if (reqProviders.includes(app) || (reqProviders.includes('google') && ['gmail', 'google_calendar', 'google_sheets'].includes(app))) {
                            return { action: a.action, status: 'blocked', error: `Authorization required. Please connect ${app.replace('_', ' ')}.` };
                        }
                        return { action: a.action, status: 'pending' };
                    })
                });
                return;
            }

            setExecuting(false);
            toast.error('Failed to create tasks', { description: e?.message });
        },
    });

    const handleGenerate = () => {
        if (!prompt) return;
        generateMutation.mutate(prompt);
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
        auto.config[field] = value;
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

    const handleConnect = async (provider: string) => {
        sessionStorage.setItem('pending_ai_plan', JSON.stringify({ prompt, plan }));
        try {
            if (provider === 'google') await integrationApi.connectGoogle();
            else if (provider === 'slack') await integrationApi.connectSlack();
            else if (provider === 'github') await integrationApi.connectGithub();
            else window.location.href = `${API_BASE_URL}/v1/connect/${provider}`;
        } catch (e) {
            toast.error('Failed to initiate connection', { description: 'The authentication server might be unavailable.' });
        }
    };

    const isConnected = (app: string) => {
        const a = app.toLowerCase();
        if (a.includes('google') || a.includes('gmail') || a.includes('sheets') || a.includes('calendar')) return oauthStatus?.google?.connected;
        if (a.includes('slack')) return oauthStatus?.slack?.connected;
        if (a.includes('github')) return oauthStatus?.github?.connected;
        return true;
    };

    const getProviderKey = (app: string) => {
        const a = app.toLowerCase();
        if (a.includes('google') || a.includes('gmail') || a.includes('sheets') || a.includes('calendar')) return 'google';
        if (a.includes('slack')) return 'slack';
        if (a.includes('github')) return 'github';
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
        ((a as any).missing_required_fields || []).some((mkey: string) => !a.config[mkey] || String(a.config[mkey]).trim() === '')
    );

    const closeAndReset = () => {
        setPlan(null);
        setPrompt('');
        setExecutionResults(null);
        setExecuting(false);
        setExecutionStartTime(null);
        setExecutionTimeout(false);
        onClose();
    };

    const safeTask = plan?.task ?? null;

    return (
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
                            <h2 className="text-2xl font-bold">What would you like to achieve?</h2>
                            <Textarea
                                className="min-h-[200px] resize-none text-lg p-6 bg-card border-none shadow-sm rounded-2xl ring-1 ring-border/50 focus-visible:ring-primary"
                                placeholder="Example: Launch our new website next Friday. Create a GitHub issue for the devs, notify the team in Slack, send an email to the client, and schedule a launch meeting..."
                                value={prompt}
                                onChange={e => setPrompt(e.target.value)}
                            />

                            <div className="flex gap-3 pt-6 w-full">
                                <Button
                                    size="lg"
                                    className="w-full h-12 text-base font-semibold shadow-md bg-gradient-to-r from-primary to-indigo-600 hover:from-primary/90 hover:to-indigo-600/90"
                                    disabled={!prompt || generateMutation.isPending}
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
                                                        {Object.entries(a.config).filter(([k]) => k !== 'body' && k !== 'description').map(([k, v]) => (
                                                            <div key={k} className="flex flex-col gap-1 w-full overflow-hidden">
                                                                <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">{k}</span>
                                                                <span className="text-xs bg-muted p-2 rounded-md whitespace-normal break-words font-mono w-full min-w-0">{String(v)}</span>
                                                            </div>
                                                        ))}
                                                        {/* Preview big fields briefly */}
                                                        {Object.entries(a.config).filter(([k]) => k === 'body' || k === 'description').map(([k, v]) => (
                                                            <div key={k} className="flex flex-col gap-1 w-full overflow-hidden">
                                                                <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">{k}</span>
                                                                <span className="text-xs bg-muted p-2 rounded-md whitespace-normal break-words font-mono w-full min-w-0 max-h-[150px] overflow-y-auto">{String(v)}</span>
                                                            </div>
                                                        ))}

                                                        {/* Missing fields inputs */}
                                                        {((a as any).missing_required_fields || []).map((mkey: string) => {
                                                            if (!a.config[mkey]) {
                                                                return (
                                                                    <div key={mkey} className="flex flex-col gap-1.5 mt-2 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                                                                        <span className="text-xs font-bold text-amber-700 flex items-center gap-1.5">
                                                                            <AlertCircle className="h-3 w-3" /> Requires: {mkey}
                                                                        </span>
                                                                        {(a as any).clarification_question && <span className="text-[10px] text-amber-700/80 leading-tight">{(a as any).clarification_question}</span>}
                                                                        <Input
                                                                            className="h-7 text-xs bg-card"
                                                                            placeholder={`Enter ${mkey}...`}
                                                                            onChange={e => updateMissingField(a.autoIdx, mkey, e.target.value)}
                                                                        />
                                                                    </div>
                                                                );
                                                            }
                                                            return null;
                                                        })}
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
                    <div className="flex-1 flex flex-col items-center justify-center bg-card p-12">
                        {executionResults?.status === 'authorization_required' ? (
                            <>
                                <div className="relative w-24 h-24 mb-6 flex items-center justify-center">
                                    <div className="absolute inset-0 border-4 border-red-500/20 rounded-full"></div>
                                    <AlertCircle className="h-10 w-10 text-red-500" />
                                </div>
                                <h2 className="text-2xl font-bold mb-2 text-red-600">Authorization Required</h2>
                                <p className="text-muted-foreground max-w-lg text-center">{executionResults.message || 'Please authorize the required services to continue.'}</p>
                            </>
                        ) : executionResults?.status === 'done' ? (
                            <>
                                <div className="relative w-24 h-24 mb-6 flex items-center justify-center">
                                    <div className="absolute inset-0 border-4 border-emerald-500/20 rounded-full"></div>
                                    <CheckCircle2 className="h-10 w-10 text-emerald-500" />
                                </div>
                                <h2 className="text-2xl font-bold mb-2">Execution Complete</h2>
                                <p className="text-muted-foreground">Your plan has been executed successfully.</p>
                            </>
                        ) : (
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

                        {executionTimeout && !executionResults && (
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

                        <div className="mt-12 w-full max-w-lg space-y-4">
                            {allAutomations.filter(a => a.selected).map((a, idx) => {
                                const executedAuto = (currentTask?.automations || executionResults?.automations)?.find((ea: any) => ea.action === a.action);
                                const exStatus = executedAuto?.status; // 'success' or 'failed' or 'pending' or 'executing'
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
                                                {exStatus === 'blocked' && <span className="text-red-500 font-medium text-xs ml-auto whitespace-nowrap overflow-hidden text-ellipsis">— {(String(error).toLowerCase().includes('permission') || String(error).toLowerCase().includes('not in channel') || String(error).toLowerCase().includes('missing_scope')) ? 'Slack Permission Error' : 'Authorization Required'}</span>}
                                                {!isDone && <span className="text-indigo-500 font-medium text-xs ml-auto whitespace-nowrap overflow-hidden text-ellipsis">— {exStatus === 'executing' ? 'Running' : 'Waiting'}</span>}
                                            </div>
                                            <p className="text-xs text-muted-foreground capitalize mb-1">{a.action.replace('_', ' ').replace('.', ' \u2192 ')}</p>

                                            {/* Display specific error if available */}
                                            {(exStatus === 'failed' || exStatus === 'blocked') && error && (
                                                <div className="mt-2 text-xs">
                                                    <p className="text-red-600/90 bg-red-500/10 p-2 rounded font-mono whitespace-pre-wrap break-all w-full">
                                                        {typeof error === 'object' ? JSON.stringify(error) : error}
                                                    </p>
                                                    {exStatus === 'blocked' && (
                                                        <Button
                                                            size="sm"
                                                            className="mt-3 bg-red-600 hover:bg-red-700 text-white"
                                                            onClick={() => handleConnect(getProviderKey(a.app) || a.app)}
                                                        >
                                                            {(String(error).toLowerCase().includes('permission') || String(error).toLowerCase().includes('not in channel') || String(error).toLowerCase().includes('missing_scope')) ? `Reconnect ${a.app.replace('_', ' ')}` : `Connect ${a.app.replace('_', ' ')}`}
                                                        </Button>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {plan && !executing && !executionResults && (
                    <div className="px-6 py-4 border-t border-border shrink-0 flex justify-between bg-card items-center shadow-lg relative z-20">
                        <Button variant="ghost" onClick={() => { setPlan(null); setPrompt(''); }} className="text-muted-foreground">
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
    );
}
