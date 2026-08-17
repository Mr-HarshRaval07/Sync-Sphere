from syncsphere.shared_kernel.domain.domain_exception import (
    DomainException,
    EntityNotFoundException,
    ValidationException,
    ExternalServiceException,
    RateLimitException
)

class ModelNotFoundException(EntityNotFoundException):
    """Raised when an requested model identifier is not configured or active (HTTP 404)."""
    def __init__(self, model_name: str) -> None:
        super().__init__(
            code="MODEL_NOT_FOUND",
            message=f"AI Model '{model_name}' could not be resolved or is currently inactive.",
            details={"model_name": model_name}
        )

class ProviderOfflineException(ExternalServiceException):
    """Raised when an LLM provider endpoint times out or returns HTTP 5xx errors (HTTP 502)."""
    def __init__(self, provider_name: str, message: str) -> None:
        super().__init__(
            code="PROVIDER_OFFLINE",
            message=f"AI Provider '{provider_name}' call failed: {message}",
            details={"provider_name": provider_name}
        )

class PromptCompilationException(ValidationException):
    """Raised when rendering a versioned prompt with incorrect context parameters (HTTP 422)."""
    def __init__(self, template_name: str, message: str) -> None:
        super().__init__(
            code="PROMPT_COMPILATION_FAILED",
            message=f"Prompt template '{template_name}' rendering failed: {message}",
            details={"template_name": template_name}
        )

class StructuredOutputValidationException(ValidationException):
    """Raised when the LLM output violates Pydantic or JSON schema rules (HTTP 422)."""
    def __init__(self, schema_name: str, raw_output: str, error_message: str) -> None:
        super().__init__(
            code="STRUCTURED_OUTPUT_VALIDATION_FAILED",
            message=f"Structured output schema '{schema_name}' validation failed: {error_message}",
            details={"schema_name": schema_name, "raw_output": raw_output}
        )

class InferenceQuotaExceededException(RateLimitException):
    """Raised when organization daily token or cost quotas are exceeded (HTTP 429)."""
    def __init__(self, org_id: str, quota_limit: float, current_usage: float) -> None:
        super().__init__(
            code="INFERENCE_QUOTA_EXCEEDED",
            message=f"Organization '{org_id}' inference usage quota exceeded. Limit: {quota_limit}, current usage: {current_usage}",
            details={"org_id": org_id, "quota_limit": quota_limit, "current_usage": current_usage}
        )
