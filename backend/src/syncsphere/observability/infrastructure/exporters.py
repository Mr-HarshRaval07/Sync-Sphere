from typing import List, Dict, Any
from syncsphere.observability.domain.entities.metric_series import MetricSeries
from syncsphere.observability.domain.entities.trace import Trace

class PrometheusExporter:
    """Formats MetricSeries into Prometheus scraping text format."""
    def format_to_text(self, series_list: List[MetricSeries]) -> str:
        lines = []
        for s in series_list:
            if not s.metrics:
                continue
            mname = s.metric_name.replace(".", "_").replace("-", "_")
            lines.append(f"# HELP {mname} Observability metric: {s.metric_name}")
            lines.append(f"# TYPE {mname} gauge")
            
            # Group metrics by label sets and retrieve the latest value for each
            latest_metrics: Dict[str, Any] = {}
            for m in s.metrics:
                lbls_str = ",".join(f'{k}="{v}"' for k, v in m.labels.items())
                lbls_str = f', {lbls_str}' if lbls_str else ""
                key = f'org_id="{s.org_id}"{lbls_str}'
                latest_metrics[key] = m.value

            for labels_kv, val in latest_metrics.items():
                lines.append(f"{mname}{{{labels_kv}}} {val}")
        return "\n".join(lines)

class GrafanaConfigGenerator:
    """Generates standard Grafana dashboard JSON configurations."""
    def get_dashboard_json(self) -> Dict[str, Any]:
        return {
            "title": "SyncSphere Platform Metrics",
            "panels": [
                {
                    "title": "AI Token Usage",
                    "type": "graph",
                    "targets": [{"expr": "ai_tokens_total"}]
                },
                {
                    "title": "API Request Count",
                    "type": "graph",
                    "targets": [{"expr": "system_usage_total"}]
                },
                {
                    "title": "Execution Latency",
                    "type": "graph",
                    "targets": [{"expr": "runtime_latency_ms"}]
                }
            ]
        }
