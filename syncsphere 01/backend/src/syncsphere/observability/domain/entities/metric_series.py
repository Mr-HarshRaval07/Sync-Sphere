from typing import Optional, Dict, Any, List
from datetime import datetime
from syncsphere.shared_kernel.domain.entity import Entity
from syncsphere.observability.domain.value_objects import Metric

class MetricSeries(Entity):
    def __init__(
        self,
        org_id: str,
        metric_name: str,
        metrics: Optional[List[Metric]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.metric_name = metric_name
        self.metrics = metrics or []

    def add_metric(self, metric: Metric) -> None:
        self.metrics.append(metric)
