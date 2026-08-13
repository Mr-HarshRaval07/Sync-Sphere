from typing import List, Dict, Any, Optional
from datetime import datetime
from syncsphere.observability.domain.entities.replay import ExecutionReplay, WorkflowReplay, PlannerReplay
from syncsphere.observability.domain.value_objects import TimelineEvent
from syncsphere.observability.domain.repositories import ReplayRepository, EventStoreRepository

class TimelineReconstructor:
    """Combines Event Store events into a unified chronological timeline."""
    def reconstruct_unified_timeline(self, events: List[Any]) -> List[TimelineEvent]:
        timeline = []
        for e in events:
            # Map domain event classifications to timeline namespaces
            etype = e.event_type.lower()
            module = "execution"
            if "planning" in etype or "workflowgenerated" in etype or "workflowoptimized" in etype:
                module = "planner"
            elif "approval" in etype:
                module = "approval"
            elif "knowledge" in etype or "memory" in etype or "search" in etype:
                module = "knowledge"
            elif "connector" in etype:
                module = "connector"
            elif "completion" in etype or "embedding" in etype or "provider" in etype:
                module = "ai"
            elif "execution" in etype or "checkpoint" in etype or "worker" in etype or "compensation" in etype:
                module = "runtime"

            payload = getattr(e, "payload", {}) or {}
            desc = payload.get("message") or f"Event {e.event_type} occurred."
            
            timeline.append(TimelineEvent(
                timestamp=e.timestamp,
                name=e.event_type,
                description=desc,
                module=module,
                context_info=payload
            ))
        
        # Sort chronologically
        timeline.sort(key=lambda x: x.timestamp)
        return timeline

class ReplayExporter:
    """Exports structured replay data to formats."""
    def export(self, replay_data: Dict[str, Any], format_type: str = "json") -> Any:
        # For simplicity, JSON export returns the dict itself or string representation
        if format_type == "csv":
            # Simple simulation: build comma-separated lines
            lines = ["timestamp,module,name,description"]
            events = replay_data.get("timeline_events", [])
            for ev in events:
                lines.append(f"{ev.get('timestamp')},{ev.get('module')},{ev.get('name')},{ev.get('description')}")
            return "\n".join(lines)
        return replay_data

class ReplaySearch:
    def __init__(self, repo: ReplayRepository) -> None:
        self.repo = repo

    async def find_replays(self, org_id: str, type_name: str) -> List[Any]:
        # Return a list of recorded replays from db
        return []


class ExecutionReplayEngine:
    def __init__(self, replay_repo: ReplayRepository, event_store_repo: EventStoreRepository) -> None:
        self.replay_repo = replay_repo
        self.event_store_repo = event_store_repo
        self.reconstructor = TimelineReconstructor()

    async def generate_replay(self, org_id: str, session_id: str) -> ExecutionReplay:
        # Query event store by correlation_id or session_id
        # Let's search events where correlation_id or payload contains session_id
        events = await self.event_store_repo.search(org_id, correlation_id=session_id)
        if not events:
            # Try searching by event type or search all to find matching session_id in payload
            all_events = await self.event_store_repo.search(org_id)
            events = [e for e in all_events if e.payload.get("session_id") == session_id or e.correlation_id == session_id]

        timeline = self.reconstructor.reconstruct_unified_timeline(events)
        replay = ExecutionReplay(org_id=org_id, session_id=session_id, timeline_events=timeline)
        await self.replay_repo.save_execution_replay(replay)
        return replay

class WorkflowReplayEngine:
    def __init__(self, replay_repo: ReplayRepository, event_store_repo: EventStoreRepository) -> None:
        self.replay_repo = replay_repo
        self.event_store_repo = event_store_repo

    async def generate_replay(self, org_id: str, workflow_id: str) -> WorkflowReplay:
        events = await self.event_store_repo.search(org_id)
        wf_events = [e for e in events if e.payload.get("workflow_id") == workflow_id]
        
        reconstruct_steps = []
        for e in wf_events:
            reconstruct_steps.append({
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "workflow_id": workflow_id,
                "details": e.payload
            })
        
        replay = WorkflowReplay(org_id=org_id, workflow_id=workflow_id, reconstruct_steps=reconstruct_steps)
        await self.replay_repo.save_workflow_replay(replay)
        return replay

class PlannerReplayEngine:
    def __init__(self, replay_repo: ReplayRepository, event_store_repo: EventStoreRepository) -> None:
        self.replay_repo = replay_repo
        self.event_store_repo = event_store_repo

    async def generate_replay(self, org_id: str, planner_session_id: str) -> PlannerReplay:
        events = await self.event_store_repo.search(org_id)
        pl_events = [e for e in events if e.payload.get("session_id") == planner_session_id or e.correlation_id == planner_session_id]
        
        cycles = []
        for e in pl_events:
            if "planning" in e.event_type.lower() or "workflow" in e.event_type.lower():
                cycles.append({
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type,
                    "details": e.payload
                })
        
        replay = PlannerReplay(org_id=org_id, planner_session_id=planner_session_id, reasoning_cycles=cycles)
        await self.replay_repo.save_planner_replay(replay)
        return replay
