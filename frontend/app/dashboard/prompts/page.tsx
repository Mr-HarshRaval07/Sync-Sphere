'use client';

import React, { useState } from 'react';
import { Button } from '../../../components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { FileCode, Plus, Check, Search, Filter, Copy, Settings2 } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../../../components/ui/dialog';
import { Label } from '../../../components/ui/label';
import { Input } from '../../../components/ui/input';
import { useWorkflowBuilderStore } from '../../../shared/stores/workflowBuilderStore';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';

const DEFAULT_TEMPLATES = [
  {
    id: '1',
    title: 'Project Planning',
    description: 'Decompose high-level project goals into actionable structured workflows.',
    category: 'Planning',
    prompt: 'Create a project plan for launching a new web application.',
    integrations: ['Planner'],
    example: 'JSON AST with 6 tasks and dependency graph'
  },
  {
    id: '2',
    title: 'Email Automation',
    description: 'Notify teams dynamically based on event triggers.',
    category: 'Communication',
    prompt: 'Send an email to the project team when a new task is created.',
    integrations: ['Gmail'],
    example: 'Drafted HTML email to team@company.com'
  },
  {
    id: '3',
    title: 'GitHub Issue Workflow',
    description: 'Bridge development tracking with real-time alerts.',
    category: 'Development',
    prompt: 'When a task is created, create a GitHub issue and notify Slack.',
    integrations: ['GitHub', 'Slack'],
    example: 'GitHub Issue #402, Slack #dev-updates alert'
  },
  {
    id: '4',
    title: 'Meeting Automation',
    description: 'Schedule synchronous events and distribute invites seamlessly.',
    category: 'Scheduling',
    prompt: 'Create a calendar event and send the meeting details by Gmail.',
    integrations: ['Calendar', 'Gmail'],
    example: 'Event scheduled Jan 1st 3:00 PM, 5 Invites sent'
  },
  {
    id: '5',
    title: 'Task Assignment',
    description: 'Ensure assignees are instantly alerted to new responsibilities.',
    category: 'Management',
    prompt: 'When a new task is assigned, notify the assignee in Slack.',
    integrations: ['Slack'],
    example: 'Slack DM to @alex'
  },
  {
    id: '6',
    title: 'Customer Follow-up',
    description: 'Maintain client relationships post-delivery.',
    category: 'CRM',
    prompt: 'Send a follow-up email after a completed task.',
    integrations: ['Gmail'],
    example: 'Polite thank you template dispatched'
  }
];

