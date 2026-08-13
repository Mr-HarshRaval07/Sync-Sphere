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

logger = logging.getLogger("syncsphere.ai.infrastructure.providers.ollama")

class OllamaProviderAdapter(AIProvider):
    """
    OllamaProviderAdapter communicates with local Ollama service.
    """
    async def generate_chat(
        self,
        model_name: str,
        messages: List[Dict[str, Any]],
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> ChatResponse:
        url = (api_url or "http://localhost:11434").rstrip("/") + "/api/chat"
        
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": settings.temperature
            }
        }
        if settings.json_output:
            payload["format"] = "json"
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    raise ProviderOfflineException("ollama", f"HTTP {response.status_code}")
                    
                data = response.json()
                content = data["message"]["content"]
                
                # Ollama returns token count parameters in response
                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                
                usage = TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens
                )
                
                return ChatResponse(
                    message_content=content,
                    role="assistant",
                    model_name=model_name,
                    provider_name="ollama",
                    token_usage=usage
                )
            except Exception as e:
                logger.error("Ollama connection failed: %s", str(e))
                if isinstance(e, ProviderOfflineException):
                    raise e
                raise ProviderOfflineException("ollama", str(e))

    async def generate_completion(
        self,
        model_name: str,
        prompt: str,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> CompletionResponse:
        url = (api_url or "http://localhost:11434").rstrip("/") + "/api/generate"
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": settings.temperature
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    raise ProviderOfflineException("ollama", f"HTTP {response.status_code}")
                    
                data = response.json()
                text = data["response"]
                
                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                
                usage = TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens
                )
                
                return CompletionResponse(
                    text=text,
                    model_name=model_name,
                    provider_name="ollama",
                    token_usage=usage
                )
            except Exception as e:
                if isinstance(e, ProviderOfflineException):
                    raise e
                raise ProviderOfflineException("ollama", str(e))

    async def generate_embedding(
        self,
        model_name: str,
        input_texts: List[str],
        api_key: str,
        api_url: Optional[str] = None
    ) -> List[List[float]]:
        url = (api_url or "http://localhost:11434").rstrip("/") + "/api/embeddings"
        
        vectors = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            for text in input_texts:
                payload = {
                    "model": model_name,
                    "prompt": text
                }
                try:
                    response = await client.post(url, json=payload)
                    if response.status_code != 200:
                        raise ProviderOfflineException("ollama", f"HTTP {response.status_code}")
                    data = response.json()
                    vectors.append(data["embedding"])
                except Exception as e:
                    raise ProviderOfflineException("ollama", str(e))
        return vectors

    async def stream_completion(
        self,
        model_name: str,
        prompt: str,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> AsyncGenerator[StreamingChunk, None]:
        url = (api_url or "http://localhost:11434").rstrip("/") + "/api/generate"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        raise ProviderOfflineException("ollama", "Ollama stream failed")
                        
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk_data = json.loads(line)
                            yield StreamingChunk(
                                delta_text=chunk_data.get("response", ""),
                                finish_reason="stop" if chunk_data.get("done") else None
                            )
                        except Exception:
                            continue
            except Exception as e:
                raise ProviderOfflineException("ollama", str(e))

    async def structured_output(
        self,
        model_name: str,
        messages: List[Dict[str, Any]],
        schema: StructuredOutputSchema,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> StructuredOutputResult:
        # Prompt enforce for Ollama JSON outputs
        system_instruction = f"Output ONLY JSON matching structure: {json.dumps(schema.json_schema)}"
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
