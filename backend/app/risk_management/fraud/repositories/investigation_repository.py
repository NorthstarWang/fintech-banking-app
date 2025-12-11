"""Investigation Repository - Data access layer for fraud investigations"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from ..models.fraud_investigation_models import (
    FraudInvestigation, DisputeRecord, InvestigationTemplate,
    InvestigationStatus, InvestigationType, InvestigationOutcome
)


class InvestigationRepository:
    def __init__(self):
        self._investigations: Dict[UUID, FraudInvestigation] = {}
        self._disputes: Dict[UUID, DisputeRecord] = {}
        self._templates: Dict[UUID, InvestigationTemplate] = {}
        self._number_index: Dict[str, UUID] = {}
        self._case_index: Dict[UUID, List[UUID]] = {}
        self._customer_index: Dict[str, List[UUID]] = {}

    async def save_investigation(self, investigation: FraudInvestigation) -> FraudInvestigation:
        self._investigations[investigation.investigation_id] = investigation
        self._number_index[investigation.investigation_number] = investigation.investigation_id
        if investigation.case_id not in self._case_index:
            self._case_index[investigation.case_id] = []
        if investigation.investigation_id not in self._case_index[investigation.case_id]:
            self._case_index[investigation.case_id].append(investigation.investigation_id)
        if investigation.customer_id not in self._customer_index:
            self._customer_index[investigation.customer_id] = []
        if investigation.investigation_id not in self._customer_index[investigation.customer_id]:
            self._customer_index[investigation.customer_id].append(investigation.investigation_id)
        return investigation

    async def find_investigation_by_id(self, investigation_id: UUID) -> Optional[FraudInvestigation]:
        return self._investigations.get(investigation_id)

    async def find_investigation_by_number(self, number: str) -> Optional[FraudInvestigation]:
        investigation_id = self._number_index.get(number)
        if investigation_id:
            return self._investigations.get(investigation_id)
        return None

    async def find_investigations_by_case(self, case_id: UUID) -> List[FraudInvestigation]:
        inv_ids = self._case_index.get(case_id, [])
        return [self._investigations[iid] for iid in inv_ids if iid in self._investigations]

    async def find_investigations_by_customer(self, customer_id: str, limit: int = 100) -> List[FraudInvestigation]:
        inv_ids = self._customer_index.get(customer_id, [])
        investigations = [self._investigations[iid] for iid in inv_ids if iid in self._investigations]
        return sorted(investigations, key=lambda x: x.created_at, reverse=True)[:limit]

    async def find_investigations_by_status(self, status: InvestigationStatus, limit: int = 100) -> List[FraudInvestigation]:
        investigations = [i for i in self._investigations.values() if i.status == status]
        return sorted(investigations, key=lambda x: x.created_at, reverse=True)[:limit]

    async def find_investigations_by_type(self, inv_type: InvestigationType, limit: int = 100) -> List[FraudInvestigation]:
        investigations = [i for i in self._investigations.values() if i.investigation_type == inv_type]
        return sorted(investigations, key=lambda x: x.created_at, reverse=True)[:limit]

    async def find_open_investigations(self, limit: int = 100) -> List[FraudInvestigation]:
        open_statuses = [InvestigationStatus.OPEN, InvestigationStatus.IN_PROGRESS, InvestigationStatus.PENDING_REVIEW]
        investigations = [i for i in self._investigations.values() if i.status in open_statuses]
        return sorted(investigations, key=lambda x: x.sla_deadline or x.created_at)[:limit]

    async def find_overdue_investigations(self, limit: int = 100) -> List[FraudInvestigation]:
        now = datetime.utcnow()
        overdue = [
            i for i in self._investigations.values()
            if i.sla_deadline and i.sla_deadline < now
            and i.status not in [InvestigationStatus.COMPLETED, InvestigationStatus.CANCELLED]
        ]
        return sorted(overdue, key=lambda x: x.sla_deadline)[:limit]

    async def find_investigations_by_investigator(self, investigator: str, limit: int = 100) -> List[FraudInvestigation]:
        investigations = [i for i in self._investigations.values() if i.assigned_investigator == investigator]
        return sorted(investigations, key=lambda x: x.created_at, reverse=True)[:limit]

    async def find_investigations_by_outcome(self, outcome: InvestigationOutcome, limit: int = 100) -> List[FraudInvestigation]:
        investigations = [i for i in self._investigations.values() if i.outcome == outcome]
        return sorted(investigations, key=lambda x: x.completed_at or x.created_at, reverse=True)[:limit]

    async def update_investigation(self, investigation: FraudInvestigation) -> FraudInvestigation:
        investigation.updated_at = datetime.utcnow()
        self._investigations[investigation.investigation_id] = investigation
        return investigation

    async def save_dispute(self, dispute: DisputeRecord) -> DisputeRecord:
        self._disputes[dispute.dispute_id] = dispute
        return dispute

    async def find_dispute_by_id(self, dispute_id: UUID) -> Optional[DisputeRecord]:
        return self._disputes.get(dispute_id)

    async def find_disputes_by_investigation(self, investigation_id: UUID) -> List[DisputeRecord]:
        return [d for d in self._disputes.values() if d.investigation_id == investigation_id]

    async def find_disputes_by_customer(self, customer_id: str, limit: int = 100) -> List[DisputeRecord]:
        disputes = [d for d in self._disputes.values() if d.customer_id == customer_id]
        return sorted(disputes, key=lambda x: x.filed_at, reverse=True)[:limit]

    async def update_dispute(self, dispute: DisputeRecord) -> DisputeRecord:
        self._disputes[dispute.dispute_id] = dispute
        return dispute

    async def save_template(self, template: InvestigationTemplate) -> InvestigationTemplate:
        self._templates[template.template_id] = template
        return template

    async def find_template_by_id(self, template_id: UUID) -> Optional[InvestigationTemplate]:
        return self._templates.get(template_id)

    async def find_active_templates(self) -> List[InvestigationTemplate]:
        return [t for t in self._templates.values() if t.is_active]

    async def find_templates_by_type(self, inv_type: InvestigationType) -> List[InvestigationTemplate]:
        return [t for t in self._templates.values() if t.investigation_type == inv_type]

    async def get_investigation_statistics(self) -> Dict[str, Any]:
        now = datetime.utcnow()
        total = len(self._investigations)
        open_count = len([i for i in self._investigations.values() if i.status in [InvestigationStatus.OPEN, InvestigationStatus.IN_PROGRESS]])
        completed_count = len([i for i in self._investigations.values() if i.status == InvestigationStatus.COMPLETED])
        overdue_count = len([i for i in self._investigations.values() if i.sla_deadline and i.sla_deadline < now and i.status not in [InvestigationStatus.COMPLETED, InvestigationStatus.CANCELLED]])
        total_disputed = sum(i.disputed_amount for i in self._investigations.values())
        total_refunded = sum(i.refund_amount for i in self._investigations.values())
        return {
            "total_investigations": total,
            "open_investigations": open_count,
            "completed_investigations": completed_count,
            "overdue_investigations": overdue_count,
            "total_disputed_amount": total_disputed,
            "total_refunded_amount": total_refunded,
            "total_disputes": len(self._disputes)
        }

    async def get_all_investigations(self, limit: int = 500, offset: int = 0) -> List[FraudInvestigation]:
        investigations = sorted(self._investigations.values(), key=lambda x: x.created_at, reverse=True)
        return investigations[offset:offset + limit]

    async def count_investigations(self) -> int:
        return len(self._investigations)


investigation_repository = InvestigationRepository()
