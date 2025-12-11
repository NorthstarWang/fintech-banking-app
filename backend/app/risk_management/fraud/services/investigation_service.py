"""Investigation Service - Fraud investigation workflow management"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from ..models.fraud_investigation_models import (
    FraudInvestigation, DisputeRecord, InvestigationTemplate,
    InvestigationStatus, InvestigationType, InvestigationOutcome,
    InvestigationStep, CustomerContact, InvestigationStatistics
)


class InvestigationService:
    def __init__(self):
        self._investigations: Dict[UUID, FraudInvestigation] = {}
        self._disputes: Dict[UUID, DisputeRecord] = {}
        self._templates: Dict[UUID, InvestigationTemplate] = {}
        self._counter = 0
        self._initialize_templates()

    def _initialize_templates(self):
        standard_template = InvestigationTemplate(
            template_name="Standard Fraud Investigation",
            investigation_type=InvestigationType.STANDARD,
            description="Standard investigation workflow",
            required_steps=[
                {"step_name": "Review Alert", "step_type": "review", "order": 1},
                {"step_name": "Customer Contact", "step_type": "contact", "order": 2},
                {"step_name": "Transaction Analysis", "step_type": "analysis", "order": 3},
                {"step_name": "Make Decision", "step_type": "decision", "order": 4},
            ],
            default_sla_hours=48,
            created_by="system"
        )
        self._templates[standard_template.template_id] = standard_template

    def _generate_number(self) -> str:
        self._counter += 1
        return f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{self._counter:06d}"

    async def create_investigation(self, case_id: UUID, customer_id: str, customer_name: str, disputed_amount: float, investigation_type: InvestigationType = InvestigationType.STANDARD) -> FraudInvestigation:
        template = next((t for t in self._templates.values() if t.investigation_type == investigation_type), None)
        steps = []
        if template:
            for step_config in template.required_steps:
                steps.append(InvestigationStep(
                    step_name=step_config["step_name"],
                    step_type=step_config["step_type"],
                    order=step_config["order"]
                ))
            sla_hours = template.default_sla_hours
        else:
            sla_hours = 48
        investigation = FraudInvestigation(
            investigation_number=self._generate_number(),
            case_id=case_id,
            investigation_type=investigation_type,
            customer_id=customer_id,
            customer_name=customer_name,
            disputed_amount=disputed_amount,
            steps=steps,
            sla_deadline=datetime.utcnow() + timedelta(hours=sla_hours)
        )
        self._investigations[investigation.investigation_id] = investigation
        return investigation

    async def get_investigation(self, investigation_id: UUID) -> Optional[FraudInvestigation]:
        return self._investigations.get(investigation_id)

    async def update_status(self, investigation_id: UUID, status: InvestigationStatus) -> Optional[FraudInvestigation]:
        investigation = self._investigations.get(investigation_id)
        if investigation:
            investigation.status = status
            investigation.updated_at = datetime.utcnow()
            if status == InvestigationStatus.COMPLETED:
                investigation.completed_at = datetime.utcnow()
        return investigation

    async def assign_investigator(self, investigation_id: UUID, investigator: str) -> Optional[FraudInvestigation]:
        investigation = self._investigations.get(investigation_id)
        if investigation:
            investigation.assigned_investigator = investigator
            investigation.status = InvestigationStatus.IN_PROGRESS
            investigation.updated_at = datetime.utcnow()
        return investigation

    async def complete_step(self, investigation_id: UUID, step_index: int, result: str, notes: str, completed_by: str) -> Optional[FraudInvestigation]:
        investigation = self._investigations.get(investigation_id)
        if investigation and step_index < len(investigation.steps):
            step = investigation.steps[step_index]
            step.status = "completed"
            step.result = result
            step.notes = notes
            step.completed_at = datetime.utcnow()
            if step_index + 1 < len(investigation.steps):
                investigation.current_step = step_index + 1
            investigation.updated_at = datetime.utcnow()
        return investigation

    async def record_customer_contact(self, investigation_id: UUID, contact: CustomerContact) -> Optional[FraudInvestigation]:
        investigation = self._investigations.get(investigation_id)
        if investigation:
            investigation.customer_contacts.append(contact)
            investigation.updated_at = datetime.utcnow()
        return investigation

    async def set_outcome(self, investigation_id: UUID, outcome: InvestigationOutcome, reason: str) -> Optional[FraudInvestigation]:
        investigation = self._investigations.get(investigation_id)
        if investigation:
            investigation.outcome = outcome
            investigation.outcome_reason = reason
            investigation.status = InvestigationStatus.COMPLETED
            investigation.completed_at = datetime.utcnow()
        return investigation

    async def process_refund(self, investigation_id: UUID, refund_amount: float) -> Optional[FraudInvestigation]:
        investigation = self._investigations.get(investigation_id)
        if investigation:
            investigation.refund_amount = refund_amount
            investigation.refund_processed = True
            investigation.updated_at = datetime.utcnow()
        return investigation

    async def create_dispute(self, investigation_id: UUID, customer_id: str, account_id: str, transaction_id: str, amount: float, reason: str, statement: str) -> DisputeRecord:
        dispute = DisputeRecord(
            investigation_id=investigation_id,
            customer_id=customer_id,
            account_id=account_id,
            transaction_id=transaction_id,
            transaction_date=datetime.utcnow(),
            transaction_amount=amount,
            dispute_reason=reason,
            customer_statement=statement
        )
        self._disputes[dispute.dispute_id] = dispute
        return dispute

    async def get_statistics(self) -> InvestigationStatistics:
        stats = InvestigationStatistics(total_investigations=len(self._investigations))
        now = datetime.utcnow()
        for inv in self._investigations.values():
            stats.by_status[inv.status.value] = stats.by_status.get(inv.status.value, 0) + 1
            stats.by_type[inv.investigation_type.value] = stats.by_type.get(inv.investigation_type.value, 0) + 1
            stats.total_disputed_amount += inv.disputed_amount
            stats.total_refunded += inv.refund_amount
            if inv.outcome:
                stats.by_outcome[inv.outcome.value] = stats.by_outcome.get(inv.outcome.value, 0) + 1
            if inv.status not in [InvestigationStatus.COMPLETED, InvestigationStatus.CANCELLED]:
                stats.open_investigations += 1
                if inv.sla_deadline < now:
                    stats.overdue_investigations += 1
        return stats


investigation_service = InvestigationService()
