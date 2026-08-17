import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator

import httpx

from syncsphere.ai.domain.services.provider import AIProvider
from syncsphere.ai.domain.value_objects import (
    InferenceSettings,
    ChatResponse,
    CompletionResponse,
    StreamingChunk,
    StructuredOutputSchema,
    StructuredOutputResult,
    TokenUsage,
)
from syncsphere.ai.domain.exceptions import ProviderOfflineException


logger = logging.getLogger("syncsphere.ai.infrastructure.providers.openrouter")


class OpenRouterProviderAdapter(AIProvider):
    """
    OpenRouterProviderAdapter communicates with OpenRouter's
    OpenAI-compatible chat completions API.
    """

    DEFAULT_API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def _build_headers(self, api_key: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "SyncSphere AI",
        }

    def _build_payload(
        self,
        model_name: str,
        messages: List[Dict[str, Any]],
        settings: InferenceSettings,
        stream: bool = False,
    ) -> Dict[str, Any]:

        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": settings.temperature,
            "stream": stream,
        }

        if settings.max_tokens:
            payload["max_tokens"] = settings.max_tokens

        return payload

    async def generate_chat(
        self,
        model_name: str,
        messages: List[Dict[str, Any]],
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None,
    ) -> ChatResponse:

        url = api_url or self.DEFAULT_API_URL

        payload = self._build_payload(
            model_name=model_name,
            messages=messages,
            settings=settings,
            stream=False,
        )

        headers = self._build_headers(api_key)

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    logger.error(
                        "OpenRouter API failed. Provider=openrouter Model=%s Status=%s Response=%s",
                        model_name,
                        response.status_code,
                        response.text,
                    )

                    raise ProviderOfflineException(
                        "openrouter",
                        f"HTTP {response.status_code}: {response.text}",
                    )

                data = response.json()

                choices = data.get("choices", [])

                if not choices:
                    raise ProviderOfflineException(
                        "openrouter",
                        f"No response choices returned: {response.text}",
                    )

                message = choices[0].get("message", {})
                content = message.get("content", "")

                if isinstance(content, list):
                    content = "".join(
                        item.get("text", "")
                        for item in content
                        if isinstance(item, dict)
                    )

                usage_data = data.get("usage", {})

                usage = TokenUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                )

                return ChatResponse(
                    message_content=content,
                    role="assistant",
                    model_name=model_name,
                    provider_name="openrouter",
                    token_usage=usage,
                )

            except ProviderOfflineException:
                raise

            except Exception as e:
                logger.exception("OpenRouter API failed")

                raise ProviderOfflineException(
                    "openrouter",
                    str(e),
                )

    async def generate_completion(
        self,
        model_name: str,
        prompt: str,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None,
    ) -> CompletionResponse:

        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        chat_resp = await self.generate_chat(
            model_name=model_name,
            messages=messages,
            settings=settings,
            api_key=api_key,
            api_url=api_url,
        )

        return CompletionResponse(
            text=chat_resp.message_content,
            model_name=model_name,
            provider_name="openrouter",
            token_usage=chat_resp.token_usage,
            cost_usage=chat_resp.cost_usage,
        )

    async def generate_embedding(
        self,
        model_name: str,
        input_texts: List[str],
        api_key: str,
        api_url: Optional[str] = None,
    ) -> List[List[float]]:

        raise ProviderOfflineException(
            "openrouter",
            "OpenRouter embedding support is not configured. "
            "Continue using your existing embedding provider.",
        )

    async def stream_completion(
        self,
        model_name: str,
        prompt: str,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None,
    ) -> AsyncGenerator[StreamingChunk, None]:

        url = api_url or self.DEFAULT_API_URL

        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        payload = self._build_payload(
            model_name=model_name,
            messages=messages,
            settings=settings,
            stream=True,
        )

        headers = self._build_headers(api_key)

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream(
                    "POST",
                    url,
                    headers=headers,
                    json=payload,
                ) as response:

                    if response.status_code != 200:
                        error_text = await response.aread()

                        raise ProviderOfflineException(
                            "openrouter",
                            f"HTTP {response.status_code}: "
                            f"{error_text.decode(errors='ignore')}",
                        )

                    async for line in response.aiter_lines():

                        if not line:
                            continue

                        if line.startswith("data: "):
                            line = line[6:]

                        if line.strip() == "[DONE]":
                            break

                        try:
                            chunk_data = json.loads(line)

                            choices = chunk_data.get(
                                "choices",
                                [],
                            )

                            if not choices:
                                continue

                            delta = choices[0].get(
                                "delta",
                                {},
                            )

                            text = delta.get(
                                "content",
                                "",
                            )

                            if text:
                                yield StreamingChunk(
                                    delta_text=text
                                )

                        except json.JSONDecodeError:
                            continue

            except ProviderOfflineException:
                raise

            except Exception as e:
                logger.exception(
                    "OpenRouter streaming failed"
                )

                raise ProviderOfflineException(
                    "openrouter",
                    str(e),
                )

    async def structured_output(
        self,
        model_name: str,
        messages: List[Dict[str, Any]],
        schema: StructuredOutputSchema,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None,
    ) -> StructuredOutputResult:

        system_instruction = (
            "You are the SyncSphere AI workflow planner.\n\n"
            "Return ONLY valid JSON.\n"
            "Do not use Markdown.\n"
            "Do not wrap the JSON in ```json blocks.\n"
            "The JSON must follow this schema exactly:\n\n"
            f"{json.dumps(schema.json_schema, indent=2)}"
        )

        modified_messages = [
            {
                "role": "system",
                "content": system_instruction,
            }
        ] + messages

        try:
            resp = await self.generate_chat(
                model_name=model_name,
                messages=modified_messages,
                settings=settings,
                api_key=api_key,
                api_url=api_url,
            )

            raw = resp.message_content.strip()

            if raw.startswith("```json"):
                raw = raw[7:]

            elif raw.startswith("```"):
                raw = raw[3:]

            if raw.endswith("```"):
                raw = raw[:-3]

            raw = raw.strip()

            parsed = json.loads(raw)

            return StructuredOutputResult(
                success=True,
                parsed_object=parsed,
                raw_output=raw,
            )

        except Exception as e:

            logger.error(
                "OpenRouter structured output failed: %s",
                str(e),
            )

            return StructuredOutputResult(
                success=False,
                raw_output="",
                error_message=str(e),
            )