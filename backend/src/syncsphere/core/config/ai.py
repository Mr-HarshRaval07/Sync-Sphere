from pydantic import BaseModel, SecretStr

class AIConfig(BaseModel):
    """LLM provider and Embedding generator settings."""
    llm_provider: str = "openai"
    llm_api_key: SecretStr = SecretStr("mock-api-key-for-local-dev")
    llm_model: str = "gpt-4o"
    llm_max_tokens: int = 4096

    embedding_provider: str = "openai"
    embedding_api_key: SecretStr = SecretStr("mock-api-key-for-local-dev")
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
