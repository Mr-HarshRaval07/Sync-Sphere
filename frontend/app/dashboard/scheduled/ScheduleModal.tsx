'use client';

import React, { useState, useEffect } from 'react';
import { Calendar, CalendarDays, Loader2, X } from 'lucide-react';
import { Button } from '../../../components/ui/button';
import { scheduleApi, workflowApi, automationApi } from '../../../shared/services/api';
import { toast } from 'sonner';
import { useQuery, useQueryClient } from '@tanstack/react-query';

export interface ScheduleModalProps {
    open: boolean;
    onClose: () => void;
    workflowId?: string | null;
    initialData?: any;
}

export function ScheduleModal({ open, onClose, workflowId: preSelectedId, initialData }: ScheduleModalProps) {
    const qc = useQueryClient();
    const [scheduleType, setScheduleType] = useState<'once' | 'hourly' | 'every_x_hours' | 'daily' | 'weekly' | 'monthly' | 'cron'>('daily');
    const [scheduleStartDate, setScheduleStartDate] = useState('');
    const [scheduleTimeOfDay, setScheduleTimeOfDay] = useState('09:00');
    const [scheduleIntervalHours, setScheduleIntervalHours] = useState(1);
    const [selectedWorkflowId, setSelectedWorkflowId] = useState<string>('');
    const [isSavingSchedule, setIsSavingSchedule] = useState(false);

    useEffect(() => {
        if (open) {
            if (initialData) {
                setScheduleType(initialData.schedule_type || 'daily');
                // Trim Z and map to datetime-local format
                let sd = initialData.start_date || '';
                if (sd && sd.endsWith('Z')) sd = sd.slice(0, 16);
                setScheduleStartDate(sd);
                setScheduleTimeOfDay(initialData.time_of_day || '09:00');
                setScheduleIntervalHours(initialData.interval_hours || 1);
                if (initialData.workflow_id) setSelectedWorkflowId(initialData.workflow_id);
            } else {
                setScheduleType('daily');
                setScheduleStartDate('');
                setScheduleTimeOfDay('09:00');
                setScheduleIntervalHours(1);
                if (preSelectedId) setSelectedWorkflowId(preSelectedId);
                else setSelectedWorkflowId('');
            }
        }
    }, [open, initialData, preSelectedId]);

    const { data: workflows, isLoading: isLoadingWf } = useQuery({
        queryKey: ['workflows'],
        queryFn: () => workflowApi.listWorkflows(),
        enabled: open && !preSelectedId && !initialData,
    });

    const { data: automations, isLoading: isLoadingAuto } = useQuery({
        queryKey: ['automations'],
        queryFn: () => automationApi.listAutomations(),
        enabled: open && !preSelectedId && !initialData,
    });

    const combinedOptions = React.useMemo(() => {
        const opts: { id: string, name: string, type: string }[] = [];
        if (workflows) {
            workflows.forEach((w: any) => opts.push({ id: w.id, name: w.name, type: 'Workflow' }));
        }
        if (automations) {
            automations.forEach((a: any) => opts.push({ id: a.id, name: a.name || 'Automation Task', type: 'Automation' }));
        }
        return opts;
    }, [workflows, automations]);

    if (!open) return null;

    const handleSave = async () => {
        const targetId = preSelectedId || selectedWorkflowId;
        if (!targetId) {
            toast.error('No workflow selected', { description: 'Please select a workflow to schedule.' });
            return;
        }

        // Validate
        if (scheduleType === 'once' && !scheduleStartDate) {
            toast.error('Start date missing', { description: 'You must provide a start date for one-time schedules.' });
            return;
        }
        if (scheduleType === 'once' && scheduleStartDate) {
            if (new Date(scheduleStartDate).getTime() < Date.now()) {
                toast.error('Invalid date', { description: 'Start date must be in the future.' });
                return;
            }
        }

        setIsSavingSchedule(true);
        try {
            let formattedDate = scheduleStartDate;
            if (formattedDate && !formattedDate.endsWith('Z')) {
                // Ensure ISO string with Z for backend if it doesn't already have tz info
                formattedDate = new Date(formattedDate).toISOString();
            }

            const schedulePayload = {
                workflow_id: targetId,
                schedule_type: scheduleType,
                start_date: scheduleType === 'once' ? formattedDate : undefined,
                time_of_day: ['daily', 'weekly', 'monthly'].includes(scheduleType) ? scheduleTimeOfDay : undefined,
                interval_hours: scheduleType === 'every_x_hours' ? scheduleIntervalHours : undefined,
                enabled: true,
            };

            if (initialData?.id) {
                await scheduleApi.updateSchedule(initialData.id, schedulePayload);
                toast.success('Schedule updated!', { description: `Workflow schedule updated successfully.` });
            } else {
                await scheduleApi.createSchedule(schedulePayload);
                toast.success('Schedule saved!', { description: `Workflow will run on a ${scheduleType} schedule.` });
            }
            qc.invalidateQueries({ queryKey: ['scheduled_workflows'] });
            qc.invalidateQueries({ queryKey: ['scheduled_automations'] });
            onClose();
        } catch (err: any) {
            toast.error('Failed to save schedule', { description: err?.response?.data?.detail?.message || err?.message });
        } finally {
            setIsSavingSchedule(false);
        }
    };

    const isDropdownVisible = !preSelectedId && !initialData;

    return (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4" onClick={onClose}>
            <div className="absolute inset-0 bg-black/60 backdrop-blur-md" />
            <div
                className="relative w-full max-w-lg bg-[#0E1117]/95 border border-indigo-500/20 rounded-3xl shadow-[0_0_60px_rgba(99,102,241,0.15)] p-8 flex flex-col gap-6"
                onClick={e => e.stopPropagation()}
            >
                <button className="absolute top-5 right-5 text-slate-500 hover:text-white transition-colors" onClick={onClose}>
                    <X className="h-5 w-5" />
                </button>
                <div className="flex items-center gap-3 mb-2">
                    <div className="h-10 w-10 bg-indigo-500/10 rounded-xl flex items-center justify-center ring-1 ring-indigo-500/30">
                        <Calendar className="h-5 w-5 text-indigo-400" />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white">{initialData ? 'Edit Schedule' : 'Schedule Workflow'}</h2>
                        <p className="text-xs text-slate-400">Set up recurring or one-time execution</p>
                    </div>
                </div>

                {isDropdownVisible && (
                    <div className="flex flex-col gap-2">
                        <label className="text-xs font-semibold uppercase tracking-widest text-slate-500">Target Workflow</label>
                        <select
                            value={selectedWorkflowId}
                            onChange={(e) => setSelectedWorkflowId(e.target.value)}
                            className="bg-[#18181b] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                        >
                            <option value="" disabled>{(isLoadingWf || isLoadingAuto) ? 'Loading...' : 'Select a workflow...'}</option>
                            {combinedOptions.map(o => (
                                <option key={o.id} value={o.id}>{o.name} ({o.type})</option>
                            ))}
                        </select>
                    </div>
                )}

                {/* Schedule Type Selector */}
                <div className="flex flex-col gap-2">
                    <label className="text-xs font-semibold uppercase tracking-widest text-slate-500">Frequency</label>
                    <div className="grid grid-cols-3 gap-2">
                        {(['once', 'hourly', 'daily', 'every_x_hours', 'weekly', 'monthly'] as const).map(t => (
                            <button
                                key={t}
                                onClick={() => setScheduleType(t as any)}
                                className={`py-2 px-3 rounded-xl text-xs font-semibold border transition-all ${scheduleType === t
                                    ? 'bg-indigo-600 border-indigo-500 text-white shadow-[0_0_20px_rgba(99,102,241,0.3)]'
                                    : 'bg-white/5 border-white/10 text-slate-400 hover:border-indigo-500/40'
                                    }`}
                            >
                                {t === 'every_x_hours' ? 'Every N hrs' : t.charAt(0).toUpperCase() + t.slice(1)}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Conditional fields */}
                {scheduleType === 'once' && (
                    <div className="flex flex-col gap-2">
                        <label className="text-xs font-semibold uppercase tracking-widest text-slate-500">Date & Time</label>
                        <input type="datetime-local" value={scheduleStartDate} onChange={e => setScheduleStartDate(e.target.value)}
                            className="bg-[#18181b] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50" />
                    </div>
                )}

                {(scheduleType === 'daily' || scheduleType === 'weekly' || scheduleType === 'monthly') && (
                    <div className="flex flex-col gap-2">
                        <label className="text-xs font-semibold uppercase tracking-widest text-slate-500">Time of Day</label>
                        <input type="time" value={scheduleTimeOfDay} onChange={e => setScheduleTimeOfDay(e.target.value)}
                            className="bg-[#18181b] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50" />
                    </div>
                )}

                {scheduleType === 'every_x_hours' && (
                    <div className="flex flex-col gap-2">
                        <label className="text-xs font-semibold uppercase tracking-widest text-slate-500">Every (hours)</label>
                        <input type="number" min={1} max={168} value={scheduleIntervalHours} onChange={e => setScheduleIntervalHours(Number(e.target.value))}
                            className="bg-[#18181b] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50" />
                    </div>
                )}

                <div className="flex gap-3 mt-2">
                    <Button variant="outline" className="flex-1 border-white/10 text-slate-400 hover:bg-white/5 hover:text-white" onClick={onClose}>Cancel</Button>
                    <Button
                        className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold"
                        disabled={isSavingSchedule}
                        onClick={handleSave}
                    >
                        {isSavingSchedule ? <Loader2 className="h-4 w-4 animate-spin" /> : <><CalendarDays className="h-4 w-4 mr-1.5" /> Save Schedule</>}
                    </Button>
                </div>
            </div>
        </div>
    );
}
