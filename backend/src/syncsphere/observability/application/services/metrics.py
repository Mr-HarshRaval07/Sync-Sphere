import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from syncsphere.observability.domain.entities.metric_series import MetricSeries
from syncsphere.observability.domain.value_objects import Metric
from syncsphere.observability.domain.repositories import MetricRepository

class CounterCollector:
    def __init__(self) -> None:
        self._counts: Dict[str, float] = {}

    def increment(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> Metric:
        label_key = f"{name}:{str(labels)}"
        self._counts[label_key] = self._counts.get(label_key, 0.0) + value
        return Metric(name=name, value=self._counts[label_key], labels=labels or {})

class GaugeCollector:
    def __init__(self) -> None:
        self._gauges: Dict[str, float] = {}

    def set_value(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> Metric:
        label_key = f"{name}:{str(labels)}"
        self._gauges[label_key] = value
        return Metric(name=name, value=value, labels=labels or {})

class HistogramCollector:
    def __init__(self) -> None:
        self._sums: Dict[str, float] = {}
        self._counts: Dict[str, int] = {}

    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> Metric:
        label_key = f"{name}:{str(labels)}"
        self._sums[label_key] = self._sums.get(label_key, 0.0) + value
        self._counts[label_key] = self._counts.get(label_key, 0) + 1
        avg = self._sums[label_key] / self._counts[label_key]
        return Metric(name=name, value=avg, labels=labels or {})

class LatencyCollector:
    def __init__(self, histogram: HistogramCollector) -> None:
        self.histogram = histogram

    def record_latency(self, name: str, duration_ms: float, labels: Optional[Dict[str, str]] = None) -> Metric:
        return self.histogram.observe(f"{name}.latency_ms", duration_ms, labels)

class ErrorCollector:
    def __init__(self, counter: CounterCollector) -> None:
        self.counter = counter

    def record_error(self, name: str, error_type: str, labels: Optional[Dict[str, str]] = None) -> Metric:
        lbl = dict(labels or {})
        lbl["error_type"] = error_type
        return self.counter.increment(f"{name}.errors_total", 1.0, lbl)

class UsageCollector:
    def __init__(self, counter: CounterCollector) -> None:
        self.counter = counter

    def record_usage(self, name: str, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> Metric:
        return self.counter.increment(f"{name}.usage_total", amount, labels)

class CostCollector:
    def __init__(self, counter: CounterCollector) -> None:
        self.counter = counter

    def record_cost(self, amount: float, model: str, labels: Optional[Dict[str, str]] = None) -> Metric:
        lbl = dict(labels or {})
        lbl["model"] = model
        return self.counter.increment("ai.cost_dollars_total", amount, lbl)

class QueueCollector:
    def __init__(self, gauge: GaugeCollector) -> None:
        self.gauge = gauge

    def set_queue_size(self, queue_name: str, size: int, labels: Optional[Dict[str, str]] = None) -> Metric:
        lbl = dict(labels or {})
        lbl["queue"] = queue_name
        return self.gauge.set_value("runtime.queue_size", float(size), lbl)

class WorkerCollector:
    def __init__(self, gauge: GaugeCollector) -> None:
        self.gauge = gauge

    def set_active_workers(self, count: int, labels: Optional[Dict[str, str]] = None) -> Metric:
        return self.gauge.set_value("runtime.active_workers", float(count), labels)

class SLACollector:
    def __init__(self, counter: CounterCollector) -> None:
        self.counter = counter

    def record_sla_breach(self, workflow_name: str, labels: Optional[Dict[str, str]] = None) -> Metric:
        lbl = dict(labels or {})
        lbl["workflow"] = workflow_name
        return self.counter.increment("sla.breaches_total", 1.0, lbl)


class MetricsAggregator:
    """Supports rollups: 1m, 5m, 15m, 1h, 1d to avoid recalculating histories."""
    def __init__(self, repo: MetricRepository) -> None:
        self.repo = repo
        self._rollups: Dict[str, Dict[str, List[Metric]]] = {}

    def aggregate_metric(self, org_id: str, metric: Metric) -> None:
        if org_id not in self._rollups:
            self._rollups[org_id] = {}
        
        mname = metric.name
        if mname not in self._rollups[org_id]:
            self._rollups[org_id][mname] = []
        
        self._rollups[org_id][mname].append(metric)

    async def run_rollup(self, org_id: str, metric_name: str, interval_minutes: int) -> Optional[Metric]:
        """Rolls up metrics into a single summary Metric for the interval."""
        if org_id not in self._rollups or metric_name not in self._rollups[org_id]:
            return None

        metrics = self._rollups[org_id][metric_name]
        now = datetime.utcnow()
        threshold = now - timedelta(minutes=interval_minutes)
        
        # Filter metrics in the rollup window
        window_metrics = [m for m in metrics if m.timestamp >= threshold]
        if not window_metrics:
            return None

        avg_value = sum(m.value for m in window_metrics) / len(window_metrics)
        labels = window_metrics[0].labels

        rollup_metric = Metric(
            name=f"{metric_name}.rollup_{interval_minutes}m",
            timestamp=now,
            value=avg_value,
            labels=labels
        )
        
        # Persist rollup back to database MetricSeries
        series = await self.repo.get_series(org_id, rollup_metric.name)
        if not series:
            series = MetricSeries(org_id=org_id, metric_name=rollup_metric.name)
        series.add_metric(rollup_metric)
        await self.repo.save_series(series)
        return rollup_metric


class MetricsCollector:
    """Collects and dispatches platform telemetry metrics."""
    def __init__(self, repo: MetricRepository) -> None:
        self.repo = repo
        self.counter = CounterCollector()
        self.gauge = GaugeCollector()
        self.histogram = HistogramCollector()
        self.latency = LatencyCollector(self.histogram)
        self.error = ErrorCollector(self.counter)
        self.usage = UsageCollector(self.counter)
        self.cost = CostCollector(self.counter)
        self.queue = QueueCollector(self.gauge)
        self.worker = WorkerCollector(self.gauge)
        self.sla = SLACollector(self.counter)
        self.aggregator = MetricsAggregator(repo)

    async def record(self, org_id: str, metric: Metric) -> None:
        series = await self.repo.get_series(org_id, metric.name)
        if not series:
            series = MetricSeries(org_id=org_id, metric_name=metric.name)
        series.add_metric(metric)
        await self.repo.save_series(series)
        self.aggregator.aggregate_metric(org_id, metric)
