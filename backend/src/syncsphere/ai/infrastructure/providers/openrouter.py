import time
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

# ---------------------------------------------------------------------------
# Fallback configuration – only touched inside this file.
# ---------------------------------------------------------------------------

FALLBACK_MODEL = "openrouter/free"

# Keywords in a 400 response body that indicate the *model* is the problem,
# not the request payload.  All checked case-insensitively.
_MODEL_UNAVAILABLE_PHRASES = (
    "model not found",
    "model is not available",
    "model unavailable",
    "no endpoints",
    "invalid model",
    "unknown model",
    "model does not exist",
)


def _is_retryable_error(status_code: int, response_text: str) -> bool:
    """
    Return True when the error is transient or model-specific and a retry
    with a different model may succeed.

    Triggers:
      - HTTP 429  (rate limit / quota)
      - HTTP 5xx  (provider-side server errors)
      - HTTP 400  ONLY when the body signals the model is missing/invalid
    """
    if status_code == 429:
        return True
    if 500 <= status_code <= 599:
        return True
    if status_code == 400:
        body_lower = response_text.lower()
        return any(phrase in body_lower for phrase in _MODEL_UNAVAILABLE_PHRASES)
    return False


class OpenRouterProviderAdapter(AIProvider):
    """
    OpenRouterProviderAdapter communicates with OpenRouter's
    OpenAI-compatible chat completions API.

    Automatic fallback
    ------------------
    If the primary model returns a retryable error (429, 5xx, or a 400
    that signals the model is unavailable), the adapter makes **exactly one**
    additional attempt using ``openrouter/free``.  The fallback is completely
    transparent to every caller — the returned ``ChatResponse`` looks identical.
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

    # ------------------------------------------------------------------
    # Internal single-attempt helper (no retry logic here)
    # ------------------------------------------------------------------

    async def _attempt_chat(
        self,
        url: str,
        headers: Dict[str, str],
        model_name: str,
        messages: List[Dict[str, Any]],
        settings: InferenceSettings,
    ) -> ChatResponse:
        """
        Make a single HTTP POST to the OpenRouter completions endpoint and
        parse the response.  Raises ``ProviderOfflineException`` on any error.
        """
        payload = self._build_payload(
            model_name=model_name,
            messages=messages,
            settings=settings,
            stream=False,
        )

        logger.info(
            "OPENROUTER CALL START | Provider: openrouter | Selected Model: %s | Payload Model: %s | URL: %s",
            model_name, payload.get("model"), url
        )

        http_start = time.perf_counter()
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                http_ms = (time.perf_counter() - http_start) * 1000.0

                logger.info(
                    "OPENROUTER CALL RESPONSE | Provider: openrouter | Model: %s | HTTP Status: %d | Body Snippet: %.200s",
                    model_name, response.status_code, response.text
                )

                if response.status_code != 200:
                    logger.error(
                        "OPENROUTER API FAILED | Provider: openrouter | Model: %s | HTTP Status: %d | Response Body: %s",
                        model_name, response.status_code, response.text
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
                prompt_tokens = usage_data.get("prompt_tokens", 0)
                completion_tokens = usage_data.get("completion_tokens", 0)
                total_tokens = usage_data.get("total_tokens", 0)

                if not total_tokens:
                    total_tokens = prompt_tokens + completion_tokens

                usage = TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                )

                logger.info("OPENROUTER RAW USAGE DUMP: %s", data.get("usage"))
                logger.info(
                    "PARSED ADAPTER USAGE: prompt=%s comp=%s total=%s",
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
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
                logger.exception("OpenRouter API failed (model=%s)", model_name)
                raise ProviderOfflineException("openrouter", str(e))

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def generate_chat(
        self,
        model_name: str,
        messages: List[Dict[str, Any]],
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None,
    ) -> ChatResponse:
        """
        Generate a chat response with automatic one-shot fallback.

        Flow:
          1. Try ``model_name`` (primary).
          2. If the primary fails with a retryable error, retry once with
             ``openrouter/free`` (fallback).
          3. If fallback also fails, re-raise the *original* exception so
             the caller sees a consistent error type.
        """
        url = api_url or self.DEFAULT_API_URL
        headers = self._build_headers(api_key)

        import asyncio
        backoff_delays = [2.0, 4.0, 8.0]
        max_rate_limit_attempts = len(backoff_delays) + 1  # Initial attempt + 3 exponential backoff retries

        for rate_limit_attempt in range(max_rate_limit_attempts):
            # ── Step 1: primary attempt ────────────────────────────────────
            logger.info("Trying primary model: %s (attempt %d/%d)", model_name, rate_limit_attempt + 1, max_rate_limit_attempts)
            primary_exc: Optional[ProviderOfflineException] = None
            primary_status: Optional[int] = None
            primary_body: str = ""

            try:
                result = await self._attempt_chat(url, headers, model_name, messages, settings)
                return result

            except ProviderOfflineException as exc:
                primary_exc = exc
                msg = str(exc)
                if msg.startswith("AI Provider 'openrouter' call failed: HTTP "):
                    try:
                        rest = msg.split("HTTP ", 1)[1]
                        primary_status = int(rest.split(":", 1)[0].strip())
                        primary_body = rest.split(":", 1)[1].strip() if ":" in rest else ""
                    except (ValueError, IndexError):
                        primary_status = None
                        primary_body = msg

            # ── Step 2: decide whether to fall back ───────────────────────
            should_fallback = False
            if primary_exc is not None:
                if primary_status is not None:
                    should_fallback = _is_retryable_error(primary_status, primary_body)
                else:
                    should_fallback = True

            if not should_fallback:
                raise primary_exc  # type: ignore[misc]

            # ── Step 3: fallback attempt ───────────────────────────────────
            logger.warning(
                "Primary model failed (model=%s), retrying with fallback: %s (attempt %d/%d)",
                model_name,
                FALLBACK_MODEL,
                rate_limit_attempt + 1,
                max_rate_limit_attempts,
            )

            fallback_exc: Optional[ProviderOfflineException] = None
            fallback_status: Optional[int] = None
            fallback_body: str = ""

            try:
                result = await self._attempt_chat(url, headers, FALLBACK_MODEL, messages, settings)
                logger.info(
                    "Fallback model succeeded (fallback=%s, original=%s)",
                    FALLBACK_MODEL,
                    model_name,
                )
                return result

            except ProviderOfflineException as f_exc:
                fallback_exc = f_exc
                msg = str(f_exc)
                if msg.startswith("AI Provider 'openrouter' call failed: HTTP "):
                    try:
                        rest = msg.split("HTTP ", 1)[1]
                        fallback_status = int(rest.split(":", 1)[0].strip())
                        fallback_body = rest.split(":", 1)[1].strip() if ":" in rest else ""
                    except (ValueError, IndexError):
                        fallback_status = None
                        fallback_body = msg

            # ── Step 4: Check if both failed due to HTTP 429 Rate Limit ──────
            is_primary_429 = (primary_status == 429) or ("429" in str(primary_exc)) or ("rate" in str(primary_exc).lower()) or ("quota" in str(primary_exc).lower())
            is_fallback_429 = (fallback_status == 429) or ("429" in str(fallback_exc)) or ("rate" in str(fallback_exc).lower()) or ("quota" in str(fallback_exc).lower())

            if (is_primary_429 or is_fallback_429) and rate_limit_attempt < len(backoff_delays):
                delay = backoff_delays[rate_limit_attempt]
                logger.warning(
                    "Rate limit (429) encountered on OpenRouter (primary=%s, fallback=%s). Waiting %.1fs before retry %d/%d...",
                    primary_status or "429", fallback_status or "429", delay, rate_limit_attempt + 1, len(backoff_delays)
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "Primary and fallback models failed (primary=%s, fallback=%s). Raising original exception.",
                    model_name,
                    FALLBACK_MODEL,
                )
                raise primary_exc  # type: ignore[misc]

        raise primary_exc  # type: ignore[misc]

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

        async with httpx.AsyncClient(timeout=120.0) as client:
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

        http_start_time = time.perf_counter()
        try:
            # generate_chat already handles primary → fallback internally.
            resp = await self.generate_chat(
                model_name=model_name,
                messages=modified_messages,
                settings=settings,
                api_key=api_key,
                api_url=api_url,
            )
            http_duration_ms = (time.perf_counter() - http_start_time) * 1000.0

            val_start = time.perf_counter()
            raw = resp.message_content.strip()

            if raw.startswith("```json"):
                raw = raw[7:]

            elif raw.startswith("```"):
                raw = raw[3:]

            if raw.endswith("```"):
                raw = raw[:-3]

            raw = raw.strip()

            parsed = json.loads(raw)
            val_duration_ms = (time.perf_counter() - val_start) * 1000.0

            return StructuredOutputResult(
                success=True,
                parsed_object=parsed,
                raw_output=raw,
                token_usage=resp.token_usage,
                cost_usage=resp.cost_usage,
                openrouter_http_ms=http_duration_ms,
                json_validation_ms=val_duration_ms,
            )

        except ProviderOfflineException:
            raise
        except Exception as e:
            # We want to know exactly what the model returned if it wasn't JSON
            raw_dump = locals().get("raw", "")
            logger.error(
                "\n==================================================\n"
                "AI DEBUG\n"
                f"provider=openrouter\n"
                f"model={model_name}\n"
                f"error={str(e)}\n"
                f"error_type={type(e)}\n"
                f"raw_received={raw_dump[:500]}\n"
                "==================================================\n"
            )

            # We pass the Exception name back in error_message so the router doesn't blindly think it's a provider HTTP error
            # If it's a JSON error, we will prefix it so it can be handled differently
            if isinstance(e, json.JSONDecodeError):
                safe_error = f"JSON parsing exception: {str(e)}"
            else:
                safe_error = str(e)

            return StructuredOutputResult(
                success=False,
                raw_output=raw_dump,
                error_message=safe_error,
            )