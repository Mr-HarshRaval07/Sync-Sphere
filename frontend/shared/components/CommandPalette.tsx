"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useGlobalSearchStore } from '../stores/globalSearchStore';
import { useThemeStore, AppTheme } from '../stores/themeStore';
import { useFeatureFlags } from '../stores/featureFlagStore';
import { Dialog, DialogContent } from '../../components/ui/dialog';
import {
  Command,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
} from '../../components/ui/command';
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
  Sun,
  Moon,
  ToggleLeft,
  ChevronRight,
} from 'lucide-react';

export const CommandPalette: React.FC = () => {
  const router = useRouter();
  const { isOpen, setOpen, toggle } = useGlobalSearchStore();
  const { theme, setTheme } = useThemeStore();
  const flags = useFeatureFlags();
  const [search, setSearch] = useState('');

  // Global keydown listeners for shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        toggle();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggle]);

  const navigateTo = (path: string) => {
    router.push(path);
    setOpen(false);
  };

  const changeTheme = (newTheme: AppTheme) => {
    setTheme(newTheme);
    setOpen(false);
  };

  // Nav actions mappings
  const actions = [
    { label: 'Go to Dashboard', icon: <LayoutDashboard className="h-4 w-4 mr-2" />, action: () => navigateTo('/dashboard') },
    { label: 'Go to Connectors', icon: <Radio className="h-4 w-4 mr-2" />, action: () => navigateTo('/dashboard/connectors'), enabled: flags.enableMcpConnectors },
    { label: 'Go to AI Models', icon: <BrainCircuit className="h-4 w-4 mr-2" />, action: () => navigateTo('/dashboard/ai-models') },
    { label: 'Go to Prompts', icon: <FileCode className="h-4 w-4 mr-2" />, action: () => navigateTo('/dashboard/prompts') },
    { label: 'Go to Workflow Builder', icon: <GitFork className="h-4 w-4 mr-2" />, action: () => navigateTo('/dashboard/workflows') },
    { label: 'Go to Executions', icon: <Activity className="h-4 w-4 mr-2" />, action: () => navigateTo('/dashboard/executions') },
    { label: 'Go to Approvals', icon: <CheckSquare className="h-4 w-4 mr-2" />, action: () => navigateTo('/dashboard/approvals'), enabled: flags.enableApprovals },
    { label: 'Go to Knowledge Base', icon: <Database className="h-4 w-4 mr-2" />, action: () => navigateTo('/dashboard/knowledge'), enabled: flags.enableKnowledge },
    { label: 'Go to Observability', icon: <Eye className="h-4 w-4 mr-2" />, action: () => navigateTo('/dashboard/observability'), enabled: flags.enableObservability },
    { label: 'Go to Settings', icon: <Settings className="h-4 w-4 mr-2" />, action: () => navigateTo('/dashboard/settings') },
  ];

  const themes: { label: string; value: AppTheme; icon: React.ReactNode }[] = [
    { label: 'Light Mode', value: 'light', icon: <Sun className="h-4 w-4 mr-2" /> },
    { label: 'Dark Mode', value: 'dark', icon: <Moon className="h-4 w-4 mr-2" /> },
    { label: 'Cyberpunk Mode', value: 'cyberpunk', icon: <ToggleLeft className="h-4 w-4 mr-2" /> },
    { label: 'Forest Mode', value: 'forest', icon: <ToggleLeft className="h-4 w-4 mr-2" /> },
    { label: 'Slate Mode', value: 'slate', icon: <ToggleLeft className="h-4 w-4 mr-2" /> },
  ];

  return (
    <Dialog open={isOpen} onOpenChange={setOpen}>
      <DialogContent className="max-w-lg p-0 overflow-hidden border-border bg-card shadow-2xl">
        <Command className="rounded-lg border-none bg-card">
          <CommandInput
            placeholder="Type a command or search..."
            value={search}
            onValueChange={setSearch}
            className="border-none focus:ring-0"
          />
          <CommandList className="max-h-[300px] overflow-y-auto">
            <CommandEmpty>No results found.</CommandEmpty>
            
            <CommandGroup heading="Navigation Actions">
              {actions
                .filter((item) => item.enabled !== false)
                .map((act, idx) => (
                  <CommandItem
                    key={idx}
                    onSelect={act.action}
                    className="flex items-center justify-between py-2 px-3 hover:bg-muted cursor-pointer transition-colors"
                  >
                    <div className="flex items-center">
                      {act.icon}
                      <span className="text-sm font-medium text-foreground">{act.label}</span>
                    </div>
                    <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/60" />
                  </CommandItem>
                ))}
            </CommandGroup>
            
            <CommandGroup heading="Theme Switching">
              {themes.map((t, idx) => (
                <CommandItem
                  key={idx}
                  onSelect={() => changeTheme(t.value)}
                  className="flex items-center justify-between py-2 px-3 hover:bg-muted cursor-pointer transition-colors"
                >
                  <div className="flex items-center">
                    {t.icon}
                    <span className="text-sm font-medium text-foreground">{t.label}</span>
                  </div>
                  {theme === t.value && (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                      Active
                    </span>
                  )}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </DialogContent>
    </Dialog>
  );
};
