from typing import List, Optional, Dict, Any
from datetime import datetime
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot

class TraceSpan:
    def __init__(
        self,
        span_id: str,
        name: str,
        correlation_id: str,
        parent_span_id: Optional[str] = None,
        status: str = "RUNNING",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        self.span_id = span_id
        self.name = name
        self.correlation_id = correlation_id
        self.parent_span_id = parent_span_id
        self.status = status
        self.start_time = start_time or datetime.utcnow()
        self.end_time = end_time
        self.attributes = attributes or {}

    def complete(self, status: str = "COMPLETED", attributes: Optional[Dict[str, Any]] = None) -> None:
        self.status = status
        self.end_time = datetime.utcnow()
        if attributes:
            self.attributes.update(attributes)

class Trace(AggregateRoot):
    def __init__(
        self,
        org_id: str,
        correlation_id: str,
        spans: Optional[List[TraceSpan]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.correlation_id = correlation_id
        self.spans = spans or []

    def add_span(self, span: TraceSpan) -> None:
        if not any(s.span_id == span.span_id for s in self.spans):
            self.spans.append(span)
