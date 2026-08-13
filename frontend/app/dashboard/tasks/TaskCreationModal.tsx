'use client';
import React, { useState } from 'react';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Textarea } from '../../../components/ui/textarea';
import { Checkbox } from '../../../components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import { Loader2, ExternalLink, ShieldAlert } from 'lucide-react';
import { TaskPriority, TaskStatus } from '../../../shared/types';
import { API_BASE_URL, integrationApi } from '../../../shared/services/api-client';
import { identityApi } from '../../../shared/services/api';
export interface TaskCreationData {
    title: string;
    description: string;
    assigned_to: string;
    priority: TaskPriority;
    status: TaskStatus;
    due_date: string;
    automations: any[]; // list of { action: string, config: object }
}

import { useQuery } from '@tanstack/react-query';

export function TaskCreationModal({
    open,
    onClose,
    onCreate,
    isCreating,
    oauthStatus
}: {
    open: boolean;
    onClose: () => void;
    onCreate: (data: TaskCreationData) => void;
    isCreating: boolean;
    oauthStatus: any;
}) {
    const [activeTab, setActiveTab] = useState('details');

    // Task Details State
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [assignedTo, setAssignedTo] = useState('');
    const [priority, setPriority] = useState<TaskPriority>('Medium');
    const [status, setStatus] = useState<TaskStatus>('Pending');
    const [dueDate, setDueDate] = useState('');

    // Automation States
    const [github, setGithub] = useState({ enabled: false, owner: '', repo: '', title: '', body: '' });
    const [slack, setSlack] = useState({ enabled: false, workspace: '', channel: '', message: '' });
    const [gmail, setGmail] = useState({ enabled: false, google_email: '', to: '', subject: '', body: '' });
    const [calendar, setCalendar] = useState({ enabled: false, summary: '', description: '', start_datetime: '', end_datetime: '', timezone: 'Asia/Kolkata' });
    const [sheets, setSheets] = useState({ enabled: false, spreadsheet_id: '', range_name: '' });
    const [notion, setNotion] = useState({ enabled: false, parent_id: '', icon: '', cover_url: '' });
    const [manualNotionParent, setManualNotionParent] = useState(false);

    const isGoogleConnected = oauthStatus?.google?.connected ?? false;
    const isGithubConnected = oauthStatus?.github?.connected ?? false;
    const isSlackConnected = oauthStatus?.slack?.connected ?? false;
    const isNotionConnected = oauthStatus?.notion?.connected ?? false;

    const { data: notionParents, isLoading: loadingParents } = useQuery({
        queryKey: ['notion-parents', open],
        queryFn: () => integrationApi.getNotionParents(),
        enabled: open && isNotionConnected,
        staleTime: 60000,
    });

    const { data: userProfile } = useQuery({
        queryKey: ['user-profile'],
        queryFn: () => identityApi.getMe(),
        enabled: open,
        staleTime: 60000,
    });

    React.useEffect(() => {
        if (open && userProfile) {
            const defaultSheetsId = userProfile.preferences?.default_google_sheets_id || userProfile.default_google_sheets_id;
            const defaultNotionId = userProfile.preferences?.default_notion_db_id || userProfile.default_notion_db_id;

            if (defaultSheetsId) {
                setSheets(prev => ({ ...prev, spreadsheet_id: prev.spreadsheet_id || defaultSheetsId }));
            }
            if (defaultNotionId) {
                setNotion(prev => ({ ...prev, parent_id: prev.parent_id || defaultNotionId }));
            }
        }
    }, [open, userProfile]);

    const handleSubmit = () => {
        if (!title.trim()) return;
        if (notion.enabled && !notion.parent_id) return;

        const automations = [];

        if (slack.enabled) {
            const config: any = { channel: slack.channel, message: slack.message || `New task: ${title}` };
            if (slack.workspace) config.slack_workspace = slack.workspace;
            automations.push({ action: 'slack.send_message', config });
        }
        if (gmail.enabled) {
            const config: any = { to: gmail.to, subject: gmail.subject || `Notification: ${title}`, body: gmail.body };
            if (gmail.google_email) config.google_email = gmail.google_email;
            automations.push({ action: 'gmail.send_email', config });
        }
        if (calendar.enabled) {
            automations.push({ action: 'google_calendar.create_event', config: { summary: calendar.summary || title, description: calendar.description, start_datetime: calendar.start_datetime, end_datetime: calendar.end_datetime, timezone: calendar.timezone } });
        }
        if (sheets.enabled) {
            automations.push({ action: 'google_sheets.append_row', config: { spreadsheet_id: sheets.spreadsheet_id, range_name: sheets.range_name, values: [title, description, assignedTo, priority, status, dueDate || new Date().toISOString()] } });
        }
        if (notion.enabled) {
            const config: any = { title: title, content: description };
            if (notion.parent_id) config.parent_id = notion.parent_id;
            if (notion.icon) config.icon = notion.icon;
            if (notion.cover_url) config.cover_url = notion.cover_url;
            automations.push({ action: 'notion.create_page', config });
        }

        onCreate({
            title,
            description,
            assigned_to: assignedTo,
            priority,
            status,
            due_date: dueDate,
            automations
        });
    };

    const reset = () => {
        setTitle(''); setDescription(''); setAssignedTo(''); setPriority('Medium'); setStatus('Pending'); setDueDate('');

        setSlack({ enabled: false, workspace: '', channel: '', message: '' });
        setGmail({ enabled: false, google_email: '', to: '', subject: '', body: '' });
        setCalendar({ enabled: false, summary: '', description: '', start_datetime: '', end_datetime: '', timezone: 'Asia/Kolkata' });
        setSheets({ enabled: false, spreadsheet_id: '', range_name: '' });
        setNotion({ enabled: false, parent_id: '', icon: '', cover_url: '' });
        setActiveTab('details');
    };

    return (
        <Dialog open={open} onOpenChange={(v) => { if (!v) { reset(); onClose(); } }}>
            <DialogContent className="sm:max-w-[700px] h-[85vh] flex flex-col p-0">
                <DialogHeader className="px-6 py-4 border-b border-border">
                    <DialogTitle>Create Task with Automations</DialogTitle>
                </DialogHeader>

                <div className="flex-1 overflow-y-auto w-full p-4">
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full h-full flex flex-col">
                        <TabsList className="grid w-full grid-cols-2 mb-4 shrink-0">
                            <TabsTrigger value="details">Task Details</TabsTrigger>
                            <TabsTrigger value="automations">Automation Integrations</TabsTrigger>
                        </TabsList>

                        <TabsContent value="details" className="flex-1 space-y-4 outline-none">
                            <div className="space-y-4 max-w-xl">
                                <div>
                                    <label className="text-xs font-semibold block mb-1">Title *</label>
                                    <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="E.g. Launch new website" />
                                </div>
                                <div>
                                    <label className="text-xs font-semibold block mb-1">Description</label>
                                    <Textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Task details here..." rows={3} />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-xs font-semibold block mb-1">Assigned To</label>
                                        <Input value={assignedTo} onChange={e => setAssignedTo(e.target.value)} placeholder="User name or email" />
                                    </div>
                                    <div>
                                        <label className="text-xs font-semibold block mb-1">Due Date</label>
                                        <Input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-xs font-semibold block mb-1">Priority</label>
                                        <Select value={priority} onValueChange={v => setPriority(v as TaskPriority)}>
                                            <SelectTrigger><SelectValue /></SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="High">High</SelectItem>
                                                <SelectItem value="Medium">Medium</SelectItem>
                                                <SelectItem value="Low">Low</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div>
                                        <label className="text-xs font-semibold block mb-1">Status</label>
                                        <Select value={status} onValueChange={v => setStatus(v as TaskStatus)}>
                                            <SelectTrigger><SelectValue /></SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="Pending">Pending</SelectItem>
                                                <SelectItem value="In Progress">In Progress</SelectItem>
                                                <SelectItem value="Completed">Completed</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>
                            </div>
                        </TabsContent>

                        <TabsContent value="automations" className="flex-1 space-y-6 outline-none pb-8">
                            {!isGoogleConnected && (
                                <div className="bg-amber-500/10 border border-amber-500/30 p-4 rounded-lg flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <ShieldAlert className="h-5 w-5 text-amber-500" />
                                        <p className="text-sm font-medium text-amber-500">Connect Google to use Gmail, Calendar, and Sheets.</p>
                                    </div>
                                    <Button size="sm" onClick={() => integrationApi.connectGoogle()} className="bg-amber-500 hover:bg-amber-600 text-white">Connect</Button>
                                </div>
                            )}



                            {/* Slack */}
                            <div className="border border-border rounded-lg p-4 bg-card shadow-sm space-y-4">
                                <div className="flex items-center gap-3">
                                    <Checkbox checked={slack.enabled} onCheckedChange={(v: boolean) => setSlack({ ...slack, enabled: v })} id="sl-check" />
                                    <label htmlFor="sl-check" className="font-semibold text-sm cursor-pointer">Slack — Send Message</label>
                                    {!isSlackConnected && <span className="ml-auto text-xs text-rose-500">Not Connected</span>}
                                </div>
                                {slack.enabled && (
                                    <div className="grid grid-cols-2 gap-4 mt-2">
                                        <div>
                                            <label className="text-xs text-muted-foreground block mb-1">Target Workspace (Optional)</label>
                                            <Input className="h-8 text-xs" value={slack.workspace} onChange={e => setSlack({ ...slack, workspace: e.target.value })} placeholder="Leave empty for default" />
                                        </div>
                                        <div>
                                            <label className="text-xs text-muted-foreground block mb-1">Channel (ID or Name) *</label>
                                            <Input className="h-8 text-xs" value={slack.channel} onChange={e => setSlack({ ...slack, channel: e.target.value })} placeholder="e.g. general" />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="text-xs text-muted-foreground block mb-1">Message Body *</label>
                                            <Textarea className="min-h-[60px] text-xs" value={slack.message} onChange={e => setSlack({ ...slack, message: e.target.value })} />
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Gmail */}
                            <div className={`border rounded-lg p-4 bg-card shadow-sm space-y-4 ${!isGoogleConnected ? 'opacity-60 grayscale cursor-not-allowed pointer-events-none' : 'border-border'}`}>
                                <div className="flex items-center gap-3">
                                    <Checkbox checked={gmail.enabled} onCheckedChange={(v: boolean) => setGmail({ ...gmail, enabled: v })} disabled={!isGoogleConnected} id="gm-check" />
                                    <label htmlFor="gm-check" className="font-semibold text-sm cursor-pointer">Gmail — Send Email</label>
                                </div>
                                {gmail.enabled && (
                                    <div className="grid grid-cols-2 gap-4 mt-2">
                                        <div>
                                            <label className="text-xs text-muted-foreground block mb-1">Sender Account (Optional)</label>
                                            <Input className="h-8 text-xs" value={gmail.google_email} onChange={e => setGmail({ ...gmail, google_email: e.target.value })} placeholder="Requires authorization" />
                                        </div>
                                        <div>
                                            <label className="text-xs text-muted-foreground block mb-1">Recipient *</label>
                                            <Input className="h-8 text-xs" value={gmail.to} onChange={e => setGmail({ ...gmail, to: e.target.value })} placeholder="someone@example.com" />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="text-xs text-muted-foreground block mb-1">Subject *</label>
                                            <Input className="h-8 text-xs" value={gmail.subject} onChange={e => setGmail({ ...gmail, subject: e.target.value })} />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="text-xs text-muted-foreground block mb-1">Body</label>
                                            <Textarea className="min-h-[60px] text-xs" value={gmail.body} onChange={e => setGmail({ ...gmail, body: e.target.value })} />
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Google Calendar */}
                            <div className={`border rounded-lg p-4 bg-card shadow-sm space-y-4 ${!isGoogleConnected ? 'opacity-60 grayscale cursor-not-allowed pointer-events-none' : 'border-border'}`}>
                                <div className="flex items-center gap-3">
                                    <Checkbox checked={calendar.enabled} onCheckedChange={(v: boolean) => setCalendar({ ...calendar, enabled: v })} disabled={!isGoogleConnected} id="gc-check" />
                                    <label htmlFor="gc-check" className="font-semibold text-sm cursor-pointer">Google Calendar — Create Event</label>
                                </div>
                                {calendar.enabled && (
                                    <div className="grid grid-cols-2 gap-4 mt-2">
                                        <div className="col-span-2">
                                            <label className="text-xs text-muted-foreground block mb-1">Event Title</label>
                                            <Input className="h-8 text-xs" value={calendar.summary} onChange={e => setCalendar({ ...calendar, summary: e.target.value })} placeholder="Leave empty for Task title" />
                                        </div>
                                        <div>
                                            <label className="text-xs text-muted-foreground block mb-1">Start Datetime</label>
                                            <Input className="h-8 text-xs" type="datetime-local" value={calendar.start_datetime} onChange={e => setCalendar({ ...calendar, start_datetime: e.target.value })} />
                                        </div>
                                        <div>
                                            <label className="text-xs text-muted-foreground block mb-1">End Datetime</label>
                                            <Input className="h-8 text-xs" type="datetime-local" value={calendar.end_datetime} onChange={e => setCalendar({ ...calendar, end_datetime: e.target.value })} />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="text-xs text-muted-foreground block mb-1">Description</label>
                                            <Textarea className="min-h-[60px] text-xs" value={calendar.description} onChange={e => setCalendar({ ...calendar, description: e.target.value })} />
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Google Sheets */}
                            <div className={`border rounded-lg p-4 bg-card shadow-sm space-y-4 ${!isGoogleConnected ? 'opacity-60 grayscale cursor-not-allowed pointer-events-none' : 'border-border'}`}>
                                <div className="flex items-center gap-3">
                                    <Checkbox checked={sheets.enabled} onCheckedChange={(v: boolean) => setSheets({ ...sheets, enabled: v })} disabled={!isGoogleConnected} id="gs-check" />
                                    <label htmlFor="gs-check" className="font-semibold text-sm cursor-pointer">Google Sheets — Add Row</label>
                                </div>
                                {sheets.enabled && (
                                    <div className="grid grid-cols-2 gap-4 mt-2">
                                        <div>
                                            <label className="text-xs text-muted-foreground block mb-1">Spreadsheet ID</label>
                                            <Input className="h-8 text-xs" value={sheets.spreadsheet_id} onChange={e => setSheets({ ...sheets, spreadsheet_id: e.target.value })} placeholder="e.g. 1BxiMvs0XRYFg..." />
                                        </div>
                                        <div>
                                            <label className="text-xs text-muted-foreground block mb-1">Sheet/Range</label>
                                            <Input className="h-8 text-xs" value={sheets.range_name} onChange={e => setSheets({ ...sheets, range_name: e.target.value })} placeholder="e.g. Sheet1!A:F" />
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Notion */}
                            <div className={`border rounded-lg p-4 bg-card shadow-sm space-y-4 ${!isNotionConnected ? 'opacity-60 grayscale cursor-not-allowed pointer-events-none' : 'border-border'}`}>
                                <div className="flex items-center gap-3">
                                    <Checkbox checked={notion.enabled} onCheckedChange={(v: boolean) => setNotion({ ...notion, enabled: v })} disabled={!isNotionConnected} id="nt-check" />
                                    <label htmlFor="nt-check" className="font-semibold text-sm cursor-pointer">Notion — Create Page</label>
                                    {!isNotionConnected && <span className="ml-auto text-xs text-rose-500">Not Connected</span>}
                                </div>
                                {notion.enabled && (
                                    <div className="grid grid-cols-2 gap-4 mt-2">
                                        <div>
                                            <div className="flex items-center gap-4 mb-2 mt-1">
                                                <label className="flex items-center gap-1.5 text-[10px] text-muted-foreground uppercase cursor-pointer tracking-wider font-semibold">
                                                    <input type="radio" checked={!manualNotionParent} onChange={() => setManualNotionParent(false)} /> Cached List
                                                </label>
                                                <label className="flex items-center gap-1.5 text-[10px] text-muted-foreground uppercase cursor-pointer tracking-wider font-semibold">
                                                    <input type="radio" checked={manualNotionParent} onChange={() => setManualNotionParent(true)} /> Manual ID
                                                </label>
                                            </div>
                                            {!manualNotionParent ? (
                                                <select
                                                    className="w-full text-xs h-8 p-1 rounded-md border border-border bg-background focus:outline-none focus:ring-1 focus:ring-primary"
                                                    value={notion.parent_id}
                                                    onChange={(e) => setNotion({ ...notion, parent_id: e.target.value })}
                                                    disabled={loadingParents}
                                                >
                                                    <option value="" disabled>{loadingParents ? "Loading..." : "Select a parent (required)"}</option>
                                                    {(Array.isArray(notionParents) ? notionParents : [])?.map((p: any) => (
                                                        <option key={p.id} value={p.id}>
                                                            {p.type === 'page' ? '📄' : '🗄 '} {p.title}
                                                        </option>
                                                    ))}
                                                </select>
                                            ) : (
                                                <Input
                                                    className="h-8 text-xs"
                                                    placeholder="Enter exact Page ID or Database ID"
                                                    value={notion.parent_id}
                                                    onChange={(e) => setNotion({ ...notion, parent_id: e.target.value })}
                                                />
                                            )}
                                        </div>
                                        <div>
                                            <label className="text-xs text-muted-foreground block mb-1">Page Icon (Emoji)</label>
                                            <Input className="h-8 text-xs" value={notion.icon} onChange={e => setNotion({ ...notion, icon: e.target.value })} placeholder="e.g. 🚀" />
                                        </div>
                                    </div>
                                )}
                            </div>

                        </TabsContent>
                    </Tabs>
                </div>

                <DialogFooter className="px-6 py-4 border-t border-border mt-auto w-full">
                    {activeTab === 'details' ? (
                        <Button onClick={() => setActiveTab('automations')} disabled={!title.trim()}>Next: Configure Automations</Button>
                    ) : (
                        <div className="flex gap-2 w-full justify-between">
                            <Button variant="outline" onClick={() => setActiveTab('details')}>Back</Button>
                            <Button onClick={handleSubmit} disabled={isCreating || !title.trim() || (notion.enabled && !notion.parent_id)}>
                                {isCreating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />} Create Task
                            </Button>
                        </div>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
