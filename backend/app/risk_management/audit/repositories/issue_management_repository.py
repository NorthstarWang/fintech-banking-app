"""Issue Management Repository - Data access for issue tracking"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.issue_management_models import (
    Issue, ActionPlan, IssueUpdate, IssueValidation, IssueEscalation, IssueReport,
    IssueStatus
)


class IssueManagementRepository:
    def __init__(self):
        self._issues: Dict[UUID, Issue] = {}
        self._action_plans: Dict[UUID, ActionPlan] = {}
        self._updates: Dict[UUID, IssueUpdate] = {}
        self._validations: Dict[UUID, IssueValidation] = {}
        self._escalations: Dict[UUID, IssueEscalation] = {}
        self._reports: Dict[UUID, IssueReport] = {}

    async def save_issue(self, issue: Issue) -> None:
        self._issues[issue.issue_id] = issue

    async def find_issue_by_id(self, issue_id: UUID) -> Optional[Issue]:
        return self._issues.get(issue_id)

    async def find_all_issues(self) -> List[Issue]:
        return list(self._issues.values())

    async def find_open_issues(self) -> List[Issue]:
        return [i for i in self._issues.values() if i.status in [IssueStatus.OPEN, IssueStatus.IN_PROGRESS]]

    async def find_issues_by_status(self, status: IssueStatus) -> List[Issue]:
        return [i for i in self._issues.values() if i.status == status]

    async def find_issues_by_owner(self, owner: str) -> List[Issue]:
        return [i for i in self._issues.values() if i.owner == owner]

    async def find_overdue_issues(self) -> List[Issue]:
        return [i for i in self._issues.values() if i.status == IssueStatus.OVERDUE]

    async def save_action_plan(self, action: ActionPlan) -> None:
        self._action_plans[action.action_id] = action

    async def find_action_plan_by_id(self, action_id: UUID) -> Optional[ActionPlan]:
        return self._action_plans.get(action_id)

    async def find_action_plans_by_issue(self, issue_id: UUID) -> List[ActionPlan]:
        return [a for a in self._action_plans.values() if a.issue_id == issue_id]

    async def save_update(self, update: IssueUpdate) -> None:
        self._updates[update.update_id] = update

    async def find_updates_by_issue(self, issue_id: UUID) -> List[IssueUpdate]:
        return [u for u in self._updates.values() if u.issue_id == issue_id]

    async def save_validation(self, validation: IssueValidation) -> None:
        self._validations[validation.validation_id] = validation

    async def find_validation_by_id(self, validation_id: UUID) -> Optional[IssueValidation]:
        return self._validations.get(validation_id)

    async def find_validations_by_issue(self, issue_id: UUID) -> List[IssueValidation]:
        return [v for v in self._validations.values() if v.issue_id == issue_id]

    async def save_escalation(self, escalation: IssueEscalation) -> None:
        self._escalations[escalation.escalation_id] = escalation

    async def find_escalation_by_id(self, escalation_id: UUID) -> Optional[IssueEscalation]:
        return self._escalations.get(escalation_id)

    async def find_escalations_by_issue(self, issue_id: UUID) -> List[IssueEscalation]:
        return [e for e in self._escalations.values() if e.issue_id == issue_id]

    async def save_report(self, report: IssueReport) -> None:
        self._reports[report.report_id] = report

    async def find_report_by_id(self, report_id: UUID) -> Optional[IssueReport]:
        return self._reports.get(report_id)

    async def find_all_reports(self) -> List[IssueReport]:
        return list(self._reports.values())

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_issues": len(self._issues),
            "open_issues": len([i for i in self._issues.values() if i.status in [IssueStatus.OPEN, IssueStatus.IN_PROGRESS]]),
            "closed_issues": len([i for i in self._issues.values() if i.status == IssueStatus.CLOSED]),
            "overdue_issues": len([i for i in self._issues.values() if i.status == IssueStatus.OVERDUE]),
            "escalated_issues": len([i for i in self._issues.values() if i.status == IssueStatus.ESCALATED]),
            "total_action_plans": len(self._action_plans),
            "total_validations": len(self._validations),
            "total_escalations": len(self._escalations),
            "total_reports": len(self._reports),
        }


issue_management_repository = IssueManagementRepository()
