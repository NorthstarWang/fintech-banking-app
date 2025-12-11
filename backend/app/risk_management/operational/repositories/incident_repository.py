"""Incident Repository - Data access layer for operational incidents"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.incident_models import (
    Incident, IncidentTimeline, IncidentEscalation, IncidentRootCauseAnalysis,
    IncidentCorrectiveAction, IncidentReport
)


class IncidentRepository:
    def __init__(self):
        self._incidents: Dict[UUID, Incident] = {}
        self._timelines: Dict[UUID, IncidentTimeline] = {}
        self._escalations: Dict[UUID, IncidentEscalation] = {}
        self._rcas: Dict[UUID, IncidentRootCauseAnalysis] = {}
        self._actions: Dict[UUID, IncidentCorrectiveAction] = {}
        self._reports: Dict[UUID, IncidentReport] = {}

    async def save_incident(self, incident: Incident) -> Incident:
        self._incidents[incident.incident_id] = incident
        return incident

    async def find_incident_by_id(self, incident_id: UUID) -> Optional[Incident]:
        return self._incidents.get(incident_id)

    async def find_incident_by_number(self, incident_number: str) -> Optional[Incident]:
        for incident in self._incidents.values():
            if incident.incident_number == incident_number:
                return incident
        return None

    async def find_all_incidents(self) -> List[Incident]:
        return list(self._incidents.values())

    async def update_incident(self, incident: Incident) -> Incident:
        self._incidents[incident.incident_id] = incident
        return incident

    async def save_timeline(self, timeline: IncidentTimeline) -> IncidentTimeline:
        self._timelines[timeline.timeline_id] = timeline
        return timeline

    async def find_timeline_by_incident(self, incident_id: UUID) -> List[IncidentTimeline]:
        return sorted(
            [t for t in self._timelines.values() if t.incident_id == incident_id],
            key=lambda x: x.event_time
        )

    async def save_escalation(self, escalation: IncidentEscalation) -> IncidentEscalation:
        self._escalations[escalation.escalation_id] = escalation
        return escalation

    async def find_escalations_by_incident(self, incident_id: UUID) -> List[IncidentEscalation]:
        return [e for e in self._escalations.values() if e.incident_id == incident_id]

    async def save_rca(self, rca: IncidentRootCauseAnalysis) -> IncidentRootCauseAnalysis:
        self._rcas[rca.analysis_id] = rca
        return rca

    async def find_rca_by_incident(self, incident_id: UUID) -> Optional[IncidentRootCauseAnalysis]:
        for rca in self._rcas.values():
            if rca.incident_id == incident_id:
                return rca
        return None

    async def save_corrective_action(self, action: IncidentCorrectiveAction) -> IncidentCorrectiveAction:
        self._actions[action.action_id] = action
        return action

    async def find_corrective_action_by_id(self, action_id: UUID) -> Optional[IncidentCorrectiveAction]:
        return self._actions.get(action_id)

    async def find_actions_by_incident(self, incident_id: UUID) -> List[IncidentCorrectiveAction]:
        return [a for a in self._actions.values() if a.incident_id == incident_id]

    async def save_report(self, report: IncidentReport) -> IncidentReport:
        self._reports[report.report_id] = report
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_incidents": len(self._incidents),
            "total_escalations": len(self._escalations),
            "total_actions": len(self._actions)
        }


incident_repository = IncidentRepository()
