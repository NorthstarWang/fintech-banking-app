"""Governance Service - Business logic for corporate governance"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from ..models.governance_models import (
    GovernanceFramework, BoardMember, BoardMeeting, GovernancePolicy,
    ConflictOfInterest, GovernanceAssessment
)
from ..repositories.governance_repository import governance_repository


class GovernanceService:
    def __init__(self):
        self.repository = governance_repository

    async def create_framework(
        self, framework_name: str, framework_version: str, description: str,
        principles: List[str], governance_structure: Dict[str, Any],
        roles_responsibilities: Dict[str, List[str]], approved_by: str
    ) -> GovernanceFramework:
        framework = GovernanceFramework(
            framework_name=framework_name, framework_version=framework_version,
            effective_date=date.today(), description=description, principles=principles,
            governance_structure=governance_structure, roles_responsibilities=roles_responsibilities,
            approved_by=approved_by, approval_date=date.today(),
            next_review_date=date(date.today().year + 1, date.today().month, date.today().day)
        )
        await self.repository.save_framework(framework)
        return framework

    async def appoint_board_member(
        self, member_name: str, position: str, member_type: str,
        term_end_date: date, qualifications: List[str], expertise_areas: List[str],
        annual_fee: Decimal
    ) -> BoardMember:
        member = BoardMember(
            member_name=member_name, position=position, member_type=member_type,
            appointment_date=date.today(), term_end_date=term_end_date,
            qualifications=qualifications, expertise_areas=expertise_areas,
            annual_fee=annual_fee
        )
        await self.repository.save_board_member(member)
        return member

    async def schedule_board_meeting(
        self, meeting_type: str, meeting_date: date, meeting_time: str,
        location: str, agenda_items: List[Dict[str, Any]]
    ) -> BoardMeeting:
        meeting = BoardMeeting(
            meeting_type=meeting_type, meeting_date=meeting_date,
            meeting_time=meeting_time, location=location, agenda_items=agenda_items
        )
        await self.repository.save_board_meeting(meeting)
        return meeting

    async def record_meeting_attendance(
        self, meeting_id: UUID, attendees: List[str], absentees: List[str]
    ) -> Optional[BoardMeeting]:
        meeting = await self.repository.find_board_meeting_by_id(meeting_id)
        if meeting:
            meeting.attendees = attendees
            meeting.absentees = absentees
            meeting.quorum_present = len(attendees) >= 3
            meeting.status = "held"
        return meeting

    async def approve_meeting_minutes(
        self, meeting_id: UUID, minutes_prepared_by: str, resolutions: List[Dict[str, Any]],
        action_items: List[Dict[str, Any]]
    ) -> Optional[BoardMeeting]:
        meeting = await self.repository.find_board_meeting_by_id(meeting_id)
        if meeting:
            meeting.minutes_prepared_by = minutes_prepared_by
            meeting.minutes_approved_date = date.today()
            meeting.resolutions = resolutions
            meeting.action_items = action_items
            meeting.status = "completed"
        return meeting

    async def create_governance_policy(
        self, policy_code: str, policy_name: str, policy_category: str,
        description: str, scope: str, owner: str, approver: str,
        key_provisions: List[str]
    ) -> GovernancePolicy:
        policy = GovernancePolicy(
            policy_code=policy_code, policy_name=policy_name, policy_category=policy_category,
            description=description, scope=scope, owner=owner, approver=approver,
            effective_date=date.today(),
            review_date=date(date.today().year + 1, date.today().month, date.today().day),
            key_provisions=key_provisions
        )
        await self.repository.save_governance_policy(policy)
        return policy

    async def declare_conflict(
        self, declarant_name: str, declarant_position: str, conflict_type: str,
        description: str, related_party: str, nature_of_interest: str,
        review_committee: str
    ) -> ConflictOfInterest:
        conflict = ConflictOfInterest(
            declarant_name=declarant_name, declarant_position=declarant_position,
            declaration_date=date.today(), conflict_type=conflict_type,
            description=description, related_party=related_party,
            nature_of_interest=nature_of_interest, review_committee=review_committee
        )
        await self.repository.save_conflict(conflict)
        return conflict

    async def review_conflict(
        self, conflict_id: UUID, decision: str, mitigation_measures: List[str]
    ) -> Optional[ConflictOfInterest]:
        conflict = await self.repository.find_conflict_by_id(conflict_id)
        if conflict:
            conflict.review_date = date.today()
            conflict.decision = decision
            conflict.mitigation_measures = mitigation_measures
            conflict.status = "reviewed"
        return conflict

    async def conduct_assessment(
        self, assessment_year: int, assessment_type: str, assessor: str,
        areas_assessed: List[str], findings: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]], overall_rating: str,
        board_effectiveness_score: Decimal
    ) -> GovernanceAssessment:
        assessment = GovernanceAssessment(
            assessment_year=assessment_year, assessment_type=assessment_type,
            assessor=assessor, assessment_date=date.today(), areas_assessed=areas_assessed,
            findings=findings, recommendations=recommendations, overall_rating=overall_rating,
            board_effectiveness_score=board_effectiveness_score
        )
        await self.repository.save_assessment(assessment)
        return assessment

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


governance_service = GovernanceService()
