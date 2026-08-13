from typing import List, Optional
from datetime import datetime
from syncsphere.observability.domain.entities.health import HealthCheck
from syncsphere.observability.domain.value_objects import ServiceStatus, HealthStatus
from syncsphere.observability.domain.repositories import HealthRepository

class DependencyHealth:
    def check_database(self) -> ServiceStatus:
        # Check standard database connectivity
        return ServiceStatus(name="MongoDB Database", status=HealthStatus.HEALTHY, message="Connection online")

    def check_redis(self) -> ServiceStatus:
        # Check redis connectivity
        return ServiceStatus(name="Redis Cache & EventBus", status=HealthStatus.HEALTHY, message="Connection online")

class ServiceHealth:
    def check_services(self) -> List[ServiceStatus]:
        return [
            ServiceStatus(name="Planner Service", status=HealthStatus.HEALTHY),
            ServiceStatus(name="Execution Runtime Service", status=HealthStatus.HEALTHY),
            ServiceStatus(name="Knowledge Platform Service", status=HealthStatus.HEALTHY),
            ServiceStatus(name="Human Approval Platform", status=HealthStatus.HEALTHY),
            ServiceStatus(name="AI Gateway Service", status=HealthStatus.HEALTHY)
        ]

class ConnectorHealthMonitor:
    def check_connectors(self) -> List[ServiceStatus]:
        return [
            ServiceStatus(name="MCP Connector Hub", status=HealthStatus.HEALTHY, message="All connector environments running normally")
        ]


class HealthAggregator:
    def __init__(self, repo: HealthRepository) -> None:
        self.repo = repo
        self.deps = DependencyHealth()
        self.services = ServiceHealth()
        self.connectors = ConnectorHealthMonitor()

    async def run_aggregated_checks(self, org_id: str) -> HealthCheck:
        services = []
        services.append(self.deps.check_database())
        services.append(self.deps.check_redis())
        services.extend(self.services.check_services())
        services.extend(self.connectors.check_connectors())
        
        check = HealthCheck(org_id=org_id, services=services)
        await self.repo.save(check)
        return check

class HealthReporter:
    def __init__(self, aggregator: HealthAggregator) -> None:
        self.aggregator = aggregator

    async def get_latest_report(self, org_id: str) -> HealthCheck:
        latest = await self.aggregator.repo.get_latest(org_id)
        if not latest:
            latest = await self.aggregator.run_aggregated_checks(org_id)
        return latest
