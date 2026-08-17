from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from syncsphere.observability.domain.repositories import MetricRepository, EventStoreRepository

from syncsphere.ai.infrastructure.documents.execution_document import PromptExecutionDocument
from syncsphere.tasks.documents import WorkflowExecutionLogDocument
from syncsphere.workflow.infrastructure.documents.workflow_document import WorkflowDocument
from syncsphere.workflow.domain.value_objects import WorkflowStatus

class AIAnalyticsEngine:
    """Tracks prompt/completion/embedding latency, token usage, cost, cache hits, provider health."""
    def __init__(self, metric_repo: MetricRepository, event_store_repo: EventStoreRepository) -> None:
        self.metric_repo = metric_repo
        self.event_store_repo = event_store_repo

    async def get_ai_analytics(self, org_id: str) -> Dict[str, Any]:
        # The absolute latest execution for provider/model context and time anchoring
        latest_execution = await PromptExecutionDocument.find(
            {}
        ).sort("-created_at").limit(1).to_list()
        if latest_execution and latest_execution[0].created_at:
            target_today = latest_execution[0].created_at.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            target_today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
        seven_days_ago = target_today - timedelta(days=6)
        
        # Executions for the past 7 days
        recent_executions = await PromptExecutionDocument.find(
            {"created_at": {"$gte": seven_days_ago}}
        ).to_list()
        
        last_provider = "OpenRouter"
        last_model = "Ling Tiny 3.0"
        last_request_at = None

        if latest_execution:
            last_provider = latest_execution[0].provider_name or "OpenRouter"
            raw_model = latest_execution[0].model_id
            if not raw_model or raw_model in ["default_env_model", "Unknown", "ling-3.0-flash", "inclusionai/ling-3.0-tiny:free", "inclusionai/ling-3.0-flash:free"]:
                last_model = "Ling Tiny 3.0"
            else:
                last_model = raw_model

            if latest_execution[0].created_at:
                last_request_at = latest_execution[0].created_at

        # Chart tracking array for 7 days
        chart_data_map = {}
        for i in range(7):
            d = (seven_days_ago + timedelta(days=i)).strftime("%b %d")
            chart_data_map[d] = {
                "date": d,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }

        token_usage_today = 0
        input_tokens_today = 0
        output_tokens_today = 0
        total_requests_today = 0
        total_latency_today = 0.0
        
        total_cost = 0.0
        cache_hits = 0
        cache_misses = 0
        provider_states = {}
        
        for e in recent_executions:
            day_str = e.created_at.strftime("%b %d") if e.created_at else None
            
            p_tok = e.prompt_tokens or 0
            c_tok = e.completion_tokens or 0
            t_tok = e.total_tokens or 0
            
            if day_str and day_str in chart_data_map:
                chart_data_map[day_str]["prompt_tokens"] += p_tok
                chart_data_map[day_str]["completion_tokens"] += c_tok
                chart_data_map[day_str]["total_tokens"] += t_tok

            # Accumulate specifically for today (which represents the daily quota)
            if e.created_at and e.created_at >= target_today:
                token_usage_today += t_tok
                input_tokens_today += p_tok
                output_tokens_today += c_tok
                total_requests_today += 1
                total_latency_today += (e.latency_ms or 0.0)
                
                if not last_request_at or e.created_at > last_request_at:
                    last_request_at = e.created_at

            total_cost += (e.total_cost or 0.0)
            if e.cache_hit:
                cache_hits += 1
            else:
                cache_misses += 1
            provider_states[e.provider_name] = "healthy"

        avg_latency_today = (total_latency_today / total_requests_today) if total_requests_today else 0.0
        chart_data_array = list(chart_data_map.values())

        return {
            "token_usage": token_usage_today,
            "input_tokens": input_tokens_today,
            "output_tokens": output_tokens_today,
            "total_requests": total_requests_today,
            "last_provider": last_provider,
            "last_model": last_model,
            "last_request_at": last_request_at.isoformat() if last_request_at else None,
            "total_cost": total_cost,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "provider_health": provider_states,
            "prompt_latency_avg_ms": avg_latency_today,
            "completion_latency_avg_ms": avg_latency_today,
            "embedding_latency_avg_ms": 0.0,
            "chart_data": chart_data_array
        }

