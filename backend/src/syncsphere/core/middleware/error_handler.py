from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
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
                "detail": {"message": exc.message},
                "meta": {
                    "request_id": correlation_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", None)
        detail_msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        code = "UNAUTHORIZED" if exc.status_code == 401 else ("BAD_REQUEST" if exc.status_code == 400 else f"HTTP_{exc.status_code}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": detail_msg,
                    "docs_url": f"https://docs.syncsphere.ai/errors/{code}"
                },
                "detail": detail_msg,
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
                "field": ".".join(str(loc) for loc in error.get("loc", []) if loc != "body"),
                "constraint": error.get("type", "unknown"),
                "message": error.get("msg", "Unknown error")
            })
            
        logger.error(
            f"Request validation failed: {errors}",
            extra={"errors": errors}
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
                "detail": {"message": "Request validation failed. " + str(errors)},
                "meta": {
                    "request_id": correlation_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
        )

    @app.exception_handler(Exception)
    async def catchall_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", None)
        
        import traceback
        tb = traceback.format_exc()

        logger.exception(
            "Unhandled system exception occurred",
            error=str(exc)
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(exc),
                    "details": {"traceback": tb},
                    "docs_url": "https://docs.syncsphere.ai/errors/INTERNAL_ERROR"
                },
                "detail": {"message": str(exc)},
                "meta": {
                    "request_id": correlation_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
        )
