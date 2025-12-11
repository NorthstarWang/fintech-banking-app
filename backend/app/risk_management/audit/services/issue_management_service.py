"""Issue Management Service - Business logic for issue tracking and remediation"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from ..models.issue_management_models import (
    Issue, ActionPlan, IssueUpdate, IssueValidation, IssueEscalation, IssueReport,
    IssueSource, IssuePriority, IssueStatus
)
from ..repositories.issue_management_repository import issue_management_repository


class IssueManagementService:
    def __init__(self):
        self.repository = issue_management_repository
        self._issue_counter = 0
        self._action_counter = 0

    async def create_issue(
        self, issue_title: str, source: IssueSource, priority: IssuePriority,
        description: str, impact: str, business_unit: str, identified_by: str,
        owner: str, due_date: date, source_reference: str = ""
    ) -> Issue:
        self._issue_counter += 1
        issue = Issue(
            issue_reference=f"ISS-{date.today().year}-{self._issue_counter:05d}",
            issue_title=issue_title, source=source, source_reference=source_reference,
            priority=priority, description=description, impact=impact,
            business_unit=business_unit, identified_date=date.today(),
            identified_by=identified_by, owner=owner, due_date=due_date
        )
        await self.repository.save_issue(issue)
        return issue

    async def create_action_plan(
        self, issue_id: UUID, action_description: str, action_type: str,
        owner: str, due_date: date, evidence_required: List[str]
    ) -> ActionPlan:
        self._action_counter += 1
        action = ActionPlan(
            issue_id=issue_id, action_reference=f"ACT-{self._action_counter:05d}",
            action_description=action_description, action_type=action_type,
            owner=owner, due_date=due_date, evidence_required=evidence_required
        )
        await self.repository.save_action_plan(action)
        return action

    async def update_action_progress(
        self, action_id: UUID, progress_percentage: int, evidence_provided: List[str],
        comments: str
    ) -> Optional[ActionPlan]:
        action = await self.repository.find_action_plan_by_id(action_id)
        if action:
            action.progress_percentage = progress_percentage
            action.evidence_provided = evidence_provided
            action.comments = comments
            if progress_percentage >= 100:
                action.status = "completed"
                action.completion_date = date.today()
        return action

    async def update_issue(
        self, issue_id: UUID, updated_by: str, update_type: str,
        progress_update: str, next_steps: str, blockers: List[str] = None
    ) -> IssueUpdate:
        issue = await self.repository.find_issue_by_id(issue_id)

        update = IssueUpdate(
            issue_id=issue_id, update_date=date.today(), updated_by=updated_by,
            update_type=update_type, previous_status=issue.status.value if issue else "",
            progress_update=progress_update, next_steps=next_steps,
            blockers=blockers or []
        )
        await self.repository.save_update(update)
        return update

    async def change_issue_status(
        self, issue_id: UUID, new_status: IssueStatus, updated_by: str
    ) -> Optional[Issue]:
        issue = await self.repository.find_issue_by_id(issue_id)
        if issue:
            old_status = issue.status
            issue.status = new_status

            update = IssueUpdate(
                issue_id=issue_id, update_date=date.today(), updated_by=updated_by,
                update_type="status_change", previous_status=old_status.value,
                new_status=new_status.value, progress_update=f"Status changed from {old_status.value} to {new_status.value}"
            )
            await self.repository.save_update(update)

        return issue

    async def validate_issue(
        self, issue_id: UUID, validator: str, validation_type: str,
        evidence_reviewed: List[str], tests_performed: List[str],
        validation_result: str, findings: str, recommendation: str
    ) -> IssueValidation:
        validation = IssueValidation(
            issue_id=issue_id, validation_date=date.today(), validator=validator,
            validation_type=validation_type, evidence_reviewed=evidence_reviewed,
            tests_performed=tests_performed, validation_result=validation_result,
            findings=findings, recommendation=recommendation,
            reopen_required=validation_result == "not_validated"
        )
        await self.repository.save_validation(validation)

        if validation_result == "validated":
            issue = await self.repository.find_issue_by_id(issue_id)
            if issue:
                issue.status = IssueStatus.CLOSED

        return validation

    async def escalate_issue(
        self, issue_id: UUID, escalated_by: str, escalation_reason: str,
        escalated_to: str, escalation_level: int, response_required_by: date
    ) -> IssueEscalation:
        escalation = IssueEscalation(
            issue_id=issue_id, escalation_date=date.today(), escalated_by=escalated_by,
            escalation_reason=escalation_reason, escalated_to=escalated_to,
            escalation_level=escalation_level, response_required_by=response_required_by
        )
        await self.repository.save_escalation(escalation)

        issue = await self.repository.find_issue_by_id(issue_id)
        if issue:
            issue.status = IssueStatus.ESCALATED

        return escalation

    async def extend_due_date(
        self, issue_id: UUID, new_due_date: date, updated_by: str, reason: str
    ) -> Optional[Issue]:
        issue = await self.repository.find_issue_by_id(issue_id)
        if issue:
            issue.extended_due_date = new_due_date
            issue.extension_count += 1

            update = IssueUpdate(
                issue_id=issue_id, update_date=date.today(), updated_by=updated_by,
                update_type="extension",
                progress_update=f"Due date extended to {new_due_date}. Reason: {reason}"
            )
            await self.repository.save_update(update)

        return issue

    async def generate_report(self, report_period: str, prepared_by: str) -> IssueReport:
        issues = await self.repository.find_all_issues()

        by_source = {}
        by_priority = {}
        by_status = {}

        for issue in issues:
            by_source[issue.source.value] = by_source.get(issue.source.value, 0) + 1
            by_priority[issue.priority.value] = by_priority.get(issue.priority.value, 0) + 1
            by_status[issue.status.value] = by_status.get(issue.status.value, 0) + 1

        report = IssueReport(
            report_period=report_period, report_date=date.today(), prepared_by=prepared_by,
            total_issues=len(issues), issues_by_source=by_source,
            issues_by_priority=by_priority, issues_by_status=by_status,
            overdue_issues=len([i for i in issues if i.status == IssueStatus.OVERDUE])
        )
        await self.repository.save_report(report)
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


issue_management_service = IssueManagementService()
