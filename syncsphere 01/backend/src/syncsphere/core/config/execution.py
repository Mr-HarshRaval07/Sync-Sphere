from pydantic import BaseModel

class ExecutionConfig(BaseModel):
    """Workflow runner timeouts and retry configurations."""
    default_timeout: int = 3600
    max_retries: int = 3
    checkpoint_enabled: bool = True
    reflection_enabled: bool = True
    approval_enabled: bool = True
