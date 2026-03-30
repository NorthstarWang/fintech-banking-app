"""RCSA Repository - Data access layer for Risk Control Self-Assessment"""

from typing import Any
from uuid import UUID

from ..models.rcsa_models import RCSAActionItem, RCSAAssessment, RCSAControl, RCSAReport, RCSARisk, RiskHeatmap


class RCSARepository:
    def __init__(self):
        self._assessments: dict[UUID, RCSAAssessment] = {}
        self._risks: dict[UUID, RCSARisk] = {}
        self._controls: dict[UUID, RCSAControl] = {}
        self._action_items: dict[UUID, RCSAActionItem] = {}
        self._heatmaps: dict[UUID, RiskHeatmap] = {}
        self._reports: dict[UUID, RCSAReport] = {}

    async def save_assessment(self, assessment: RCSAAssessment) -> RCSAAssessment:
        self._assessments[assessment.assessment_id] = assessment
        return assessment

    async def find_assessment_by_id(self, assessment_id: UUID) -> RCSAAssessment | None:
        return self._assessments.get(assessment_id)

    async def find_all_assessments(self) -> list[RCSAAssessment]:
        return list(self._assessments.values())

    async def update_assessment(self, assessment: RCSAAssessment) -> RCSAAssessment:
        self._assessments[assessment.assessment_id] = assessment
        return assessment

    async def save_risk(self, risk: RCSARisk) -> RCSARisk:
        self._risks[risk.risk_id] = risk
        return risk

    async def find_risk_by_id(self, risk_id: UUID) -> RCSARisk | None:
        return self._risks.get(risk_id)

    async def find_risks_by_assessment(self, assessment_id: UUID) -> list[RCSARisk]:
        return [r for r in self._risks.values() if r.assessment_id == assessment_id]

    async def find_all_risks(self) -> list[RCSARisk]:
        return list(self._risks.values())

    async def save_control(self, control: RCSAControl) -> RCSAControl:
        self._controls[control.control_id] = control
        return control

    async def find_control_by_id(self, control_id: UUID) -> RCSAControl | None:
        return self._controls.get(control_id)

    async def find_controls_by_assessment(self, assessment_id: UUID) -> list[RCSAControl]:
        return [c for c in self._controls.values() if c.assessment_id == assessment_id]

    async def find_all_controls(self) -> list[RCSAControl]:
        return list(self._controls.values())

    async def save_action_item(self, action: RCSAActionItem) -> RCSAActionItem:
        self._action_items[action.action_id] = action
        return action

    async def find_action_item_by_id(self, action_id: UUID) -> RCSAActionItem | None:
        return self._action_items.get(action_id)

    async def find_action_items_by_assessment(self, assessment_id: UUID) -> list[RCSAActionItem]:
        return [a for a in self._action_items.values() if a.assessment_id == assessment_id]

    async def find_all_action_items(self) -> list[RCSAActionItem]:
        return list(self._action_items.values())

    async def save_heatmap(self, heatmap: RiskHeatmap) -> RiskHeatmap:
        self._heatmaps[heatmap.heatmap_id] = heatmap
        return heatmap

    async def save_report(self, report: RCSAReport) -> RCSAReport:
        self._reports[report.report_id] = report
        return report

    async def get_statistics(self) -> dict[str, Any]:
        return {
            "total_assessments": len(self._assessments),
            "total_risks": len(self._risks),
            "total_controls": len(self._controls),
            "total_action_items": len(self._action_items)
        }


rcsa_repository = RCSARepository()
