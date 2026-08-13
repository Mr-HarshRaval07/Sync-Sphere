import json
import logging
import httpx
from typing import List, Dict, Any, Optional, AsyncGenerator
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

logger = logging.getLogger("syncsphere.ai.infrastructure.providers.anthropic")

class AnthropicProviderAdapter(AIProvider):
    """
    AnthropicProviderAdapter communicates directly with the Anthropic Messages API.
    """
    async def generate_chat(
        self,
        model_name: str,
        messages: List[Dict[str, Any]],
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> ChatResponse:
        url = api_url or "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Anthropic messages format mapping
        anthropic_messages = []
        system_instruction = None
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                # System instructions go in the top-level parameters in Anthropic API
                system_instruction = content
            else:
                anthropic_messages.append({"role": role, "content": content})
                
        payload = {
            "model": model_name,
            "messages": anthropic_messages,
            "max_tokens": settings.max_tokens or 2048,
            "temperature": settings.temperature
        }
        if system_instruction:
            payload["system"] = system_instruction
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    raise ProviderOfflineException("anthropic", f"HTTP {response.status_code}: {response.text}")
                    
                data = response.json()
                content = data["content"][0]["text"]
                usage_data = data.get("usage", {})
                
                usage = TokenUsage(
                    prompt_tokens=usage_data.get("input_tokens", 0),
                    completion_tokens=usage_data.get("output_tokens", 0),
                    total_tokens=usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0)
                )
                
                return ChatResponse(
                    message_content=content,
                    role="assistant",
                    model_name=model_name,
                    provider_name="anthropic",
                    token_usage=usage
                )
            except Exception as e:
                logger.error("Anthropic API failed: %s", str(e))
                if isinstance(e, ProviderOfflineException):
                    raise e
                raise ProviderOfflineException("anthropic", str(e))

    async def generate_completion(
        self,
        model_name: str,
        prompt: str,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> CompletionResponse:
        messages = [{"role": "user", "content": prompt}]
        chat_resp = await self.generate_chat(model_name, messages, settings, api_key, api_url)
        return CompletionResponse(
            text=chat_resp.message_content,
            model_name=model_name,
            provider_name="anthropic",
            token_usage=chat_resp.token_usage,
            cost_usage=chat_resp.cost_usage
        )

    async def generate_embedding(
        self,
        model_name: str,
        input_texts: List[str],
        api_key: str,
        api_url: Optional[str] = None
    ) -> List[List[float]]:
        # Anthropic does not provide native embedding models; raise exception
        raise NotImplementedError("Anthropic does not support native text embedding generation.")

    async def stream_completion(
        self,
        model_name: str,
        prompt: str,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> AsyncGenerator[StreamingChunk, None]:
        url = api_url or "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": settings.max_tokens or 2048,
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        raise ProviderOfflineException("anthropic", f"Stream HTTP {response.status_code}")
                        
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        
                        raw_data = line[6:].strip()
                        try:
                            event_data = json.loads(raw_data)
                            event_type = event_data.get("type")
                            
                            if event_type == "content_block_delta":
                                delta_text = event_data["delta"].get("text", "")
                                yield StreamingChunk(delta_text=delta_text)
                            elif event_type == "message_delta":
                                yield StreamingChunk(delta_text="", finish_reason=event_data.get("delta", {}).get("stop_reason"))
                        except Exception:
                            continue
            except Exception as e:
                raise ProviderOfflineException("anthropic", str(e))

    async def structured_output(
        self,
        model_name: str,
        messages: List[Dict[str, Any]],
        schema: StructuredOutputSchema,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> StructuredOutputResult:
        # Structured output for Anthropic via standard system prompt coercion
        system_instruction = f"Output strictly a valid JSON object matching the JSON Schema: {json.dumps(schema.json_schema)}. Do NOT wrap in markdown block, do not include any preamble."
        
        modified_messages = [{"role": "system", "content": system_instruction}] + messages
        try:
            resp = await self.generate_chat(model_name, modified_messages, settings, api_key, api_url)
            parsed = json.loads(resp.message_content)
            return StructuredOutputResult(
                success=True,
                parsed_object=parsed,
                raw_output=resp.message_content
            )
        except Exception as e:
            return StructuredOutputResult(
                success=False,
                raw_output="",
                error_message=str(e)
            )
