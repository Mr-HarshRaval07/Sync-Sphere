'use client';

'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowRight, Bot, Zap, Lock, Activity, LayoutGrid, CheckCircle2 } from 'lucide-react';

export default function RootIndexPage() {
  return (
    <div className="min-h-screen bg-[#020817] text-slate-50 font-sans selection:bg-indigo-500/30">

      {/* Navigation */}
      <nav className="fixed top-0 inset-x-0 z-50 bg-[#020817]/80 backdrop-blur-md border-b border-indigo-500/10 transition-all px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Bot className="h-5 w-5 text-white" />
          </div>
          <span className="font-bold text-xl tracking-tight text-white">SyncSphere <span className="text-indigo-400 font-medium">AI</span></span>
        </div>
        <div className="flex gap-4">
          <Link href="/login">
            <Button variant="ghost" className="text-slate-300 hover:text-white hover:bg-white/5">Log in</Button>
          </Link>
          <Link href="/register">
            <Button className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium shadow-[0_0_20px_rgba(79,70,229,0.3)]">Get Started</Button>
          </Link>
        </div>
      </nav>

      <main className="pt-32 pb-24 px-6 max-w-7xl mx-auto flex flex-col items-center">
        {/* Hero Section */}
        <section className="text-center max-w-4xl mx-auto flex flex-col items-center mt-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm font-medium mb-8">
            <SparkleIcon /> Introducing Automations Engine v2.0
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-br from-white via-slate-200 to-slate-500 mb-6 leading-[1.1]">
            Turn Your Ideas Into <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Automated Workflows</span>
          </h1>

          <p className="text-lg md:text-xl text-slate-400 mb-10 max-w-2xl leading-relaxed">
            SyncSphere AI connects your tools, plans your work, and executes your workflows — all from one intelligent workspace.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 items-center">
            <Link href="/register">
              <Button size="lg" className="h-14 px-8 text-lg font-semibold bg-white text-slate-900 hover:bg-slate-200 shadow-[0_0_40px_rgba(255,255,255,0.2)] transition-all">
                Start Building Free <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="h-14 px-8 text-lg font-semibold border-slate-700 bg-slate-900/50 hover:bg-slate-800 text-white">
              Explore Integrations
            </Button>
          </div>
        </section>

        {/* Visual Hero Section */}
        <section className="mt-28 w-full max-w-5xl mx-auto">
          <div className="relative rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-3xl p-8 overflow-hidden shadow-2xl shadow-indigo-900/20">
            {/* Soft decorative background glows */}
            <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent"></div>
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-500/20 blur-[120px] rounded-full pointer-events-none"></div>

            <div className="relative flex flex-col md:flex-row items-center justify-between gap-8 z-10">

              <div className="flex-1 bg-slate-950/80 rounded-xl p-6 border border-slate-800/80 w-full min-h-[220px] flex flex-col items-center justify-center">
                <span className="text-sm text-slate-400 font-medium mb-4 uppercase tracking-wider">User Goal</span>
                <p className="text-lg font-medium text-white italic text-center">
                  "Create an onboarding issue for the new dev, and send a Slack notification."
                </p>
              </div>

              <div className="flex flex-col items-center text-indigo-400">
                <ArrowRight className="h-8 w-8 hidden md:block" />
                <ArrowRight className="h-8 w-8 md:hidden rotate-90 my-2" />
              </div>

              <div className="flex-1 rounded-xl p-1 w-full relative">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl blur opacity-30"></div>
                <div className="relative bg-slate-950 rounded-xl p-6 border border-indigo-500/30 flex flex-col items-center min-h-[220px]">
                  <span className="text-sm text-indigo-300 font-bold mb-4 uppercase tracking-wider flex items-center gap-2">
                    <Bot className="h-4 w-4" /> SyncSphere AI Plan
                  </span>
                  <div className="w-full space-y-3">
                    <div className="flex items-center gap-3 p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
                      <LayoutGrid className="h-5 w-5 text-indigo-400" />
                      <span className="text-sm font-medium text-slate-200">GitHub — Issue Created</span>
                    </div>
                    <div className="flex items-center gap-3 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                      <LayoutGrid className="h-5 w-5 text-emerald-400" />
                      <span className="text-sm font-medium text-slate-200">Slack — Message Sent</span>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="mt-32 w-full max-w-5xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-4">How it works</h2>
            <p className="text-slate-400 text-lg">Four steps to absolute workflow supremacy.</p>
          </div>

          <div className="grid md:grid-cols-4 gap-8">
            {[
              { num: '1', title: 'Describe your goal', desc: 'Tell the AI what you want to achieve in plain English.' },
              { num: '2', title: 'AI creates a plan', desc: 'SyncSphere instantly translates your prompt into an executable roadmap.' },
              { num: '3', title: 'Connect your apps', desc: 'Securely authenticate with dozens of critical SaaS tools via OAuth.' },
              { num: '4', title: 'Execute automatically', desc: 'Watch your plan run with real-time UI tracking and self-healing retries.' },
            ].map((step) => (
              <div key={step.num} className="flex flex-col items-center text-center group">
                <div className="h-16 w-16 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center text-2xl font-bold text-indigo-400 mb-6 group-hover:scale-110 group-hover:bg-indigo-500/10 group-hover:border-indigo-500/30 transition-all">
                  {step.num}
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{step.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Features */}
        <section className="mt-32 w-full max-w-6xl">
          <div className="grid md:grid-cols-2 gap-6">
            <FeatureCard
              icon={<Bot />}
              title="Plan with AI"
              desc="Next-generation language models map complex operational workflows instantly."
            />
            <FeatureCard
              icon={<LayoutGrid />}
              title="Multi-App Automation"
              desc="Coordinate actions across multiple platforms seamlessly in a single trace."
            />
            <FeatureCard
              icon={<Zap />}
              title="Smart Workflow Execution"
              desc="Resilient, idempotent execution engine prevents duplicate actions on failures."
            />
            <FeatureCard
              icon={<Lock />}
              title="Secure OAuth Connections"
              desc="Enterprise-grade token management scopes execution safely on your behalf."
            />
            <FeatureCard
              icon={<Activity />}
              title="Real-Time Tracking"
              desc="Watch every node in your strategy execute with precise observability."
            />
          </div>
        </section>

        {/* Integrations Grid */}
        <section className="mt-32 w-full text-center">
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-16">Connects with what you use.</h2>
          <div className="flex flex-wrap items-center justify-center gap-6">
            <AppCard name="Slack" icon="https://upload.wikimedia.org/wikipedia/commons/d/d5/Slack_icon_2019.svg" />
            <AppCard name="GitHub" icon="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" darkInvert />
            <AppCard name="Gmail" icon="https://upload.wikimedia.org/wikipedia/commons/7/7e/Gmail_icon_%282020%29.svg" />
            <AppCard name="Google Calendar" icon="https://upload.wikimedia.org/wikipedia/commons/a/a5/Google_Calendar_icon_%282020%29.svg" />
            <AppCard name="Google Sheets" icon="https://upload.wikimedia.org/wikipedia/commons/3/30/Google_Sheets_logo_%282014-2020%29.svg" />
          </div>
        </section>

        {/* Final CTA */}
        <section className="mt-32 mb-20 text-center relative max-w-4xl mx-auto bg-gradient-to-b from-indigo-900/40 to-slate-950 border border-indigo-500/20 rounded-3xl p-12 overflow-hidden shadow-2xl">
          <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay"></div>
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6 relative z-10">
            Build your first workflow with SyncSphere AI
          </h2>
          <Link href="/register">
            <Button size="lg" className="h-14 px-8 text-lg font-bold bg-white text-indigo-950 hover:bg-slate-200 relative z-10">
              Get Started Now <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 bg-[#020817] py-8 text-center text-slate-500 text-sm">
        <p>&copy; {new Date().getFullYear()} SyncSphere AI. All rights reserved.</p>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) {
  return (
    <div className="flex gap-4 p-6 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-indigo-500/40 transition-colors">
      <div className="h-12 w-12 shrink-0 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
        {icon}
      </div>
      <div>
        <h3 className="text-xl font-semibold text-slate-100 mb-2">{title}</h3>
        <p className="text-slate-400 leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}

function AppCard({ name, icon, darkInvert = false }: { name: string, icon: string, darkInvert?: boolean }) {
  return (
    <div className="flex flex-col items-center gap-3 p-6 w-32 rounded-2xl bg-slate-900 border border-slate-800 hover:bg-slate-800 transition-colors">
      <img src={icon} alt={name} className={`w-12 h-12 object-contain ${darkInvert ? 'invert contrast-200' : ''}`} />
      <span className="text-xs font-semibold text-slate-300">{name}</span>
    </div>
  );
}

function SparkleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-400">
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
      <path d="M5 3v4M3 5h4M19 3v4M17 5h4" />
    </svg>
  );
}
