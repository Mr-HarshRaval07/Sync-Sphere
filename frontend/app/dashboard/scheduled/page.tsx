'use client';

import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { scheduleApi } from '../../../shared/services/api';
import { CalendarClock, Clock, Loader2, Play, Plus, RefreshCw, Filter, ToggleLeft, ToggleRight, CalendarDays, Repeat, Trash2, Edit, Info } from 'lucide-react';
import { toast } from 'sonner';
import { ScheduleModal } from './ScheduleModal';

export default function ScheduledWorkflowsPage() {
    const qc = useQueryClient();
    const { data: schedules, isLoading, refetch } = useQuery({
        queryKey: ['scheduled_workflows_list'],
        queryFn: () => scheduleApi.listSchedules(),
    });

    const [filter, setFilter] = useState<'all' | 'active' | 'paused'>('all');
    const [showModal, setShowModal] = useState(false);
    const [editingSchedule, setEditingSchedule] = useState<any>(null);

    const filtered = (schedules || []).filter((s: any) => {
        if (filter === 'active') return s.enabled;
        if (filter === 'paused') return !s.enabled;
        return true;
    });

    const handleToggle = async (id: string, currentlyEnabled: boolean) => {
        try {
            await scheduleApi.toggleSchedule(id, !currentlyEnabled);
            toast.success(`Schedule ${currentlyEnabled ? 'paused' : 'resumed'} successfully.`);
            qc.invalidateQueries({ queryKey: ['scheduled_workflows_list'] });
        } catch (err: any) {
            toast.error('Failed to toggle schedule', { description: err?.message || 'Check your connection.' });
        }
    };

    const handleDelete = async (id: string) => {
        if (!window.confirm('Are you sure you want to delete this schedule? This action cannot be undone.')) return;
        try {
            await scheduleApi.deleteSchedule(id);
            toast.success('Schedule deleted.');
            qc.invalidateQueries({ queryKey: ['scheduled_workflows_list'] });
        } catch (err: any) {
            toast.error('Failed to delete schedule', { description: err?.message });
        }
    };

    const handleRunNow = async (id: string) => {
        try {
            const res = await scheduleApi.runScheduleNow(id);
            toast.success('Execution triggered!', { description: `Log ID: ${res.execution_log_id}` });
        } catch (err: any) {
            toast.error('Failed to trigger execution', { description: err?.response?.data?.detail?.message || err?.message });
        }
    };

    return (
        <div className="w-full h-full p-4 md:p-8 flex flex-col pt-24 md:pt-8 bg-[#09090b]">
            <ScheduleModal
                open={showModal}
                onClose={() => {
                    setShowModal(false);
                    setEditingSchedule(null);
                }}
                initialData={editingSchedule}
            />

            {/* Header Area */}
            <div className="mb-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
                            <CalendarClock className="h-8 w-8 text-indigo-500" />
                            Scheduled Workflows
                        </h1>
                        <p className="text-slate-400 mt-1">Manage and monitor recurring automated tasks.</p>
                    </div>

                    <div className="flex items-center gap-3">
                        <button onClick={() => refetch()} className="p-2.5 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-colors text-slate-300">
                            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                        </button>
                        <button
                            onClick={() => {
                                setEditingSchedule(null);
                                setShowModal(true);
                            }}
                            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-xl font-medium transition-colors shadow-lg shadow-indigo-500/20"
                        >
                            <Plus className="h-4 w-4" /> New Schedule
                        </button>
                    </div>
                </div>

                {/* Prototype Mode Banner (matching Knowledge Base visual treatment) */}
                <div className="bg-indigo-500/10 border border-indigo-500/20 text-indigo-200 px-4 py-3 rounded-xl flex gap-3 text-sm items-start shadow-sm">
                    <Info className="h-4 w-4 shrink-0 mt-0.5 text-indigo-400" />
                    <div className="flex flex-col gap-1">
                        <span className="font-semibold text-indigo-300">Prototype Mode:</span>
                        <span className="opacity-90 leading-relaxed text-xs text-slate-300">
                            Scheduled Workflows currently operate in demonstration mode. In production, schedules run automatically via background CRON worker tasks with full audit logging and alerting.
                        </span>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 min-h-0 bg-[#0E1117] border border-white/10 rounded-3xl p-6 md:p-8 flex flex-col overflow-hidden relative shadow-2xl">
                {/* Background effects */}
                <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 blur-[100px] rounded-full pointer-events-none" />
                <div className="absolute bottom-[-100px] left-[-100px] w-80 h-80 bg-cyan-500/5 blur-[80px] rounded-full pointer-events-none" />

                {/* Filters */}
                <div className="flex items-center gap-2 mb-6 border-b border-white/5 pb-6 relative z-10">
                    <Filter className="h-4 w-4 text-slate-500 mr-2" />
                    {(['all', 'active', 'paused'] as const).map(f => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-4 py-1.5 rounded-full text-xs font-semibold capitalize transition-all ${filter === f
                                ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                                : 'bg-transparent text-slate-400 hover:bg-white/5 hover:text-slate-300'
                                }`}
                        >
                            {f}
                        </button>
                    ))}
                </div>

                {isLoading ? (
                    <div className="flex-1 flex flex-col items-center justify-center relative z-10">
                        <Loader2 className="h-8 w-8 text-indigo-500 animate-spin mb-4" />
                        <p className="text-slate-400">Loading schedules...</p>
                    </div>
                ) : filtered.length === 0 ? (
                    <div className="flex-1 flex flex-col items-center justify-center text-center max-w-md mx-auto relative z-10">
                        <div className="h-20 w-20 bg-indigo-500/10 rounded-full flex items-center justify-center mb-6 ring-1 ring-indigo-500/20">
                            <CalendarDays className="h-8 w-8 text-indigo-400" />
                        </div>
                        <h2 className="text-xl font-bold text-white mb-2">No schedules {filter !== 'all' ? `(${filter})` : 'found'}</h2>
                        <p className="text-slate-400 mb-8">
                            You haven't scheduled any workflows yet. Use the modal to set up recurring automation tasks.
                        </p>
                    </div>
                ) : (
                    <div className="flex-1 overflow-y-auto pr-2 -mr-2 space-y-4 relative z-10">
                        {filtered.map((s: any) => (
                            <div key={s.id} className="bg-[#18181b] border border-[#27272a] hover:border-indigo-500/40 rounded-2xl p-5 transition-all group flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden group">

                                <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-indigo-500 to-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity" />

                                <div className="flex items-center gap-4">
                                    <div className={`h-12 w-12 rounded-xl flex items-center justify-center border shrink-0 transition-colors ${s.enabled ? 'bg-indigo-500/10 border-indigo-500/20' : 'bg-white/5 border-white/10'}`}>
                                        <Clock className={`h-5 w-5 ${s.enabled ? 'text-indigo-400' : 'text-slate-500'}`} />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-white group-hover:text-indigo-300 transition-colors">
                                            {s.workflow_id ? `Workflow: ${s.workflow_id.slice(-8)}` : 'Schedule'}
                                        </h3>
                                        <div className="flex items-center gap-3 mt-1.5">
                                            <span className="text-xs font-mono bg-white/5 text-slate-300 px-2.5 py-1 rounded-md border border-white/5 tracking-wider uppercase flex flex-row gap-1.5 items-center">
                                                <Repeat className="h-3 w-3 opacity-60" /> {s.schedule_type}
                                            </span>
                                            {s.next_run_at && (
                                                <span className="text-xs text-slate-400 flex items-center gap-1.5">
                                                    Next run: <span className="text-white font-medium">{new Date(s.next_run_at).toLocaleString()}</span>
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-3 w-full md:w-auto mt-4 md:mt-0 justify-between md:justify-end border-t md:border-t-0 border-white/5 pt-4 md:pt-0">
                                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 mr-2">
                                        <div className={`h-2 w-2 rounded-full ${s.enabled ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]' : 'bg-slate-500'}`} />
                                        <span className="text-xs font-medium text-slate-300">{s.enabled ? 'Active' : 'Paused'}</span>
                                    </div>

                                    <div className="flex items-center gap-1">
                                        <button
                                            title="Run Now"
                                            onClick={() => handleRunNow(s.id)}
                                            className="p-2 hover:bg-emerald-500/10 hover:text-emerald-400 rounded-lg text-slate-400 transition-colors"
                                        >
                                            <Play className="h-5 w-5" />
                                        </button>
                                        <button
                                            title="Edit Schedule"
                                            onClick={() => {
                                                setEditingSchedule(s);
                                                setShowModal(true);
                                            }}
                                            className="p-2 hover:bg-indigo-500/10 hover:text-indigo-400 rounded-lg text-slate-400 transition-colors"
                                        >
                                            <Edit className="h-5 w-5" />
                                        </button>
                                        <button
                                            title="Toggle Active"
                                            onClick={() => handleToggle(s.id, s.enabled)}
                                            className={`p-2 hover:bg-white/10 rounded-lg transition-colors ${s.enabled ? 'text-emerald-400' : 'text-slate-400 hover:text-white'}`}
                                        >
                                            {s.enabled ? <ToggleRight className="h-5 w-5" /> : <ToggleLeft className="h-5 w-5" />}
                                        </button>
                                        <button
                                            title="Delete Schedule"
                                            onClick={() => handleDelete(s.id)}
                                            className="p-2 hover:bg-red-500/10 hover:text-red-400 rounded-lg text-slate-400 transition-colors"
                                        >
                                            <Trash2 className="h-5 w-5" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

