"""Fraud Case Service - Manages fraud investigation cases"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from ..models.fraud_case_models import (
    FraudCase, FraudCaseSummary, FraudCaseStatistics,
    FraudCaseStatus, FraudCasePriority, CaseAction, CaseFinding
)


class FraudCaseService:
    def __init__(self):
        self._cases: Dict[UUID, FraudCase] = {}
        self._counter = 0

    def _generate_number(self) -> str:
        self._counter += 1
        return f"FCASE-{datetime.utcnow().strftime('%Y%m%d')}-{self._counter:06d}"

    async def create_case(self, customer_id: str, customer_name: str, fraud_type: str, alert_ids: List[UUID] = None) -> FraudCase:
        case = FraudCase(
            case_number=self._generate_number(),
            title=f"Fraud Investigation - {customer_name}",
            description=f"Investigation for potential {fraud_type}",
            customer_id=customer_id,
            customer_name=customer_name,
            fraud_type=fraud_type,
            alert_ids=alert_ids or [],
            due_date=datetime.utcnow() + timedelta(days=14)
        )
        self._cases[case.case_id] = case
        return case

    async def get_case(self, case_id: UUID) -> Optional[FraudCase]:
        return self._cases.get(case_id)

    async def update_status(self, case_id: UUID, status: FraudCaseStatus) -> Optional[FraudCase]:
        case = self._cases.get(case_id)
        if case:
            case.status = status
            case.updated_at = datetime.utcnow()
            if status == FraudCaseStatus.CONFIRMED_FRAUD:
                case.fraud_confirmed = True
            if status == FraudCaseStatus.CLOSED:
                case.closed_at = datetime.utcnow()
        return case

    async def assign_case(self, case_id: UUID, assignee: str) -> Optional[FraudCase]:
        case = self._cases.get(case_id)
        if case:
            case.assigned_to = assignee
            case.status = FraudCaseStatus.IN_PROGRESS
            case.updated_at = datetime.utcnow()
        return case

    async def add_action(self, case_id: UUID, action: CaseAction) -> Optional[FraudCase]:
        case = self._cases.get(case_id)
        if case:
            case.actions.append(action)
            case.updated_at = datetime.utcnow()
        return case

    async def add_finding(self, case_id: UUID, finding: CaseFinding) -> Optional[FraudCase]:
        case = self._cases.get(case_id)
        if case:
            case.findings.append(finding)
            case.updated_at = datetime.utcnow()
        return case

    async def update_recovery(self, case_id: UUID, recovered_amount: float) -> Optional[FraudCase]:
        case = self._cases.get(case_id)
        if case:
            case.recovered_amount = recovered_amount
            case.updated_at = datetime.utcnow()
        return case

    async def get_statistics(self) -> FraudCaseStatistics:
        stats = FraudCaseStatistics(total_cases=len(self._cases))
        now = datetime.utcnow()
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
