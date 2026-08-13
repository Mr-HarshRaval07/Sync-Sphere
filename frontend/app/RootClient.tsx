'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Button } from '../components/ui/button';
import { Bot, Mail, Calendar, Grid, Database, Server, Plus, MessageSquare, AlertCircle, PlayCircle, Lock, Cpu, Rocket, ChevronRight, Share2, Workflow, ArrowRight } from 'lucide-react';
import { ThreeDHeroVisual } from '../shared/components/ThreeDHeroVisual';
import { motion, useScroll, useTransform, useInView } from 'framer-motion';

export default function RootClient({ hasSessionCookie }: { hasSessionCookie: boolean }) {
    const [mounted, setMounted] = useState(false);
    const [activeSection, setActiveSection] = useState('home');
    const { scrollY } = useScroll();

    // Navbar visual effects
    const navBackground = useTransform(scrollY, [0, 50], ['rgba(5, 7, 10, 0)', 'rgba(5, 7, 10, 0.8)']);
    const navBorder = useTransform(scrollY, [0, 50], ['rgba(255, 255, 255, 0)', 'rgba(255, 255, 255, 0.1)']);
    const navBackdrop = useTransform(scrollY, [0, 50], ['blur(0px)', 'blur(12px)']);

    useEffect(() => {
        setMounted(true);
        // Force dark mode context in HTML body if possible, or override with classes locally
        document.documentElement.classList.add('dark');

        const handleScroll = () => {
            const sections = ['home', 'how-it-works', 'integrations', 'features', 'mcp'];
            for (const section of [...sections].reverse()) {
                const el = document.getElementById(section);
                if (el && window.scrollY >= (el.offsetTop - 300)) {
                    setActiveSection(section);
                    break;
                }
            }
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const scrollToSection = (e: React.MouseEvent<HTMLAnchorElement>, id: string) => {
        e.preventDefault();
        const el = document.getElementById(id);
        if (el) {
            const y = el.getBoundingClientRect().top + window.scrollY - 100; // Account for fixed header
            window.scrollTo({ top: y, behavior: 'smooth' });
            window.history.pushState(null, '', '#' + id);
        }
    };

    if (!mounted) return <div className="min-h-screen bg-[#05070A]" />; // Prevent SSR flash

    return (
        <div className="min-h-screen bg-[#05070A] text-slate-100 font-sans selection:bg-cyan-500/30 selection:text-white overflow-x-hidden transition-colors duration-500">
            {/* Ambient Background Glows */}
            <div className="fixed inset-0 z-0 pointer-events-none opacity-40">
                <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-[radial-gradient(circle_at_center,rgba(56,189,248,0.1),transparent_70%)] blur-[100px]" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] rounded-full bg-[radial-gradient(circle_at_center,rgba(168,85,247,0.05),transparent_70%)] blur-[120px]" />
            </div>

            {/* Premium Sticky Navbar */}
            <motion.nav
                style={{ background: navBackground, borderBottomColor: navBorder, backdropFilter: navBackdrop, WebkitBackdropFilter: navBackdrop }}
                className="fixed top-0 inset-x-0 z-50 px-6 py-4 flex items-center justify-between border-b transition-all duration-300"
            >
                <div className="flex items-center gap-3 w-48 shrink-0">
                    <div className="h-9 w-9 rounded-xl bg-white text-black flex items-center justify-center shadow-[0_0_15px_rgba(255,255,255,0.3)] border border-white/20">
                        <Bot className="h-5 w-5" />
                    </div>
                    <span className="font-extrabold text-xl tracking-tight text-white drop-shadow-md">SYNCSPHERE</span>
                </div>

                <div className="hidden lg:flex items-center justify-center gap-8 font-semibold text-sm text-slate-400 flex-1">
                    {['home', 'how-it-works', 'integrations', 'features', 'mcp'].map((item) => (
                        <a
                            key={item}
                            href={`#${item}`}
                            onClick={(e) => scrollToSection(e, item)}
                            className={`transition-colors relative group py-2 capitalize ${activeSection === item ? 'text-white' : 'hover:text-white'}`}
                        >
                            {item.replace(/-/g, ' ')}
                            {activeSection === item && (
                                <motion.div layoutId="nav-indicator" className="absolute -bottom-[1px] left-0 right-0 h-0.5 bg-cyan-400 rounded-t-full shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
                            )}
                        </a>
                    ))}
                </div>

                <div className="flex gap-4 items-center w-48 justify-end shrink-0">
                    <Button variant="ghost" className="text-slate-300 hover:text-white hover:bg-white/10 rounded-full px-5 font-semibold transition-all" asChild>
                        <Link href="/login">Sign In</Link>
                    </Button>
                </div>
            </motion.nav>

            <main className="relative z-10 w-full pt-32 pb-24 px-6 md:px-12 max-w-[1400px] mx-auto flex flex-col">

                {/* HERO SECTION */}
                <section id="home" className="w-full flex flex-col lg:flex-row items-center justify-between gap-12 lg:gap-16 min-h-[60vh] md:min-h-[75vh]">
                    {/* Left: Copy */}
                    <div className="flex flex-col items-center lg:items-start text-center lg:text-left flex-1 max-w-2xl mt-8">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                            className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 font-semibold text-xs tracking-wider uppercase mb-8 shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                        >
                            <Cpu className="h-3.5 w-3.5" />
                            AI Powered Workflow Automation
                        </motion.div>

                        <motion.h1
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.1 }}
                            className="text-5xl sm:text-7xl lg:text-[5.5rem] font-black tracking-tighter text-white mb-6 leading-[1.05]"
                        >
                            SYNCSPHERE
                        </motion.h1>

                        <motion.h2
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                            className="text-2xl sm:text-3xl lg:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-200 to-slate-500 mb-6 tracking-tight"
                        >
                            Connect. Automate. Scale.
                        </motion.h2>

                        <motion.p
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.3 }}
                            className="text-lg sm:text-xl text-slate-400 mb-10 leading-relaxed font-medium max-w-lg"
                        >
                            SyncSphere AI connects your tools, understands your work context, and automates workflows using intelligent AI agents.
                        </motion.p>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: 0.4 }}
                            className="flex flex-col sm:flex-row items-center gap-4 mb-10"
                        >
                            <Button size="lg" className="h-14 px-8 text-base font-bold bg-white text-black hover:bg-slate-200 hover:scale-105 active:scale-95 transition-all shadow-[0_0_30px_rgba(255,255,255,0.2)] rounded-2xl flex items-center gap-2" asChild>
                                <Link href="/login">
                                    Start Building <ArrowRight className="h-4 w-4" />
                                </Link>
                            </Button>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.5, delay: 0.6 }}
                            className="flex flex-wrap items-center justify-center lg:justify-start gap-4 text-xs font-semibold text-slate-400"
                        >
                            <div className="flex items-center gap-1.5"><CheckBadge /> No Code</div>
                            <div className="flex items-center gap-1.5"><CheckBadge /> AI Powered</div>
                            <div className="flex items-center gap-1.5"><CheckBadge /> Secure</div>
                            <div className="flex items-center gap-1.5"><CheckBadge /> Enterprise Ready</div>
                        </motion.div>
                    </div>

                    {/* Right: Interactive Node Diagram */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 1, delay: 0.2 }}
                        className="flex-1 w-full flex justify-center lg:justify-end xl:mr-10 h-full relative"
                    >
                        <ThreeDHeroVisual />
                    </motion.div>
                </section>

                {/* HOW SYNCSPHERE WORKS (WORKFLOW PIPELINE) */}
                <section id="how-it-works" className="w-full mt-32 md:mt-48 pt-10 scroll-mt-24">
                    <div className="flex flex-col items-center mb-16">
                        <h3 className="text-3xl md:text-5xl font-black tracking-tighter text-white mb-6">How SyncSphere Works</h3>
                        <p className="text-slate-400 text-lg font-medium text-center max-w-2xl">The complete pipeline from human intent to secure execution using autonomous intelligent agents.</p>
                    </div>

                    <div className="relative w-full max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 md:gap-0 mt-10">
                        {/* Connecting Line Desktop */}
                        <div className="hidden md:block absolute top-1/2 left-0 w-full h-[2px] bg-white/10 -translate-y-1/2" />
                        <motion.div
                            initial={{ scaleX: 0 }}
                            whileInView={{ scaleX: 1 }}
                            viewport={{ once: true, margin: "-100px" }}
                            transition={{ duration: 1.5, ease: "easeInOut" }}
                            className="hidden md:block absolute top-1/2 left-0 w-full h-[2px] bg-gradient-to-r from-cyan-500 via-purple-500 to-emerald-500 origin-left -translate-y-1/2 shadow-[0_0_10px_currentColor]"
                        />

                        {/* Pipeline Nodes */}
                        <PipelineNode icon={<Bot />} label="User Request" color="cyan" delay={0.1} />
                        <PipelineNode icon={<Cpu />} label="AI Planner" color="purple" delay={0.3} />
                        <PipelineNode icon={<Workflow />} label="Workflow Engine" color="indigo" delay={0.5} />
                        <PipelineNode icon={<Share2 />} label="Execution API" color="blue" delay={0.7} />
                        <PipelineNode icon={<Grid />} label="Integrations" color="sky" delay={0.9} />
                        <PipelineNode icon={<CheckBadge />} label="Execution Complete" color="emerald" delay={1.1} />
                    </div>
                </section>

                {/* INTEGRATIONS */}
                <section id="integrations" className="w-full mt-32 md:mt-48 pt-10 scroll-mt-24">
                    <div className="flex flex-col lg:flex-row items-center gap-12 lg:gap-20">
                        <div className="flex-1 text-center lg:text-left">
                            <h3 className="text-4xl md:text-5xl font-black tracking-tighter text-white mb-6">Native Integrations built for Enterprise</h3>
                            <p className="text-lg text-slate-400 font-medium mb-8 leading-relaxed">
                                Securely connect the tools your team relies on. SyncSphere utilizes strict OAuth 2.0 scoping ensuring intelligent agents only touch the data you explicitly permit.
                            </p>
                            <Button size="lg" variant="outline" className="h-12 px-6 font-bold bg-[#0E1117] text-white border-white/20 hover:border-white/40 hover:bg-white/5 transition-all rounded-xl">
                                View All Connectors
                            </Button>
                        </div>

                        <div className="flex-1 grid grid-cols-3 sm:grid-cols-4 gap-4 w-full">
                            {[
                                { name: 'GitHub', icon: <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" /></svg> },
                                { name: 'Slack', icon: <MessageSquare /> },
                                { name: 'Google', icon: <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" /><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" /><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" /><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" /></svg> },
                                { name: 'Calendar', icon: <Calendar /> },
                                { name: 'Sheets', icon: <Grid /> },
                                { name: 'Jira', icon: <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" viewBox="0 0 24 24"><path d="M11.53 22l-7-7.01-4-4 11 11.01 4-4 7-7.01-4-4-11 11.01z" /><path d="M2.53 13l7-7.01 4-4 11 11.01-4 4-7 7.01-4 4-11-11.01z" /></svg> },
                                { name: 'MongoDB', icon: <Database /> },
                                { name: 'Redis', icon: <Server /> },
                                { name: 'MCP Servers', icon: <Cpu /> },
                                { name: 'Future', icon: <Plus /> },
                                { name: 'Notion', icon: <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" viewBox="0 0 24 24"><path d="M4.459 4.208c.745-.606 1.831-.741 2.919-.741h8.463c2.046 0 3.39 1.135 3.39 3.253v11.839c0 1.258-.87 2.23-2.19 2.23H5.666a2.12 2.12 0 0 1-2.124-2.12V5.553c0-1.127.351-1.345 1.054-1.345ZM6 6v13h12V6s-1.8.4-3 .4-4-.4-5-.4-2.8.4-4 .4Z" /></svg> },
                            ].map((app, i) => (
                                <motion.div
                                    key={app.name}
                                    initial={{ opacity: 0, y: 20 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ duration: 0.5, delay: i * 0.05 }}
                                    className="group relative cursor-pointer"
                                >
                                    <div className="absolute inset-0 bg-cyan-500/10 rounded-2xl blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                                    <div className="bg-[#0E1117] border border-white/5 p-4 h-28 rounded-2xl flex flex-col items-center justify-center text-center gap-3 transition-all duration-300 shadow-md hover:shadow-cyan-500/20 hover:border-cyan-500/30 hover:-translate-y-2 z-10 relative overflow-hidden">
                                        <div className="absolute inset-0 bg-gradient-to-b from-white/[0.03] to-transparent" />
                                        <div className="text-slate-400 group-hover:text-white transition-colors duration-300 z-10">
                                            {app.icon}
                                        </div>
                                        <span className="font-semibold text-xs tracking-tight text-slate-300 group-hover:text-white transition-colors z-10">{app.name}</span>

                                        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                                            <div className="flex items-center gap-1 bg-emerald-500/20 text-emerald-400 text-[8px] font-bold px-1.5 py-0.5 rounded-full border border-emerald-500/30">
                                                <span className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse" /> Live
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* FEATURES */}
                <section id="features" className="w-full mt-32 md:mt-48 scroll-mt-24">
                    <div className="text-center w-full max-w-3xl mx-auto mb-16">
                        <h3 className="text-3xl md:text-5xl font-black tracking-tighter text-white mb-6">Enterprise Features</h3>
                        <p className="text-lg text-slate-400 font-medium">Built from the ground up for teams that demand absolute control and total transparency in their automated workflows.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <FeatureCard icon={<Bot />} title="AI Planning" desc="LLMs dynamically map out multi-step processes across various APIs securely without coding." />
                        <FeatureCard icon={<Workflow />} title="Workflow Automation" desc="Seamlessly orchestrate logic flows with conditional routing and robust failure recovery." />
                        <FeatureCard icon={<Lock />} title="Targeted OAuth" desc="Complete control over per-tenant token scoping to ensure sensitive resources remain untampered." />
                        <FeatureCard icon={<FileText />} title="Prompt Templates" desc="Codify and reuse standardized LLM instructions globally across organizational pipelines." />
                        <FeatureCard icon={<AlertCircle />} title="Human Approvals" desc="Introduce required checkpoint halts where administrators must verify actions before critical API calls." />
                        <FeatureCard icon={<Activity />} title="Real-time Analytics" desc="Detailed observability spanning latency, request/response headers, and execution traces per task." />
                    </div>
                </section>

                {/* MCP SECTION */}
                <section id="mcp" className="w-full mt-32 md:mt-48 mb-20 pt-16 flex flex-col lg:flex-row items-center gap-12 lg:gap-20 border-t border-white/5 scroll-mt-24">
                    <div className="flex-1 text-center lg:text-left">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            viewport={{ once: true }}
                            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 font-semibold text-xs tracking-wider uppercase mb-6 shadow-[0_0_15px_rgba(168,85,247,0.15)]"
                        >
                            <Server className="h-3.5 w-3.5" /> Next Gen Architecture
                        </motion.div>
                        <h3 className="text-4xl md:text-5xl font-black tracking-tighter text-white mb-6">Model Context Protocol</h3>
                        <p className="text-lg text-slate-400 font-medium leading-relaxed mb-8">
                            SyncSphere implements standard MCP bridging to connect your secure internal databases and APIs to generalized AI agents. The hub strictly governs context ingestion natively.
                        </p>
                        <Button variant="outline" className="h-12 px-6 font-bold bg-transparent text-white border-white/20 hover:border-purple-500/50 hover:bg-purple-500/5 transition-all rounded-xl">
                            Read MCP Documentation
                        </Button>
                    </div>

                    <div className="flex-1 w-full flex items-center justify-center p-8 bg-[#0E1117]/50 rounded-[3rem] border border-white/5 relative overflow-hidden">
                        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(168,85,247,0.1),transparent_60%)]" />

                        <div className="flex flex-col items-center gap-6 relative z-10 w-full max-w-sm">
                            <div className="w-full p-4 rounded-2xl bg-[#141824] border border-purple-500/30 flex items-center justify-between shadow-xl">
                                <div className="flex items-center gap-3">
                                    <Bot className="text-cyan-400" />
                                    <span className="font-bold text-white tracking-tight">AI Orchestrator</span>
                                </div>
                                <div className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_10px_#22d3ee]" />
                            </div>

                            <div className="flex gap-1 py-2">
                                {[...Array(3)].map((_, i) => (
                                    <motion.div
                                        key={i}
                                        className="h-3 w-1 rounded-full bg-purple-500/50"
                                        animate={{ opacity: [0.3, 1, 0.3] }}
                                        transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
                                    />
                                ))}
                            </div>

                            <div className="w-full p-5 rounded-2xl bg-gradient-to-r from-purple-900/40 to-indigo-900/40 border border-purple-500/40 flex flex-col items-center shadow-2xl relative overflow-hidden">
                                <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-10" />
                                <Server className="h-10 w-10 text-purple-400 mb-2 relative z-10" />
                                <span className="font-extrabold text-xl text-white tracking-tight relative z-10">MCP Hub</span>
                            </div>

                            <div className="flex gap-1 py-2">
                                {[...Array(3)].map((_, i) => (
                                    <motion.div
                                        key={i}
                                        className="h-3 w-1 rounded-full bg-purple-500/50"
                                        animate={{ opacity: [0.3, 1, 0.3] }}
                                        transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 + 0.6 }}
                                    />
                                ))}
                            </div>

                            <div className="flex w-full gap-4 relative z-10">
                                <div className="flex-1 p-3 rounded-xl bg-[#141824] border border-white/10 flex flex-col items-center justify-center gap-2">
                                    <Database className="h-5 w-5 text-slate-400" />
                                    <span className="text-xs font-semibold text-slate-400">Internal DB</span>
                                </div>
                                <div className="flex-1 p-3 rounded-xl bg-[#141824] border border-white/10 flex flex-col items-center justify-center gap-2">
                                    <Lock className="h-5 w-5 text-slate-400" />
                                    <span className="text-xs font-semibold text-slate-400">Secure APIs</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

            </main>

            {/* FOOTER */}
            <footer className="w-full py-12 border-t border-white/5 bg-[#030406] text-sm text-slate-500 font-medium z-10 relative">
                <div className="max-w-[1400px] mx-auto px-6 md:px-12 flex flex-col lg:flex-row items-center justify-between gap-6">
                    <div className="flex items-center gap-3">
                        <Bot className="h-5 w-5 text-slate-400" />
                        <span className="font-bold text-lg tracking-tight text-slate-300">SYNCSPHERE</span>
                    </div>
                    <p>© 2026 SyncSphere Inc. Built for autonomous systems.</p>
                    <div className="flex items-center gap-6">
                        <a href="#" className="hover:text-white transition-colors">Documentation</a>
                        <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
                        <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
                    </div>
                </div>
            </footer>
        </div>
    );
}

