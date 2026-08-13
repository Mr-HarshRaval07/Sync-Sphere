from typing import List
from pydantic import Field
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument
from syncsphere.observability.domain.value_objects import Metric

class MetricSeriesDocument(BaseTenantDocument):
    metric_name: str
    metrics: List[Metric] = Field(default_factory=list)

    class Settings:
        name = "observability_metrics"
        indexes = [
            "org_id",
            "metric_name"
        ]
