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
    CostUsage,
)
from syncsphere.ai.domain.exceptions import ProviderOfflineException

logger = logging.getLogger("syncsphere.ai.infrastructure.providers.openai")

class OpenAIProviderAdapter(AIProvider):
    """
    OpenAIProviderAdapter communicates directly with the OpenAI chat completion
    and embedding REST APIs via standard async HTTP requests.
    """
    
    async def generate_chat(
        self,
        model_name: str,
        messages: List[Dict[str, Any]],
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> ChatResponse:
        url = api_url or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": settings.temperature,
            "top_p": settings.top_p,
            "presence_penalty": settings.presence_penalty,
            "frequency_penalty": settings.frequency_penalty
        }
        if settings.max_tokens:
            payload["max_tokens"] = settings.max_tokens
        if settings.json_output:
            payload["response_format"] = {"type": "json_object"}
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    raise ProviderOfflineException(
                        "openai",
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                usage_data = data.get("usage", {})
                
                usage = TokenUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0)
                )
                
                return ChatResponse(
                    message_content=content,
                    role="assistant",
                    model_name=model_name,
                    provider_name="openai",
                    token_usage=usage
                )
            except Exception as e:
                logger.error("OpenAI API call failed: %s", str(e))
                if isinstance(e, ProviderOfflineException):
                    raise e
                raise ProviderOfflineException("openai", str(e))

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
            provider_name="openai",
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
        url = api_url or "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_name,
            "input": input_texts
        }
        
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    raise ProviderOfflineException("openai", f"Embed HTTP {response.status_code}: {response.text}")
                    
                data = response.json()
                return [item["embedding"] for item in data["data"]]
            except Exception as e:
                if isinstance(e, ProviderOfflineException):
                    raise e
                raise ProviderOfflineException("openai", str(e))

    async def stream_completion(
        self,
        model_name: str,
        prompt: str,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> AsyncGenerator[StreamingChunk, None]:
        url = api_url or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": settings.temperature,
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        raise ProviderOfflineException("openai", f"Stream HTTP {response.status_code}")
                        
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        
                        raw_data = line[6:].strip()
                        if raw_data == "[DONE]":
                            break
                            
                        try:
                            chunk_data = json.loads(raw_data)
                            choices = chunk_data.get("choices", [])
                            if not choices:
                                continue
                                
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            finish_reason = choices[0].get("finish_reason")
                            
                            yield StreamingChunk(
                                delta_text=content,
                                finish_reason=finish_reason
                            )
                        except Exception:
                            continue
            except Exception as e:
                logger.error("OpenAI stream failed: %s", str(e))
                raise ProviderOfflineException("openai", str(e))

    async def structured_output(
        self,
        model_name: str,
        messages: List[Dict[str, Any]],
        schema: StructuredOutputSchema,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> StructuredOutputResult:
        url = api_url or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Format payload utilizing OpenAI JSON Schema Structured Output format
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": settings.temperature,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.schema_name,
                    "strict": schema.strict,
                    "schema": schema.json_schema
                }
            }
        }
        
        async with httpx.AsyncClient(timeout=45.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    return StructuredOutputResult(
                        success=False,
                        raw_output="",
                        error_message=f"HTTP {response.status_code}: {response.text}"
                    )
                    
                data = response.json()
                raw_text = data["choices"][0]["message"]["content"]
                
                # Attempt to parse json structure
                try:
                    parsed = json.loads(raw_text)
                    return StructuredOutputResult(
                        success=True,
                        parsed_object=parsed,
                        raw_output=raw_text
                    )
                except json.JSONDecodeError as decode_err:
                    return StructuredOutputResult(
                        success=False,
                        raw_output=raw_text,
                        error_message=f"JSON Decode Error: {str(decode_err)}"
                    )
            except Exception as e:
                return StructuredOutputResult(
                    success=False,
                    raw_output="",
                    error_message=f"Request failed: {str(e)}"
                )