export default function PromptsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | 'All'>('All');

  const [isNewTemplateOpen, setIsNewTemplateOpen] = useState(false);
  const [isViewTemplateOpen, setIsViewTemplateOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);

  const { setActivePromptContext } = useWorkflowBuilderStore();
  const router = useRouter();

  // Derive categories
  const categories = ['All', ...Array.from(new Set(DEFAULT_TEMPLATES.map(t => t.category)))];

  const filteredTemplates = DEFAULT_TEMPLATES.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(searchTerm.toLowerCase()) || item.prompt.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || item.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleUseTemplate = (template: any) => {
    setSelectedTemplate(template);
    setIsViewTemplateOpen(true);
  };

  const handleLoadToPlanner = () => {
    setActivePromptContext(selectedTemplate);
    toast.success('Redirecting to AI Planner...', { description: `The ${selectedTemplate?.title} prompt has been loaded into your planner context.` });
    setIsViewTemplateOpen(false);
    router.push('/dashboard/tasks');
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight">Prompt Templates</h2>
          <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
            Reusable prompts for quickly creating common automation workflows.
          </p>
        </div>
        <Button onClick={() => setIsNewTemplateOpen(true)} className="bg-primary hover:bg-primary/90 text-primary-foreground">
          <Plus className="h-4 w-4 mr-2" /> New Template
        </Button>
      </div>

      <div className="flex items-center gap-4 border-b border-border/50 pb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="h-10 w-full rounded-md border border-border bg-background px-9 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary/30"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {categories.map(cat => (
            <Button
              key={cat}
              variant={selectedCategory === cat ? 'default' : 'outline'}
              size="sm"
              className={selectedCategory === cat ? 'bg-primary text-primary-foreground' : 'border-border text-muted-foreground'}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </Button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTemplates.map((template) => (
          <Card key={template.id} className="border-border bg-card shadow-sm flex flex-col hover:border-primary/30 transition-colors">
            <CardHeader className="pb-3 border-b border-border/30">
              <div className="flex items-start justify-between">
                <div>
                  <Badge variant="outline" className="mb-3 text-[10px] uppercase tracking-wider font-bold border-indigo-500/30 text-indigo-500 bg-indigo-500/5">{template.category}</Badge>
                  <CardTitle className="text-base font-bold text-foreground leading-tight">{template.title}</CardTitle>
                </div>
                <div className="h-8 w-8 rounded bg-muted flex items-center justify-center border border-border">
                  <FileCode className="h-4 w-4 text-muted-foreground" />
                </div>
              </div>
              <CardDescription className="text-xs font-medium mt-1">
                {template.description}
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4 flex-1 flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Prompt String</span>
                <div className="p-3 bg-muted/40 border border-border/60 rounded-md text-sm text-foreground italic font-serif">
                  "{template.prompt}"
                </div>
              </div>

              <div className="flex flex-col gap-2 mt-auto">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider min-w-[70px]">Integrations:</span>
                  <div className="flex flex-wrap gap-1">
                    {template.integrations.map((int, i) => (
                      <Badge key={i} variant="secondary" className="px-1.5 py-0 text-[9px] bg-slate-800 text-slate-300 border border-slate-700">{int}</Badge>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider min-w-[70px]">Output:</span>
                  <span className="text-xs font-mono text-emerald-500/90 truncate">{template.example}</span>
                </div>
              </div>
            </CardContent>
            <CardFooter className="pt-0 pb-4 px-6 border-t border-border/30 mt-4 h-16 flex items-center">
              <Button
                onClick={() => handleUseTemplate(template)}
                variant="default"
                className="w-full bg-slate-900 border border-slate-700 text-slate-200 hover:bg-slate-800 hover:text-white"
              >
                Use Template
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>

      {filteredTemplates.length === 0 && (
        <div className="flex flex-col items-center justify-center p-12 border border-dashed border-border rounded-xl">
          <FileCode className="h-10 w-10 text-muted-foreground mb-4" />
          <p className="text-foreground font-bold">No templates found</p>
          <p className="text-sm text-muted-foreground">Try adjusting your search criteria.</p>
        </div>
      )}

      {/* New Template Modal */}
      <Dialog open={isNewTemplateOpen} onOpenChange={setIsNewTemplateOpen}>
        <DialogContent className="max-w-xl border-border bg-card shadow-2xl">
          <DialogHeader>
            <DialogTitle>Create Prompt Template</DialogTitle>
            <DialogDescription>Draft a reusable system prompt for orchestrating actions.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label className="text-xs">Template Name</Label>
                <Input placeholder="e.g. Lead Qualification" className="bg-background border-border" />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Category</Label>
                <Input placeholder="e.g. CRM" className="bg-background border-border" />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Description</Label>
              <Input placeholder="Briefly describe the automation purpose..." className="bg-background border-border" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">System Prompt</Label>
              <textarea
                className="flex min-h-[120px] w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-none placeholder-muted-foreground"
                placeholder="Enter the instructions for the AI orchestration system..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setIsNewTemplateOpen(false)}>Cancel</Button>
            <Button onClick={() => { setIsNewTemplateOpen(false); toast.success('Template Created'); }} className="bg-primary hover:bg-primary/95 text-primary-foreground">Save Template</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View/Load Template Modal */}
      {selectedTemplate && (
        <Dialog open={isViewTemplateOpen} onOpenChange={setIsViewTemplateOpen}>
          <DialogContent className="max-w-2xl border-border bg-card shadow-2xl">
            <DialogHeader>
              <div className="flex justify-between items-start">
                <div>
                  <DialogTitle className="flex items-center gap-2">
                    {selectedTemplate.title}
                    <Badge variant="outline" className="text-[10px] font-bold border-indigo-500/30 text-indigo-500 bg-indigo-500/5">{selectedTemplate.category}</Badge>
                  </DialogTitle>
                  <DialogDescription className="mt-1">{selectedTemplate.description}</DialogDescription>
                </div>
              </div>
            </DialogHeader>

            <div className="space-y-4 py-2">
              <div className="bg-muted border border-border/80 rounded-lg p-4 font-serif italic text-sm text-foreground">
                "{selectedTemplate.prompt}"
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="font-semibold text-muted-foreground block mb-2">Required Integrations</span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedTemplate.integrations.map((int: string, i: number) => (
                      <Badge key={i} variant="secondary" className="bg-slate-800 text-slate-300 border-slate-700">{int}</Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <span className="font-semibold text-muted-foreground block mb-2">Expected Output</span>
                  <span className="font-mono text-emerald-400 bg-muted px-2 py-1 flex rounded border border-border">{selectedTemplate.example}</span>
                </div>
              </div>
            </div>

            <DialogFooter className="flex justify-between sm:justify-between items-center w-full mt-4">
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="border-border text-foreground hover:bg-muted font-semibold flex items-center gap-1.5">
                  <Copy className="h-3.5 w-3.5" /> Copy
                </Button>
                <Button variant="outline" size="sm" className="border-border text-foreground hover:bg-muted font-semibold flex items-center gap-1.5">
                  <Settings2 className="h-3.5 w-3.5" /> Edit
                </Button>
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" onClick={() => setIsViewTemplateOpen(false)}>Cancel</Button>
                <Button onClick={handleLoadToPlanner} className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold">Use in Planner</Button>
              </div>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

