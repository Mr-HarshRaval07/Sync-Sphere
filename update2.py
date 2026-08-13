import re

file_path = r"d:\syncsphere 01\syncsphere 01\frontend\app\RootClient.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add activeSection state and useEffect
state_str = """    const [mounted, setMounted] = useState(false);
    const [activeSection, setActiveSection] = useState('home');

    useEffect(() => {
        setMounted(true);
        const handleScroll = () => {
            const sections = ['home', 'features', 'integrations', 'ai-models', 'mcp'];
            for (const section of [...sections].reverse()) {
                const el = document.getElementById(section);
                if (el && window.scrollY >= (el.offsetTop - 100)) {
                    setActiveSection(section);
                    break;
                }
            }
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);"""

content = re.sub(r'const \[mounted.*?\];', state_str, content, flags=re.DOTALL)

# 2. Add scrollToSection helper
scroll_helper = """
    const scrollToSection = (e: React.MouseEvent<HTMLAnchorElement>, id: string) => {
        e.preventDefault();
        const el = document.getElementById(id);
        if (el) {
            el.scrollIntoView({ behavior: 'smooth' });
            window.history.pushState(null, '', '#' + id);
        }
    };
"""
content = re.sub(r'return \(', scroll_helper + '\n    return (', content, 1)

# 3. Update active classes and onClick for nav links
nav_links_old = """                    <a href="#home" className="hover:text-foreground transition-all relative group">
                        Home
                        <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all group-hover:w-full"></span>
                    </a>
                    <a href="#features" className="hover:text-foreground transition-all relative group">
                        Features
                        <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all group-hover:w-full"></span>
                    </a>
                    <a href="#integrations" className="hover:text-foreground transition-all relative group">
                        Integrations
                        <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all group-hover:w-full"></span>
                    </a>
                    <a href="#mcp" className="hover:text-foreground transition-all relative group">
                        MCP
                        <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-primary transition-all group-hover:w-full"></span>
                    </a>"""

nav_links_new = """                    <a href="#home" onClick={(e) => scrollToSection(e, 'home')} className={`transition-all relative group ${activeSection === 'home' ? 'text-foreground' : 'hover:text-foreground'}`}>
                        Home
                        <span className={`absolute -bottom-1 left-0 h-0.5 bg-primary transition-all ${activeSection === 'home' ? 'w-full' : 'w-0 group-hover:w-full'}`}></span>
                    </a>
                    <a href="#features" onClick={(e) => scrollToSection(e, 'features')} className={`transition-all relative group ${activeSection === 'features' ? 'text-foreground' : 'hover:text-foreground'}`}>
                        Features
                        <span className={`absolute -bottom-1 left-0 h-0.5 bg-primary transition-all ${activeSection === 'features' ? 'w-full' : 'w-0 group-hover:w-full'}`}></span>
                    </a>
                    <a href="#integrations" onClick={(e) => scrollToSection(e, 'integrations')} className={`transition-all relative group ${activeSection === 'integrations' ? 'text-foreground' : 'hover:text-foreground'}`}>
                        Integrations
                        <span className={`absolute -bottom-1 left-0 h-0.5 bg-primary transition-all ${activeSection === 'integrations' ? 'w-full' : 'w-0 group-hover:w-full'}`}></span>
                    </a>
                    <a href="#ai-models" onClick={(e) => scrollToSection(e, 'ai-models')} className={`transition-all relative group ${activeSection === 'ai-models' ? 'text-foreground' : 'hover:text-foreground'}`}>
                        AI Models
                        <span className={`absolute -bottom-1 left-0 h-0.5 bg-primary transition-all ${activeSection === 'ai-models' ? 'w-full' : 'w-0 group-hover:w-full'}`}></span>
                    </a>
                    <a href="#mcp" onClick={(e) => scrollToSection(e, 'mcp')} className={`transition-all relative group ${activeSection === 'mcp' ? 'text-foreground' : 'hover:text-foreground'}`}>
                        MCP
                        <span className={`absolute -bottom-1 left-0 h-0.5 bg-primary transition-all ${activeSection === 'mcp' ? 'w-full' : 'w-0 group-hover:w-full'}`}></span>
                    </a>"""

content = content.replace(nav_links_old, nav_links_new)

# 4. Fix Logos with SimpleIcons or Lucide fallback mapping
old_logos = """                            {[
                                { name: 'GitHub', icon: '/github-svgrepo-com.svg' },
                                { name: 'Slack', icon: '/slack-svgrepo-com.svg' },
                                { name: 'Gmail', icon: '/gmail-svgrepo-com.svg' },
                                { name: 'Calendar', icon: '/google-calendar-svgrepo-com.svg' },
                                { name: 'Sheets', icon: '/google-sheets-svgrepo-com.svg' },
                                { name: 'Jira', icon: '/jira-svgrepo-com.svg' },
                                { name: 'MongoDB', icon: '/mongodb-svgrepo-com.svg' },
                                { name: 'Redis', icon: '/redis-svgrepo-com.svg' },
                                { name: 'FastAPI', icon: '/fastapi-svgrepo-com.svg' },
                                { name: 'OpenRouter', icon: '/openrouter-svgrepo-com.svg' },
                            ]"""

new_logos = """                            {[
                                { name: 'GitHub', icon: 'https://cdn.simpleicons.org/github/aaaaaa' },
                                { name: 'Slack', icon: 'https://cdn.simpleicons.org/slack/aaaaaa' },
                                { name: 'Gmail', icon: 'https://cdn.simpleicons.org/gmail/aaaaaa' },
                                { name: 'Calendar', icon: 'https://cdn.simpleicons.org/googlecalendar/aaaaaa' },
                                { name: 'Sheets', icon: 'https://cdn.simpleicons.org/googlesheets/aaaaaa' },
                                { name: 'Jira', icon: 'https://cdn.simpleicons.org/jira/aaaaaa' },
                                { name: 'MongoDB', icon: 'https://cdn.simpleicons.org/mongodb/aaaaaa' },
                                { name: 'Redis', icon: 'https://cdn.simpleicons.org/redis/aaaaaa' },
                                { name: 'FastAPI', icon: 'https://cdn.simpleicons.org/fastapi/aaaaaa' },
                            ]"""
content = content.replace(old_logos, new_logos)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated RootClient.tsx successfully")