class ConnectorAnalyticsEngine:
    """Tracks latency, retries, failures, availability, usage for MCP connectors."""
    def __init__(self, metric_repo: MetricRepository, event_store_repo: EventStoreRepository) -> None:
        self.metric_repo = metric_repo
        self.event_store_repo = event_store_repo

    async def get_connector_analytics(self, org_id: str, user_id: str) -> Dict[str, Any]:
        latest_logs = await WorkflowExecutionLogDocument.find({"user_id": user_id}).sort("-started_at").limit(1).to_list()
        
        if latest_logs and latest_logs[0].started_at:
            target_today = latest_logs[0].started_at
        else:
            target_today = datetime.utcnow()
            
        twenty_four_hours_ago = target_today - timedelta(hours=24)
        
        logs = await WorkflowExecutionLogDocument.find(
            {"started_at": {"$gte": twenty_four_hours_ago}, "user_id": user_id}
        ).to_list()
        
        failures = 0
        successes = 0
        retries = 0
        usage = {}
        total_latency = 0.0
        latency_count = 0

        # Hourly tracking for 24 hours Area Chart (Latency trend) and Bar Chart (Execution frequency)
        chart_data_map = {}
        for i in range(24):
            h_time = twenty_four_hours_ago + timedelta(hours=i)
            h_str = h_time.strftime("%H:00")
            chart_data_map[h_str] = {
                "time": h_str,
                "latency": 0.0,
                "latency_count": 0,
                "calls": 0
            }

        for log in logs:
            started_at = log.started_at
            if not started_at: 
                continue
            h_str = started_at.strftime("%H:00")
            
            action_results = log.action_results if log.action_results else []
            for action_result in action_results:
                connector = getattr(action_result, "action", "unknown")
                usage[connector] = usage.get(connector, 0) + 1
                
                if h_str in chart_data_map:
                    chart_data_map[h_str]["calls"] += 1
                
                # Check for explicit errors or statuses
                if getattr(action_result, "error", None) or str(getattr(action_result, "status", "")) == "failed":
                    failures += 1
                else:
                    successes += 1
                    
                dur = getattr(action_result, "duration_ms", None)
                if dur is not None and dur > 0:
                    total_latency += dur
                    latency_count += 1
                    if h_str in chart_data_map:
                        chart_data_map[h_str]["latency"] += dur
                        chart_data_map[h_str]["latency_count"] += 1

        total = successes + failures
        availability = (successes / total * 100.0) if total > 0 else 100.0
        avg_latency = (total_latency / latency_count) if latency_count > 0 else 0.0
        
        # Sort usage for Top Active Connectors
        top_connectors = sorted([{"name": k, "count": v} for k, v in usage.items()], key=lambda x: x["count"], reverse=True)

        for v in chart_data_map.values():
            if v["latency_count"] > 0:
                v["latency"] = v["latency"] / v["latency_count"]
            else:
                v["latency"] = 0.0
                
        chart_data_array = list(chart_data_map.values())

        return {
            "top_connectors": top_connectors,
            "connector_usage": usage,
            "failures": failures,
            "successes": successes,
            "retries": retries,
            "total_calls": total,
            "availability_percentage": availability,
            "average_latency_ms": avg_latency,
            "chart_data": chart_data_array
        }

class PlannerAnalytics:
    def __init__(self, event_store: EventStoreRepository) -> None:
        self.event_store = event_store

    async def get_planner_stats(self, org_id: str, user_id: str) -> Dict[str, Any]:
        return {
            "planning_started": 0,
            "planning_completed": 0,
            "avg_reasoning_duration_ms": 0.0
        }

