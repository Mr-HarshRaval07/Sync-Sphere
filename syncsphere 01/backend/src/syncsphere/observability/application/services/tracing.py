import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from syncsphere.observability.domain.entities.trace import Trace, TraceSpan
from syncsphere.observability.domain.repositories import TraceRepository
from syncsphere.shared_kernel.infrastructure.logging.context import get_correlation_id

class CorrelationManager:
    """Manages tracking correlation IDs across threads/coroutines."""
    def get_current_correlation_id(self) -> str:
        cid = get_correlation_id()
        return cid or str(uuid.uuid4())

class ContextPropagation:
    """Handles extracting and injecting tracing headers/metadata."""
    def extract_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        correlation_id = headers.get("x-correlation-id") or headers.get("x-request-id") or str(uuid.uuid4())
        span_id = headers.get("x-span-id") or str(uuid.uuid4())
        return {
            "correlation_id": correlation_id,
            "span_id": span_id,
            "parent_span_id": headers.get("x-parent-span-id")
        }

    def inject_context(self, correlation_id: str, span_id: str) -> Dict[str, str]:
        return {
            "x-correlation-id": correlation_id,
            "x-span-id": span_id
        }

class SpanBuilder:
    """Helper to build TraceSpan instances."""
    def build(
        self,
        name: str,
        correlation_id: str,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> TraceSpan:
        return TraceSpan(
            span_id=str(uuid.uuid4()),
            name=name,
            correlation_id=correlation_id,
            parent_span_id=parent_span_id,
            attributes=attributes
        )

class OpenTelemetryExporter:
    """Converts TraceSpans into OpenTelemetry-compliant JSON payloads for exports."""
    def export_spans(self, trace: Trace) -> List[Dict[str, Any]]:
        otel_spans = []
        for s in trace.spans:
            otel_spans.append({
                "traceId": trace.correlation_id,
                "spanId": s.span_id,
                "parentSpanId": s.parent_span_id or "",
                "name": s.name,
                "kind": "INTERNAL",
                "startTimeUnixNano": int(s.start_time.timestamp() * 1e9),
                "endTimeUnixNano": int(s.end_time.timestamp() * 1e9) if s.end_time else 0,
                "attributes": s.attributes,
                "status": {"code": "STATUS_CODE_OK" if s.status == "COMPLETED" else "STATUS_CODE_ERROR"}
            })
        return otel_spans

class TraceSampler:
    """Decides if trace should be sampled based on config or rules."""
    def should_sample(self, correlation_id: str) -> bool:
        # Default to 100% sampling for complete enterprise auditing
        return True

class DistributedTracer:
    def __init__(self, repo: TraceRepository) -> None:
        self.repo = repo
        self.builder = SpanBuilder()
        self.correlation = CorrelationManager()
        self.propagation = ContextPropagation()
        self.exporter = OpenTelemetryExporter()
        self.sampler = TraceSampler()

    async def start_span(
        self,
        org_id: str,
        name: str,
        correlation_id: str,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> TraceSpan:
        trace = await self.repo.get_by_correlation_id(org_id, correlation_id)
        if not trace:
            trace = Trace(org_id=org_id, correlation_id=correlation_id)
        
        span = self.builder.build(name, correlation_id, parent_span_id, attributes)
        trace.add_span(span)
        await self.repo.save(trace)
        return span

    async def complete_span(
        self,
        org_id: str,
        correlation_id: str,
        span_id: str,
        status: str = "COMPLETED",
        attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        trace = await self.repo.get_by_correlation_id(org_id, correlation_id)
        if trace:
            for s in trace.spans:
                if s.span_id == span_id:
                    s.complete(status, attributes)
                    break
            await self.repo.save(trace)

class TraceCollector:
    """Subscribes to events on EventBus and populates Distributed Traces."""
    def __init__(self, tracer: DistributedTracer) -> None:
        self.tracer = tracer

    async def collect_from_event(self, event_type: str, org_id: str, correlation_id: str, payload: Dict[str, Any]) -> None:
        # Use event information to automatically capture spans
        # E.g. execution.started starts an execution span, execution.completed completes it
        timestamp = datetime.utcnow()
        if "started" in event_type or "start" in event_type:
            await self.tracer.start_span(
                org_id=org_id,
                name=event_type,
                correlation_id=correlation_id,
                attributes={"payload": payload}
            )
        elif "completed" in event_type or "failed" in event_type or "cancelled" in event_type:
            trace = await self.tracer.repo.get_by_correlation_id(org_id, correlation_id)
            if trace and trace.spans:
                # Complete the last matching running span of this type
                for s in reversed(trace.spans):
                    if s.status == "RUNNING" and (s.name in event_type or event_type in s.name or "start" in s.name):
                        status = "COMPLETED" if "completed" in event_type else "FAILED"
                        await self.tracer.complete_span(
                            org_id=org_id,
                            correlation_id=correlation_id,
                            span_id=s.span_id,
                            status=status,
                            attributes={"end_payload": payload}
                        )
                        break
