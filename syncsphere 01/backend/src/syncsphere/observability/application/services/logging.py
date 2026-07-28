from typing import Dict, Any, Optional, List
from datetime import datetime
from syncsphere.observability.domain.entities.log import StructuredLog
from syncsphere.observability.domain.repositories import LogRepository

class LogFormatter:
    """Formats log messages for stdout or export."""
    def format_log(self, log: StructuredLog) -> str:
        return f"[{log.timestamp.isoformat()}] [{log.level}] [{log.module}] correlation_id={log.correlation_id} org_id={log.org_id}: {log.message} - context={log.context_info}"

class LogEnricher:
    """Enriches log context metadata with tenant/correlation contexts."""
    def enrich(self, context_info: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        info = dict(context_info or {})
        info["env"] = "production"
        info["pid"] = 1
        return info

class CorrelationLogger:
    def __init__(self, logger: "StructuredLogger") -> None:
        self.logger = logger

    async def log(self, org_id: str, correlation_id: str, message: str, level: str = "INFO", module: str = "observability", context: Optional[Dict[str, Any]] = None) -> None:
        await self.logger.log(org_id, correlation_id, message, level, module, context)

class TenantLogger:
    def __init__(self, logger: "StructuredLogger") -> None:
        self.logger = logger

    async def log(self, org_id: str, message: str, level: str = "INFO", module: str = "observability", context: Optional[Dict[str, Any]] = None) -> None:
        # Generate or use correlation ID
        correlation_id = (context or {}).get("correlation_id", "N/A")
        await self.logger.log(org_id, correlation_id, message, level, module, context)

class AuditLogger:
    def __init__(self, logger: "StructuredLogger") -> None:
        self.logger = logger

    async def log_audit(self, org_id: str, correlation_id: str, action: str, actor: str, target: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        context = {
            "actor": actor,
            "target": target,
            "status": status,
            "action": action,
            "is_audit": True
        }
        if details:
            context.update(details)
        await self.logger.log(org_id, correlation_id, f"Audit Action: {action} on {target} by {actor} ended with status {status}", "INFO", "audit", context)


class StructuredLogger:
    """Main structured logging implementation."""
    def __init__(self, repo: LogRepository) -> None:
        self.repo = repo
        self.formatter = LogFormatter()
        self.enricher = LogEnricher()
        self.correlation = CorrelationLogger(self)
        self.tenant = TenantLogger(self)
        self.audit = AuditLogger(self)

    async def log(
        self,
        org_id: str,
        correlation_id: str,
        message: str,
        level: str = "INFO",
        module: str = "observability",
        context_info: Optional[Dict[str, Any]] = None
    ) -> StructuredLog:
        enriched_info = self.enricher.enrich(context_info)
        log_entry = StructuredLog(
            org_id=org_id,
            correlation_id=correlation_id,
            message=message,
            level=level,
            module=module,
            timestamp=datetime.utcnow(),
            context_info=enriched_info
        )
        await self.repo.save(log_entry)
        # Also print to python standard logger
        import logging
        py_logger = logging.getLogger(f"syncsphere.{module}")
        py_logger.log(getattr(logging, level, logging.INFO), self.formatter.format_log(log_entry))
        return log_entry
