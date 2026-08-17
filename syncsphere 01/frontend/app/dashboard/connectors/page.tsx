'use client';
import { FaGithub } from 'react-icons/fa';
import { useSearchParams, useRouter } from 'next/navigation';
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { connectorApi } from '../../../shared/services/api';
import { API_BASE_URL, integrationApi } from '../../../shared/services/api-client';

import {
  DataGrid,
  EmptyState,
  SkeletonLoader,
} from '../../../shared/components/DesignSystem';

import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Badge } from '../../../components/ui/badge';

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../../../components/ui/dialog';

import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '../../../components/ui/card';

import { Label } from '../../../components/ui/label';

import {
  Radio,
  Plus,
  Trash2,
  Terminal,
  Layers,
  CheckCircle2,
  XCircle,
  Mail,
  CalendarDays,
  Table2,
  MessageSquare,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react';

import { toast } from 'sonner';

import { Connector } from '../../../shared/types';

export default function ConnectorsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();

  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [selectedConnector, setSelectedConnector] =
    useState<Connector | null>(null);

  const [isGoogleTesting, setIsGoogleTesting] = useState(false);
  const [googleTestResult, setGoogleTestResult] = useState<any>(null);

  // ---------------------------------------------------------
  // OAuth status from backend redirect
  // ---------------------------------------------------------

  const githubStatus = searchParams?.get('github');
  const slackStatus = searchParams?.get('slack');
  const googleStatus = searchParams?.get('google');

  // ---------------------------------------------------------
  // OAuth result handling
  // ---------------------------------------------------------

  useEffect(() => {
    if (githubStatus === 'connected') {
      toast.success('GitHub Connected', {
        description:
          'Your GitHub account has been successfully connected to SyncSphere.',
      });
    }

    if (githubStatus === 'denied') {
      toast.error('GitHub Authorization Denied', {
        description:
          'GitHub access was denied. Please try connecting again.',
      });
    }

    if (slackStatus === 'connected') {
      toast.success('Slack Connected', {
        description:
          'Your Slack workspace has been successfully connected to SyncSphere.',
      });
    }

    if (slackStatus === 'denied') {
      toast.error('Slack Authorization Denied', {
        description:
          'Slack access was denied. Please try connecting again.',
      });
    }

    if (googleStatus === 'connected') {
      toast.success('Google Connected', {
        description:
          'Gmail, Google Calendar, and Google Sheets are now available to SyncSphere.',
      });
    }

    if (googleStatus === 'denied') {
      toast.error('Google Authorization Denied', {
        description:
          'Google access was denied. Please try connecting again.',
      });
    }

    // Remove OAuth query parameters after displaying notification.
    if (githubStatus || slackStatus || googleStatus) {
      // FORCE React Query Cache Invalidation
      queryClient.invalidateQueries({
        queryKey: ['connector-status'],
      });

      router.replace('/dashboard/connectors', {
        scroll: false,
      });
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---------------------------------------------------------
  // Form states
  // ---------------------------------------------------------

  const [name, setName] = useState('');
  const [type, setType] = useState('slack');
  const [configJson, setConfigJson] = useState('{}');

  // ---------------------------------------------------------
  // Query connectors
  // ---------------------------------------------------------

  const {
    data: connectors = [],
    isLoading,
  } = useQuery({
    queryKey: ['connectors-list'],
    queryFn: () => connectorApi.listConnectors(),
  });

  // ---------------------------------------------------------
  // Query real OAuth connection status from DB
  // ---------------------------------------------------------

  const { data: oauthStatus, refetch: refetchStatus } = useQuery({
    queryKey: ['connector-status'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/v1/connect/status`, {
        credentials: 'include',
      });
      if (!res.ok) return { google: { connected: false }, github: { connected: false }, slack: { connected: false } };
      return res.json();
    },
    staleTime: 30_000,
    refetchOnWindowFocus: true,
  });

  const isGoogleConnected = oauthStatus?.google?.connected ?? false;
  const isGitHubConnected = oauthStatus?.github?.connected ?? false;
  const isSlackConnected = oauthStatus?.slack?.connected ?? false;

  // ---------------------------------------------------------
  // Register connector mutation
  // ---------------------------------------------------------

  const registerMutation = useMutation({
    mutationFn: (payload: any) =>
      connectorApi.registerConnector(payload),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['connectors-list'],
      });

      setIsRegisterOpen(false);
      setName('');
      setConfigJson('{}');

      toast.success('Connector Registered', {
        description:
          'Capability schema handshake complete!',
      });
    },

    onError: (err: any) => {
      toast.error('Registration Failed', {
        description:
          err.response?.data?.error?.message ||
          'Handshake failed.',
      });
    },
  });

  // ---------------------------------------------------------
  // Delete connector mutation
  // ---------------------------------------------------------

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      connectorApi.deleteConnector(id),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['connectors-list'],
      });

      setSelectedConnector(null);

      toast.success('Connector Removed', {
        description:
          'Connector node was successfully deleted.',
      });
    },
  });

  // ---------------------------------------------------------
  // Register connector
  // ---------------------------------------------------------

  const handleRegister = (
    e: React.FormEvent
  ) => {
    e.preventDefault();

    try {
      const parsedConfig =
        JSON.parse(configJson);

      registerMutation.mutate({
        name: name.toLowerCase().trim(),
        connector_type: type,
        config: parsedConfig,
      });
    } catch {
      toast.error('Invalid Config', {
        description:
          'Please enter valid JSON config data.',
      });
    }
  };

  // ---------------------------------------------------------
  // Google OAuth
  // ---------------------------------------------------------

  const handleGoogleConnect = () => {
    integrationApi.connectGoogle();
  };

  // ---------------------------------------------------------
  // Google Test Connection
  // ---------------------------------------------------------

  const handleGoogleTest = async () => {
    setIsGoogleTesting(true);
    setGoogleTestResult(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/v1/connect/google/test`,
        {
          method: 'GET',
          credentials: 'include',
          headers: {
            Accept: 'application/json',
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
          data?.message ||
          'Google connection test failed.'
        );
      }

      setGoogleTestResult(data);

      toast.success(
        'Google Connection Successful',
        {
          description:
            'SyncSphere can successfully communicate with Google services.',
        }
      );
    } catch (error: any) {
      setGoogleTestResult({
        success: false,
        error:
          error?.message ||
          'Google connection test failed.',
      });

      toast.error(
        'Google Connection Failed',
        {
          description:
            error?.message ||
            'SyncSphere could not connect to Google.',
        }
      );
    } finally {
      setIsGoogleTesting(false);
    }
  };

  // ---------------------------------------------------------
  // Helper: check if a connector exists
  // ---------------------------------------------------------

  const hasConnector = (
    name: string
  ) => {
    return connectors.some(
      (connector: Connector) =>
        connector.name?.toLowerCase() ===
        name.toLowerCase()
    );
  };

  // ---------------------------------------------------------
  // Existing MCP table columns
  // ---------------------------------------------------------

  const columns = [
    {
      key: 'name',
      header: 'Name',
      render: (row: Connector) => (
        <span className="font-semibold capitalize text-foreground">
          {row.name}
        </span>
      ),
    },

    {
      key: 'connector_type',
      header: 'Type',
      render: (row: Connector) => (
        <Badge
          variant="outline"
          className="capitalize border-border"
        >
          {row.connector_type}
        </Badge>
      ),
    },

    {
      key: 'status',
      header: 'Status',
      render: (row: Connector) => {
        const isEnabled =
          row.status === 'enabled';

        return (
          <Badge
            className={`text-xs px-2 py-0.5 border ${isEnabled
              ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
              : 'bg-rose-500/10 text-rose-500 border-rose-500/20'
              }`}
          >
            {row.status}
          </Badge>
        );
      },
    },

    {
      key: 'created_at',
      header: 'Registered On',
      render: (row: Connector) =>
        new Date(
          row.created_at
        ).toLocaleDateString(),
    },

    {
      key: 'actions',
      header: 'Actions',
      render: (row: Connector) => (
        <div className="flex gap-2">
          <Button
            size="xs"
            variant="outline"
            className="border-border hover:bg-muted text-foreground"
            onClick={(e) => {
              e.stopPropagation();
              setSelectedConnector(row);
            }}
          >
            Configure
          </Button>

          <Button
            size="xs"
            variant="ghost"
            className="text-rose-500 hover:bg-rose-500/5 hover:text-rose-600"
            onClick={(e) => {
              e.stopPropagation();
              deleteMutation.mutate(row.id);
            }}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      ),
    },
  ];

  // ---------------------------------------------------------
  // Render
  // ---------------------------------------------------------

  return (
    <div className="space-y-6">

      {/* =====================================================
          HEADER
      ====================================================== */}

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight">
            Connectors
          </h2>

          <p className="text-xs text-muted-foreground mt-0.5">
            Connect SyncSphere with the services you use
            to automate your workflows.
          </p>
        </div>

        <div className="flex gap-2">

          <Button
            onClick={() =>
              setIsRegisterOpen(true)
            }
            className="bg-primary hover:bg-primary/95"
          >
            <Plus className="h-4 w-4 mr-1" />
            Register Node
          </Button>

        </div>
      </div>


      {/* =====================================================
          REAL WORLD OAUTH CONNECTIONS
      ====================================================== */}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* ---------------------------------------------------
            GITHUB
        ---------------------------------------------------- */}

        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FaGithub className="h-5 w-5" />
                GitHub
              </div>

              <Badge
                className={
                  isGitHubConnected
                    ? 'bg-emerald-500/10 text-emerald-500'
                    : 'bg-muted text-muted-foreground'
                }
              >
                {isGitHubConnected
                  ? `Connected${oauthStatus?.github?.username ? ` · @${oauthStatus.github.username}` : ''}`
                  : 'Not Connected'}
              </Badge>
            </CardTitle>
          </CardHeader>

          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Connect GitHub to allow SyncSphere
              to work with repositories and issues.
            </p>

            <Button
              className="w-full"
              variant={
                isGitHubConnected
                  ? 'outline'
                  : 'default'
              }
              onClick={() => integrationApi.connectGithub()}
            >
              {isGitHubConnected
                ? 'Reconnect GitHub'
                : 'Connect GitHub'}
            </Button>
          </CardContent>
        </Card>


        {/* ---------------------------------------------------
            SLACK
        ---------------------------------------------------- */}

        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Slack
              </div>

              <Badge
                className={
                  isSlackConnected
                    ? 'bg-emerald-500/10 text-emerald-500'
                    : 'bg-muted text-muted-foreground'
                }
              >
                {isSlackConnected
                  ? `Connected${oauthStatus?.slack?.workspace ? ` · ${oauthStatus.slack.workspace}` : ''}`
                  : 'Not Connected'}
              </Badge>
            </CardTitle>
          </CardHeader>

          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Connect Slack so SyncSphere can
              automatically send workflow notifications.
            </p>

            <Button
              className="w-full"
              variant={
                isSlackConnected
                  ? 'outline'
                  : 'default'
              }
              onClick={() => integrationApi.connectSlack()}
            >
              {isSlackConnected
                ? 'Reconnect Slack'
                : 'Connect Slack'}
            </Button>
          </CardContent>
        </Card>


        {/* ---------------------------------------------------
            GOOGLE
        ---------------------------------------------------- */}

        <Card className="border-border bg-card">

          <CardHeader>

            <CardTitle className="flex items-center justify-between">

              <div className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5" />
                Google
              </div>

              <Badge
                className={
                  isGoogleConnected
                    ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                    : 'bg-muted text-muted-foreground'
                }
              >
                {isGoogleConnected
                  ? `Connected${oauthStatus?.google?.email ? ` · ${oauthStatus.google.email}` : ''}`
                  : 'Not Connected'}
              </Badge>

            </CardTitle>

          </CardHeader>


          <CardContent className="space-y-4">

            <p className="text-sm text-muted-foreground">
              Connect your Google account to use
              Gmail, Calendar, and Google Sheets
              inside SyncSphere workflows.
            </p>


            {/* Google Services */}

            <div className="space-y-2">

              <div className="flex items-center justify-between rounded-md border border-border p-2">

                <div className="flex items-center gap-2 text-sm">
                  <Mail className="h-4 w-4" />
                  Gmail
                </div>

                {isGoogleConnected ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-muted-foreground" />
                )}

              </div>


              <div className="flex items-center justify-between rounded-md border border-border p-2">

                <div className="flex items-center gap-2 text-sm">
                  <CalendarDays className="h-4 w-4" />
                  Google Calendar
                </div>

                {isGoogleConnected ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-muted-foreground" />
                )}

              </div>


              <div className="flex items-center justify-between rounded-md border border-border p-2">

                <div className="flex items-center gap-2 text-sm">
                  <Table2 className="h-4 w-4" />
                  Google Sheets
                </div>

                {isGoogleConnected ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-muted-foreground" />
                )}

              </div>

            </div>


            {/* Google Buttons */}

            <div className="flex gap-2">

              <Button
                className="flex-1"
                variant="outline"
                onClick={handleGoogleConnect}
              >
                Reconnect Google
              </Button>

              <Button
                className="flex-1"
                onClick={handleGoogleTest}
                disabled={isGoogleTesting}
              >

                {isGoogleTesting ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                    Testing...
                  </>
                ) : (
                  'Test Connection'
                )}

              </Button>

            </div>


            {/* Google Test Result */}

            {googleTestResult && (

              <div
                className={`rounded-md border p-3 text-xs ${googleTestResult.success
                  ? 'border-emerald-500/30 bg-emerald-500/5'
                  : 'border-rose-500/30 bg-rose-500/5'
                  }`}
              >

                <div className="flex items-center gap-2 font-semibold">

                  {googleTestResult.success ? (
                    <>
                      <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                      Google Connection Healthy
                    </>
                  ) : (
                    <>
                      <XCircle className="h-4 w-4 text-rose-500" />
                      Google Connection Failed
                    </>
                  )}

                </div>


                {googleTestResult.message && (
                  <p className="mt-1 text-muted-foreground">
                    {googleTestResult.message}
                  </p>
                )}

              </div>

            )}

          </CardContent>

        </Card>

      </div>


      {/* =====================================================
          MCP CONNECTORS
      ====================================================== */}

      <Card className="border-border bg-card">

        <CardHeader>

          <CardTitle>
            MCP Connectors
          </CardTitle>

          <p className="text-xs text-muted-foreground">
            Manage registered MCP clients and tool
            environments.
          </p>

        </CardHeader>

        <CardContent>

          {isLoading ? (
            <SkeletonLoader rows={4} />

          ) : connectors.length === 0 ? (

            <EmptyState
              title="No Connectors Active"
              description="Register local stdio or remote SSE connector endpoints to export integrations to planners."
              icon={
                <Radio className="h-10 w-10 text-muted-foreground" />
              }
              actionLabel="Register First Node"
              onAction={() =>
                setIsRegisterOpen(true)
              }
            />

          ) : (

            <DataGrid
              columns={columns}
              data={connectors}
              onRowClick={(row) =>
                setSelectedConnector(row)
              }
            />

          )}

        </CardContent>

      </Card>


      {/* =====================================================
          REGISTER CONNECTOR MODAL
      ====================================================== */}

      <Dialog
        open={isRegisterOpen}
        onOpenChange={setIsRegisterOpen}
      >

        <DialogContent className="max-w-md border-border bg-card shadow-2xl">

          <DialogHeader>

            <DialogTitle>
              Register MCP Connector
            </DialogTitle>

            <DialogDescription>
              Input configuration settings to perform
              capability handshake.
            </DialogDescription>

          </DialogHeader>


          <form
            onSubmit={handleRegister}
            className="space-y-4 py-2"
          >

            <div className="space-y-1.5">

              <Label className="text-xs">
                Connector Name
              </Label>

              <Input
                placeholder="slack-notifier"
                value={name}
                onChange={(e) =>
                  setName(e.target.value)
                }
                required
                className="bg-card border-border placeholder-muted-foreground"
              />

            </div>


            <div className="space-y-1.5">

              <Label className="text-xs">
                Transport Driver Type
              </Label>

              <select
                className="flex h-9 w-full rounded-md border border-border bg-card px-3 py-1 text-sm text-foreground focus-visible:outline-none"
                value={type}
                onChange={(e) =>
                  setType(e.target.value)
                }
              >

                <option value="slack">
                  Slack Messenger (Stdio)
                </option>

                <option value="github">
                  GitHub PR Actions (SSE)
                </option>

                <option value="jira">
                  Jira Tickets (SSE)
                </option>

                <option value="custom">
                  Custom Transport Protocol
                </option>

              </select>

            </div>


            <div className="space-y-1.5">

              <Label className="text-xs">
                Transport Config Options (JSON)
              </Label>

              <textarea
                className="flex min-h-[80px] w-full rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus-visible:outline-none font-mono"
                placeholder='{ "channel": "#alerts" }'
                value={configJson}
                onChange={(e) =>
                  setConfigJson(e.target.value)
                }
                required
              />

            </div>


            <DialogFooter className="pt-2">

              <Button
                type="button"
                variant="ghost"
                onClick={() =>
                  setIsRegisterOpen(false)
                }
                className="hover:bg-muted text-foreground"
              >
                Cancel
              </Button>

              <Button
                type="submit"
                disabled={
                  registerMutation.isPending
                }
                className="bg-primary hover:bg-primary/95 text-primary-foreground"
              >
                {registerMutation.isPending
                  ? 'Connecting...'
                  : 'Initialize Node'}
              </Button>

            </DialogFooter>

          </form>

        </DialogContent>

      </Dialog>


      {/* =====================================================
          CONNECTOR DETAILS MODAL
      ====================================================== */}

      {selectedConnector && (

        <Dialog
          open={!!selectedConnector}
          onOpenChange={() =>
            setSelectedConnector(null)
          }
        >

          <DialogContent className="max-w-2xl border-border bg-card shadow-2xl overflow-y-auto max-h-[85vh]">

            <DialogHeader>

              <DialogTitle className="capitalize">
                {selectedConnector.name} Details
              </DialogTitle>

              <DialogDescription>
                View registered tools list, schema
                configurations, and nodes.
              </DialogDescription>

            </DialogHeader>


            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4">

              <Card className="border-border bg-muted/20">

                <CardHeader className="pb-2">

                  <CardTitle className="text-xs font-bold text-muted-foreground uppercase flex items-center gap-1.5">

                    <Layers className="h-3.5 w-3.5" />

                    Node Settings

                  </CardTitle>

                </CardHeader>


                <CardContent className="space-y-3 text-xs leading-relaxed">

                  <div>

                    <span className="font-semibold text-muted-foreground block">
                      Connector UUID
                    </span>

                    <span className="font-mono text-foreground">
                      {selectedConnector.id}
                    </span>

                  </div>


                  <div>

                    <span className="font-semibold text-muted-foreground block">
                      Transport Protocol
                    </span>

                    <span className="capitalize text-foreground">
                      {selectedConnector.connector_type}
                    </span>

                  </div>


                  <div>

                    <span className="font-semibold text-muted-foreground block">
                      Environment variables
                    </span>

                    <pre className="font-mono bg-card border border-border p-2 rounded mt-1 overflow-x-auto text-[10px]">
                      {JSON.stringify(
                        selectedConnector.config,
                        null,
                        2
                      )}
                    </pre>

                  </div>

                </CardContent>

              </Card>


              <Card className="border-border bg-muted/20">

                <CardHeader className="pb-2">

                  <CardTitle className="text-xs font-bold text-muted-foreground uppercase flex items-center gap-1.5">

                    <Terminal className="h-3.5 w-3.5" />

                    Synchronized Schema Tools

                  </CardTitle>

                </CardHeader>


                <CardContent className="space-y-3 overflow-y-auto max-h-[220px]">

                  {selectedConnector.tools?.length === 0 ? (

                    <span className="text-xs text-muted-foreground block py-4">
                      No tools synchronized yet.
                      Run initialize handshake.
                    </span>

                  ) : (

                    selectedConnector.tools.map(
                      (t, idx) => (

                        <div
                          key={idx}
                          className="border border-border bg-card p-2 rounded flex flex-col gap-1"
                        >

                          <span className="text-xs font-bold text-primary font-mono">
                            {t.name}
                          </span>

                          <span className="text-[10px] text-muted-foreground leading-normal">
                            {t.description}
                          </span>

                        </div>

                      )
                    )

                  )}

                </CardContent>

              </Card>

            </div>


            <DialogFooter className="border-t border-border/50 pt-4">

              <Button
                onClick={() =>
                  setSelectedConnector(null)
                }
                className="bg-primary hover:bg-primary/95 text-primary-foreground"
              >
                Close Detail
              </Button>

            </DialogFooter>

          </DialogContent>

        </Dialog>

      )}

    </div>
  );
}