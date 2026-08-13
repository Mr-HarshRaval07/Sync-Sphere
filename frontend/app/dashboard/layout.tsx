'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '../../shared/stores/authStore';
import { useOrgStore } from '../../shared/stores/orgStore';
import { useThemeStore, AppTheme } from '../../shared/stores/themeStore';
import { useNotificationStore } from '../../shared/stores/notificationStore';
import { useSidebarStore } from '../../shared/stores/sidebarStore';
import { useFeatureFlags } from '../../shared/stores/featureFlagStore';
import { useGlobalSearch } from '../../shared/stores/globalSearchStore';
import { useLiveTelemetry } from '../../shared/hooks/useLiveTelemetry';
import { CommandPalette } from '../../shared/components/CommandPalette';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Popover, PopoverContent, PopoverTrigger } from '../../components/ui/popover';
import { Toaster } from 'sonner';
import {
  LayoutDashboard,
  Radio,
  BrainCircuit,
  FileCode,
  GitFork,
  Activity,
  CheckSquare,
  Database,
  Eye,
  Settings,
  LogOut,
  Sun,
  Moon,
  Menu,
  Bell,
  ChevronDown,
  User,
  ChevronsUpDown,
  Search,
  Sparkles,
  ShieldCheck,
  ClipboardList,
  CalendarClock,
} from 'lucide-react';
import { cn } from '../../lib/utils';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  // State Stores
  const { user, logout, isAuthenticated } = useAuthStore();
  const { currentOrg, orgs, setCurrentOrg } = useOrgStore();
  const { theme, setTheme } = useThemeStore();
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotificationStore();
  const { isOpen: isSidebarOpen, toggle: toggleSidebar } = useSidebarStore();
  const { toggle: toggleSearch } = useGlobalSearch();
  const flags = useFeatureFlags();

  // Establish Live Telemetry Connection (WebSocket)
  const { isConnected: isWsConnected } = useLiveTelemetry();

  // Track whether the component has mounted on the client.
  // Zustand's `persist` middleware rehydrates from localStorage asynchronously
  // AFTER the first render, so `isAuthenticated` is always `false` on the
  // very first paint.  We must wait for mounting before reading auth state or
  // rendering children (which would fire API calls without a token).
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  // Enforce client-side authentication and sync theme — only after hydration.
  useEffect(() => {
    if (!mounted) return;

    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    // Re-apply saved theme on mount
    useThemeStore.getState().setTheme(theme);
  }, [theme, isAuthenticated, router, mounted]);

  // Sidebar navigation routes mapping
  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard className="h-4 w-4" />, enabled: true },
    { label: 'Connectors', path: '/dashboard/connectors', icon: <Radio className="h-4 w-4" />, enabled: flags.enableMcpConnectors },
    { label: 'Tasks', path: '/dashboard/tasks', icon: <ClipboardList className="h-4 w-4" />, enabled: true },
    { label: 'AI Models', path: '/dashboard/ai-models', icon: <Sparkles className="h-4 w-4" />, enabled: true },
    { label: 'Prompt Templates', path: '/dashboard/prompts', icon: <FileCode className="h-4 w-4" />, enabled: true },
    { label: 'Workflow Builder', path: '/dashboard/workflows', icon: <GitFork className="h-4 w-4" />, enabled: true },
    { label: 'Execution Runs', path: '/dashboard/executions', icon: <Activity className="h-4 w-4" />, enabled: true },
    { label: 'Scheduled Workflows', path: '/dashboard/scheduled', icon: <CalendarClock className="h-4 w-4" />, enabled: true },
    { label: 'Human Approvals', path: '/dashboard/approvals', icon: <CheckSquare className="h-4 w-4" />, enabled: flags.enableApprovals },
    { label: 'Knowledge Base', path: '/dashboard/knowledge', icon: <Database className="h-4 w-4" />, enabled: flags.enableKnowledge },
    { label: 'Observability', path: '/dashboard/observability', icon: <Eye className="h-4 w-4" />, enabled: flags.enableObservability },
    { label: 'Settings', path: '/dashboard/settings', icon: <Settings className="h-4 w-4" />, enabled: true },
  ];

  // Breadcrumbs generation
  const getBreadcrumbs = () => {
    const segments = pathname.split('/').filter(Boolean);
    return segments.map((seg, idx) => {
      const path = '/' + segments.slice(0, idx + 1).join('/');
      const label = seg.charAt(0).toUpperCase() + seg.slice(1).replace('-', ' ');
      return { label, path };
    });
  };

  const breadcrumbs = getBreadcrumbs();

  const handleLogout = () => {
    // Clear cookies & stores
    document.cookie = 'refresh_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    document.cookie = 'syncsphere-session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    logout();
    router.push('/login');
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background font-sans text-foreground">
      {/* Reusable Toast Center */}
      <Toaster position="top-right" theme={theme === 'light' ? 'light' : 'dark'} />

      {/* Global Cmd+K Command Palette */}
      <CommandPalette />

      {/* Collapsible Sidebar Pane */}
      <aside
        className={cn(
          "flex flex-col border-r border-border bg-card transition-all duration-300 ease-in-out select-none",
          isSidebarOpen ? "w-64" : "w-16"
        )}
      >
        {/* Sidebar Header Brand Logo */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-border/50">
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-black shrink-0">
              S
            </div>
            {isSidebarOpen && <span className="font-extrabold text-sm tracking-wider">SYNCOSPHERE</span>}
          </div>
        </div>

        {/* Sidebar Navigation Items */}
        <nav className="flex-1 space-y-1 p-2 overflow-y-auto">
          {navItems
            .filter((item) => item.enabled)
            .map((item) => {
              const isActive = item.path === '/dashboard' ? pathname === '/dashboard' : pathname.startsWith(item.path);
              return (
                <Button
                  key={item.path}
                  variant={isActive ? 'secondary' : 'ghost'}
                  className={cn(
                    "w-full justify-start gap-3 text-sm font-medium transition-all duration-200",
                    isActive
                      ? "bg-secondary text-secondary-foreground shadow-sm font-semibold"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                    !isSidebarOpen && "justify-center p-0"
                  )}
                  onClick={() => router.push(item.path)}
                  title={item.label}
                >
                  {item.icon}
                  {isSidebarOpen && <span>{item.label}</span>}
                </Button>
              );
            })}
        </nav>

        {/* Sidebar Footer Org Switcher */}
        <div className="p-2 border-t border-border/50 bg-muted/20">
          {isSidebarOpen ? (
            <Popover>
              <PopoverTrigger className="w-full inline-flex items-center justify-between gap-2 border border-border rounded bg-card px-3 py-2 text-xs font-semibold text-foreground hover:bg-muted transition-colors">
                <div className="flex items-center gap-1.5 overflow-hidden">
                  <div className="h-4 w-4 rounded bg-primary/10 text-primary flex items-center justify-center shrink-0 font-bold">
                    O
                  </div>
                  <span className="truncate">{currentOrg?.name || 'Loading Organization...'}</span>
                </div>
                <ChevronsUpDown className="h-3 w-3 text-muted-foreground shrink-0" />
              </PopoverTrigger>
              <PopoverContent className="w-56 p-1 border-border bg-card shadow-lg" align="center">
                <div className="px-2 py-1.5 text-xs font-medium text-muted-foreground">Switch Tenant</div>
                {(Array.isArray(orgs) ? orgs : []).map((org) => (
                  <Button
                    key={org.id}
                    variant={currentOrg?.id === org.id ? 'secondary' : 'ghost'}
                    size="sm"
                    className="w-full justify-start text-xs font-medium"
                    onClick={() => setCurrentOrg(org)}
                  >
                    {org.name}
                  </Button>
                ))}
              </PopoverContent>
            </Popover>
          ) : (
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-foreground border border-border mx-auto font-black text-xs">
              {currentOrg?.name?.charAt(0) || 'O'}
            </div>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header toolbar */}
        <header className="flex h-16 items-center justify-between border-b border-border/50 bg-card px-6">
          {/* Left: Sidebar Toggle & Breadcrumbs */}
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-muted text-muted-foreground" onClick={toggleSidebar}>
              <Menu className="h-4 w-4" />
            </Button>

            <nav className="hidden md:flex items-center space-x-2 text-sm text-muted-foreground">
              {breadcrumbs.map((crumb, idx) => (
                <React.Fragment key={crumb.path}>
                  {idx > 0 && <span className="text-muted-foreground/50">/</span>}
                  <span
                    className={cn(
                      "font-medium",
                      idx === breadcrumbs.length - 1 ? "text-foreground font-semibold" : "hover:text-foreground cursor-pointer"
                    )}
                    onClick={() => idx < breadcrumbs.length - 1 && router.push(crumb.path)}
                  >
                    {crumb.label}
                  </span>
                </React.Fragment>
              ))}
            </nav>
          </div>

          {/* Right: Search, Live Telemetry, Theme, Notification, Account dropdown */}
          <div className="flex items-center gap-4">
            {/* Global Search Bar (Trigger Cmd+K Palette) */}
            <div
              className="relative w-48 md:w-64 cursor-pointer"
              onClick={toggleSearch}
            >
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
              <div className="flex h-9 w-full rounded-md border border-border bg-muted/30 px-9 py-2 text-sm text-muted-foreground select-none items-center justify-between">
                <span>Search...</span>
                <kbd className="hidden sm:inline-flex h-5 items-center gap-0.5 rounded border border-border bg-card px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
                  <span>Ctrl+K</span>
                </kbd>
              </div>
            </div>

            {/* Live Telemetry Socket State Indicator */}
            <Badge
              variant="outline"
              className={cn(
                "text-xs font-semibold px-2 py-0.5 flex items-center gap-1 border shrink-0",
                isWsConnected ? "text-emerald-500 bg-emerald-500/10 border-emerald-500/25" : "text-amber-500 bg-amber-500/10 border-amber-500/25"
              )}
            >
              <span className={cn("h-1.5 w-1.5 rounded-full", isWsConnected ? "bg-emerald-500 animate-pulse" : "bg-amber-500")} />
              {isWsConnected ? "Live Link" : "Offline"}
            </Badge>

            {/* Expanded Theme Switcher Dropdown */}
            <Popover>
              <PopoverTrigger className="inline-flex h-8 w-8 items-center justify-center rounded hover:bg-muted text-muted-foreground">
                {theme === 'light' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </PopoverTrigger>
              <PopoverContent className="w-40 p-1 border-border bg-card shadow-lg" align="end">
                <div className="px-2 py-1 text-xs text-muted-foreground font-medium">Select Theme</div>
                {(['light', 'dark', 'cyberpunk', 'forest', 'slate'] as AppTheme[]).map((t) => (
                  <Button
                    key={t}
                    variant={theme === t ? 'secondary' : 'ghost'}
                    size="sm"
                    className="w-full justify-start text-xs capitalize"
                    onClick={() => setTheme(t)}
                  >
                    {t}
                  </Button>
                ))}
              </PopoverContent>
            </Popover>

            {/* Notification Bell Panel */}
            <Popover>
              <PopoverTrigger className="inline-flex h-8 w-8 items-center justify-center rounded hover:bg-muted text-muted-foreground relative">
                <Bell className="h-4 w-4" />
                {unreadCount > 0 && (
                  <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[9px] font-bold text-white">
                    {unreadCount}
                  </span>
                )}
              </PopoverTrigger>
              <PopoverContent className="w-80 p-0 border-border bg-card shadow-xl overflow-hidden" align="end">
                <div className="flex items-center justify-between border-b border-border p-3 bg-muted/40">
                  <span className="text-sm font-semibold">Alert Feed</span>
                  {unreadCount > 0 && (
                    <Button variant="ghost" size="sm" className="h-6 text-[10px] hover:bg-muted" onClick={markAllAsRead}>
                      Mark Read
                    </Button>
                  )}
                </div>
                <div className="max-h-[300px] overflow-y-auto divide-y divide-border/50">
                  {notifications.length === 0 ? (
                    <div className="text-center py-8 text-xs text-muted-foreground">No alerts active.</div>
                  ) : (
                    notifications.map((notif) => (
                      <div
                        key={notif.id}
                        className={cn(
                          "p-3 flex flex-col gap-1 transition-colors hover:bg-muted/10 cursor-pointer",
                          notif.status === 'ACTIVE' && "bg-primary/5 font-medium"
                        )}
                        onClick={() => markAsRead(notif.id)}
                      >
                        <div className="flex justify-between items-center gap-2">
                          <span className="text-xs font-semibold">{notif.name}</span>
                          <span className="text-[9px] text-muted-foreground">{new Date(notif.created_at).toLocaleTimeString()}</span>
                        </div>
                        <p className="text-[11px] text-muted-foreground leading-normal">{notif.message}</p>
                      </div>
                    ))
                  )}
                </div>
              </PopoverContent>
            </Popover>

            {/* User Dropdown Profile Menu */}
            <Popover>
              <PopoverTrigger className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-border bg-muted p-0 shrink-0 text-muted-foreground hover:bg-muted/80 transition-colors">
                <User className="h-4 w-4" />
              </PopoverTrigger>
              <PopoverContent className="w-56 p-1 border-border bg-card shadow-lg" align="end">
                <div className="px-2 py-1.5 flex flex-col">
                  <span className="text-xs font-bold text-foreground">
                    {user?.first_name} {user?.last_name}
                  </span>
                  <span className="text-[10px] text-muted-foreground">{user?.email}</span>
                </div>
                <div className="h-px bg-border my-1" />
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs"
                  onClick={() => router.push('/dashboard/settings')}
                >
                  <Settings className="h-3.5 w-3.5 mr-2 text-muted-foreground" /> Account Settings
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-xs text-rose-500 hover:bg-rose-500/5"
                  onClick={handleLogout}
                >
                  <LogOut className="h-3.5 w-3.5 mr-2 text-rose-500" /> Log Out
                </Button>
              </PopoverContent>
            </Popover>
          </div>
        </header>

        {/* Content Viewport scroll container */}
        {/* Only render children after hydration – prevents API calls going out
            before the access token is restored from localStorage. */}
        <main className="flex-1 overflow-y-auto bg-background p-6">
          {mounted ? children : null}
        </main>
      </div>
    </div>
  );
}
