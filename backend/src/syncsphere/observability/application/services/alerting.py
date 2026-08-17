from typing import List, Optional, Dict, Any
from datetime import datetime
from syncsphere.observability.domain.entities.alert import Alert
from syncsphere.observability.domain.value_objects import Metric, AlertPolicy, AlertRule
from syncsphere.observability.domain.repositories import AlertRepository

class AlertPolicyResolver:
    """Matches Metrics against active Alert Policies to resolve triggers."""
    def __init__(self) -> None:
        self._policies: Dict[str, AlertPolicy] = {}

    def register_policy(self, policy: AlertPolicy) -> None:
        self._policies[policy.policy_id] = policy

    def evaluate_metric(self, metric: Metric) -> List[AlertRule]:
        triggered_rules = []
        for policy in self._policies.values():
            if not policy.is_enabled:
                continue
            for rule in policy.rules:
                cond = rule.condition
                if cond.metric_name == metric.name:
                    is_breached = False
                    if cond.operator == "GREATER_THAN" and metric.value > cond.threshold:
                        is_breached = True
                    elif cond.operator == "LESS_THAN" and metric.value < cond.threshold:
                        is_breached = True
                    elif cond.operator == "EQUAL" and metric.value == cond.threshold:
                        is_breached = True
                    
                    if is_breached:
                        triggered_rules.append(rule)
        return triggered_rules


class ThresholdAlerts:
    def evaluate(self, metric: Metric, rule: AlertRule) -> str:
        return f"Threshold alert breached: {metric.name} = {metric.value} (Threshold: {rule.condition.threshold})"

class AnomalyAlerts:
    def evaluate(self, metric: Metric) -> Optional[str]:
        # Basic static deviation anomaly check
        if "anomaly" in metric.name:
            return f"Anomaly detected on {metric.name} with value {metric.value}"
        return None

class SLAAlerts:
    def evaluate(self, metric: Metric) -> Optional[str]:
        if "sla.breaches" in metric.name and metric.value > 0:
            return f"SLA breach detected: {metric.name} counter is at {metric.value}"
        return None

class FailureAlerts:
    def evaluate(self, metric: Metric) -> Optional[str]:
        if "errors" in metric.name and metric.value > 5:
            return f"High error count detected: {metric.name} is at {metric.value}"
        return None

class ConnectorAlerts:
    def evaluate(self, metric: Metric) -> Optional[str]:
        if "connector.failures" in metric.name and metric.value > 0:
            return f"Connector framework failure detected on {metric.name}"
        return None

class AIProviderAlerts:
    def evaluate(self, metric: Metric) -> Optional[str]:
        if "ai.provider.healthy" in metric.name and metric.value == 0:
            return f"AI Provider is marked unhealthy: {metric.name}"
        return None

class RuntimeAlerts:
    def evaluate(self, metric: Metric) -> Optional[str]:
        if "runtime.queue_size" in metric.name and metric.value > 100:
            return f"Critical queue build up in runtime: {metric.name} size is {metric.value}"
        return None


class AlertEngine:
    """Main Alerting evaluation and lifecycle engine."""
    def __init__(self, repo: AlertRepository) -> None:
        self.repo = repo
        self.resolver = AlertPolicyResolver()
        self.threshold = ThresholdAlerts()
        self.anomaly = AnomalyAlerts()
        self.sla = SLAAlerts()
        self.failure = FailureAlerts()
        self.connector = ConnectorAlerts()
        self.ai_provider = AIProviderAlerts()
        self.runtime = RuntimeAlerts()

    async def evaluate_metric(self, org_id: str, metric: Metric) -> List[Alert]:
        triggered_alerts = []
        
        # 1. Evaluate registered policies
        rules = self.resolver.evaluate_metric(metric)
        for rule in rules:
            msg = self.threshold.evaluate(metric, rule)
            alert = Alert(
                org_id=org_id,
                name=rule.name,
                message=msg,
                severity=rule.severity,
                metric_name=metric.name
            )
            await self.repo.save(alert)
            triggered_alerts.append(alert)

        # 2. Evaluate static engine rules
        msg = self.anomaly.evaluate(metric)
        if msg:
            alert = Alert(org_id=org_id, name="Anomaly Alert", message=msg, severity="WARNING", metric_name=metric.name)
            await self.repo.save(alert)
            triggered_alerts.append(alert)

        msg = self.sla.evaluate(metric)
        if msg:
            alert = Alert(org_id=org_id, name="SLA Alert", message=msg, severity="CRITICAL", metric_name=metric.name)
            await self.repo.save(alert)
            triggered_alerts.append(alert)

        msg = self.failure.evaluate(metric)
        if msg:
            alert = Alert(org_id=org_id, name="Failure Rate Alert", message=msg, severity="WARNING", metric_name=metric.name)
            await self.repo.save(alert)
            triggered_alerts.append(alert)

        msg = self.connector.evaluate(metric)
        if msg:
            alert = Alert(org_id=org_id, name="Connector Alert", message=msg, severity="CRITICAL", metric_name=metric.name)
            await self.repo.save(alert)
            triggered_alerts.append(alert)

        msg = self.ai_provider.evaluate(metric)
        if msg:
            alert = Alert(org_id=org_id, name="AI Provider Alert", message=msg, severity="CRITICAL", metric_name=metric.name)
            await self.repo.save(alert)
            triggered_alerts.append(alert)

        msg = self.runtime.evaluate(metric)
        if msg:
            alert = Alert(org_id=org_id, name="Runtime Alert", message=msg, severity="WARNING", metric_name=metric.name)
            await self.repo.save(alert)
            triggered_alerts.append(alert)

        return triggered_alerts
