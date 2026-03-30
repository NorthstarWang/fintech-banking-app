"""Business Continuity Repository - Data access layer for BCP/DR"""

from typing import Any
from uuid import UUID

from ..models.business_continuity_models import (
    BCPIncident,
    BCPMetrics,
    BCPTest,
    BusinessContinuityPlan,
    BusinessProcess,
    CrisisTeamMember,
    DisasterRecoveryPlan,
)


class BusinessContinuityRepository:
    def __init__(self):
        self._processes: dict[UUID, BusinessProcess] = {}
        self._bcps: dict[UUID, BusinessContinuityPlan] = {}
        self._drps: dict[UUID, DisasterRecoveryPlan] = {}
        self._tests: dict[UUID, BCPTest] = {}
        self._incidents: dict[UUID, BCPIncident] = {}
        self._team_members: dict[UUID, CrisisTeamMember] = {}
        self._metrics: dict[UUID, BCPMetrics] = {}

    async def save_process(self, process: BusinessProcess) -> BusinessProcess:
        self._processes[process.process_id] = process
        return process

    async def find_process_by_id(self, process_id: UUID) -> BusinessProcess | None:
        return self._processes.get(process_id)

    async def find_all_processes(self) -> list[BusinessProcess]:
        return list(self._processes.values())

    async def update_process(self, process: BusinessProcess) -> BusinessProcess:
        self._processes[process.process_id] = process
        return process

    async def save_bcp(self, bcp: BusinessContinuityPlan) -> BusinessContinuityPlan:
        self._bcps[bcp.plan_id] = bcp
        return bcp

    async def find_bcp_by_id(self, plan_id: UUID) -> BusinessContinuityPlan | None:
        return self._bcps.get(plan_id)

    async def find_all_bcps(self) -> list[BusinessContinuityPlan]:
        return list(self._bcps.values())

    async def update_bcp(self, bcp: BusinessContinuityPlan) -> BusinessContinuityPlan:
        self._bcps[bcp.plan_id] = bcp
        return bcp

    async def save_drp(self, drp: DisasterRecoveryPlan) -> DisasterRecoveryPlan:
        self._drps[drp.dr_plan_id] = drp
        return drp

    async def find_drp_by_id(self, plan_id: UUID) -> DisasterRecoveryPlan | None:
        return self._drps.get(plan_id)

    async def find_all_drps(self) -> list[DisasterRecoveryPlan]:
        return list(self._drps.values())

    async def update_drp(self, drp: DisasterRecoveryPlan) -> DisasterRecoveryPlan:
        self._drps[drp.dr_plan_id] = drp
        return drp

    async def save_test(self, test: BCPTest) -> BCPTest:
        self._tests[test.test_id] = test
        return test

    async def find_test_by_id(self, test_id: UUID) -> BCPTest | None:
        return self._tests.get(test_id)

    async def find_tests_by_plan(self, plan_id: UUID) -> list[BCPTest]:
        return sorted(
            [t for t in self._tests.values() if t.plan_id == plan_id],
            key=lambda x: x.test_date,
            reverse=True
        )

    async def find_all_tests(self) -> list[BCPTest]:
        return list(self._tests.values())

    async def save_incident(self, incident: BCPIncident) -> BCPIncident:
        self._incidents[incident.incident_id] = incident
        return incident

    async def find_incident_by_id(self, incident_id: UUID) -> BCPIncident | None:
        return self._incidents.get(incident_id)

    async def find_all_incidents(self) -> list[BCPIncident]:
        return list(self._incidents.values())

    async def save_team_member(self, member: CrisisTeamMember) -> CrisisTeamMember:
        self._team_members[member.member_id] = member
        return member

    async def find_team_members_by_team(self, team_name: str) -> list[CrisisTeamMember]:
        return [m for m in self._team_members.values() if m.team_name == team_name]

    async def save_metrics(self, metrics: BCPMetrics) -> BCPMetrics:
        self._metrics[metrics.metrics_id] = metrics
        return metrics

    async def get_statistics(self) -> dict[str, Any]:
        return {
            "total_processes": len(self._processes),
            "total_bcps": len(self._bcps),
            "total_drps": len(self._drps),
            "total_tests": len(self._tests)
        }


business_continuity_repository = BusinessContinuityRepository()
