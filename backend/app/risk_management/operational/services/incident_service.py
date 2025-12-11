"""Incident Service - Business logic for operational incident management"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID
from decimal import Decimal
from ..models.incident_models import (
    Incident, IncidentTimeline, IncidentEscalation, IncidentRootCauseAnalysis,
    IncidentCorrectiveAction, IncidentReport, IncidentSeverity, IncidentStatus,
    IncidentCategory, IncidentImpact
)
from ..repositories.incident_repository import incident_repository


class IncidentService:
    def __init__(self):
        self.repository = incident_repository
        self._incident_counter = 0

    def _generate_incident_number(self) -> str:
        self._incident_counter += 1
        return f"INC-{date.today().strftime('%Y%m')}-{self._incident_counter:05d}"

    async def create_incident(
        self,
        title: str,
        description: str,
        category: IncidentCategory,
        severity: IncidentSeverity,
        reported_by: str,
        occurred_date: datetime,
        detected_date: datetime,
        business_unit: str,
        affected_systems: List[str] = None,
        impact_types: List[IncidentImpact] = None,
        estimated_loss: Optional[Decimal] = None
    ) -> Incident:
        incident = Incident(
            incident_number=self._generate_incident_number(),
            title=title,
            description=description,
            category=category,
            severity=severity,
            reported_by=reported_by,
            occurred_date=occurred_date,
            detected_date=detected_date,
            business_unit=business_unit,
            affected_systems=affected_systems or [],
            impact_types=impact_types or [],
            estimated_loss=estimated_loss
        )

        await self.repository.save_incident(incident)

        timeline = IncidentTimeline(
            incident_id=incident.incident_id,
            event_type="created",
            description="Incident created",
            performed_by=reported_by,
            new_status=IncidentStatus.OPEN
        )
        await self.repository.save_timeline(timeline)

        if severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
            await self._auto_escalate(incident)

        return incident

    async def _auto_escalate(self, incident: Incident) -> None:
        incident.escalated = True
        incident.escalation_level = 1
        await self.repository.update_incident(incident)

    async def get_incident(self, incident_id: UUID) -> Optional[Incident]:
        return await self.repository.find_incident_by_id(incident_id)

    async def get_incident_by_number(self, incident_number: str) -> Optional[Incident]:
        return await self.repository.find_incident_by_number(incident_number)

    async def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        category: Optional[IncidentCategory] = None,
        business_unit: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Incident]:
        incidents = await self.repository.find_all_incidents()

        if status:
            incidents = [i for i in incidents if i.status == status]
        if severity:
            incidents = [i for i in incidents if i.severity == severity]
        if category:
            incidents = [i for i in incidents if i.category == category]
        if business_unit:
            incidents = [i for i in incidents if i.business_unit == business_unit]
        if start_date:
            incidents = [i for i in incidents if i.reported_date.date() >= start_date]
        if end_date:
            incidents = [i for i in incidents if i.reported_date.date() <= end_date]

        return incidents

    async def update_incident_status(
        self,
        incident_id: UUID,
        new_status: IncidentStatus,
        updated_by: str,
        notes: Optional[str] = None
    ) -> Optional[Incident]:
        incident = await self.repository.find_incident_by_id(incident_id)
        if not incident:
            return None

        old_status = incident.status
        incident.status = new_status

        if new_status == IncidentStatus.RESOLVED:
            incident.resolved_date = datetime.utcnow()
        elif new_status == IncidentStatus.CLOSED:
            incident.closed_date = datetime.utcnow()

        await self.repository.update_incident(incident)

        timeline = IncidentTimeline(
            incident_id=incident_id,
            event_type="status_change",
            description=notes or f"Status changed from {old_status} to {new_status}",
            performed_by=updated_by,
            old_status=old_status,
            new_status=new_status
        )
        await self.repository.save_timeline(timeline)

        return incident

    async def assign_incident(
        self,
        incident_id: UUID,
        assigned_to: str,
        assigned_by: str
    ) -> Optional[Incident]:
        incident = await self.repository.find_incident_by_id(incident_id)
        if not incident:
            return None

        incident.assigned_to = assigned_to
        if incident.status == IncidentStatus.OPEN:
            incident.status = IncidentStatus.IN_PROGRESS

        await self.repository.update_incident(incident)

        timeline = IncidentTimeline(
            incident_id=incident_id,
            event_type="assignment",
            description=f"Incident assigned to {assigned_to}",
            performed_by=assigned_by
        )
        await self.repository.save_timeline(timeline)

        return incident

    async def escalate_incident(
        self,
        incident_id: UUID,
        escalated_to: str,
        escalated_by: str,
        reason: str
    ) -> Optional[IncidentEscalation]:
        incident = await self.repository.find_incident_by_id(incident_id)
        if not incident:
            return None

        incident.escalated = True
        incident.escalation_level += 1
        await self.repository.update_incident(incident)

        escalation = IncidentEscalation(
            incident_id=incident_id,
            escalation_level=incident.escalation_level,
            escalated_to=escalated_to,
            escalated_by=escalated_by,
            reason=reason
        )
        await self.repository.save_escalation(escalation)

        return escalation

    async def add_root_cause_analysis(
        self,
        incident_id: UUID,
        analyst: str,
        root_causes: List[str],
        contributing_factors: List[str],
        methodology: str,
        findings: str,
        recommendations: List[str],
        preventive_measures: List[str]
    ) -> IncidentRootCauseAnalysis:
        rca = IncidentRootCauseAnalysis(
            incident_id=incident_id,
            analysis_date=date.today(),
            analyst=analyst,
            root_causes=root_causes,
            contributing_factors=contributing_factors,
            methodology=methodology,
            findings=findings,
            recommendations=recommendations,
            preventive_measures=preventive_measures
        )

        await self.repository.save_rca(rca)

        incident = await self.repository.find_incident_by_id(incident_id)
        if incident:
            incident.root_cause = "; ".join(root_causes)
            await self.repository.update_incident(incident)

        return rca

    async def add_corrective_action(
        self,
        incident_id: UUID,
        action_type: str,
        description: str,
        assigned_to: str,
        due_date: date,
        analysis_id: Optional[UUID] = None
    ) -> IncidentCorrectiveAction:
        action = IncidentCorrectiveAction(
            incident_id=incident_id,
            analysis_id=analysis_id,
            action_type=action_type,
            description=description,
            assigned_to=assigned_to,
            due_date=due_date
        )

        await self.repository.save_corrective_action(action)
        return action

    async def complete_corrective_action(
        self,
        action_id: UUID,
        verified_by: str
    ) -> Optional[IncidentCorrectiveAction]:
        action = await self.repository.find_corrective_action_by_id(action_id)
        if not action:
            return None

        action.status = "completed"
        action.completion_date = date.today()
        action.verified_by = verified_by
        action.verification_date = date.today()

        return action

    async def get_incident_timeline(self, incident_id: UUID) -> List[IncidentTimeline]:
        return await self.repository.find_timeline_by_incident(incident_id)

    async def generate_report(
        self,
        report_type: str,
        period_start: date,
        period_end: date,
        generated_by: str
    ) -> IncidentReport:
        incidents = await self.list_incidents(start_date=period_start, end_date=period_end)

        by_severity = {}
        by_category = {}
        by_status = {}
        total_estimated = Decimal("0")
        total_actual = Decimal("0")
        resolution_times = []
        escalation_count = 0

        for incident in incidents:
            by_severity[incident.severity.value] = by_severity.get(incident.severity.value, 0) + 1
            by_category[incident.category.value] = by_category.get(incident.category.value, 0) + 1
            by_status[incident.status.value] = by_status.get(incident.status.value, 0) + 1

            if incident.estimated_loss:
                total_estimated += incident.estimated_loss
            if incident.actual_loss:
                total_actual += incident.actual_loss
            if incident.resolved_date and incident.reported_date:
                resolution_times.append(
                    (incident.resolved_date - incident.reported_date).total_seconds() / 3600
                )
            if incident.escalated:
                escalation_count += 1

        avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        escalation_rate = escalation_count / len(incidents) if incidents else 0

        trending = sorted(by_category.items(), key=lambda x: x[1], reverse=True)[:3]

        report = IncidentReport(
            report_date=date.today(),
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            total_incidents=len(incidents),
            incidents_by_severity=by_severity,
            incidents_by_category=by_category,
            incidents_by_status=by_status,
            total_estimated_loss=total_estimated,
            total_actual_loss=total_actual,
            average_resolution_time=avg_resolution,
            escalation_rate=escalation_rate,
            trending_categories=[t[0] for t in trending],
            generated_by=generated_by
        )

        await self.repository.save_report(report)
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


incident_service = IncidentService()
