"""Business Continuity Repository - Data access layer for BCP/DR"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.business_continuity_models import (
    BusinessProcess, BusinessContinuityPlan, DisasterRecoveryPlan,
    BCPTest, BCPIncident, CrisisTeamMember, BCPMetrics
)


class BusinessContinuityRepository:
    def __init__(self):
        self._processes: Dict[UUID, BusinessProcess] = {}
        self._bcps: Dict[UUID, BusinessContinuityPlan] = {}
        self._drps: Dict[UUID, DisasterRecoveryPlan] = {}
        self._tests: Dict[UUID, BCPTest] = {}
        self._incidents: Dict[UUID, BCPIncident] = {}
        self._team_members: Dict[UUID, CrisisTeamMember] = {}
        self._metrics: Dict[UUID, BCPMetrics] = {}

    async def save_process(self, process: BusinessProcess) -> BusinessProcess:
        self._processes[process.process_id] = process
        return process

    async def find_process_by_id(self, process_id: UUID) -> Optional[BusinessProcess]:
        return self._processes.get(process_id)

    async def find_all_processes(self) -> List[BusinessProcess]:
        return list(self._processes.values())

    async def update_process(self, process: BusinessProcess) -> BusinessProcess:
        self._processes[process.process_id] = process
        return process

    async def save_bcp(self, bcp: BusinessContinuityPlan) -> BusinessContinuityPlan:
        self._bcps[bcp.plan_id] = bcp
        return bcp

    async def find_bcp_by_id(self, plan_id: UUID) -> Optional[BusinessContinuityPlan]:
        return self._bcps.get(plan_id)

    async def find_all_bcps(self) -> List[BusinessContinuityPlan]:
        return list(self._bcps.values())

    async def update_bcp(self, bcp: BusinessContinuityPlan) -> BusinessContinuityPlan:
        self._bcps[bcp.plan_id] = bcp
        return bcp

    async def save_drp(self, drp: DisasterRecoveryPlan) -> DisasterRecoveryPlan:
        self._drps[drp.dr_plan_id] = drp
        return drp

    async def find_drp_by_id(self, plan_id: UUID) -> Optional[DisasterRecoveryPlan]:
        return self._drps.get(plan_id)

    async def find_all_drps(self) -> List[DisasterRecoveryPlan]:
        return list(self._drps.values())

    async def update_drp(self, drp: DisasterRecoveryPlan) -> DisasterRecoveryPlan:
        self._drps[drp.dr_plan_id] = drp
        return drp

    async def save_test(self, test: BCPTest) -> BCPTest:
        self._tests[test.test_id] = test
        return test

    async def find_test_by_id(self, test_id: UUID) -> Optional[BCPTest]:
        return self._tests.get(test_id)

    async def find_tests_by_plan(self, plan_id: UUID) -> List[BCPTest]:
        return sorted(
            [t for t in self._tests.values() if t.plan_id == plan_id],
            key=lambda x: x.test_date,
            reverse=True
        )

    async def find_all_tests(self) -> List[BCPTest]:
        return list(self._tests.values())

    async def save_incident(self, incident: BCPIncident) -> BCPIncident:
        self._incidents[incident.incident_id] = incident
        return incident

    async def find_incident_by_id(self, incident_id: UUID) -> Optional[BCPIncident]:
        return self._incidents.get(incident_id)

    async def find_all_incidents(self) -> List[BCPIncident]:
        return list(self._incidents.values())

    async def save_team_member(self, member: CrisisTeamMember) -> CrisisTeamMember:
        self._team_members[member.member_id] = member
        return member

    async def find_team_members_by_team(self, team_name: str) -> List[CrisisTeamMember]:
        return [m for m in self._team_members.values() if m.team_name == team_name]

    async def save_metrics(self, metrics: BCPMetrics) -> BCPMetrics:
        self._metrics[metrics.metrics_id] = metrics
        return metrics

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_processes": len(self._processes),
            "total_bcps": len(self._bcps),
            "total_drps": len(self._drps),
            "total_tests": len(self._tests)
        }


business_continuity_repository = BusinessContinuityRepository()
