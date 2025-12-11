"""
AML Case Service

Handles case management for AML investigations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from ..models.case_models import (
    AMLCase, CaseSummary, CaseStatistics, CaseStatus, CasePriority, CaseCategory,
    InvestigationFinding, CaseTimeline, CaseDocument, RelatedEntity, CaseAssignment,
    CaseCreateRequest, CaseUpdateRequest, CaseSearchCriteria
)


class CaseService:
    """Service for managing AML investigation cases"""

    def __init__(self):
        self._cases: Dict[UUID, AMLCase] = {}
        self._case_counter = 0

    def _generate_case_number(self) -> str:
        """Generate unique case number"""
        self._case_counter += 1
        return f"CASE-{datetime.utcnow().strftime('%Y%m%d')}-{self._case_counter:06d}"

    async def create_case(self, request: CaseCreateRequest, created_by: str) -> AMLCase:
        """Create a new AML case"""
        case_id = uuid4()
        case = AMLCase(
            case_id=case_id,
            case_number=self._generate_case_number(),
            title=request.title,
            description=request.description,
            category=request.category,
            priority=request.priority,
            primary_subject_id=request.primary_subject_id,
            primary_subject_type=request.primary_subject_type,
            primary_subject_name=request.primary_subject_name,
            alert_ids=request.alert_ids,
            tags=request.tags,
            due_date=datetime.utcnow() + timedelta(days=self._get_due_days(request.priority))
        )

        # Add initial timeline entry
        timeline_entry = CaseTimeline(
            activity_type="case_created",
            description=f"Case created by {created_by}",
            actor_id=created_by,
            actor_name=created_by
        )
        case.timeline.append(timeline_entry)

        self._cases[case_id] = case
        return case

    def _get_due_days(self, priority: CasePriority) -> int:
        """Get due days based on priority"""
        priority_days = {
            CasePriority.LOW: 90,
            CasePriority.MEDIUM: 60,
            CasePriority.HIGH: 30,
            CasePriority.URGENT: 14
        }
        return priority_days.get(priority, 60)

    async def get_case(self, case_id: UUID) -> Optional[AMLCase]:
        """Get case by ID"""
        return self._cases.get(case_id)

    async def get_case_by_number(self, case_number: str) -> Optional[AMLCase]:
        """Get case by case number"""
        for case in self._cases.values():
            if case.case_number == case_number:
                return case
        return None

    async def update_case(
        self, case_id: UUID, request: CaseUpdateRequest, updated_by: str
    ) -> Optional[AMLCase]:
        """Update an existing case"""
        case = self._cases.get(case_id)
        if not case:
            return None

        changes = []

        if request.title and request.title != case.title:
            changes.append(f"Title changed from '{case.title}' to '{request.title}'")
            case.title = request.title

        if request.status and request.status != case.status:
            changes.append(f"Status changed from {case.status.value} to {request.status.value}")
            case.status = request.status
            if request.status == CaseStatus.OPEN and not case.opened_at:
                case.opened_at = datetime.utcnow()
            elif request.status in [CaseStatus.CLOSED_NO_ACTION, CaseStatus.CLOSED_WITH_ACTION]:
                case.closed_at = datetime.utcnow()

        if request.priority and request.priority != case.priority:
            changes.append(f"Priority changed from {case.priority.value} to {request.priority.value}")
            case.priority = request.priority

        if request.category and request.category != case.category:
            changes.append(f"Category changed from {case.category.value} to {request.category.value}")
            case.category = request.category

        if request.lead_investigator:
            case.lead_investigator = request.lead_investigator

        if request.sar_required is not None:
            case.sar_required = request.sar_required

        if request.sar_deadline:
            case.sar_deadline = request.sar_deadline

        if request.due_date:
            case.due_date = request.due_date

        if request.tags:
            case.tags = request.tags

        # Add timeline entry for changes
        if changes:
            timeline_entry = CaseTimeline(
                activity_type="case_updated",
                description="; ".join(changes),
                actor_id=updated_by,
                actor_name=updated_by
            )
            case.timeline.append(timeline_entry)

        case.updated_at = datetime.utcnow()
        return case

    async def open_case(self, case_id: UUID, opened_by: str) -> Optional[AMLCase]:
        """Open a case for investigation"""
        case = self._cases.get(case_id)
        if not case:
            return None

        case.status = CaseStatus.OPEN
        case.opened_at = datetime.utcnow()

        timeline_entry = CaseTimeline(
            activity_type="case_opened",
            description=f"Case opened for investigation",
            actor_id=opened_by,
            actor_name=opened_by
        )
        case.timeline.append(timeline_entry)
        case.updated_at = datetime.utcnow()
        return case

    async def assign_case(
        self, case_id: UUID, assignee: str, assigned_by: str, role: str = "investigator"
    ) -> Optional[AMLCase]:
        """Assign case to an investigator"""
        case = self._cases.get(case_id)
        if not case:
            return None

        assignment = CaseAssignment(
            assigned_to=assignee,
            assigned_by=assigned_by,
            role=role,
            is_primary=role == "lead_investigator"
        )
        case.assignments.append(assignment)

        if role == "lead_investigator":
            case.lead_investigator = assignee

        timeline_entry = CaseTimeline(
            activity_type="case_assigned",
            description=f"Case assigned to {assignee} as {role}",
            actor_id=assigned_by,
            actor_name=assigned_by
        )
        case.timeline.append(timeline_entry)
        case.updated_at = datetime.utcnow()
        return case

    async def add_finding(
        self, case_id: UUID, finding: InvestigationFinding
    ) -> Optional[AMLCase]:
        """Add investigation finding to case"""
        case = self._cases.get(case_id)
        if not case:
            return None

        case.findings.append(finding)

        timeline_entry = CaseTimeline(
            activity_type="finding_added",
            description=f"New finding added: {finding.finding_type}",
            actor_id=finding.created_by,
            actor_name=finding.created_by
        )
        case.timeline.append(timeline_entry)
        case.updated_at = datetime.utcnow()
        return case

    async def add_document(
        self, case_id: UUID, document: CaseDocument
    ) -> Optional[AMLCase]:
        """Add document to case"""
        case = self._cases.get(case_id)
        if not case:
            return None

        case.documents.append(document)

        timeline_entry = CaseTimeline(
            activity_type="document_added",
            description=f"Document added: {document.document_name}",
            actor_id=document.uploaded_by,
            actor_name=document.uploaded_by
        )
        case.timeline.append(timeline_entry)
        case.updated_at = datetime.utcnow()
        return case

    async def add_related_entity(
        self, case_id: UUID, entity: RelatedEntity, added_by: str
    ) -> Optional[AMLCase]:
        """Add related entity to case"""
        case = self._cases.get(case_id)
        if not case:
            return None

        case.related_entities.append(entity)

        timeline_entry = CaseTimeline(
            activity_type="entity_added",
            description=f"Related entity added: {entity.entity_name}",
            actor_id=added_by,
            actor_name=added_by
        )
        case.timeline.append(timeline_entry)
        case.updated_at = datetime.utcnow()
        return case

    async def link_alert(self, case_id: UUID, alert_id: UUID, linked_by: str) -> Optional[AMLCase]:
        """Link an alert to the case"""
        case = self._cases.get(case_id)
        if not case:
            return None

        if alert_id not in case.alert_ids:
            case.alert_ids.append(alert_id)

            timeline_entry = CaseTimeline(
                activity_type="alert_linked",
                description=f"Alert {alert_id} linked to case",
                actor_id=linked_by,
                actor_name=linked_by
            )
            case.timeline.append(timeline_entry)
            case.updated_at = datetime.utcnow()

        return case

    async def escalate_case(
        self, case_id: UUID, escalated_by: str, reason: str
    ) -> Optional[AMLCase]:
        """Escalate a case"""
        case = self._cases.get(case_id)
        if not case:
            return None

        case.status = CaseStatus.ESCALATED

        timeline_entry = CaseTimeline(
            activity_type="case_escalated",
            description=f"Case escalated: {reason}",
            actor_id=escalated_by,
            actor_name=escalated_by
        )
        case.timeline.append(timeline_entry)
        case.updated_at = datetime.utcnow()
        return case

    async def close_case(
        self, case_id: UUID, closed_by: str, resolution_type: str, resolution_summary: str
    ) -> Optional[AMLCase]:
        """Close a case"""
        case = self._cases.get(case_id)
        if not case:
            return None

        case.status = (
            CaseStatus.CLOSED_WITH_ACTION if resolution_type == "with_action"
            else CaseStatus.CLOSED_NO_ACTION
        )
        case.resolution_type = resolution_type
        case.resolution_summary = resolution_summary
        case.resolved_by = closed_by
        case.closed_at = datetime.utcnow()

        timeline_entry = CaseTimeline(
            activity_type="case_closed",
            description=f"Case closed: {resolution_summary}",
            actor_id=closed_by,
            actor_name=closed_by
        )
        case.timeline.append(timeline_entry)
        case.updated_at = datetime.utcnow()
        return case

    async def search_cases(self, criteria: CaseSearchCriteria) -> List[CaseSummary]:
        """Search cases based on criteria"""
        results = []
        for case in self._cases.values():
            if not self._matches_criteria(case, criteria):
                continue

            summary = CaseSummary(
                case_id=case.case_id,
                case_number=case.case_number,
                title=case.title,
                status=case.status,
                priority=case.priority,
                category=case.category,
                primary_subject_name=case.primary_subject_name,
                alert_count=len(case.alert_ids),
                total_suspicious_amount=case.total_suspicious_amount,
                lead_investigator=case.lead_investigator,
                created_at=case.created_at,
                due_date=case.due_date,
                sar_required=case.sar_required
            )
            results.append(summary)

        # Sort results
        reverse = criteria.sort_order == "desc"
        results.sort(key=lambda x: getattr(x, criteria.sort_by), reverse=reverse)

        # Paginate
        start = (criteria.page - 1) * criteria.page_size
        end = start + criteria.page_size
        return results[start:end]

    def _matches_criteria(self, case: AMLCase, criteria: CaseSearchCriteria) -> bool:
        """Check if case matches search criteria"""
        if criteria.statuses and case.status not in criteria.statuses:
            return False
        if criteria.priorities and case.priority not in criteria.priorities:
            return False
        if criteria.categories and case.category not in criteria.categories:
            return False
        if criteria.investigators and case.lead_investigator not in criteria.investigators:
            return False
        if criteria.subject_ids and case.primary_subject_id not in criteria.subject_ids:
            return False
        if criteria.date_from and case.created_at < criteria.date_from:
            return False
        if criteria.date_to and case.created_at > criteria.date_to:
            return False
        if criteria.min_amount and case.total_suspicious_amount < criteria.min_amount:
            return False
        if criteria.max_amount and case.total_suspicious_amount > criteria.max_amount:
            return False
        if criteria.sar_required is not None and case.sar_required != criteria.sar_required:
            return False
        if criteria.overdue_only and case.due_date and case.due_date > datetime.utcnow():
            return False
        return True

    async def get_statistics(self) -> CaseStatistics:
        """Get case statistics"""
        stats = CaseStatistics()
        stats.total_cases = len(self._cases)

        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        for case in self._cases.values():
            # By status
            status_key = case.status.value
            stats.by_status[status_key] = stats.by_status.get(status_key, 0) + 1

            # By priority
            priority_key = case.priority.value
            stats.by_priority[priority_key] = stats.by_priority.get(priority_key, 0) + 1

            # By category
            category_key = case.category.value
            stats.by_category[category_key] = stats.by_category.get(category_key, 0) + 1

            # Open cases
            if case.status not in [CaseStatus.CLOSED_NO_ACTION, CaseStatus.CLOSED_WITH_ACTION]:
                stats.open_cases += 1

            # Closed this month
            if case.closed_at and case.closed_at >= month_start:
                stats.closed_this_month += 1

            # Overdue
            if case.due_date and case.due_date < now and case.status not in [
                CaseStatus.CLOSED_NO_ACTION, CaseStatus.CLOSED_WITH_ACTION
            ]:
                stats.overdue_count += 1

        return stats

    async def get_cases_for_subject(self, subject_id: str) -> List[AMLCase]:
        """Get all cases for a subject"""
        return [
            case for case in self._cases.values()
            if case.primary_subject_id == subject_id
        ]


# Global service instance
case_service = CaseService()
