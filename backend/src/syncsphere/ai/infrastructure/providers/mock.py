import asyncio
import json
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

class MockAIProvider(AIProvider):
    """
    MockAIProvider implements the abstract AIProvider interface to support unit and
    integration testing of the gateway routing and prompt compiling.
    """
    def __init__(self, mock_response_text: str = "This is a mock assistant response.") -> None:
        self.mock_response_text = mock_response_text

    async def generate_chat(
        self,
        model_name: str,
        messages: List[Dict[str, Any]],
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> ChatResponse:
        # Simulate small network latency
        await asyncio.sleep(0.01)
        
        # Estimate tokens usage
        prompt_words = sum(len(str(m.get("content", "")).split()) for m in messages)
        prompt_tokens = int(prompt_words * 1.5)
        completion_tokens = int(len(self.mock_response_text.split()) * 1.5)
        
        return ChatResponse(
            message_content=self.mock_response_text,
            role="assistant",
            model_name=model_name,
            provider_name="mock",
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            ),
            cost_usage=CostUsage(
                prompt_cost=prompt_tokens * 0.00001,
                completion_cost=completion_tokens * 0.00003,
                total_cost=(prompt_tokens * 0.00001) + (completion_tokens * 0.00003)
            )
        )

    async def generate_completion(
        self,
        model_name: str,
        prompt: str,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> CompletionResponse:
        await asyncio.sleep(0.01)
        
        prompt_tokens = int(len(prompt.split()) * 1.5)
        completion_tokens = int(len(self.mock_response_text.split()) * 1.5)
        
        return CompletionResponse(
            text=self.mock_response_text,
            model_name=model_name,
            provider_name="mock",
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            ),
            cost_usage=CostUsage(
                prompt_cost=prompt_tokens * 0.00001,
                completion_cost=completion_tokens * 0.00003,
                total_cost=(prompt_tokens * 0.00001) + (completion_tokens * 0.00003)
            )
        )

    async def generate_embedding(
        self,
        model_name: str,
        input_texts: List[str],
        api_key: str,
        api_url: Optional[str] = None
    ) -> List[List[float]]:
        await asyncio.sleep(0.01)
        # Return a mock 1536 float embedding vector for each input
        return [[0.1] * 1536 for _ in input_texts]

    async def stream_completion(
        self,
        model_name: str,
        prompt: str,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> AsyncGenerator[StreamingChunk, None]:
        # Split mock response into words to stream in chunks
        words = self.mock_response_text.split()
        for idx, word in enumerate(words):
            await asyncio.sleep(0.005)
            # Add trailing space to simulate real text chunking
            delta = word + (" " if idx < len(words) - 1 else "")
            
            # Yield token usage metrics only on final chunk
            finish_reason = "stop" if idx == len(words) - 1 else None
            yield StreamingChunk(delta_text=delta, finish_reason=finish_reason)

    async def structured_output(
        self,
        model_name: str,
        messages: List[Dict[str, Any]],
        schema: StructuredOutputSchema,
        settings: InferenceSettings,
        api_key: str,
        api_url: Optional[str] = None
    ) -> StructuredOutputResult:
        await asyncio.sleep(0.01)
        
        # Inspect messages for prior retry failure injections
        # If the last message contains validation failure guidance, fix and return success JSON.
        last_user_msg = messages[-1].get("content", "")
        if "violated" in last_user_msg or "error" in last_user_msg.lower():
            # Auto-correction path: construct a valid mock JSON dictionary matching requested schema
            mock_json_content = {}
            for field_name, field_props in schema.json_schema.get("properties", {}).items():
                t = field_props.get("type", "string")
                if t == "integer" or t == "number":
                    mock_json_content[field_name] = 42
                elif t == "boolean":
                    mock_json_content[field_name] = True
                else:
                    mock_json_content[field_name] = "corrected_mock_val"
                    
            raw_text = json.dumps(mock_json_content)
            return StructuredOutputResult(
                success=True,
                parsed_object=mock_json_content,
                raw_output=raw_text
            )
            
        # By default, trigger a single validation failure if it's the first attempt,
        # to test the auto-retry validation loop in the gateway!
        # But wait, to check standard successful structured outputs as well:
        # if the user specifically asked for success or if we are not testing retries, return valid json
        # Let's inspect the system/user instruction to determine.
        if "test_failure_path" in str(messages):
            # Return invalid json
            return StructuredOutputResult(
                success=False,
                raw_output="{invalid_json_missing_quotes}",
                error_message="Expecting property name enclosed in double quotes: line 1 column 2 (char 1)"
            )
            
        # Standard path: generate matching mock schema values
        mock_json_content = {}
        for field_name, field_props in schema.json_schema.get("properties", {}).items():
            t = field_props.get("type", "string")
            if t == "integer" or t == "number":
                mock_json_content[field_name] = 100
            elif t == "boolean":
                mock_json_content[field_name] = False
            else:
                mock_json_content[field_name] = "mock_value"
                
        raw_text = json.dumps(mock_json_content)
        return StructuredOutputResult(
            success=True,
            parsed_object=mock_json_content,
            raw_output=raw_text
        )
