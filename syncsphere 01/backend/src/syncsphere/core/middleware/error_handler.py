from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
from syncsphere.shared_kernel.domain.domain_exception import DomainException
from syncsphere.shared_kernel.infrastructure.logging.logger import get_logger

logger = get_logger("syncsphere.core.middleware.error_handler")

def register_error_handlers(app: FastAPI) -> None:
    """
    Registers global exception handlers for the FastAPI application.
    Converts domain-specific exceptions and validation errors into standardized JSON error envelopes.
    """
    
    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", None)
        
        logger.warning(
            "Domain exception occurred",
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "docs_url": f"https://docs.syncsphere.ai/errors/{exc.code}"
                },
                "meta": {
                    "request_id": correlation_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", None)
        
        errors = []
        for error in exc.errors():
            errors.append({
                "field": "".join(str(loc) for loc in error["loc"] if loc != "body"),
                "constraint": error["type"],
                "message": error["msg"]
            })
            
        logger.warning(
            "Request validation failed",
            errors=errors
        )
        
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {
                        "field_errors": errors
                    },
                    "docs_url": "https://docs.syncsphere.ai/errors/VALIDATION_ERROR"
                },
                "meta": {
                    "request_id": correlation_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
        )

    @app.exception_handler(Exception)
    async def catchall_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", None)
        
        logger.exception(
            "Unhandled system exception occurred",
            error=str(exc)
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected server error occurred.",
                    "details": {},
                    "docs_url": "https://docs.syncsphere.ai/errors/INTERNAL_ERROR"
                },
                "meta": {
                    "request_id": correlation_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
        )
