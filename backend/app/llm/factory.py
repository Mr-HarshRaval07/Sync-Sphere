from app.core.config import settings
from app.llm.gemini import GeminiLLM


def get_llm():

    if settings.LLM_PROVIDER.lower() == "gemini":
        return GeminiLLM()

    raise ValueError("Unsupported LLM Provider")