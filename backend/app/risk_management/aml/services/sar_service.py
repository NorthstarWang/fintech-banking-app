"""
SAR Service

Handles Suspicious Activity Report creation, management, and filing.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from ..models.sar_models import (
    SAR, SARSummary, SARStatistics, SARStatus, SARType, SuspiciousActivityType,
    FilingInstitution, SubjectInfo, SuspiciousActivity, TransactionDetail,
    Narrative, SARDocument, SARApproval, SARSubmission,
    SARCreateRequest, SARUpdateRequest, SARSearchCriteria
)


class SARService:
    """Service for SAR management and filing"""

    def __init__(self):
        self._sars: Dict[UUID, SAR] = {}
        self._sar_counter = 0
        self._default_institution = FilingInstitution(
            institution_name="BankFlow Financial",
            institution_type="Bank",
            ein="12-3456789",
            address="123 Financial Street",
            city="New York",
            state="NY",
            zip_code="10001",
            country="US",
            regulator="OCC",
            regulatory_id="BK-123456"
        )

    def _generate_sar_number(self) -> str:
        """Generate unique SAR number"""
        self._sar_counter += 1
        return f"SAR-{datetime.utcnow().strftime('%Y%m%d')}-{self._sar_counter:06d}"

    async def create_sar(self, request: SARCreateRequest, created_by: str) -> SAR:
        """Create a new SAR"""
        sar_id = uuid4()

        # Calculate filing deadline (30 days from detection for most cases)
        filing_deadline = datetime.utcnow() + timedelta(days=30)

        sar = SAR(
            sar_id=sar_id,
            sar_number=self._generate_sar_number(),
            sar_type=request.sar_type,
            prior_sar_number=request.prior_sar_number,
            filing_institution=self._default_institution,
            primary_activity_type=request.primary_activity_type,
            case_ids=request.case_ids,
            alert_ids=request.alert_ids,
            filing_deadline=filing_deadline,
            prepared_by=created_by
        )

        self._sars[sar_id] = sar
        return sar

    async def get_sar(self, sar_id: UUID) -> Optional[SAR]:
        """Get SAR by ID"""
        return self._sars.get(sar_id)

    async def get_sar_by_number(self, sar_number: str) -> Optional[SAR]:
        """Get SAR by SAR number"""
        for sar in self._sars.values():
            if sar.sar_number == sar_number:
                return sar
        return None

    async def update_sar(
        self, sar_id: UUID, request: SARUpdateRequest, updated_by: str
    ) -> Optional[SAR]:
        """Update a SAR"""
        sar = self._sars.get(sar_id)
        if not sar:
            return None

        if request.status:
            sar.status = request.status

        if request.subjects:
            sar.subjects = request.subjects

        if request.activities:
            sar.activities = request.activities
            # Update total amount
            sar.total_suspicious_amount = sum(a.total_amount for a in request.activities)

        if request.full_narrative:
            sar.full_narrative = request.full_narrative

        if request.law_enforcement_contacted is not None:
            sar.law_enforcement_contacted = request.law_enforcement_contacted

        if request.law_enforcement_agency:
            sar.law_enforcement_agency = request.law_enforcement_agency

        sar.updated_at = datetime.utcnow()
        return sar

    async def add_subject(self, sar_id: UUID, subject: SubjectInfo) -> Optional[SAR]:
        """Add subject to SAR"""
        sar = self._sars.get(sar_id)
        if not sar:
            return None

        sar.subjects.append(subject)
        sar.updated_at = datetime.utcnow()
        return sar

    async def add_activity(self, sar_id: UUID, activity: SuspiciousActivity) -> Optional[SAR]:
        """Add suspicious activity to SAR"""
        sar = self._sars.get(sar_id)
        if not sar:
            return None

        sar.activities.append(activity)
        sar.total_suspicious_amount += activity.total_amount
        sar.updated_at = datetime.utcnow()
        return sar

    async def add_transaction(self, sar_id: UUID, transaction: TransactionDetail) -> Optional[SAR]:
        """Add transaction detail to SAR"""
        sar = self._sars.get(sar_id)
        if not sar:
            return None

        sar.transactions.append(transaction)
        sar.transaction_count += 1
        sar.updated_at = datetime.utcnow()
        return sar

    async def add_narrative(
        self, sar_id: UUID, section: str, content: str, author: str
    ) -> Optional[Narrative]:
        """Add or update narrative section"""
        sar = self._sars.get(sar_id)
        if not sar:
            return None

        # Check if section exists
        for narrative in sar.narratives:
            if narrative.section == section:
                narrative.content = content
                narrative.modified_by = author
                narrative.modified_at = datetime.utcnow()
                narrative.version += 1
                sar.updated_at = datetime.utcnow()
                return narrative

        # Create new section
        narrative = Narrative(
            section=section,
            content=content,
            created_by=author
        )
        sar.narratives.append(narrative)

        # Update full narrative
        await self._compile_full_narrative(sar)
        sar.updated_at = datetime.utcnow()
        return narrative

    async def _compile_full_narrative(self, sar: SAR):
        """Compile full narrative from sections"""
        sections_order = ["who", "what", "when", "where", "why", "how"]
        narratives_dict = {n.section: n.content for n in sar.narratives}

        full_text_parts = []
        for section in sections_order:
            if section in narratives_dict:
                full_text_parts.append(f"[{section.upper()}]\n{narratives_dict[section]}")

        sar.full_narrative = "\n\n".join(full_text_parts)

    async def add_document(self, sar_id: UUID, document: SARDocument) -> Optional[SAR]:
        """Add supporting document to SAR"""
        sar = self._sars.get(sar_id)
        if not sar:
            return None

        sar.documents.append(document)
        sar.updated_at = datetime.utcnow()
        return sar

    async def submit_for_approval(self, sar_id: UUID, submitted_by: str) -> Optional[SAR]:
        """Submit SAR for approval"""
        sar = self._sars.get(sar_id)
        if not sar:
            return None

        sar.status = SARStatus.PENDING_REVIEW
        sar.requires_approval_from = ["compliance_officer", "bsa_officer"]
        sar.updated_at = datetime.utcnow()
        return sar

    async def approve_sar(
        self, sar_id: UUID, approver_id: str, approver_name: str, approver_role: str, comments: Optional[str] = None
    ) -> Optional[SAR]:
        """Approve SAR"""
        sar = self._sars.get(sar_id)
        if not sar:
            return None

        approval = SARApproval(
            approver_id=approver_id,
            approver_name=approver_name,
            approver_role=approver_role,
            decision="approved",
            comments=comments
        )
        sar.approvals.append(approval)

        # Check if all required approvals received
        approved_roles = {a.approver_role for a in sar.approvals if a.decision == "approved"}
        required_roles = set(sar.requires_approval_from)

        if required_roles.issubset(approved_roles):
            sar.status = SARStatus.APPROVED

        sar.updated_at = datetime.utcnow()
        return sar

    async def reject_sar(
        self, sar_id: UUID, approver_id: str, approver_name: str, approver_role: str, reason: str
    ) -> Optional[SAR]:
        """Reject SAR for revisions"""
        sar = self._sars.get(sar_id)
        if not sar:
            return None

        approval = SARApproval(
            approver_id=approver_id,
            approver_name=approver_name,
            approver_role=approver_role,
            decision="rejected",
            comments=reason
        )
        sar.approvals.append(approval)
        sar.status = SARStatus.DRAFT
        sar.updated_at = datetime.utcnow()
        return sar

    async def file_sar(self, sar_id: UUID, submission_method: str = "efiling") -> Optional[SAR]:
        """File SAR with FinCEN"""
        sar = self._sars.get(sar_id)
        if not sar:
            return None

        if sar.status != SARStatus.APPROVED:
            raise ValueError("SAR must be approved before filing")

        submission = SARSubmission(
            submission_date=datetime.utcnow(),
            submission_method=submission_method,
            bsa_id=f"BSA-{uuid4().hex[:12].upper()}",
            response_received=True,
            response_date=datetime.utcnow(),
            response_status="accepted"
        )

        sar.submissions.append(submission)
        sar.last_submission = submission
        sar.status = SARStatus.SUBMITTED
        sar.submitted_at = datetime.utcnow()
        sar.updated_at = datetime.utcnow()

        return sar

    async def acknowledge_sar(
        self, sar_id: UUID, acknowledgment_number: str
    ) -> Optional[SAR]:
        """Record SAR acknowledgment from FinCEN"""
        sar = self._sars.get(sar_id)
        if not sar or not sar.last_submission:
            return None

        sar.last_submission.acknowledgment_number = acknowledgment_number
        sar.status = SARStatus.ACKNOWLEDGED
        sar.updated_at = datetime.utcnow()
        return sar

    async def request_extension(
        self, sar_id: UUID, reason: str, new_deadline: datetime, requested_by: str
    ) -> Optional[SAR]:
        """Request filing deadline extension"""
        sar = self._sars.get(sar_id)
        if not sar:
            return None

        sar.extension_granted = True
        sar.extension_reason = reason
        sar.new_deadline = new_deadline
        sar.updated_at = datetime.utcnow()
        return sar

    async def search_sars(self, criteria: SARSearchCriteria) -> List[SARSummary]:
        """Search SARs based on criteria"""
        results = []
        for sar in self._sars.values():
            if not self._matches_criteria(sar, criteria):
                continue

            primary_subject_name = "Unknown"
            if sar.subjects:
                subject = sar.subjects[sar.primary_subject_index]
                primary_subject_name = (
                    f"{subject.first_name} {subject.last_name}"
                    if subject.first_name else subject.entity_name or "Unknown"
                )

            summary = SARSummary(
                sar_id=sar.sar_id,
                sar_number=sar.sar_number,
                sar_type=sar.sar_type,
                status=sar.status,
                primary_subject_name=primary_subject_name,
                primary_activity_type=sar.primary_activity_type,
                total_amount=sar.total_suspicious_amount,
                filing_deadline=sar.new_deadline or sar.filing_deadline,
                prepared_by=sar.prepared_by,
                created_at=sar.created_at,
                submitted_at=sar.submitted_at
            )
            results.append(summary)

        # Sort results
        reverse = criteria.sort_order == "desc"
        results.sort(key=lambda x: getattr(x, criteria.sort_by), reverse=reverse)

        # Paginate
        start = (criteria.page - 1) * criteria.page_size
        end = start + criteria.page_size
        return results[start:end]

    def _matches_criteria(self, sar: SAR, criteria: SARSearchCriteria) -> bool:
        """Check if SAR matches search criteria"""
        if criteria.statuses and sar.status not in criteria.statuses:
            return False
        if criteria.sar_types and sar.sar_type not in criteria.sar_types:
            return False
        if criteria.activity_types and sar.primary_activity_type not in criteria.activity_types:
            return False
        if criteria.date_from and sar.created_at < criteria.date_from:
            return False
        if criteria.date_to and sar.created_at > criteria.date_to:
            return False
        if criteria.min_amount and sar.total_suspicious_amount < criteria.min_amount:
            return False
        if criteria.max_amount and sar.total_suspicious_amount > criteria.max_amount:
            return False
        if criteria.prepared_by and sar.prepared_by not in criteria.prepared_by:
            return False

        deadline = sar.new_deadline or sar.filing_deadline
        if criteria.overdue_only and deadline > datetime.utcnow():
            return False

        return True

    async def get_statistics(self) -> SARStatistics:
        """Get SAR statistics"""
        stats = SARStatistics()
        stats.total_sars = len(self._sars)

        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        quarter_start = now.replace(month=((now.month - 1) // 3) * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        for sar in self._sars.values():
            # By status
            status_key = sar.status.value
            stats.by_status[status_key] = stats.by_status.get(status_key, 0) + 1

            # By activity type
            activity_key = sar.primary_activity_type.value
            stats.by_activity_type[activity_key] = stats.by_activity_type.get(activity_key, 0) + 1

            # By SAR type
            type_key = sar.sar_type.value
            stats.by_sar_type[type_key] = stats.by_sar_type.get(type_key, 0) + 1

            # Filing counts
            if sar.submitted_at:
                if sar.submitted_at >= month_start:
                    stats.filed_this_month += 1
                if sar.submitted_at >= quarter_start:
                    stats.filed_this_quarter += 1
                if sar.submitted_at >= year_start:
                    stats.filed_this_year += 1

            # Pending
            if sar.status in [SARStatus.DRAFT, SARStatus.PENDING_REVIEW, SARStatus.APPROVED]:
                stats.pending_filing += 1

            # Overdue
            deadline = sar.new_deadline or sar.filing_deadline
            if deadline < now and sar.status not in [SARStatus.SUBMITTED, SARStatus.ACKNOWLEDGED]:
                stats.overdue += 1

        return stats


# Global service instance
sar_service = SARService()
