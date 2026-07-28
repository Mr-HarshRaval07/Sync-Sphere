import asyncio
from typing import Dict, Set, Any, List
from fastapi import WebSocket
import logging

logger = logging.getLogger("syncsphere.observability.live_telemetry")

class WebSocketHub:
    """Manages active WebSockets scoped by tenant organization."""
    def __init__(self) -> None:
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, org_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if org_id not in self.active_connections:
            self.active_connections[org_id] = set()
        self.active_connections[org_id].add(websocket)
        logger.info(f"WebSocket client connected to org {org_id}. Total connections: {len(self.active_connections[org_id])}")

    def disconnect(self, org_id: str, websocket: WebSocket) -> None:
        if org_id in self.active_connections:
            self.active_connections[org_id].discard(websocket)
            if not self.active_connections[org_id]:
                del self.active_connections[org_id]
        logger.info(f"WebSocket client disconnected from org {org_id}.")

    async def broadcast_to_org(self, org_id: str, message: Dict[str, Any]) -> None:
        connections = self.active_connections.get(org_id, set())
        if not connections:
            return
        
        # Broadcast concurrently, handling closed connections safely
        closed = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send websocket message in org {org_id}: {e}")
                closed.append(ws)

        for ws in closed:
            self.disconnect(org_id, ws)

class LiveMetricsStream:
    def __init__(self, hub: WebSocketHub) -> None:
        self.hub = hub

    async def push_metric(self, org_id: str, metric_name: str, value: float, labels: Dict[str, str]) -> None:
        await self.hub.broadcast_to_org(org_id, {
            "type": "metric",
            "metric_name": metric_name,
            "value": value,
            "labels": labels,
            "timestamp": asyncio.get_event_loop().time()
        })

class LiveTraceStream:
    def __init__(self, hub: WebSocketHub) -> None:
        self.hub = hub

    async def push_span(self, org_id: str, correlation_id: str, span_name: str, status: str, duration_ms: float) -> None:
        await self.hub.broadcast_to_org(org_id, {
            "type": "trace",
            "correlation_id": correlation_id,
            "span_name": span_name,
            "status": status,
            "duration_ms": duration_ms
        })

class LiveAlertStream:
    def __init__(self, hub: WebSocketHub) -> None:
        self.hub = hub

    async def push_alert(self, org_id: str, alert_id: str, alert_name: str, message: str, severity: str, status: str) -> None:
        await self.hub.broadcast_to_org(org_id, {
            "type": "alert",
            "alert_id": alert_id,
            "name": alert_name,
            "message": message,
            "severity": severity,
            "status": status
        })

class TelemetryBroadcaster:
    def __init__(self, hub: WebSocketHub) -> None:
        self.hub = hub
        self.metrics = LiveMetricsStream(hub)
        self.traces = LiveTraceStream(hub)
        self.alerts = LiveAlertStream(hub)

    async def broadcast_event(self, org_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        await self.hub.broadcast_to_org(org_id, {
            "type": "telemetry_event",
            "event_type": event_type,
            "payload": payload
        })
