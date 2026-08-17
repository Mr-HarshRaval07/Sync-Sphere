from pydantic import BaseModel

class LoggingConfig(BaseModel):
    """Logging settings for standard and structured output."""
    level: str = "INFO"
    format_json: bool = False