// Subcomponents

function CheckBadge() {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-400"><path d="M20 6 9 17l-5-5" /></svg>
    )
}

function PipelineNode({ icon, label, color, delay }: { icon: React.ReactNode, label: string, color: 'cyan' | 'purple' | 'indigo' | 'emerald' | 'sky' | 'blue', delay: number }) {
    const borders = {
        cyan: 'border-cyan-500/30 hover:border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.1)] hover:shadow-cyan-400/20',
        purple: 'border-purple-500/30 hover:border-purple-400 shadow-[0_0_15px_rgba(168,85,247,0.1)] hover:shadow-purple-400/20',
        indigo: 'border-indigo-500/30 hover:border-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.1)] hover:shadow-indigo-400/20',
        emerald: 'border-emerald-500/30 hover:border-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.1)] hover:shadow-emerald-400/20',
        sky: 'border-sky-500/30 hover:border-sky-400 shadow-[0_0_15px_rgba(14,165,233,0.1)] hover:shadow-sky-400/20',
        blue: 'border-blue-500/30 hover:border-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.1)] hover:shadow-blue-400/20',
    };

    const textColors = {
        cyan: 'text-cyan-400',
        purple: 'text-purple-400',
        indigo: 'text-indigo-400',
        emerald: 'text-emerald-400',
        sky: 'text-sky-400',
        blue: 'text-blue-400',
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay }}
            className={`w-36 h-32 md:w-32 bg-[#0E1117] border rounded-2xl flex flex-col items-center justify-center p-4 gap-3 relative z-10 transition-all duration-300 cursor-default flex-shrink-0 mb-4 md:mb-0 ${borders[color]}`}
        >
            <div className={`p-2 rounded-lg bg-white/5 ${textColors[color]}`}>
                {React.isValidElement<{ className?: string }>(icon) ? React.cloneElement(icon, { className: 'h-6 w-6' }) : icon}
            </div>
            <span className="text-[11px] font-bold text-center tracking-tight text-slate-300 leading-snug">{label}</span>
        </motion.div>
    );
}

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="group p-8 rounded-3xl bg-[#0E1117] border border-white/5 hover:border-cyan-500/30 transition-all duration-300 shadow-lg relative overflow-hidden"
        >
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="h-12 w-12 rounded-2xl bg-white/5 border border-white/10 text-white flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-cyan-500/10 group-hover:text-cyan-400 group-hover:border-cyan-500/30 transition-all duration-500">
                {React.isValidElement<{ className?: string }>(icon) ? React.cloneElement(icon, { className: 'h-6 w-6' }) : icon}
            </div>
            <h4 className="text-xl font-bold text-white mb-3 tracking-tight">{title}</h4>
            <p className="text-slate-400 font-medium text-sm leading-relaxed">{desc}</p>
        </motion.div>
    );
}

function FileText(props: any) {
    return <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" /><path d="M14 2v4a2 2 0 0 0 2 2h4" /><path d="M10 9H8" /><path d="M16 13H8" /><path d="M16 17H8" /></svg>
}

function Activity(props: any) {
    return <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.48 12H2" /></svg>
}
