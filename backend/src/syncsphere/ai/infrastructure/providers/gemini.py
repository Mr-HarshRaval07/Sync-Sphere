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

logger = logging.getLogger("syncsphere.ai.infrastructure.providers.gemini")

class GeminiProviderAdapter(AIProvider):
    """
    GeminiProviderAdapter communicates directly with the Google Gemini API.
    """
    async def generate_chat(
        self,
        model_name: str,
        messages: List[Dict[str, Any]],
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> ChatResponse:
        model_clean = model_name if model_name.startswith("models/") else f"models/{model_name}"
        url = api_url or f"https://generativelanguage.googleapis.com/v1beta/{model_clean}:generateContent?key={api_key}"
        
        # Format messages for Gemini API
        contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            else:
                # Gemini roles: "user" or "model"
                gemini_role = "model" if role == "assistant" else "user"
                contents.append({"role": gemini_role, "parts": [{"text": content}]})
                
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": settings.temperature,
            }
        }
        if settings.max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = settings.max_tokens
        if system_instruction:
            payload["systemInstruction"] = system_instruction
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    raise ProviderOfflineException("gemini", f"HTTP {response.status_code}: {response.text}")
                    
                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise ProviderOfflineException("gemini", f"No response candidate returned: {response.text}")
                    
                content = candidates[0]["content"]["parts"][0]["text"]
                usage_data = data.get("usageMetadata", {})
                
                usage = TokenUsage(
                    prompt_tokens=usage_data.get("promptTokenCount", 0),
                    completion_tokens=usage_data.get("candidatesTokenCount", 0),
                    total_tokens=usage_data.get("totalTokenCount", 0)
                )
                
                return ChatResponse(
                    message_content=content,
                    role="assistant",
                    model_name=model_name,
                    provider_name="gemini",
                    token_usage=usage
                )
            except Exception as e:
                logger.error("Gemini API failed: %s", str(e))
                if isinstance(e, ProviderOfflineException):
                    raise e
                raise ProviderOfflineException("gemini", str(e))

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
            provider_name="gemini",
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
        # Assume embedding endpoint URL
        model_clean = model_name if model_name.startswith("models/") else f"models/{model_name}"
        url = api_url or f"https://generativelanguage.googleapis.com/v1beta/{model_clean}:embedContent?key={api_key}"
        
        # For simplicity, handle single string embeddings (Gemini supports batch but this covers simple calls)
        vectors = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            for text in input_texts:
                payload = {
                    "content": {
                        "parts": [{"text": text}]
                    }
                }
                try:
                    response = await client.post(url, json=payload)
                    if response.status_code != 200:
                        raise ProviderOfflineException("gemini", f"HTTP {response.status_code}")
                    data = response.json()
                    vectors.append(data["embedding"]["values"])
                except Exception as e:
                    raise ProviderOfflineException("gemini", str(e))
        return vectors

    async def stream_completion(
        self,
        model_name: str,
        prompt: str,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> AsyncGenerator[StreamingChunk, None]:
        # Google Gemini server streaming API endpoints use: streamGenerateContent
        model_clean = model_name if model_name.startswith("models/") else f"models/{model_name}"
        url = api_url or f"https://generativelanguage.googleapis.com/v1beta/{model_clean}:streamGenerateContent?key={api_key}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Gemini returns list of Candidates chunks, handle stream chunk
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        raise ProviderOfflineException("gemini", "Gemini streaming failed")
                        
                    async for line in response.aiter_lines():
                        if not line.strip() or line.strip() == "[" or line.strip() == "]":
                            continue
                        
                        clean_line = line.strip().rstrip(",")
                        try:
                            chunk_data = json.loads(clean_line)
                            candidate = chunk_data.get("candidates", [])[0]
                            text = candidate["content"]["parts"][0]["text"]
                            yield StreamingChunk(delta_text=text)
                        except Exception:
                            continue
            except Exception as e:
                raise ProviderOfflineException("gemini", str(e))

    async def structured_output(
        self,
        model_name: str,
        messages: List[Dict[str, Any]],
        schema: StructuredOutputSchema,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> StructuredOutputResult:
        # Prompt engineer Gemini to conform to schema structure
        system_instruction = f"Output ONLY valid JSON matching exactly this schema: {json.dumps(schema.json_schema)}. Do NOT wrap the response in markdown code blocks like ```json."
        modified_messages = [{"role": "system", "content": system_instruction}] + messages
        try:
            resp = await self.generate_chat(model_name, modified_messages, settings, api_key, api_url)
            
            # Clean markdown code blocks representing JSON before parsing
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
                token_usage=resp.token_usage,
                cost_usage=resp.cost_usage,
            )
        except Exception as e:
            return StructuredOutputResult(
                success=False,
                raw_output="",
                error_message=str(e)
            )
