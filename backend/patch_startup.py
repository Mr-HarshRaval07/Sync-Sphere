import sys

with open('src/syncsphere/core/lifecycle/startup.py', 'r') as f:
    c = f.read()

target = """        if settings.ai.llm_provider not in gateway.provider_registry:
            logger.error(f"Startup Validation: Configured AI provider '{settings.ai.llm_provider}' is not registered in the AI gateway.")"""

repl = """        if settings.ai.llm_provider not in gateway.provider_registry:
            logger.error(f"Startup Validation: Configured AI provider '{settings.ai.llm_provider}' is not registered in the AI gateway.")
            raise ValueError(f"Configured AI provider {settings.ai.llm_provider} is not registered in the AI gateway.")"""

c = c.replace(target, repl)

with open('src/syncsphere/core/lifecycle/startup.py', 'w') as f:
    f.write(c)
