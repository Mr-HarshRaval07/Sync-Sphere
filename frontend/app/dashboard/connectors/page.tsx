'use client';
import { useSearchParams, useRouter } from 'next/navigation';
import React, { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';

import { API_BASE_URL, integrationApi, apiClient } from '../../../shared/services/api-client';
import { Button } from '../../../components/ui/button';
import { MessageSquare, ShieldCheck, Mail, CalendarDays, Table2, CheckCircle2, RefreshCw, GitPullRequest, LayoutList, FileEdit, Users, Phone, Send, Settings, HardDrive, Cpu, Webhook, Box, Cloud, Network } from 'lucide-react';
import { toast } from 'sonner';

export default function ConnectorsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();

  // OAuth status from backend redirect
  const slackStatus = searchParams?.get('slack');
  const googleStatus = searchParams?.get('google');
  const githubStatus = searchParams?.get('github');
  const jiraStatus = searchParams?.get('jira');
  const notionStatus = searchParams?.get('notion');

  useEffect(() => {
    if (slackStatus === 'connected') {
      toast.success('Slack Connected', {
        description: 'Your Slack workspace has been successfully connected to SyncSphere.',
      });
    }
    if (slackStatus === 'denied') {
      toast.error('Slack Authorization Denied', {
        description: 'Slack access was denied. Please try connecting again.',
      });
    }
    if (googleStatus === 'connected') {
      toast.success('Google Connected', {
        description: 'Gmail, Google Calendar, and Google Sheets are now available to SyncSphere.',
      });
    }
    if (googleStatus === 'denied') {
      toast.error('Google Authorization Denied', {
        description: 'Google access was denied. Please try connecting again.',
      });
    }
    if (githubStatus === 'connected') {
      toast.success('GitHub Connected', {
        description: 'Your GitHub account has been successfully connected to SyncSphere.',
      });
    }
    if (githubStatus === 'denied') {
      toast.error('GitHub Authorization Denied', {
        description: 'GitHub access was denied. Please try connecting again.',
      });
    }
    if (jiraStatus === 'connected') {
      toast.success('Jira Connected', {
        description: 'Your Atlassian Jira account has been successfully connected to SyncSphere.',
      });
    }
    if (jiraStatus === 'denied') {
      toast.error('Jira Authorization Denied', {
        description: 'Jira access was denied. Please try connecting again.',
      });
    }
    if (notionStatus === 'connected') {
      toast.success('Notion Connected', {
        description: 'Your Notion workspace has been successfully connected to SyncSphere.',
      });
    }
    if (notionStatus === 'denied') {
      toast.error('Notion Authorization Denied', {
        description: 'Notion access was denied. Please try connecting again.',
      });
    }

    if (slackStatus || googleStatus || githubStatus || jiraStatus || notionStatus) {
      queryClient.invalidateQueries({ queryKey: ['connector-status'] });
      router.replace('/dashboard/connectors', { scroll: false });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slackStatus, googleStatus, githubStatus, jiraStatus, notionStatus]);

  // Query real OAuth connection status from DB
  const { data: oauthStatus, isFetching, refetch } = useQuery({
    queryKey: ['connector-status'],
    queryFn: async () => {
      const res = await apiClient.get('/v1/connect/status');
      if (res.status !== 200) return { google: { connected: false }, slack: { connected: false }, github: { connected: false } };
      return res.data;
    },
    refetchOnWindowFocus: true,
  });

  const handleRefresh = async () => {
    try {
      await refetch();
      toast.success('Status Refreshed', { description: 'Connection statuses are up to date.' });
    } catch (error) {
      toast.error('Refresh Failed', { description: 'Could not fetch connection statuses.' });
    }
  };

  const isGoogleConnected = oauthStatus?.google?.connected ?? false;
  const isSlackConnected = oauthStatus?.slack?.connected ?? false;
  const isGithubConnected = oauthStatus?.github?.connected ?? false;
  const isJiraConnected = oauthStatus?.jira?.connected ?? false;
  const isNotionConnected = oauthStatus?.notion?.connected ?? false;

  const handleSlackConnect = () => {
    integrationApi.connectSlack();
  };

  const handleGoogleConnect = () => {
    integrationApi.connectGoogle();
  };

  const handleGithubConnect = () => {
    integrationApi.connectGithub();
  };

  const handleJiraConnect = () => {
    integrationApi.connectJira();
  };

  const handleNotionConnect = () => {
    integrationApi.connectNotion();
  };

  const handleSlackDisconnect = async () => {
    try {
      await apiClient.post('/v1/connect/slack/disconnect');
      toast.success('Slack Disconnected');
      refetch();
    } catch (e) {
      toast.error('Failed to disconnect Slack');
    }
  };

  const handleGoogleDisconnect = async () => {
    try {
      await apiClient.post('/v1/connect/google/disconnect');
      toast.success('Google Disconnected');
      refetch();
    } catch (e) {
      toast.error('Failed to disconnect Google');
    }
  };

  const handleGithubDisconnect = async () => {
    try {
      await apiClient.post('/v1/connect/github/disconnect');
      toast.success('GitHub Disconnected');
      refetch();
    } catch (e) {
      toast.error('Failed to disconnect GitHub');
    }
  };

  const handleJiraDisconnect = async () => {
    try {
      await apiClient.post('/v1/connect/jira/disconnect');
      toast.success('Jira Disconnected');
      refetch();
    } catch (e) {
      toast.error('Failed to disconnect Jira');
    }
  };

  const handleNotionDisconnect = async () => {
    try {
      await apiClient.post('/v1/connect/notion/disconnect');
      toast.success('Notion Disconnected');
      refetch();
    } catch (e) {
      toast.error('Failed to disconnect Notion');
    }
  };


  const { data: notionParents, isFetching: loadingParents } = useQuery({
    queryKey: ['notion-parents'],
    queryFn: () => integrationApi.getNotionParents(),
    enabled: isNotionConnected,
    refetchOnWindowFocus: false,
  });

  const handleParentSelect = async (parentId: string, parentType: string) => {
    try {
      await integrationApi.saveNotionParent(parentId, parentType);
      toast.success('Default Parent Saved');
      refetch();
    } catch {
      toast.error('Failed to save default parent');
    }
  };

  const [isTestingNotion, setIsTestingNotion] = React.useState(false);
  const [isRefreshingNotion, setIsRefreshingNotion] = React.useState(false);

  const handleNotionRefresh = async () => {
    setIsRefreshingNotion(true);
    try {
      await integrationApi.refreshNotionParents();
      toast.success('Notion Pages Refreshed');
      queryClient.invalidateQueries({ queryKey: ['notion-parents'] });
    } catch (e: any) {
      toast.error('Failed to refresh Notion resources');
    } finally {
      setIsRefreshingNotion(false);
    }
  };

  const handleTestNotion = async () => {
    setIsTestingNotion(true);
    try {
      const res = await apiClient.post('/v1/connect/notion/test');
      if (res.data?.success) {
        toast.success('Connection Verified', {
          description: 'Page Created Successfully',
          action: { label: 'Open Page', onClick: () => window.open(res.data.page_url, '_blank') }
        });
      }
    } catch (e: any) {
      toast.error('Test Failed', { description: e.response?.data?.detail || 'Could not verify Notion connection.' });
    } finally {
      setIsTestingNotion(false);
    }
  };

  const comingSoonConnectors = [
    { title: "Microsoft Teams", category: "Communication", icon: Users },
    { title: "Salesforce", category: "CRM", icon: ShieldCheck },
    { title: "SAP", category: "ERP", icon: Settings },
  ];

  return (
    <div className="space-y-8 bg-background max-w-6xl mx-auto p-6 md:p-8">

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-foreground">
            Connectors
          </h2>
          <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
            Connect the tools you use to automate work with SyncSphere.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isFetching}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
          {isFetching ? 'Refreshing...' : 'Refresh Status'}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
        {/* Slack Card */}
        <div className="border border-border/80 bg-card rounded-2xl p-6 shadow-sm flex flex-col h-full hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-muted rounded-xl border border-border">
                <MessageSquare className="h-5 w-5 text-foreground" />
              </div>
              <div>
                <h3 className="text-lg font-bold">Slack</h3>
                <p className="text-xs text-muted-foreground">Team messaging and notifications</p>
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col gap-4 mt-2">
            <div className="flex items-center gap-2">
              {isSlackConnected ? (
                <>
                  <div className="h-2 w-2 rounded-full bg-emerald-500" />
                  <span className="text-sm font-semibold text-emerald-600">Connected</span>
                </>
              ) : (
                <>
                  <div className="h-2 w-2 rounded-full bg-muted-foreground" />
                  <span className="text-sm font-medium text-muted-foreground">Not Connected</span>
                </>
              )}
            </div>

            {isSlackConnected && oauthStatus?.slack?.workspace && (
              <div className="text-sm text-muted-foreground bg-muted/50 p-3 rounded-lg border border-border/50">
                Connected account: <span className="font-semibold text-foreground">{oauthStatus.slack.workspace}</span>
              </div>
            )}

            <div className="mt-auto pt-4 flex gap-3">
              {!isSlackConnected ? (
                <Button className="w-full bg-foreground text-background hover:bg-foreground/90 font-medium" onClick={handleSlackConnect}>
                  Connect Slack
                </Button>
              ) : (
                <>
                  <Button variant="outline" className="flex-1 font-semibold" onClick={handleSlackConnect}>
                    Reconnect
                  </Button>
                  <Button variant="ghost" className="flex-1 text-red-500 hover:text-red-600 hover:bg-red-50 font-semibold" onClick={handleSlackDisconnect}>
                    Disconnect
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Google Card */}
        <div className="border border-border/80 bg-card rounded-2xl p-6 shadow-sm flex flex-col h-full hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-muted rounded-xl border border-border">
                <ShieldCheck className="h-5 w-5 text-foreground" />
              </div>
              <div>
                <h3 className="text-lg font-bold">Google Account</h3>
                <p className="text-xs text-muted-foreground">Authenticate once for all Google tools</p>
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col gap-4 mt-2">
            <div className="flex items-center gap-2">
              {isGoogleConnected ? (
                <>
                  <div className="h-2 w-2 rounded-full bg-emerald-500" />
                  <span className="text-sm font-semibold text-emerald-600">Connected</span>
                </>
              ) : (
                <>
                  <div className="h-2 w-2 rounded-full bg-muted-foreground" />
                  <span className="text-sm font-medium text-muted-foreground">Not Connected</span>
                </>
              )}
            </div>

            {isGoogleConnected && oauthStatus?.google?.email && (
              <div className="text-sm text-muted-foreground bg-muted/50 p-3 rounded-lg border border-border/50">
                Connected account: <span className="font-semibold text-foreground">{oauthStatus.google.email}</span>
              </div>
            )}

            <div className="space-y-3 mt-2 bg-muted/30 p-4 rounded-xl border border-border/50">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Capabilities</span>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-2">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className={`h-4 w-4 ${isGoogleConnected ? 'text-emerald-500' : 'text-muted-foreground'}`} />
                  <div className="flex items-center gap-2 text-sm text-foreground">
                    <Mail className="h-4 w-4 text-foreground/70" /> Gmail
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className={`h-4 w-4 ${isGoogleConnected ? 'text-emerald-500' : 'text-muted-foreground'}`} />
                  <div className="flex items-center gap-2 text-sm text-foreground">
                    <CalendarDays className="h-4 w-4 text-foreground/70" /> Google Calendar
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className={`h-4 w-4 ${isGoogleConnected ? 'text-emerald-500' : 'text-muted-foreground'}`} />
                  <div className="flex items-center gap-2 text-sm text-foreground">
                    <Table2 className="h-4 w-4 text-foreground/70" /> Google Sheets
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-auto pt-4 flex gap-3">
              {!isGoogleConnected ? (
                <Button className="w-full bg-foreground text-background hover:bg-foreground/90 font-medium" onClick={handleGoogleConnect}>
                  Connect Google
                </Button>
              ) : (
                <>
                  <Button variant="outline" className="flex-1 font-semibold" onClick={handleGoogleConnect}>
                    Reconnect
                  </Button>
                  <Button variant="ghost" className="flex-1 text-red-500 hover:text-red-600 hover:bg-red-50 font-semibold" onClick={handleGoogleDisconnect}>
                    Disconnect
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* GitHub Card */}
        <div className="border border-border/80 bg-card rounded-2xl p-6 shadow-sm flex flex-col h-full hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-muted rounded-xl border border-border">
                <GitPullRequest className="h-5 w-5 text-foreground" />
              </div>
              <div>
                <h3 className="text-lg font-bold">GitHub</h3>
                <p className="text-xs text-muted-foreground">Connect your GitHub account to create and manage issues.</p>
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col gap-4 mt-2">
            <div className="flex items-center gap-2">
              {isGithubConnected ? (
                <>
                  <div className="h-2 w-2 rounded-full bg-emerald-500" />
                  <span className="text-sm font-semibold text-emerald-600">Connected</span>
                </>
              ) : (
                <>
                  <div className="h-2 w-2 rounded-full bg-muted-foreground" />
                  <span className="text-sm font-medium text-muted-foreground">Not connected</span>
                </>
              )}
            </div>

            {isGithubConnected && oauthStatus?.github?.username && (
              <div className="text-sm text-muted-foreground bg-muted/50 p-3 rounded-lg border border-border/50">
                Connected as <span className="font-semibold text-foreground">@{oauthStatus.github.username}</span>
              </div>
            )}

            <div className="mt-auto pt-4 flex gap-3">
              {!isGithubConnected ? (
                <Button className="w-full bg-foreground text-background hover:bg-foreground/90 font-medium" onClick={handleGithubConnect}>
                  Connect GitHub
                </Button>
              ) : (
                <>
                  <Button variant="ghost" className="flex-1 text-red-500 hover:text-red-600 hover:bg-red-50 font-semibold" onClick={handleGithubDisconnect}>
                    Disconnect
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Jira Card */}
        <div className="border border-border/80 bg-card rounded-2xl p-6 shadow-sm flex flex-col h-full hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-muted rounded-xl border border-border">
                <LayoutList className="h-5 w-5 text-foreground" />
              </div>
              <div>
                <h3 className="text-lg font-bold">Jira</h3>
                <p className="text-xs text-muted-foreground">Connect Atlassian Jira to track issues and manage Agile boards.</p>
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col gap-4 mt-2">
            <div className="flex items-center gap-2">
              {isJiraConnected ? (
                <>
                  <div className="h-2 w-2 rounded-full bg-emerald-500" />
                  <span className="text-sm font-semibold text-emerald-600">Connected</span>
                </>
              ) : (
                <>
                  <div className="h-2 w-2 rounded-full bg-muted-foreground" />
                  <span className="text-sm font-medium text-muted-foreground">Not connected</span>
                </>
              )}
            </div>

            {isJiraConnected && oauthStatus?.jira?.site_name && (
              <div className="text-sm text-muted-foreground bg-muted/50 p-3 rounded-lg border border-border/50 break-all">
                Connected to site <span className="font-semibold text-foreground">{(oauthStatus.jira.site_name)}</span>
              </div>
            )}

            <div className="mt-auto pt-4 flex gap-3">
              {!isJiraConnected ? (
                <Button className="w-full bg-foreground text-background hover:bg-foreground/90 font-medium" onClick={handleJiraConnect}>
                  Connect Jira
                </Button>
              ) : (
                <>
                  <Button variant="outline" className="flex-1 font-semibold" onClick={handleJiraConnect}>
                    Reconnect
                  </Button>
                  <Button variant="ghost" className="flex-1 text-red-500 hover:text-red-600 hover:bg-red-50 font-semibold" onClick={handleJiraDisconnect}>
                    Disconnect
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Notion Card */}
        <div className="border border-border/80 bg-card rounded-2xl p-6 shadow-sm flex flex-col h-full hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-muted rounded-xl border border-border">
                <FileEdit className="h-5 w-5 text-foreground" />
              </div>
              <div>
                <h3 className="text-lg font-bold">Notion</h3>
                <p className="text-xs text-muted-foreground">Connect your Notion workspace for pages and databases.</p>
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col gap-4 mt-2">
            <div className="flex items-center gap-2">
              {isNotionConnected ? (
                <>
                  <div className="h-2 w-2 rounded-full bg-emerald-500" />
                  <span className="text-sm font-semibold text-emerald-600">Connected</span>
                </>
              ) : (
                <>
                  <div className="h-2 w-2 rounded-full bg-muted-foreground" />
                  <span className="text-sm font-medium text-muted-foreground">Not connected</span>
                </>
              )}
            </div>

            {isNotionConnected && (
              <>
                {oauthStatus?.notion?.workspace_name && (
                  <div className="text-sm text-muted-foreground bg-muted/50 p-3 rounded-lg border border-border/50 break-all flex items-center gap-2 mt-2">
                    {oauthStatus?.notion?.workspace_icon && <span className="text-lg leading-none">{oauthStatus.notion.workspace_icon}</span>}
                    <div>Connected to <span className="font-semibold text-foreground">{oauthStatus.notion.workspace_name}</span></div>
                  </div>
                )}
                <div className="flex flex-col gap-1 mt-2">
                  <label className="text-xs font-semibold text-foreground">Default Parent <span className="text-red-500">*</span></label>
                  <select
                    className="w-full text-sm p-2 rounded-md border border-border bg-background focus:outline-none focus:ring-2 focus:ring-foreground/20"
                    value={oauthStatus?.notion?.default_parent_id || ""}
                    onChange={(e) => {
                      const selected = (Array.isArray(notionParents) ? notionParents : [])?.find((p: any) => p.id === e.target.value);
                      if (selected) {
                        handleParentSelect(selected.id, selected.type);
                      }
                    }}
                    disabled={loadingParents}
                  >
                    <option value="" disabled>{loadingParents ? "Loading..." : "Select a default page/database"}</option>
                    {(Array.isArray(notionParents) ? notionParents : [])?.map((p: any) => (
                      <option key={p.id} value={p.id}>
                        {p.type === 'page' ? '📄' : '🗄 '} {p.title}
                      </option>
                    ))}
                  </select>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    Required. SyncSphere AI creates notes inside this parent by default.
                  </p>
                </div>
              </>
            )}

            <div className="mt-auto pt-4 flex gap-3">
              {!isNotionConnected ? (
                <Button className="w-full bg-foreground text-background hover:bg-foreground/90 font-medium" onClick={handleNotionConnect}>
                  Connect Notion
                </Button>
              ) : (
                <>
                  <Button variant="outline" className="flex-1 font-semibold" onClick={handleTestNotion} disabled={isTestingNotion}>
                    {isTestingNotion ? 'Testing...' : 'Test Notion'}
                  </Button>
                  <Button variant="outline" className="font-semibold" onClick={handleNotionRefresh} disabled={isRefreshingNotion} title="Refresh Pages">
                    <RefreshCw className={`h-4 w-4 ${isRefreshingNotion ? 'animate-spin' : ''}`} />
                  </Button>
                  <Button variant="ghost" className="text-red-500 hover:text-red-600 hover:bg-red-50 font-semibold" onClick={handleNotionDisconnect} title="Disconnect">
                    Disconnect
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Coming Soon Cards */}
        {comingSoonConnectors.map((c, i) => (
          <div key={c.title} className="border border-border/40 bg-card/60 rounded-2xl p-6 shadow-sm flex flex-col h-full opacity-70 hover:opacity-100 transition-opacity">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-muted rounded-xl border border-border">
                  <c.icon className="h-5 w-5 text-foreground" />
                </div>
                <div>
                  <h3 className="text-lg font-bold">{c.title}</h3>
                  <p className="text-xs text-muted-foreground">{c.category}</p>
                </div>
              </div>
            </div>
            <div className="flex-1 flex flex-col gap-4 mt-2 justify-center items-center h-full pt-6 border-t border-border/10">
              <div className="py-1.5 px-3 bg-muted/80 rounded-full border border-border/50 flex items-center gap-2 shadow-inner">
                <div className="h-1.5 w-1.5 rounded-full bg-cyan-500/80 animate-pulse" />
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Coming Soon</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}