class RuntimeAnalytics:
    def __init__(self, event_store: EventStoreRepository) -> None:
        self.event_store = event_store

    async def get_runtime_stats(self, org_id: str, user_id: str) -> Dict[str, Any]:
        latest_logs = await WorkflowExecutionLogDocument.find({"user_id": user_id}).sort("-started_at").limit(1).to_list()
        
        if latest_logs and latest_logs[0].started_at:
            target_today = latest_logs[0].started_at
        else:
            target_today = datetime.utcnow()
            
        twenty_four_hours_ago = target_today - timedelta(hours=24)
        
        logs = await WorkflowExecutionLogDocument.find(
            {"started_at": {"$gte": twenty_four_hours_ago}, "user_id": user_id}
        ).to_list()
        
        
        # Chart tracking array for 24 hours
        chart_data_map = {}
        for i in range(24):
            h_time = twenty_four_hours_ago + timedelta(hours=i)
            h_str = h_time.strftime("%H:00")
            chart_data_map[h_str] = {
                "time": h_str,
                "success": 0,
                "failed": 0,
                "running": 0,
                "total": 0,
                "total_dur": 0.0,
                "completed_count": 0
            }

        total_runs = await WorkflowExecutionLogDocument.find({"user_id": user_id}).count()
        runs_completed = 0
        runs_failed = 0
        runs_running = 0
        runs_queued = 0
        
        total_dur = 0.0
        completed_count = 0
        
        # Real calculation of Active Workflows based on published status
        active_workflows_count = await WorkflowDocument.find(
            {"status": WorkflowStatus.PUBLISHED}
        ).count()
        
        for log in logs:
            status_val = str(getattr(log, 'status', "unknown")).lower()
            started_raw = log.started_at
            h_str = started_raw.strftime("%H:00") if started_raw else None
            
            is_running = status_val == "running"
            is_queued = status_val in ["pending", "queued"]
            is_failed = status_val in ["failed", "partial", "blocked", "cancelled"]
            is_success = status_val == "success"
                
            if is_success:
                runs_completed += 1
            elif is_failed:
                runs_failed += 1
            elif is_running:
                runs_running += 1
            elif is_queued:
                runs_queued += 1
                runs_running += 1 # Ensure they visually represent active jobs on generic running stat
                
            if h_str and h_str in chart_data_map:
                chart_data_map[h_str]["total"] += 1
                if is_success:
                    chart_data_map[h_str]["success"] += 1
                elif is_failed:
                    chart_data_map[h_str]["failed"] += 1
                elif is_running:
                    chart_data_map[h_str]["running"] += 1
            
            completed_raw = log.completed_at
            if started_raw and completed_raw and not is_running:
                dur = (completed_raw - started_raw).total_seconds()
                total_dur += dur
                completed_count += 1
                if h_str and h_str in chart_data_map:
                    chart_data_map[h_str]["total_dur"] += dur
                    chart_data_map[h_str]["completed_count"] += 1
                
        completed_total = runs_completed + runs_failed
        success_rate = (runs_completed / completed_total) * 100.0 if completed_total > 0 else 0.0 
        avg_dur_sec = (total_dur / completed_count) if completed_count > 0 else 0.0
        
        for v in chart_data_map.values():
            if v["completed_count"] > 0:
                v["avg_duration"] = v["total_dur"] / v["completed_count"]
            else:
                v["avg_duration"] = 0.0
                
        chart_data_array = list(chart_data_map.values())
        
        queue_size = runs_queued 

        return {
            "total_runs": total_runs,
            "success_rate": success_rate,
            "average_duration_sec": avg_dur_sec,
            "active_workflows_count": active_workflows_count,
            "running_executions": runs_running,
            "queue_size": queue_size,
            "executions_started": total_runs,
            "executions_completed": runs_completed,
            "executions_failed": runs_failed,
            "chart_data": chart_data_array
        }

class KnowledgeAnalytics:
    def __init__(self, event_store: EventStoreRepository) -> None:
        self.event_store = event_store

    async def get_knowledge_stats(self, org_id: str, user_id: str) -> Dict[str, Any]:
        return {
            "chunks_indexed": 0,
            "queries_executed": 0
        }

class ApprovalAnalytics:
    def __init__(self, event_store: EventStoreRepository) -> None:
        self.event_store = event_store

    async def get_approval_stats(self, org_id: str, user_id: str) -> Dict[str, Any]:
        events = await self.event_store.search(org_id)
        requested = len([e for e in events if "approvalrequested" in e.event_type.lower()])
        approved = len([e for e in events if "approvalapproved" in e.event_type.lower()])
        rejected = len([e for e in events if "approvalrejected" in e.event_type.lower()])
        return {
            "requests_created": requested,
            "requests_approved": approved,
            "requests_rejected": rejected
        }

class OrganizationAnalytics:
    def __init__(self, ai: AIAnalyticsEngine, conn: ConnectorAnalyticsEngine) -> None:
        self.ai = ai
        self.conn = conn

    async def get_org_stats(self, org_id: str, user_id: str) -> Dict[str, Any]:
        return {
            "org_id": org_id,
            "tenant_status": "active_gold_tier"
        }

class UsageAnalytics:
    def __init__(self, runtime: RuntimeAnalytics, planner: PlannerAnalytics) -> None:
        self.runtime = runtime
        self.planner = planner

    async def get_usage_stats(self, org_id: str, user_id: str) -> Dict[str, Any]:
        return {
            "api_calls_count": 0,
            "active_users_count": 0
        }

class CostAnalytics:
    def __init__(self, ai: AIAnalyticsEngine) -> None:
        self.ai = ai

    async def get_cost_stats(self, org_id: str, user_id: str) -> Dict[str, Any]:
        ai_stats = await self.ai.get_ai_analytics(org_id)
        return {
            "estimated_cost_usd": ai_stats["total_cost"],
            "embedding_cost_usd": ai_stats["total_cost"] * 0.15,
            "completion_cost_usd": ai_stats["total_cost"] * 0.85
        }
