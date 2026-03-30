"""Committee Repository - Data access for board committee management"""

from typing import Any
from uuid import UUID

from ..models.committee_models import Committee, CommitteeMeeting, CommitteeMember, CommitteeReport, CommitteeResolution


class CommitteeRepository:
    def __init__(self):
        self._committees: dict[UUID, Committee] = {}
        self._meetings: dict[UUID, CommitteeMeeting] = {}
        self._resolutions: dict[UUID, CommitteeResolution] = {}
        self._reports: dict[UUID, CommitteeReport] = {}
        self._members: dict[UUID, CommitteeMember] = {}

    async def save_committee(self, committee: Committee) -> None:
        self._committees[committee.committee_id] = committee

    async def find_committee_by_id(self, committee_id: UUID) -> Committee | None:
        return self._committees.get(committee_id)

    async def find_all_committees(self) -> list[Committee]:
        return list(self._committees.values())

    async def find_active_committees(self) -> list[Committee]:
        return [c for c in self._committees.values() if c.status == "active"]

    async def save_meeting(self, meeting: CommitteeMeeting) -> None:
        self._meetings[meeting.meeting_id] = meeting

    async def find_meeting_by_id(self, meeting_id: UUID) -> CommitteeMeeting | None:
        return self._meetings.get(meeting_id)

    async def find_all_meetings(self) -> list[CommitteeMeeting]:
        return list(self._meetings.values())

    async def find_meetings_by_committee(self, committee_id: UUID) -> list[CommitteeMeeting]:
        return [m for m in self._meetings.values() if m.committee_id == committee_id]

    async def save_resolution(self, resolution: CommitteeResolution) -> None:
        self._resolutions[resolution.resolution_id] = resolution

    async def find_resolution_by_id(self, resolution_id: UUID) -> CommitteeResolution | None:
        return self._resolutions.get(resolution_id)

    async def find_all_resolutions(self) -> list[CommitteeResolution]:
        return list(self._resolutions.values())

    async def find_resolutions_by_committee(self, committee_id: UUID) -> list[CommitteeResolution]:
        return [r for r in self._resolutions.values() if r.committee_id == committee_id]

    async def save_report(self, report: CommitteeReport) -> None:
        self._reports[report.report_id] = report

    async def find_report_by_id(self, report_id: UUID) -> CommitteeReport | None:
        return self._reports.get(report_id)

    async def find_reports_by_committee(self, committee_id: UUID) -> list[CommitteeReport]:
        return [r for r in self._reports.values() if r.committee_id == committee_id]

    async def save_member(self, member: CommitteeMember) -> None:
        self._members[member.membership_id] = member

    async def find_member_by_id(self, membership_id: UUID) -> CommitteeMember | None:
        return self._members.get(membership_id)

    async def find_members_by_committee(self, committee_id: UUID) -> list[CommitteeMember]:
        return [m for m in self._members.values() if m.committee_id == committee_id]

    async def get_statistics(self) -> dict[str, Any]:
        return {
            "total_committees": len(self._committees),
            "active_committees": len([c for c in self._committees.values() if c.status == "active"]),
            "total_meetings": len(self._meetings),
            "total_resolutions": len(self._resolutions),
            "passed_resolutions": len([r for r in self._resolutions.values() if r.passed]),
            "total_reports": len(self._reports),
            "total_memberships": len(self._members),
        }


committee_repository = CommitteeRepository()
