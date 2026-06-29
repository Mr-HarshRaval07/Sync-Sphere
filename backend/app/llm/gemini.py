from google import genai

from app.core.config import settings
from app.llm.base import BaseLLM


class GeminiLLM(BaseLLM):

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def generate(self, prompt: str) -> str:

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        return response.text