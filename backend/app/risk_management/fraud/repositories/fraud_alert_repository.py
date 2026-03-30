"""Fraud Alert Repository - Data access layer for fraud alerts"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from ..models.fraud_alert_models import FraudAlert, FraudAlertSeverity, FraudAlertStatus, FraudType


class FraudAlertRepository:
    def __init__(self):
        self._alerts: dict[UUID, FraudAlert] = {}
        self._alert_number_index: dict[str, UUID] = {}
        self._customer_index: dict[str, list[UUID]] = {}
        self._status_index: dict[FraudAlertStatus, list[UUID]] = {}

    async def save(self, alert: FraudAlert) -> FraudAlert:
        self._alerts[alert.alert_id] = alert
        self._alert_number_index[alert.alert_number] = alert.alert_id
        if alert.customer_id not in self._customer_index:
            self._customer_index[alert.customer_id] = []
        if alert.alert_id not in self._customer_index[alert.customer_id]:
            self._customer_index[alert.customer_id].append(alert.alert_id)
        if alert.status not in self._status_index:
            self._status_index[alert.status] = []
        if alert.alert_id not in self._status_index[alert.status]:
            self._status_index[alert.status].append(alert.alert_id)
        return alert

    async def find_by_id(self, alert_id: UUID) -> FraudAlert | None:
        return self._alerts.get(alert_id)

    async def find_by_number(self, alert_number: str) -> FraudAlert | None:
        alert_id = self._alert_number_index.get(alert_number)
        if alert_id:
            return self._alerts.get(alert_id)
        return None

    async def find_by_customer(self, customer_id: str, limit: int = 100) -> list[FraudAlert]:
        alert_ids = self._customer_index.get(customer_id, [])
        alerts = [self._alerts[aid] for aid in alert_ids if aid in self._alerts]
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)[:limit]

    async def find_by_status(self, status: FraudAlertStatus, limit: int = 100) -> list[FraudAlert]:
        alert_ids = self._status_index.get(status, [])
        alerts = [self._alerts[aid] for aid in alert_ids if aid in self._alerts]
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)[:limit]

    async def find_by_severity(self, severity: FraudAlertSeverity, limit: int = 100) -> list[FraudAlert]:
        alerts = [a for a in self._alerts.values() if a.severity == severity]
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)[:limit]

    async def find_by_fraud_type(self, fraud_type: FraudType, limit: int = 100) -> list[FraudAlert]:
        alerts = [a for a in self._alerts.values() if a.fraud_type == fraud_type]
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)[:limit]

    async def find_high_priority(self, limit: int = 50) -> list[FraudAlert]:
        high_priority = [
            a for a in self._alerts.values()
            if a.severity in [FraudAlertSeverity.HIGH, FraudAlertSeverity.CRITICAL]
            and a.status == FraudAlertStatus.NEW
        ]
        return sorted(high_priority, key=lambda x: (x.severity.value, x.fraud_score), reverse=True)[:limit]

    async def find_unassigned(self, limit: int = 100) -> list[FraudAlert]:
        unassigned = [
            a for a in self._alerts.values()
            if a.assigned_to is None and a.status == FraudAlertStatus.NEW
        ]
        return sorted(unassigned, key=lambda x: x.created_at, reverse=True)[:limit]

    async def find_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 500) -> list[FraudAlert]:
        alerts = [
            a for a in self._alerts.values()
            if start_date <= a.created_at <= end_date
        ]
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)[:limit]

    async def find_recent(self, hours: int = 24, limit: int = 100) -> list[FraudAlert]:
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        recent = [a for a in self._alerts.values() if a.created_at >= cutoff]
        return sorted(recent, key=lambda x: x.created_at, reverse=True)[:limit]

    async def update(self, alert: FraudAlert) -> FraudAlert:
        alert.updated_at = datetime.now(UTC)
        self._alerts[alert.alert_id] = alert
        return alert

    async def delete(self, alert_id: UUID) -> bool:
        if alert_id in self._alerts:
            alert = self._alerts[alert_id]
            del self._alerts[alert_id]
            if alert.alert_number in self._alert_number_index:
                del self._alert_number_index[alert.alert_number]
            return True
        return False

    async def count_by_status(self) -> dict[str, int]:
        counts = {}
        for alert in self._alerts.values():
            status_key = alert.status.value
            counts[status_key] = counts.get(status_key, 0) + 1
        return counts

    async def count_by_severity(self) -> dict[str, int]:
        counts = {}
        for alert in self._alerts.values():
            severity_key = alert.severity.value
            counts[severity_key] = counts.get(severity_key, 0) + 1
        return counts

    async def get_all(self, limit: int = 1000, offset: int = 0) -> list[FraudAlert]:
        alerts = sorted(self._alerts.values(), key=lambda x: x.created_at, reverse=True)
        return alerts[offset:offset + limit]

    async def count(self) -> int:
        return len(self._alerts)


fraud_alert_repository = FraudAlertRepository()
