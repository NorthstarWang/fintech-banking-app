"""Business Continuity Service - Business logic for BCP/DR management"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from ..models.business_continuity_models import (
    BusinessProcess, BusinessContinuityPlan, DisasterRecoveryPlan, BCPTest,
    BCPIncident, CrisisTeamMember, BCPMetrics, BCPStatus, CriticalityLevel,
    DisasterType, RecoveryStrategy, TestType
)
from ..repositories.business_continuity_repository import business_continuity_repository


class BusinessContinuityService:
    def __init__(self):
        self.repository = business_continuity_repository

    async def register_process(
        self,
        process_name: str,
        process_description: str,
        business_unit: str,
        process_owner: str,
        criticality: CriticalityLevel,
        rto_hours: int,
        rpo_hours: int,
        mtpd_hours: int,
        minimum_staff: int,
        normal_staff: int,
        recovery_strategy: RecoveryStrategy,
        financial_impact_per_hour: Decimal,
        dependencies: List[str] = None,
        systems_required: List[str] = None,
        vendors_required: List[str] = None
    ) -> BusinessProcess:
        process = BusinessProcess(
            process_name=process_name,
            process_description=process_description,
            business_unit=business_unit,
            process_owner=process_owner,
            criticality=criticality,
            rto_hours=rto_hours,
            rpo_hours=rpo_hours,
            mtpd_hours=mtpd_hours,
            minimum_staff=minimum_staff,
            normal_staff=normal_staff,
            recovery_strategy=recovery_strategy,
            financial_impact_per_hour=financial_impact_per_hour,
            dependencies=dependencies or [],
            systems_required=systems_required or [],
            vendors_required=vendors_required or []
        )

        await self.repository.save_process(process)
        return process

    async def get_process(self, process_id: UUID) -> Optional[BusinessProcess]:
        return await self.repository.find_process_by_id(process_id)

    async def list_processes(
        self,
        criticality: Optional[CriticalityLevel] = None,
        business_unit: Optional[str] = None
    ) -> List[BusinessProcess]:
        processes = await self.repository.find_all_processes()

        if criticality:
            processes = [p for p in processes if p.criticality == criticality]
        if business_unit:
            processes = [p for p in processes if p.business_unit == business_unit]

        return processes

    async def create_bcp(
        self,
        plan_name: str,
        plan_version: str,
        business_unit: str,
        plan_owner: str,
        scope: str,
        objectives: List[str],
        assumptions: List[str],
        processes_covered: List[UUID],
        activation_criteria: List[str],
        deactivation_criteria: List[str],
        document_location: str
    ) -> BusinessContinuityPlan:
        plan = BusinessContinuityPlan(
            plan_name=plan_name,
            plan_version=plan_version,
            business_unit=business_unit,
            plan_owner=plan_owner,
            scope=scope,
            objectives=objectives,
            assumptions=assumptions,
            processes_covered=processes_covered,
            activation_criteria=activation_criteria,
            deactivation_criteria=deactivation_criteria,
            document_location=document_location
        )

        await self.repository.save_bcp(plan)
        return plan

    async def get_bcp(self, plan_id: UUID) -> Optional[BusinessContinuityPlan]:
        return await self.repository.find_bcp_by_id(plan_id)

    async def list_bcps(
        self,
        status: Optional[BCPStatus] = None,
        business_unit: Optional[str] = None
    ) -> List[BusinessContinuityPlan]:
        plans = await self.repository.find_all_bcps()

        if status:
            plans = [p for p in plans if p.status == status]
        if business_unit:
            plans = [p for p in plans if p.business_unit == business_unit]

        return plans

    async def approve_bcp(
        self,
        plan_id: UUID,
        approved_by: str
    ) -> Optional[BusinessContinuityPlan]:
        plan = await self.repository.find_bcp_by_id(plan_id)
        if not plan:
            return None

        plan.status = BCPStatus.APPROVED
        plan.approved_by = approved_by
        plan.approval_date = date.today()
        plan.effective_date = date.today()
        plan.expiry_date = date(date.today().year + 1, date.today().month, date.today().day)
        plan.next_review_date = date(date.today().year + 1, date.today().month, date.today().day)

        await self.repository.update_bcp(plan)
        return plan

    async def activate_bcp(self, plan_id: UUID) -> Optional[BusinessContinuityPlan]:
        plan = await self.repository.find_bcp_by_id(plan_id)
        if not plan:
            return None

        plan.status = BCPStatus.ACTIVE
        await self.repository.update_bcp(plan)
        return plan

    async def create_drp(
        self,
        plan_name: str,
        plan_version: str,
        system_name: str,
        system_criticality: CriticalityLevel,
        rto_hours: int,
        rpo_hours: int,
        recovery_site: str,
        recovery_strategy: RecoveryStrategy,
        backup_frequency: str,
        backup_location: str,
        backup_retention: str,
        recovery_procedures: List[str],
        verification_steps: List[str],
        owner: str,
        dependencies: List[str] = None
    ) -> DisasterRecoveryPlan:
        plan = DisasterRecoveryPlan(
            plan_name=plan_name,
            plan_version=plan_version,
            system_name=system_name,
            system_criticality=system_criticality,
            rto_hours=rto_hours,
            rpo_hours=rpo_hours,
            recovery_site=recovery_site,
            recovery_strategy=recovery_strategy,
            backup_frequency=backup_frequency,
            backup_location=backup_location,
            backup_retention=backup_retention,
            recovery_procedures=recovery_procedures,
            verification_steps=verification_steps,
            owner=owner,
            dependencies=dependencies or []
        )

        await self.repository.save_drp(plan)
        return plan

    async def get_drp(self, plan_id: UUID) -> Optional[DisasterRecoveryPlan]:
        return await self.repository.find_drp_by_id(plan_id)

    async def list_drps(
        self,
        status: Optional[BCPStatus] = None,
        criticality: Optional[CriticalityLevel] = None
    ) -> List[DisasterRecoveryPlan]:
        plans = await self.repository.find_all_drps()

        if status:
            plans = [p for p in plans if p.status == status]
        if criticality:
            plans = [p for p in plans if p.system_criticality == criticality]

        return plans

    async def schedule_test(
        self,
        plan_id: UUID,
        test_name: str,
        test_type: TestType,
        test_date: date,
        scope: str,
        objectives: List[str],
        scenarios_tested: List[str],
        test_coordinator: str,
        participants: List[str]
    ) -> BCPTest:
        test = BCPTest(
            plan_id=plan_id,
            test_name=test_name,
            test_type=test_type,
            test_date=test_date,
            test_duration_hours=0,
            scope=scope,
            objectives=objectives,
            scenarios_tested=scenarios_tested,
            test_coordinator=test_coordinator,
            participants=participants,
            test_result="scheduled"
        )

        await self.repository.save_test(test)
        return test

    async def complete_test(
        self,
        test_id: UUID,
        test_duration_hours: float,
        test_result: str,
        rto_achieved: int,
        rpo_achieved: int,
        findings: List[str],
        recommendations: List[str],
        lessons_learned: List[str]
    ) -> Optional[BCPTest]:
        test = await self.repository.find_test_by_id(test_id)
        if not test:
            return None

        test.test_duration_hours = test_duration_hours
        test.test_result = test_result
        test.rto_achieved = rto_achieved
        test.rpo_achieved = rpo_achieved
        test.findings = findings
        test.recommendations = recommendations
        test.lessons_learned = lessons_learned
        test.report_date = date.today()

        plan = await self.repository.find_bcp_by_id(test.plan_id)
        if not plan:
            plan = await self.repository.find_drp_by_id(test.plan_id)

        if plan:
            plan.last_test_date = test.test_date
            plan.next_test_date = date(test.test_date.year + 1, test.test_date.month, test.test_date.day)
            plan.test_result = test_result

        return test

    async def get_plan_tests(self, plan_id: UUID) -> List[BCPTest]:
        return await self.repository.find_tests_by_plan(plan_id)

    async def declare_incident(
        self,
        incident_name: str,
        disaster_type: DisasterType,
        declared_by: str,
        affected_locations: List[str],
        affected_processes: List[UUID],
        impact_description: str,
        plan_activated: UUID
    ) -> BCPIncident:
        now = datetime.utcnow()

        incident = BCPIncident(
            incident_name=incident_name,
            disaster_type=disaster_type,
            declaration_time=now,
            declared_by=declared_by,
            affected_locations=affected_locations,
            affected_processes=affected_processes,
            impact_description=impact_description,
            plan_activated=plan_activated,
            activation_time=now
        )

        await self.repository.save_incident(incident)

        await self.activate_bcp(plan_activated)

        return incident

    async def start_recovery(self, incident_id: UUID) -> Optional[BCPIncident]:
        incident = await self.repository.find_incident_by_id(incident_id)
        if not incident:
            return None

        incident.recovery_start_time = datetime.utcnow()
        incident.status = "recovering"

        return incident

    async def complete_recovery(
        self,
        incident_id: UUID,
        lessons_learned: List[str]
    ) -> Optional[BCPIncident]:
        incident = await self.repository.find_incident_by_id(incident_id)
        if not incident:
            return None

        incident.recovery_end_time = datetime.utcnow()
        incident.status = "recovered"
        incident.lessons_learned = lessons_learned

        if incident.recovery_start_time:
            incident.actual_rto_hours = (
                incident.recovery_end_time - incident.recovery_start_time
            ).total_seconds() / 3600

        return incident

    async def close_incident(
        self,
        incident_id: UUID,
        financial_impact: Decimal
    ) -> Optional[BCPIncident]:
        incident = await self.repository.find_incident_by_id(incident_id)
        if not incident:
            return None

        incident.deactivation_time = datetime.utcnow()
        incident.status = "closed"
        incident.financial_impact = financial_impact
        incident.post_incident_review_date = date.today()

        return incident

    async def get_active_incidents(self) -> List[BCPIncident]:
        incidents = await self.repository.find_all_incidents()
        return [i for i in incidents if i.status in ["active", "recovering"]]

    async def add_crisis_team_member(
        self,
        team_name: str,
        role: str,
        primary_contact: str,
        primary_phone: str,
        primary_email: str,
        responsibilities: List[str],
        alternate_contact: Optional[str] = None,
        alternate_phone: Optional[str] = None,
        backup_person: Optional[str] = None,
        backup_phone: Optional[str] = None
    ) -> CrisisTeamMember:
        member = CrisisTeamMember(
            team_name=team_name,
            role=role,
            primary_contact=primary_contact,
            primary_phone=primary_phone,
            primary_email=primary_email,
            responsibilities=responsibilities,
            alternate_contact=alternate_contact,
            alternate_phone=alternate_phone,
            backup_person=backup_person,
            backup_phone=backup_phone
        )

        await self.repository.save_team_member(member)
        return member

    async def get_crisis_team(self, team_name: str) -> List[CrisisTeamMember]:
        return await self.repository.find_team_members_by_team(team_name)

    async def generate_metrics(
        self,
        business_unit: Optional[str] = None
    ) -> BCPMetrics:
        processes = await self.list_processes(business_unit=business_unit)
        bcps = await self.list_bcps(business_unit=business_unit)

        total_processes = len(processes)
        critical_processes = len([p for p in processes if p.criticality == CriticalityLevel.MISSION_CRITICAL])

        plans_approved = len([p for p in bcps if p.status == BCPStatus.APPROVED])
        plans_expired = len([p for p in bcps if p.status == BCPStatus.EXPIRED])

        tests = await self.repository.find_all_tests()
        current_year = date.today().year
        tests_ytd = [t for t in tests if t.test_date.year == current_year]
        tests_passed = len([t for t in tests_ytd if t.test_result == "pass"])

        rto_achievements = [t.rto_achieved for t in tests_ytd if t.rto_achieved]
        rpo_achievements = [t.rpo_achieved for t in tests_ytd if t.rpo_achieved]

        avg_rto = Decimal(str(sum(rto_achievements) / len(rto_achievements))) if rto_achievements else Decimal("0")
        avg_rpo = Decimal(str(sum(rpo_achievements) / len(rpo_achievements))) if rpo_achievements else Decimal("0")

        incidents = await self.repository.find_all_incidents()
        incidents_ytd = [i for i in incidents if i.declaration_time.year == current_year]
        successful = len([i for i in incidents_ytd if i.status == "closed"])

        overdue_reviews = len([p for p in bcps if p.next_review_date and p.next_review_date < date.today()])

        covered_processes = set()
        for plan in bcps:
            covered_processes.update(plan.processes_covered)
        coverage = Decimal(str(len(covered_processes) / total_processes * 100)) if total_processes > 0 else Decimal("0")

        metrics = BCPMetrics(
            metrics_date=date.today(),
            business_unit=business_unit,
            total_processes=total_processes,
            critical_processes=critical_processes,
            plans_count=len(bcps),
            plans_approved=plans_approved,
            plans_expired=plans_expired,
            tests_conducted_ytd=len(tests_ytd),
            tests_passed=tests_passed,
            average_rto_achievement=avg_rto,
            average_rpo_achievement=avg_rpo,
            incidents_ytd=len(incidents_ytd),
            successful_recoveries=successful,
            open_action_items=0,
            overdue_reviews=overdue_reviews,
            coverage_percentage=coverage
        )

        await self.repository.save_metrics(metrics)
        return metrics

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


business_continuity_service = BusinessContinuityService()
