'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Bot, Mail, Calendar, Grid, Database, Server, Plus, MessageSquare, AlertCircle, PlayCircle, Loader2 } from 'lucide-react';

const integrationNodes = [
    { id: 'github', name: 'GitHub', icon: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" /><path d="M9 18c-4.51 2-5-2-7-2" /></svg>, angle: 0 },
    { id: 'slack', name: 'Slack', icon: <MessageSquare className="h-6 w-6" />, angle: 36 },
    { id: 'gmail', name: 'Gmail', icon: <Mail className="h-6 w-6" />, angle: 72 },
    { id: 'calendar', name: 'Google Calendar', icon: <Calendar className="h-6 w-6" />, angle: 108 },
    { id: 'sheets', name: 'Google Sheets', icon: <Grid className="h-6 w-6" />, angle: 144 },
    { id: 'jira', name: 'Jira', icon: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m22 2l-7 7.01-7-7-4 4 11 11.01 11-11-4-4Z" /><path d="m2 22 7-7.01 7 7 4-4-11-11.01L2 18l1.72 1.72Z" /></svg>, angle: 180 },
    { id: 'mongodb', name: 'MongoDB', icon: <Database className="h-6 w-6" />, angle: 216 },
    { id: 'redis', name: 'Redis', icon: <Server className="h-6 w-6" />, angle: 252 },
    { id: 'mcp', name: 'MCP Servers', icon: <Bot className="h-6 w-6" />, angle: 288 },
    { id: 'future', name: 'Future Integrations', icon: <Plus className="h-6 w-6" />, angle: 324 },
];

export function ThreeDHeroVisual() {
    const [hoveredNode, setHoveredNode] = useState<string | null>(null);

    // Calculate node position on a circle
    const getPosition = (angleDeg: number, radius: number) => {
        const rad = (angleDeg - 90) * (Math.PI / 180);
        return {
            x: Math.cos(rad) * radius,
            y: Math.sin(rad) * radius,
        };
    };

    return (
        <div className="relative w-full h-full min-h-[500px] flex items-center justify-center p-8">
            <div className="relative w-[300px] h-[300px] sm:w-[450px] sm:h-[450px] md:w-[500px] md:h-[500px] flex items-center justify-center -translate-y-6">

                {/* SVG Connections */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ overflow: 'visible' }}>
                    <defs>
                        <radialGradient id="line-glow" cx="50%" cy="50%" r="50%">
                            <stop offset="0%" stopColor="rgba(56, 189, 248, 1)" />
                            <stop offset="100%" stopColor="rgba(56, 189, 248, 0)" />
                        </radialGradient>
                    </defs>
                    {integrationNodes.map((node, i) => {
                        const radius = typeof window !== 'undefined' && window.innerWidth < 640 ? 120 : 180;
                        const pos = getPosition(node.angle, radius);
                        // Ensure svg has correct relative center coordinate
                        const centerX = radius;
                        const centerY = radius;
                        const isHovered = hoveredNode === node.id || hoveredNode === 'center';

                        return (
                            <motion.line
                                key={`line-${i}`}
                                x1="50%"
                                y1="50%"
                                x2={`calc(50% + ${pos.x}px)`}
                                y2={`calc(50% + ${pos.y}px)`}
                                stroke={isHovered ? "rgba(56, 189, 248, 0.9)" : "rgba(56, 189, 248, 0.2)"}
                                strokeWidth={isHovered ? 2 : 1}
                                className="transition-all duration-300 ease-out"
                                initial={{ pathLength: 0, opacity: 0 }}
                                animate={{
                                    pathLength: 1,
                                    opacity: 1,
                                    strokeDasharray: isHovered ? ["10,5"] : ["0,0"]
                                }}
                                transition={{ duration: 1.5, delay: i * 0.1 }}
                                style={{ strokeLinecap: "round" }}
                            />
                        );
                    })}
                </svg>

                {/* Satellite Nodes */}
                {integrationNodes.map((node, i) => {
                    const radius = typeof window !== 'undefined' && window.innerWidth < 640 ? 120 : 190;
                    const pos = getPosition(node.angle, radius);
                    const isHovered = hoveredNode === node.id;

                    return (
                        <motion.div
                            key={node.id}
                            className="absolute z-20 flex flex-col items-center justify-center cursor-pointer"
                            style={{
                                x: pos.x,
                                y: pos.y,
                                marginLeft: -28, // width/2
                                marginTop: -28, // height/2
                            }}
                            initial={{ scale: 0, opacity: 0 }}
                            animate={{
                                scale: 1,
                                opacity: 1,
                                y: [pos.y - 5, pos.y + 5, pos.y - 5]
                            }}
                            transition={{
                                scale: { duration: 0.5, delay: 0.5 + i * 0.1 },
                                opacity: { duration: 0.5, delay: 0.5 + i * 0.1 },
                                y: { duration: 4, repeat: Infinity, ease: "easeInOut", delay: i * 0.2 }
                            }}
                            onMouseEnter={() => setHoveredNode(node.id)}
                            onMouseLeave={() => setHoveredNode(null)}
                        >
                            <motion.div
                                className={`w-14 h-14 rounded-2xl flex items-center justify-center backdrop-blur-xl border ${isHovered ? 'bg-[#0E1117] border-cyan-400 shadow-[0_0_20px_rgba(34,211,238,0.6)]' : 'bg-[#0E1117]/80 border-white/10 shadow-xl'}`}
                                animate={{ scale: isHovered ? 1.15 : 1 }}
                                transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                            >
                                <div className={`transition-colors duration-300 ${isHovered ? 'text-cyan-400' : 'text-slate-400'}`}>
                                    {node.icon}
                                </div>
                            </motion.div>

                            {/* Tooltip */}
                            <motion.div
                                className={`absolute top-full mt-3 bg-[#0E1117] border border-cyan-500/30 px-3 py-1.5 rounded-lg text-xs font-bold text-white shadow-lg flex items-center gap-1.5 whitespace-nowrap pointer-events-none transition-all duration-300`}
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: isHovered ? 1 : 0, y: isHovered ? 0 : -10 }}
                            >
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                {node.name} Connected
                            </motion.div>
                        </motion.div>
                    );
                })}

                {/* Central Node */}
                <motion.div
                    className="absolute z-30 flex flex-col items-center justify-center cursor-pointer"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 200, damping: 20, delay: 0.2 }}
                    onMouseEnter={() => setHoveredNode('center')}
                    onMouseLeave={() => setHoveredNode(null)}
                >
                    <motion.div
                        className={`w-28 h-28 sm:w-36 sm:h-36 rounded-[2rem] bg-[#0E1117] border backdrop-blur-xl flex flex-col items-center justify-center shadow-2xl relative overflow-hidden`}
                        animate={{
                            scale: hoveredNode === 'center' ? 1.05 : 1,
                            borderColor: hoveredNode === 'center' ? 'rgba(56, 189, 248, 0.8)' : 'rgba(255, 255, 255, 0.15)',
                            boxShadow: hoveredNode === 'center' ? '0 0 50px rgba(56, 189, 248, 0.4)' : '0 10px 40px rgba(0,0,0,0.5)'
                        }}
                        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                    >
                        {/* Internal Glow */}
                        <motion.div
                            className="absolute inset-0 bg-cyan-500/20 blur-2xl"
                            animate={{ opacity: hoveredNode === 'center' ? 1 : 0.5 }}
                        />
                        <Bot className="h-12 w-12 sm:h-14 sm:w-14 text-white mb-2 relative z-10" />
                        <span className="font-bold text-sm sm:text-base tracking-tight text-white relative z-10">SyncSphere AI</span>
                    </motion.div>
                </motion.div>

            </div>
        </div>
    );
}
