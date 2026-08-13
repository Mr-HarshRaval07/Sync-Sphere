import re

file_path = r"d:\syncsphere 01\syncsphere 01\frontend\shared\components\ThreeDHeroVisual.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_svg_lines = """                        <g filter="url(#glow)">
                            {/* Vertical core pipeline */}
                            <path d="M 350 50 L 350 130" fill="none" stroke="url(#lineGrad)" strokeWidth="3" strokeDasharray="6 6" className="animate-[dash_20s_linear_infinite]" />
                            <path d="M 350 130 L 350 210" fill="none" stroke="url(#lineGrad)" strokeWidth="3" strokeDasharray="6 6" className="animate-[dash_20s_linear_infinite]" />
                            <path d="M 350 210 L 350 290" fill="none" stroke="url(#lineGrad)" strokeWidth="3" strokeDasharray="6 6" className="animate-[dash_20s_linear_infinite]" />
                            
                            {/* Side connection to Workflow */}
                            <path d="M 220 290 L 350 290" fill="none" stroke="url(#lineGrad)" strokeWidth="3" strokeDasharray="6 6" className="animate-[dash_20s_linear_infinite]" />
                            
                            <path d="M 350 290 L 350 370" fill="none" stroke="url(#lineGrad)" strokeWidth="3" strokeDasharray="6 6" className="animate-[dash_20s_linear_infinite]" />
                            <path d="M 350 370 L 350 450" fill="none" stroke="url(#lineGrad)" strokeWidth="3" strokeDasharray="6 6" className="animate-[dash_20s_linear_infinite]" />
                            
                            {/* Left Flank Integrations */}
                            <path d="M 350 450 Q 275 465 200 480" fill="none" stroke="url(#lineGrad)" strokeWidth="2" strokeDasharray="4 4" className="animate-[dash_20s_linear_infinite]" />
                            <path d="M 350 450 Q 235 450 120 450" fill="none" stroke="url(#lineGrad)" strokeWidth="2" strokeDasharray="4 4" className="animate-[dash_20s_linear_infinite]" />
                            <path d="M 350 450 Q 205 415 60 380" fill="none" stroke="url(#lineGrad)" strokeWidth="2" strokeDasharray="4 4" className="animate-[dash_20s_linear_infinite]" />
                            <path d="M 350 450 Q 205 475 60 500" fill="none" stroke="url(#lineGrad)" strokeWidth="2" strokeDasharray="4 4" className="animate-[dash_20s_linear_infinite]" />
                            <path d="M 350 450 Q 235 505 120 560" fill="none" stroke="url(#lineGrad)" strokeWidth="2" strokeDasharray="4 4" className="animate-[dash_20s_linear_infinite]" />
                            <path d="M 350 450 Q 290 510 230 570" fill="none" stroke="url(#lineGrad)" strokeWidth="2" strokeDasharray="4 4" className="animate-[dash_20s_linear_infinite]" />

                            {/* Right Flank Integrations */}
                            <path d="M 350 450 Q 425 465 500 480" fill="none" stroke="url(#lineGrad)" strokeWidth="2" strokeDasharray="4 4" className="animate-[dash_20s_linear_infinite]" />
                            <path d="M 350 450 Q 465 450 580 450" fill="none" stroke="url(#lineGrad)" strokeWidth="2" strokeDasharray="4 4" className="animate-[dash_20s_linear_infinite]" />
                            <path d="M 350 450 Q 495 415 640 380" fill="none" stroke="url(#lineGrad)" strokeWidth="2" strokeDasharray="4 4" className="animate-[dash_20s_linear_infinite]" />
                            <path d="M 350 450 Q 495 475 640 500" fill="none" stroke="url(#lineGrad)" strokeWidth="2" strokeDasharray="4 4" className="animate-[dash_20s_linear_infinite]" />
                            <path d="M 350 450 Q 465 505 580 560" fill="none" stroke="url(#lineGrad)" strokeWidth="2" strokeDasharray="4 4" className="animate-[dash_20s_linear_infinite]" />

                            {/* Final completion paths */}
                            <path d="M 350 450 L 350 540" fill="none" stroke="url(#lineGrad)" strokeWidth="3" strokeDasharray="6 6" className="animate-[dash_20s_linear_infinite]" />
                            <path d="M 350 540 L 350 620" fill="none" stroke="url(#lineGrad)" strokeWidth="3" strokeDasharray="6 6" className="animate-[dash_20s_linear_infinite]" />
                        </g>"""

content = re.sub(r'<g filter="url\(#glow\)".*?</g>', new_svg_lines, content, flags=re.DOTALL)

new_nodes = """{/* 3D Nodes Core Vertical */}
                <Node icon={<User className="w-6 h-6 text-white" />} label="USER" delay={0.1} x={350} y={50} />
                <Node icon={<Bot className="w-6 h-6 text-white" />} label="AI PLANNER" delay={0.2} x={350} y={130} isMain href="/dashboard/ai-models" />
                <Node icon={<Cog className="w-6 h-6 text-white" />} label="TASK ENGINE" delay={0.3} x={350} y={210} />
                <Node icon={<GitFork className="w-6 h-6 text-white" />} label="WORKFLOW BUILDER" delay={0.4} x={350} y={290} isMain href="/dashboard/workflows" />
                <Node icon={<FileText className="w-6 h-6 text-white" />} label="PROMPT TEMPLATES" delay={0.3} x={220} y={290} href="/dashboard/prompts" />
                <Node icon={<ThumbsUp className="w-6 h-6 text-white" />} label="HUMAN APPROVALS" delay={0.5} x={350} y={370} href="/dashboard/approvals" />
                <Node icon={<Play className="w-6 h-6 text-white" />} label="EXECUTION RUNS" delay={0.6} x={350} y={450} isMain href="/dashboard/executions" />
                <Node icon={<Activity className="w-6 h-6 text-white" />} label="OBSERVABILITY" delay={0.7} x={350} y={540} href="/dashboard/observability" />
                <Node icon={<CheckCircle2 className="w-6 h-6 text-emerald-400" />} label="EXECUTION COMPLETE" delay={0.8} x={350} y={620} isMain />

                {/* Left Flank Integrations */}
                <Node icon={<img src="/github-svgrepo-com.svg" className="w-6 h-6 object-contain invert" alt="GitHub" />} label="GITHUB" delay={0.85} x={200} y={480} href="/dashboard/connectors" />
                <Node icon={<Layout className="w-6 h-6 text-white" />} label="JIRA" delay={0.9} x={120} y={450} href="/dashboard/connectors" />
                <Node icon={<img src="/slack-svgrepo-com.svg" className="w-6 h-6 object-contain" alt="Slack" />} label="SLACK" delay={0.95} x={60} y={380} href="/dashboard/connectors" />
                <Node icon={<img src="/gmail-svgrepo-com.svg" className="w-6 h-6 object-contain" alt="Gmail" />} label="GMAIL" delay={1.0} x={60} y={500} href="/dashboard/connectors" />
                <Node icon={<img src="/google-calendar-svgrepo-com.svg" className="w-6 h-6 object-contain" alt="Calendar" />} label="GOOGLE CALENDAR" delay={1.05} x={120} y={560} href="/dashboard/connectors" />
                <Node icon={<img src="/google-sheets-svgrepo-com.svg" className="w-6 h-6 object-contain" alt="Sheets" />} label="GOOGLE SHEETS" delay={1.1} x={230} y={570} href="/dashboard/connectors" />

                {/* Right Flank Integrations */}
                <Node icon={<BrainCircuit className="w-6 h-6 text-white" />} label="OPENROUTER" delay={0.85} x={500} y={480} href="/dashboard/connectors" />
                <Node icon={<HardDrive className="w-6 h-6 text-white" />} label="REDIS" delay={0.9} x={580} y={450} href="/dashboard/connectors" />
                <Node icon={<Database className="w-6 h-6 text-white" />} label="MONGODB" delay={0.95} x={640} y={380} href="/dashboard/connectors" />
                <Node icon={<Server className="w-6 h-6 text-white" />} label="FASTAPI" delay={1.0} x={640} y={500} href="/dashboard/connectors" />
                <Node icon={<Network className="w-6 h-6 text-white" />} label="MCP SERVERS" delay={1.05} x={580} y={560} href="/dashboard/connectors" />"""

content = re.sub(r'\{/\* 3D Nodes Icons \*/\}.*?</motion\.div>', new_nodes + "\\n            </motion.div>", content, flags=re.DOTALL)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated ThreeDHeroVisual.tsx successfully")
