"""Governance Repository - Data access for corporate governance"""

from typing import Any
from uuid import UUID

from ..models.governance_models import (
    BoardMeeting,
    BoardMember,
    ConflictOfInterest,
    GovernanceAssessment,
    GovernanceFramework,
    GovernancePolicy,
)


class GovernanceRepository:
    def __init__(self):
        self._frameworks: dict[UUID, GovernanceFramework] = {}
        self._board_members: dict[UUID, BoardMember] = {}
        self._board_meetings: dict[UUID, BoardMeeting] = {}
        self._policies: dict[UUID, GovernancePolicy] = {}
        self._conflicts: dict[UUID, ConflictOfInterest] = {}
        self._assessments: dict[UUID, GovernanceAssessment] = {}

    async def save_framework(self, framework: GovernanceFramework) -> None:
        self._frameworks[framework.framework_id] = framework

    async def find_framework_by_id(self, framework_id: UUID) -> GovernanceFramework | None:
        return self._frameworks.get(framework_id)

    async def find_all_frameworks(self) -> list[GovernanceFramework]:
        return list(self._frameworks.values())

    async def find_active_framework(self) -> GovernanceFramework | None:
        for f in self._frameworks.values():
            if f.status == "active":
                return f
        return None

    async def save_board_member(self, member: BoardMember) -> None:
        self._board_members[member.member_id] = member

    async def find_board_member_by_id(self, member_id: UUID) -> BoardMember | None:
        return self._board_members.get(member_id)

    async def find_all_board_members(self) -> list[BoardMember]:
        return list(self._board_members.values())

    async def find_active_board_members(self) -> list[BoardMember]:
        return [m for m in self._board_members.values() if m.is_active]

    async def find_independent_members(self) -> list[BoardMember]:
        return [m for m in self._board_members.values() if m.member_type == "independent" and m.is_active]

    async def save_board_meeting(self, meeting: BoardMeeting) -> None:
        self._board_meetings[meeting.meeting_id] = meeting

    async def find_board_meeting_by_id(self, meeting_id: UUID) -> BoardMeeting | None:
        return self._board_meetings.get(meeting_id)

    async def find_all_board_meetings(self) -> list[BoardMeeting]:
        return list(self._board_meetings.values())

    async def save_governance_policy(self, policy: GovernancePolicy) -> None:
        self._policies[policy.policy_id] = policy

    async def find_governance_policy_by_id(self, policy_id: UUID) -> GovernancePolicy | None:
        return self._policies.get(policy_id)

    async def find_all_governance_policies(self) -> list[GovernancePolicy]:
        return list(self._policies.values())

    async def save_conflict(self, conflict: ConflictOfInterest) -> None:
        self._conflicts[conflict.conflict_id] = conflict

    async def find_conflict_by_id(self, conflict_id: UUID) -> ConflictOfInterest | None:
        return self._conflicts.get(conflict_id)

    async def find_all_conflicts(self) -> list[ConflictOfInterest]:
        return list(self._conflicts.values())

    async def find_pending_conflicts(self) -> list[ConflictOfInterest]:
        return [c for c in self._conflicts.values() if c.status == "pending"]

    async def save_assessment(self, assessment: GovernanceAssessment) -> None:
        self._assessments[assessment.assessment_id] = assessment

    async def find_assessment_by_id(self, assessment_id: UUID) -> GovernanceAssessment | None:
        return self._assessments.get(assessment_id)

    async def find_all_assessments(self) -> list[GovernanceAssessment]:
        return list(self._assessments.values())

    async def get_statistics(self) -> dict[str, Any]:
        return {
            "total_frameworks": len(self._frameworks),
            "total_board_members": len(self._board_members),
            "active_board_members": len([m for m in self._board_members.values() if m.is_active]),
            "independent_members": len([m for m in self._board_members.values() if m.member_type == "independent"]),
            "total_meetings": len(self._board_meetings),
            "total_policies": len(self._policies),
            "total_conflicts": len(self._conflicts),
            "pending_conflicts": len([c for c in self._conflicts.values() if c.status == "pending"]),
            "total_assessments": len(self._assessments),
        }


governance_repository = GovernanceRepository()
