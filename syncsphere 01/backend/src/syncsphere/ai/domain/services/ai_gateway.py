from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from syncsphere.ai.domain.value_objects import (
    ModelSelectionPolicy,
    InferenceSettings,
    ChatResponse,
    CompletionResponse,
    StreamingChunk,
    StructuredOutputSchema,
    StructuredOutputResult,
    ToolCall,
)

class AIGateway(ABC):
    """Unified entry point interface for all AI/LLM bounded context interactions."""
    
    @abstractmethod
    async def generate_chat(
        self,
        org_id: str,
        messages: List[Dict[str, Any]],
        policy: ModelSelectionPolicy,
        settings: Optional[InferenceSettings] = None,
        correlation_id: Optional[str] = None
    ) -> ChatResponse:
        pass

    @abstractmethod
    async def generate_completion(
        self,
        org_id: str,
        prompt: str,
        policy: ModelSelectionPolicy,
        settings: Optional[InferenceSettings] = None,
        correlation_id: Optional[str] = None
    ) -> CompletionResponse:
        pass

    @abstractmethod
    async def generate_embedding(
        self,
        org_id: str,
        input_texts: List[str],
        correlation_id: Optional[str] = None
    ) -> List[List[float]]:
        pass

    @abstractmethod
    def stream_completion(
        self,
        org_id: str,
        prompt: str,
        policy: ModelSelectionPolicy,
        settings: Optional[InferenceSettings] = None,
        correlation_id: Optional[str] = None
    ) -> AsyncGenerator[StreamingChunk, None]:
        pass

    @abstractmethod
    async def structured_output(
        self,
        org_id: str,
        messages: List[Dict[str, Any]],
        schema: StructuredOutputSchema,
        policy: ModelSelectionPolicy,
        settings: Optional[InferenceSettings] = None,
        correlation_id: Optional[str] = None
    ) -> StructuredOutputResult:
        pass
