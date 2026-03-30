"""
Alert Repository

Data access layer for AML alerts.
"""

from datetime import UTC, datetime
from uuid import UUID

from ..models.alert_models import AlertSeverity, AlertStatus, AlertType, AMLAlert


class AlertRepository:
    """Repository for AML alert data access"""

    def __init__(self):
        self._alerts: dict[UUID, AMLAlert] = {}

    async def create(self, alert: AMLAlert) -> AMLAlert:
        """Create a new alert"""
        self._alerts[alert.alert_id] = alert
        return alert

    async def get_by_id(self, alert_id: UUID) -> AMLAlert | None:
        """Get alert by ID"""
        return self._alerts.get(alert_id)

    async def get_by_number(self, alert_number: str) -> AMLAlert | None:
        """Get alert by alert number"""
        for alert in self._alerts.values():
            if alert.alert_number == alert_number:
                return alert
        return None

    async def update(self, alert: AMLAlert) -> AMLAlert:
        """Update an existing alert"""
        self._alerts[alert.alert_id] = alert
        return alert

    async def delete(self, alert_id: UUID) -> bool:
        """Delete an alert"""
        if alert_id in self._alerts:
            del self._alerts[alert_id]
            return True
        return False

    async def find_by_customer(self, customer_id: str) -> list[AMLAlert]:
        """Find alerts by customer ID"""
        return [a for a in self._alerts.values() if a.customer_id == customer_id]

    async def find_by_status(self, statuses: list[AlertStatus]) -> list[AMLAlert]:
        """Find alerts by status"""
        return [a for a in self._alerts.values() if a.status in statuses]

    async def find_by_severity(self, severities: list[AlertSeverity]) -> list[AMLAlert]:
        """Find alerts by severity"""
        return [a for a in self._alerts.values() if a.severity in severities]

    async def find_by_type(self, alert_types: list[AlertType]) -> list[AMLAlert]:
        """Find alerts by type"""
        return [a for a in self._alerts.values() if a.alert_type in alert_types]

    async def find_by_assignee(self, assignee: str) -> list[AMLAlert]:
        """Find alerts by assignee"""
        return [a for a in self._alerts.values() if a.current_assignee == assignee]

    async def find_unassigned(self) -> list[AMLAlert]:
        """Find unassigned alerts"""
        return [a for a in self._alerts.values() if not a.current_assignee]

    async def find_overdue(self) -> list[AMLAlert]:
        """Find overdue alerts"""
        now = datetime.now(UTC)
        return [
            a for a in self._alerts.values()
            if a.due_date and a.due_date < now and a.status not in [
                AlertStatus.CLOSED_FALSE_POSITIVE,
                AlertStatus.CLOSED_TRUE_POSITIVE,
                AlertStatus.SAR_FILED
            ]
        ]

    async def find_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[AMLAlert]:
        """Find alerts within a date range"""
        return [
            a for a in self._alerts.values()
            if start_date <= a.created_at <= end_date
        ]

    async def count_by_status(self) -> dict[str, int]:
        """Count alerts by status"""
        counts: dict[str, int] = {}
        for alert in self._alerts.values():
            key = alert.status.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    async def count_by_severity(self) -> dict[str, int]:
        """Count alerts by severity"""
        counts: dict[str, int] = {}
        for alert in self._alerts.values():
            key = alert.severity.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[AMLAlert]:
        """Get all alerts with pagination"""
        alerts = list(self._alerts.values())
        return alerts[offset:offset + limit]

    async def count(self) -> int:
        """Count total alerts"""
        return len(self._alerts)


# Global repository instance
alert_repository = AlertRepository()
