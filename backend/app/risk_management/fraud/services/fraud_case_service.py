"""Fraud Case Service - Manages fraud investigation cases"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from ..models.fraud_case_models import CaseAction, CaseFinding, FraudCase, FraudCaseStatistics, FraudCaseStatus


class FraudCaseService:
    def __init__(self):
        self._cases: dict[UUID, FraudCase] = {}
        self._counter = 0

    def _generate_number(self) -> str:
        self._counter += 1
        return f"FCASE-{datetime.now(UTC).strftime('%Y%m%d')}-{self._counter:06d}"

    async def create_case(self, customer_id: str, customer_name: str, fraud_type: str, alert_ids: list[UUID] | None = None) -> FraudCase:
        case = FraudCase(
            case_number=self._generate_number(),
            title=f"Fraud Investigation - {customer_name}",
            description=f"Investigation for potential {fraud_type}",
            customer_id=customer_id,
            customer_name=customer_name,
            fraud_type=fraud_type,
            alert_ids=alert_ids or [],
            due_date=datetime.now(UTC) + timedelta(days=14)
        )
        self._cases[case.case_id] = case
        return case

    async def get_case(self, case_id: UUID) -> FraudCase | None:
        return self._cases.get(case_id)

    async def update_status(self, case_id: UUID, status: FraudCaseStatus) -> FraudCase | None:
        case = self._cases.get(case_id)
        if case:
            case.status = status
            case.updated_at = datetime.now(UTC)
            if status == FraudCaseStatus.CONFIRMED_FRAUD:
                case.fraud_confirmed = True
            if status == FraudCaseStatus.CLOSED:
                case.closed_at = datetime.now(UTC)
        return case

    async def assign_case(self, case_id: UUID, assignee: str) -> FraudCase | None:
        case = self._cases.get(case_id)
        if case:
            case.assigned_to = assignee
            case.status = FraudCaseStatus.IN_PROGRESS
            case.updated_at = datetime.now(UTC)
        return case

    async def add_action(self, case_id: UUID, action: CaseAction) -> FraudCase | None:
        case = self._cases.get(case_id)
        if case:
            case.actions.append(action)
            case.updated_at = datetime.now(UTC)
        return case

    async def add_finding(self, case_id: UUID, finding: CaseFinding) -> FraudCase | None:
        case = self._cases.get(case_id)
        if case:
            case.findings.append(finding)
            case.updated_at = datetime.now(UTC)
        return case

    async def update_recovery(self, case_id: UUID, recovered_amount: float) -> FraudCase | None:
        case = self._cases.get(case_id)
        if case:
            case.recovered_amount = recovered_amount
            case.updated_at = datetime.now(UTC)
        return case

    async def get_statistics(self) -> FraudCaseStatistics:
        stats = FraudCaseStatistics(total_cases=len(self._cases))
        now = datetime.now(UTC)
        for case in self._cases.values():
            stats.by_status[case.status.value] = stats.by_status.get(case.status.value, 0) + 1
            stats.by_priority[case.priority.value] = stats.by_priority.get(case.priority.value, 0) + 1
            stats.total_fraud_amount += case.total_fraud_amount
            stats.total_recovered += case.recovered_amount
            if case.fraud_confirmed:
                stats.confirmed_fraud_cases += 1
            if case.status not in [FraudCaseStatus.CLOSED, FraudCaseStatus.NOT_FRAUD]:
                stats.open_cases += 1
            if case.due_date and case.due_date < now and case.status != FraudCaseStatus.CLOSED:
                stats.overdue_cases += 1
        if stats.total_fraud_amount > 0:
            stats.recovery_rate = stats.total_recovered / stats.total_fraud_amount * 100
        return stats


fraud_case_service = FraudCaseService()
