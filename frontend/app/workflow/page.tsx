'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Button } from '../../components/ui/button';
import { Bot, Moon, Sun, Home, ChevronRight, ArrowRight } from 'lucide-react';
import { useThemeStore } from '../../shared/stores/themeStore';
import { ThreeDHeroVisual } from '../../shared/components/ThreeDHeroVisual';

export default function WorkflowPage() {
    const { theme, setTheme } = useThemeStore();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        // Ensure theme relies on persisted zustand state properly
        useThemeStore.getState().setTheme(theme);
    }, [theme]);

    return (
        <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/50 relative overflow-hidden transition-colors duration-500">
            {/* Background ambient lighting */}
            <div className="absolute inset-0 z-0 flex items-center justify-center pointer-events-none opacity-20">
                <div className="w-[1000px] h-[1000px] rounded-full bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-white/10 via-transparent to-transparent blur-3xl"></div>
            </div>

            {/* Navigation (identical to RootClient design) */}
            <nav className="fixed top-0 inset-x-0 z-50 bg-[#060606]/90 backdrop-blur-md border-b border-white/5 transition-all px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3 w-48">
                    <div className="h-8 w-8 rounded-lg bg-foreground text-background flex items-center justify-center shadow-lg">
                        <Bot className="h-5 w-5" />
                    </div>
                    <span className="font-bold text-xl tracking-tight text-foreground drop-shadow-sm">SYNCSPHERE</span>
                </div>

                <div className="hidden lg:flex items-center justify-center gap-6 font-medium text-sm text-muted-foreground flex-1">
                    <Link href="/" className="hover:text-foreground transition-colors flex items-center gap-1.5"><Home className="h-4 w-4" /> Home</Link>
                    <ChevronRight className="h-4 w-4 text-muted-foreground/40" />
                    <span className="text-foreground font-bold flex items-center gap-1.5">Workflow Engine</span>
                </div>

                <div className="flex gap-4 items-center w-48 justify-end">
                    {!mounted ? (
                        <div className="w-9 h-9" />
                    ) : (
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                            className="text-muted-foreground hover:text-foreground rounded-full h-9 w-9"
                        >
                            {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                        </Button>
                    )}
                    <Link href="/dashboard">
                        <Button variant="ghost" className="text-muted-foreground hover:text-foreground hover:bg-muted font-bold tracking-tight">Open Dashboard <ArrowRight className="ml-2 h-4 w-4" /></Button>
                    </Link>
                </div>
            </nav>

            <main className="relative z-10 w-full pt-32 pb-4 px-6 md:px-12 max-w-[1400px] mx-auto flex flex-col min-h-screen">
                {/* Title Overlay Section */}
                <div className="flex flex-col items-start lg:items-start text-center lg:text-left max-w-3xl mb-8 relative z-20">
                    <div className="flex items-center gap-2 mb-4">
                        <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-ping absolute"></span>
                        <span className="flex h-2 w-2 rounded-full bg-emerald-500 relative"></span>
                        <span className="text-xs font-bold tracking-widest uppercase text-emerald-500">Live Orchestration</span>
                    </div>
                    <h1 className="text-4xl md:text-5xl font-black tracking-tight text-foreground mb-4">
                        WORKFLOW AUTOMATION
                    </h1>
                    <p className="text-lg text-muted-foreground font-medium max-w-2xl">
                        Design, visualize and execute intelligent workflows across your connected applications through our advanced AI engine.
                    </p>
                </div>

                {/* Interactive 3D Visualization */}
                <div className="flex-1 w-full flex items-center justify-center lg:justify-start min-h-[500px] relative animate-in fade-in duration-[1500ms] fill-mode-both z-10 lg:pl-16">
                    {/* Decorative glow behind 3D component */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-primary/5 rounded-full blur-3xl pointer-events-none" />

                    {/* 3D Visual container aligned left specifically to feature all connected nodes without clipping */}
                    <div className="relative w-full max-w-5xl h-full min-h-[600px] flex items-center justify-start xl:-translate-y-12">
                        <ThreeDHeroVisual />
                    </div>
                </div>
            </main>
        </div>
    );
}
