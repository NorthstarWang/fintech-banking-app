"""
AML Alert Service

Handles alert creation, management, and workflow operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from ..models.alert_models import (
    AMLAlert, AlertSummary, AlertStatistics, AlertStatus, AlertSeverity,
    AlertType, AlertTrigger, AlertEvidence, AlertComment, AlertAssignment,
    AlertCreateRequest, AlertUpdateRequest, AlertSearchCriteria
)


class AlertService:
    """Service for managing AML alerts"""

    def __init__(self):
        self._alerts: Dict[UUID, AMLAlert] = {}
        self._alert_counter = 0

    def _generate_alert_number(self) -> str:
        """Generate unique alert number"""
        self._alert_counter += 1
        return f"ALT-{datetime.utcnow().strftime('%Y%m%d')}-{self._alert_counter:06d}"

    async def create_alert(self, request: AlertCreateRequest, created_by: str) -> AMLAlert:
        """Create a new AML alert"""
        alert_id = uuid4()
        alert = AMLAlert(
            alert_id=alert_id,
            alert_number=self._generate_alert_number(),
            alert_type=request.alert_type,
            severity=request.severity,
            customer_id=request.customer_id,
            account_ids=request.account_ids,
            title=request.title,
            description=request.description,
            risk_score=request.risk_score,
            transaction_ids=request.transaction_ids,
            triggers=request.triggers,
            tags=request.tags,
            transaction_count=len(request.transaction_ids),
            due_date=datetime.utcnow() + timedelta(days=self._get_due_days(request.severity))
        )
        self._alerts[alert_id] = alert
        return alert

    def _get_due_days(self, severity: AlertSeverity) -> int:
        """Get due days based on severity"""
        severity_days = {
            AlertSeverity.LOW: 30,
            AlertSeverity.MEDIUM: 14,
            AlertSeverity.HIGH: 7,
            AlertSeverity.CRITICAL: 3
        }
        return severity_days.get(severity, 14)

    async def get_alert(self, alert_id: UUID) -> Optional[AMLAlert]:
        """Get alert by ID"""
        return self._alerts.get(alert_id)

    async def get_alert_by_number(self, alert_number: str) -> Optional[AMLAlert]:
        """Get alert by alert number"""
        for alert in self._alerts.values():
            if alert.alert_number == alert_number:
                return alert
        return None

    async def update_alert(
        self, alert_id: UUID, request: AlertUpdateRequest, updated_by: str
    ) -> Optional[AMLAlert]:
        """Update an existing alert"""
        alert = self._alerts.get(alert_id)
        if not alert:
            return None

        if request.status:
            alert.status = request.status
            if request.status in [AlertStatus.CLOSED_FALSE_POSITIVE, AlertStatus.CLOSED_TRUE_POSITIVE]:
                alert.closed_at = datetime.utcnow()

        if request.severity:
            alert.severity = request.severity
            alert.due_date = datetime.utcnow() + timedelta(days=self._get_due_days(request.severity))

        if request.current_assignee:
            alert.current_assignee = request.current_assignee

        if request.sar_required is not None:
            alert.sar_required = request.sar_required

        if request.due_date:
            alert.due_date = request.due_date

        if request.tags:
            alert.tags = request.tags

        alert.updated_at = datetime.utcnow()
        return alert

    async def assign_alert(
        self, alert_id: UUID, assignee: str, assigned_by: str, reason: Optional[str] = None
    ) -> Optional[AMLAlert]:
        """Assign alert to an analyst"""
        alert = self._alerts.get(alert_id)
        if not alert:
            return None

        assignment = AlertAssignment(
            assigned_to=assignee,
            assigned_by=assigned_by,
            reason=reason
        )
        alert.assignments.append(assignment)
        alert.current_assignee = assignee

        if alert.status == AlertStatus.NEW:
            alert.status = AlertStatus.ASSIGNED

        alert.updated_at = datetime.utcnow()
        return alert

    async def add_comment(
        self, alert_id: UUID, author_id: str, author_name: str, content: str, is_internal: bool = True
    ) -> Optional[AMLAlert]:
        """Add comment to an alert"""
        alert = self._alerts.get(alert_id)
        if not alert:
            return None

        comment = AlertComment(
            author_id=author_id,
            author_name=author_name,
            content=content,
            is_internal=is_internal
        )
        alert.comments.append(comment)
        alert.updated_at = datetime.utcnow()
        return alert

    async def add_evidence(
        self, alert_id: UUID, evidence: AlertEvidence
    ) -> Optional[AMLAlert]:
        """Add evidence to an alert"""
        alert = self._alerts.get(alert_id)
        if not alert:
            return None

        alert.evidence.append(evidence)
        alert.updated_at = datetime.utcnow()
        return alert

    async def escalate_alert(
        self, alert_id: UUID, escalated_by: str, reason: str
    ) -> Optional[AMLAlert]:
        """Escalate an alert"""
        alert = self._alerts.get(alert_id)
        if not alert:
            return None

        alert.status = AlertStatus.ESCALATED
        comment = AlertComment(
            author_id=escalated_by,
            author_name=escalated_by,
            content=f"Alert escalated: {reason}",
            is_internal=True
        )
        alert.comments.append(comment)
        alert.updated_at = datetime.utcnow()
        return alert

    async def close_alert(
        self, alert_id: UUID, closed_by: str, is_true_positive: bool, notes: str
    ) -> Optional[AMLAlert]:
        """Close an alert"""
        alert = self._alerts.get(alert_id)
        if not alert:
            return None

        alert.status = (
            AlertStatus.CLOSED_TRUE_POSITIVE if is_true_positive
            else AlertStatus.CLOSED_FALSE_POSITIVE
        )
        alert.closed_at = datetime.utcnow()

        comment = AlertComment(
            author_id=closed_by,
            author_name=closed_by,
            content=f"Alert closed: {notes}",
            is_internal=True
        )
        alert.comments.append(comment)
        alert.updated_at = datetime.utcnow()
        return alert

    async def link_to_case(self, alert_id: UUID, case_id: UUID) -> Optional[AMLAlert]:
        """Link alert to a case"""
        alert = self._alerts.get(alert_id)
        if not alert:
            return None

        alert.case_id = case_id
        alert.updated_at = datetime.utcnow()
        return alert

    async def search_alerts(self, criteria: AlertSearchCriteria) -> List[AlertSummary]:
        """Search alerts based on criteria"""
        results = []
        for alert in self._alerts.values():
            if not self._matches_criteria(alert, criteria):
                continue

            summary = AlertSummary(
                alert_id=alert.alert_id,
                alert_number=alert.alert_number,
                alert_type=alert.alert_type,
                severity=alert.severity,
                status=alert.status,
                customer_id=alert.customer_id,
                risk_score=alert.risk_score,
                created_at=alert.created_at,
                due_date=alert.due_date,
                current_assignee=alert.current_assignee,
                transaction_count=alert.transaction_count,
                total_amount=alert.total_transaction_amount
            )
            results.append(summary)

        # Sort results
        reverse = criteria.sort_order == "desc"
        results.sort(key=lambda x: getattr(x, criteria.sort_by), reverse=reverse)

        # Paginate
        start = (criteria.page - 1) * criteria.page_size
        end = start + criteria.page_size
        return results[start:end]

    def _matches_criteria(self, alert: AMLAlert, criteria: AlertSearchCriteria) -> bool:
        """Check if alert matches search criteria"""
        if criteria.alert_types and alert.alert_type not in criteria.alert_types:
            return False
        if criteria.severities and alert.severity not in criteria.severities:
            return False
        if criteria.statuses and alert.status not in criteria.statuses:
            return False
        if criteria.customer_ids and alert.customer_id not in criteria.customer_ids:
            return False
        if criteria.assignees and alert.current_assignee not in criteria.assignees:
            return False
        if criteria.date_from and alert.created_at < criteria.date_from:
            return False
        if criteria.date_to and alert.created_at > criteria.date_to:
            return False
        if criteria.min_risk_score and alert.risk_score < criteria.min_risk_score:
            return False
        if criteria.max_risk_score and alert.risk_score > criteria.max_risk_score:
            return False
        if criteria.overdue_only and alert.due_date and alert.due_date > datetime.utcnow():
            return False
        if criteria.unassigned_only and alert.current_assignee:
            return False
        return True

    async def get_statistics(self) -> AlertStatistics:
        """Get alert statistics"""
        stats = AlertStatistics()
        stats.total_alerts = len(self._alerts)

        for alert in self._alerts.values():
            # By severity
            severity_key = alert.severity.value
            stats.by_severity[severity_key] = stats.by_severity.get(severity_key, 0) + 1

            # By status
            status_key = alert.status.value
            stats.by_status[status_key] = stats.by_status.get(status_key, 0) + 1

            # By type
            type_key = alert.alert_type.value
            stats.by_type[type_key] = stats.by_type.get(type_key, 0) + 1

            # Overdue
            if alert.due_date and alert.due_date < datetime.utcnow() and alert.status not in [
                AlertStatus.CLOSED_FALSE_POSITIVE, AlertStatus.CLOSED_TRUE_POSITIVE, AlertStatus.SAR_FILED
            ]:
                stats.overdue_count += 1

            # Assignment
            if alert.current_assignee:
                stats.assigned_count += 1
            else:
                stats.unassigned_count += 1

        return stats

    async def get_alerts_for_customer(self, customer_id: str) -> List[AMLAlert]:
        """Get all alerts for a customer"""
        return [
            alert for alert in self._alerts.values()
            if alert.customer_id == customer_id
        ]

    async def get_open_alerts(self) -> List[AMLAlert]:
        """Get all open alerts"""
        open_statuses = [AlertStatus.NEW, AlertStatus.ASSIGNED, AlertStatus.UNDER_REVIEW]
        return [
            alert for alert in self._alerts.values()
            if alert.status in open_statuses
        ]

    async def bulk_assign_alerts(
        self, alert_ids: List[UUID], assignee: str, assigned_by: str
    ) -> int:
        """Bulk assign multiple alerts"""
        count = 0
        for alert_id in alert_ids:
            result = await self.assign_alert(alert_id, assignee, assigned_by)
            if result:
                count += 1
        return count


# Global service instance
alert_service = AlertService()
