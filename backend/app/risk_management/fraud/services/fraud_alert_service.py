"""Fraud Alert Service - Manages fraud alerts"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from ..models.fraud_alert_models import (
    FraudAlert, FraudAlertSummary, FraudAlertStatistics,
    FraudAlertStatus, FraudAlertSeverity, FraudType,
    FraudAlertCreateRequest, FraudAlertSearchCriteria
)


class FraudAlertService:
    def __init__(self):
        self._alerts: Dict[UUID, FraudAlert] = {}
        self._counter = 0

    def _generate_number(self) -> str:
        self._counter += 1
        return f"FRD-{datetime.utcnow().strftime('%Y%m%d')}-{self._counter:06d}"

    async def create_alert(self, request: FraudAlertCreateRequest) -> FraudAlert:
        alert = FraudAlert(
            alert_number=self._generate_number(),
            fraud_type=request.fraud_type,
            severity=request.severity,
            customer_id=request.customer_id,
            account_id=request.account_id,
            transaction_id=request.transaction_id,
            title=request.title,
            description=request.description,
            fraud_score=request.fraud_score,
            detection_method=request.detection_method,
            transaction_amount=request.transaction_amount,
            potential_loss=request.transaction_amount or 0.0
        )
        self._alerts[alert.alert_id] = alert
        return alert

    async def get_alert(self, alert_id: UUID) -> Optional[FraudAlert]:
        return self._alerts.get(alert_id)

    async def update_status(self, alert_id: UUID, status: FraudAlertStatus) -> Optional[FraudAlert]:
        alert = self._alerts.get(alert_id)
        if alert:
            alert.status = status
            alert.updated_at = datetime.utcnow()
            if status in [FraudAlertStatus.CONFIRMED_FRAUD, FraudAlertStatus.FALSE_POSITIVE, FraudAlertStatus.CLOSED]:
                alert.resolved_at = datetime.utcnow()
        return alert

    async def assign_alert(self, alert_id: UUID, assignee: str) -> Optional[FraudAlert]:
        alert = self._alerts.get(alert_id)
        if alert:
            alert.assigned_to = assignee
            alert.status = FraudAlertStatus.ASSIGNED
            alert.updated_at = datetime.utcnow()
        return alert

    async def search_alerts(self, criteria: FraudAlertSearchCriteria) -> List[FraudAlertSummary]:
        results = []
        for alert in self._alerts.values():
            if criteria.fraud_types and alert.fraud_type not in criteria.fraud_types:
                continue
            if criteria.severities and alert.severity not in criteria.severities:
                continue
            if criteria.statuses and alert.status not in criteria.statuses:
                continue
            results.append(FraudAlertSummary(
                alert_id=alert.alert_id,
                alert_number=alert.alert_number,
                fraud_type=alert.fraud_type,
                severity=alert.severity,
                status=alert.status,
                customer_id=alert.customer_id,
                fraud_score=alert.fraud_score,
                potential_loss=alert.potential_loss,
                created_at=alert.created_at,
                assigned_to=alert.assigned_to
            ))
        return results[: criteria.page_size]

    async def get_statistics(self) -> FraudAlertStatistics:
        stats = FraudAlertStatistics(total_alerts=len(self._alerts))
        for alert in self._alerts.values():
            stats.by_severity[alert.severity.value] = stats.by_severity.get(alert.severity.value, 0) + 1
            stats.by_status[alert.status.value] = stats.by_status.get(alert.status.value, 0) + 1
            stats.by_fraud_type[alert.fraud_type.value] = stats.by_fraud_type.get(alert.fraud_type.value, 0) + 1
            stats.total_potential_loss += alert.potential_loss
            if alert.status == FraudAlertStatus.CONFIRMED_FRAUD:
                stats.confirmed_fraud_count += 1
            elif alert.status == FraudAlertStatus.FALSE_POSITIVE:
                stats.false_positive_count += 1
        return stats


fraud_alert_service = FraudAlertService()
