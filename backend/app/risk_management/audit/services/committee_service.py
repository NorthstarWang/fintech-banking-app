"""Committee Service - Business logic for board committee management"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from ..models.committee_models import (
    Committee, CommitteeMeeting, CommitteeResolution, CommitteeReport,
    CommitteeMember, CommitteeType
)
from ..repositories.committee_repository import committee_repository


class CommitteeService:
    def __init__(self):
        self.repository = committee_repository
        self._resolution_counter = 0

    async def establish_committee(
        self, committee_name: str, committee_type: CommitteeType, charter: str,
        mandate: List[str], responsibilities: List[str], minimum_members: int,
        meeting_frequency: str
    ) -> Committee:
        committee = Committee(
            committee_name=committee_name, committee_type=committee_type,
            charter=charter, mandate=mandate, responsibilities=responsibilities,
            minimum_members=minimum_members, meeting_frequency=meeting_frequency,
            established_date=date.today(), charter_last_reviewed=date.today()
        )
        await self.repository.save_committee(committee)
        return committee

    async def appoint_member(
        self, committee_id: UUID, member_id: UUID, member_name: str, role: str,
        term_end_date: date, is_independent: bool, expertise_relevant: List[str]
    ) -> CommitteeMember:
        membership = CommitteeMember(
            committee_id=committee_id, member_id=member_id, member_name=member_name,
            role=role, appointment_date=date.today(), term_end_date=term_end_date,
            is_independent=is_independent, expertise_relevant=expertise_relevant
        )
        await self.repository.save_member(membership)

        committee = await self.repository.find_committee_by_id(committee_id)
        if committee:
            if role == "chairman":
                committee.chairman = member_name
            elif role == "secretary":
                committee.secretary = member_name
            committee.members.append(member_name)

        return membership

    async def schedule_meeting(
        self, committee_id: UUID, meeting_date: date, meeting_time: str,
        meeting_type: str, location: str, agenda: List[Dict[str, Any]]
    ) -> CommitteeMeeting:
        meeting = CommitteeMeeting(
            committee_id=committee_id,
            meeting_reference=f"CM-{date.today().strftime('%Y%m%d')}-001",
            meeting_date=meeting_date, meeting_time=meeting_time,
            meeting_type=meeting_type, location=location, agenda=agenda
        )
        await self.repository.save_meeting(meeting)
        return meeting

    async def record_meeting(
        self, meeting_id: UUID, attendees: List[str], discussions: List[Dict[str, Any]],
        decisions: List[Dict[str, Any]], action_items: List[Dict[str, Any]]
    ) -> Optional[CommitteeMeeting]:
        meeting = await self.repository.find_meeting_by_id(meeting_id)
        if meeting:
            meeting.attendees = attendees
            meeting.discussions = discussions
            meeting.decisions = decisions
            meeting.action_items = action_items
            meeting.minutes_status = "drafted"
        return meeting

    async def approve_minutes(self, meeting_id: UUID) -> Optional[CommitteeMeeting]:
        meeting = await self.repository.find_meeting_by_id(meeting_id)
        if meeting:
            meeting.minutes_status = "approved"
            meeting.minutes_approved_date = date.today()
        return meeting

    async def pass_resolution(
        self, committee_id: UUID, meeting_id: UUID, subject: str, resolution_text: str,
        proposed_by: str, seconded_by: str, votes_for: int, votes_against: int,
        votes_abstained: int, implementation_required: bool = False,
        implementation_deadline: date = None, implementation_owner: str = ""
    ) -> CommitteeResolution:
        self._resolution_counter += 1
        passed = votes_for > votes_against

        resolution = CommitteeResolution(
            committee_id=committee_id, meeting_id=meeting_id,
            resolution_reference=f"RES-{date.today().year}-{self._resolution_counter:04d}",
            resolution_date=date.today(), subject=subject, resolution_text=resolution_text,
            proposed_by=proposed_by, seconded_by=seconded_by, votes_for=votes_for,
            votes_against=votes_against, votes_abstained=votes_abstained, passed=passed,
            effective_date=date.today(), implementation_required=implementation_required,
            implementation_deadline=implementation_deadline, implementation_owner=implementation_owner
        )
        await self.repository.save_resolution(resolution)
        return resolution

    async def generate_committee_report(
        self, committee_id: UUID, report_period: str, prepared_by: str,
        key_activities: List[str], key_decisions: List[str],
        oversight_activities: List[str], recommendations_to_board: List[str]
    ) -> CommitteeReport:
        meetings = await self.repository.find_meetings_by_committee(committee_id)

        report = CommitteeReport(
            committee_id=committee_id, report_period=report_period,
            report_date=date.today(), prepared_by=prepared_by,
            key_activities=key_activities, meetings_held=len(meetings),
            key_decisions=key_decisions, oversight_activities=oversight_activities,
            recommendations_to_board=recommendations_to_board
        )
        await self.repository.save_report(report)
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


committee_service = CommitteeService()
