"""RCSA Service - Business logic for Risk Control Self-Assessment"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from ..models.rcsa_models import (
    RCSAAssessment, RCSARisk, RCSAControl, RCSAActionItem, RiskHeatmap, RCSAReport,
    RiskCategory, RiskLikelihood, RiskImpact, ControlEffectiveness, AssessmentStatus
)
from ..repositories.rcsa_repository import rcsa_repository


class RCSAService:
    LIKELIHOOD_SCORES = {
        RiskLikelihood.RARE: 1,
        RiskLikelihood.UNLIKELY: 2,
        RiskLikelihood.POSSIBLE: 3,
        RiskLikelihood.LIKELY: 4,
        RiskLikelihood.ALMOST_CERTAIN: 5
    }

    IMPACT_SCORES = {
        RiskImpact.NEGLIGIBLE: 1,
        RiskImpact.MINOR: 2,
        RiskImpact.MODERATE: 3,
        RiskImpact.MAJOR: 4,
        RiskImpact.CATASTROPHIC: 5
    }

    def __init__(self):
        self.repository = rcsa_repository
        self._risk_counter = 0
        self._control_counter = 0

    def _calculate_risk_score(self, likelihood: RiskLikelihood, impact: RiskImpact) -> int:
        return self.LIKELIHOOD_SCORES[likelihood] * self.IMPACT_SCORES[impact]

    def _get_risk_rating(self, score: int) -> str:
        if score >= 20:
            return "critical"
        elif score >= 12:
            return "high"
        elif score >= 6:
            return "medium"
        return "low"

    async def create_assessment(
        self,
        assessment_name: str,
        business_unit: str,
        process_name: str,
        process_owner: str,
        due_date: date,
        assessor: str
    ) -> RCSAAssessment:
        assessment = RCSAAssessment(
            assessment_name=assessment_name,
            business_unit=business_unit,
            process_name=process_name,
            process_owner=process_owner,
            assessment_date=date.today(),
            due_date=due_date,
            assessor=assessor
        )

        await self.repository.save_assessment(assessment)
        return assessment

    async def get_assessment(self, assessment_id: UUID) -> Optional[RCSAAssessment]:
        return await self.repository.find_assessment_by_id(assessment_id)

    async def list_assessments(
        self,
        status: Optional[AssessmentStatus] = None,
        business_unit: Optional[str] = None
    ) -> List[RCSAAssessment]:
        assessments = await self.repository.find_all_assessments()

        if status:
            assessments = [a for a in assessments if a.status == status]
        if business_unit:
            assessments = [a for a in assessments if a.business_unit == business_unit]

        return assessments

    async def update_assessment_status(
        self,
        assessment_id: UUID,
        new_status: AssessmentStatus,
        reviewer: Optional[str] = None,
        approver: Optional[str] = None
    ) -> Optional[RCSAAssessment]:
        assessment = await self.repository.find_assessment_by_id(assessment_id)
        if not assessment:
            return None

        assessment.status = new_status

        if new_status == AssessmentStatus.PENDING_REVIEW and reviewer:
            assessment.reviewer = reviewer
            assessment.review_date = date.today()
        elif new_status == AssessmentStatus.APPROVED and approver:
            assessment.approver = approver
            assessment.approval_date = date.today()
            assessment.next_assessment_date = date(
                date.today().year + 1,
                date.today().month,
                date.today().day
            )

        await self.repository.update_assessment(assessment)
        return assessment

    async def add_risk(
        self,
        assessment_id: UUID,
        risk_name: str,
        risk_description: str,
        risk_category: RiskCategory,
        risk_owner: str,
        inherent_likelihood: RiskLikelihood,
        inherent_impact: RiskImpact,
        residual_likelihood: RiskLikelihood,
        residual_impact: RiskImpact,
        risk_appetite: str
    ) -> RCSARisk:
        self._risk_counter += 1

        inherent_score = self._calculate_risk_score(inherent_likelihood, inherent_impact)
        residual_score = self._calculate_risk_score(residual_likelihood, residual_impact)

        risk = RCSARisk(
            assessment_id=assessment_id,
            risk_reference=f"RISK-{self._risk_counter:04d}",
            risk_name=risk_name,
            risk_description=risk_description,
            risk_category=risk_category,
            risk_owner=risk_owner,
            inherent_likelihood=inherent_likelihood,
            inherent_impact=inherent_impact,
            inherent_risk_score=inherent_score,
            inherent_risk_rating=self._get_risk_rating(inherent_score),
            residual_likelihood=residual_likelihood,
            residual_impact=residual_impact,
            residual_risk_score=residual_score,
            residual_risk_rating=self._get_risk_rating(residual_score),
            risk_appetite=risk_appetite,
            within_appetite=residual_score <= int(risk_appetite) if risk_appetite.isdigit() else True
        )

        await self.repository.save_risk(risk)

        assessment = await self.repository.find_assessment_by_id(assessment_id)
        if assessment:
            assessment.total_risks_identified += 1
            await self.repository.update_assessment(assessment)

        return risk

    async def get_assessment_risks(self, assessment_id: UUID) -> List[RCSARisk]:
        return await self.repository.find_risks_by_assessment(assessment_id)

    async def add_control(
        self,
        assessment_id: UUID,
        control_name: str,
        control_description: str,
        control_type: str,
        control_nature: str,
        control_owner: str,
        frequency: str,
        design_effectiveness: ControlEffectiveness,
        operating_effectiveness: ControlEffectiveness,
        risks_mitigated: List[UUID] = None
    ) -> RCSAControl:
        self._control_counter += 1

        if design_effectiveness == ControlEffectiveness.EFFECTIVE and operating_effectiveness == ControlEffectiveness.EFFECTIVE:
            overall = ControlEffectiveness.EFFECTIVE
        elif design_effectiveness == ControlEffectiveness.INEFFECTIVE or operating_effectiveness == ControlEffectiveness.INEFFECTIVE:
            overall = ControlEffectiveness.INEFFECTIVE
        else:
            overall = ControlEffectiveness.PARTIALLY_EFFECTIVE

        control = RCSAControl(
            assessment_id=assessment_id,
            control_reference=f"CTRL-{self._control_counter:04d}",
            control_name=control_name,
            control_description=control_description,
            control_type=control_type,
            control_nature=control_nature,
            control_owner=control_owner,
            frequency=frequency,
            design_effectiveness=design_effectiveness,
            operating_effectiveness=operating_effectiveness,
            overall_effectiveness=overall,
            risks_mitigated=risks_mitigated or [],
            improvement_required=overall != ControlEffectiveness.EFFECTIVE
        )

        await self.repository.save_control(control)

        assessment = await self.repository.find_assessment_by_id(assessment_id)
        if assessment:
            assessment.total_controls_assessed += 1
            await self.repository.update_assessment(assessment)

        return control

    async def get_assessment_controls(self, assessment_id: UUID) -> List[RCSAControl]:
        return await self.repository.find_controls_by_assessment(assessment_id)

    async def add_action_item(
        self,
        assessment_id: UUID,
        action_type: str,
        action_description: str,
        assigned_to: str,
        due_date: date,
        priority: str,
        risk_id: Optional[UUID] = None,
        control_id: Optional[UUID] = None
    ) -> RCSAActionItem:
        action = RCSAActionItem(
            assessment_id=assessment_id,
            risk_id=risk_id,
            control_id=control_id,
            action_type=action_type,
            action_description=action_description,
            assigned_to=assigned_to,
            due_date=due_date,
            priority=priority
        )

        await self.repository.save_action_item(action)

        assessment = await self.repository.find_assessment_by_id(assessment_id)
        if assessment:
            assessment.action_items_count += 1
            await self.repository.update_assessment(assessment)

        return action

    async def complete_action_item(
        self,
        action_id: UUID,
        verified_by: str
    ) -> Optional[RCSAActionItem]:
        action = await self.repository.find_action_item_by_id(action_id)
        if not action:
            return None

        action.status = "completed"
        action.completion_date = date.today()
        action.verified_by = verified_by
        action.verification_date = date.today()

        return action

    async def get_assessment_actions(self, assessment_id: UUID) -> List[RCSAActionItem]:
        return await self.repository.find_action_items_by_assessment(assessment_id)

    async def generate_heatmap(
        self,
        assessment_id: Optional[UUID] = None,
        business_unit: Optional[str] = None,
        heatmap_type: str = "residual"
    ) -> RiskHeatmap:
        if assessment_id:
            risks = await self.repository.find_risks_by_assessment(assessment_id)
        else:
            risks = await self.repository.find_all_risks()
            if business_unit:
                assessments = await self.list_assessments(business_unit=business_unit)
                assessment_ids = {a.assessment_id for a in assessments}
                risks = [r for r in risks if r.assessment_id in assessment_ids]

        matrix = [[0] * 5 for _ in range(5)]
        distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for risk in risks:
            if heatmap_type == "inherent":
                likelihood = risk.inherent_likelihood
                impact = risk.inherent_impact
                rating = risk.inherent_risk_rating
            else:
                likelihood = risk.residual_likelihood
                impact = risk.residual_impact
                rating = risk.residual_risk_rating

            l_idx = self.LIKELIHOOD_SCORES[likelihood] - 1
            i_idx = self.IMPACT_SCORES[impact] - 1
            matrix[l_idx][i_idx] += 1
            distribution[rating] += 1

        heatmap = RiskHeatmap(
            assessment_id=assessment_id,
            generated_date=date.today(),
            heatmap_type=heatmap_type,
            business_unit=business_unit,
            matrix_data=matrix,
            risk_distribution=distribution,
            high_risk_count=distribution["critical"] + distribution["high"],
            medium_risk_count=distribution["medium"],
            low_risk_count=distribution["low"],
            total_risks=len(risks)
        )

        await self.repository.save_heatmap(heatmap)
        return heatmap

    async def generate_report(
        self,
        report_type: str,
        period: str,
        business_unit: Optional[str] = None,
        generated_by: str = "system"
    ) -> RCSAReport:
        assessments = await self.list_assessments(business_unit=business_unit)

        completed = len([a for a in assessments if a.status == AssessmentStatus.APPROVED])
        pending = len([a for a in assessments if a.status != AssessmentStatus.APPROVED])

        all_risks = await self.repository.find_all_risks()
        if business_unit:
            assessment_ids = {a.assessment_id for a in assessments}
            all_risks = [r for r in all_risks if r.assessment_id in assessment_ids]

        high_risks = len([r for r in all_risks if r.residual_risk_rating in ["critical", "high"]])
        medium_risks = len([r for r in all_risks if r.residual_risk_rating == "medium"])
        low_risks = len([r for r in all_risks if r.residual_risk_rating == "low"])
        outside_appetite = len([r for r in all_risks if not r.within_appetite])

        all_controls = await self.repository.find_all_controls()
        if business_unit:
            all_controls = [c for c in all_controls if c.assessment_id in assessment_ids]

        effective = len([c for c in all_controls if c.overall_effectiveness == ControlEffectiveness.EFFECTIVE])
        partial = len([c for c in all_controls if c.overall_effectiveness == ControlEffectiveness.PARTIALLY_EFFECTIVE])
        ineffective = len([c for c in all_controls if c.overall_effectiveness == ControlEffectiveness.INEFFECTIVE])

        all_actions = await self.repository.find_all_action_items()
        if business_unit:
            all_actions = [a for a in all_actions if a.assessment_id in assessment_ids]

        open_actions = len([a for a in all_actions if a.status == "open"])
        overdue = len([a for a in all_actions if a.status == "open" and a.due_date < date.today()])

        report = RCSAReport(
            report_date=date.today(),
            report_type=report_type,
            period=period,
            business_unit=business_unit,
            assessments_completed=completed,
            assessments_pending=pending,
            total_risks=len(all_risks),
            high_risks=high_risks,
            medium_risks=medium_risks,
            low_risks=low_risks,
            risks_outside_appetite=outside_appetite,
            total_controls=len(all_controls),
            effective_controls=effective,
            partially_effective_controls=partial,
            ineffective_controls=ineffective,
            open_action_items=open_actions,
            overdue_action_items=overdue,
            generated_by=generated_by
        )

        await self.repository.save_report(report)
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


rcsa_service = RCSAService()
