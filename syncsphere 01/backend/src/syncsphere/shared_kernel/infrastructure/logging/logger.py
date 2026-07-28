import logging.config
import sys
import structlog
from typing import Any, Dict
from syncsphere.core.config import settings, Environment
from syncsphere.shared_kernel.infrastructure.logging.context import (
    get_correlation_id,
    get_org_id,
)

def inject_contextvars(
    logger: Any, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Injects correlation_id and org_id contextvars into the log event."""
    correlation_id = get_correlation_id()
    org_id = get_org_id()
    
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    if org_id:
        event_dict["org_id"] = org_id
        
    return event_dict

def configure_logging() -> None:
    """
    Configures standard library logging and structlog to work together harmoniously.
    Applies JSON formatting in production and colored console output in local/test environments.
    """
    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Shared processors between standard logging and structlog
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        inject_contextvars,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.environment in (Environment.STAGING, Environment.PRODUCTION):
        # Production JSON logs
        processor = structlog.processors.JSONRenderer()
    else:
        # Development human-readable colored logs
        processor = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [processor],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        cache_logger_on_first_use=True,
    )

    # Redirect standard library logging to structlog
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_metadata,
                    processor,
                ],
                "foreign_pre_process_processors": shared_processors,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "plain",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": log_level,
            },
            "uvicorn.error": {
                "handlers": ["console"],
                "level": logging.INFO,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": logging.INFO,
                "propagate": False,
            },
        },
    })

def get_logger(name: str) -> Any:
    """Factory to retrieve a structured logger instance."""
    return structlog.get_logger(name)
