"""Vendor Risk Service - Business logic for third-party risk management"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from ..models.vendor_risk_models import (
    Vendor, VendorContract, VendorAssessment, VendorDueDiligence,
    VendorIncident, VendorPerformance, VendorRiskMetrics,
    VendorTier, VendorStatus, ServiceCategory, RiskRating, AssessmentType
)
from ..repositories.vendor_risk_repository import vendor_risk_repository


class VendorRiskService:
    def __init__(self):
        self.repository = vendor_risk_repository
        self._vendor_counter = 0

    def _generate_vendor_code(self) -> str:
        self._vendor_counter += 1
        return f"VND-{self._vendor_counter:05d}"

    def _calculate_tier(
        self,
        annual_spend: Decimal,
        data_access: bool,
        pii_access: bool,
        system_access: bool,
        critical_vendor: bool
    ) -> VendorTier:
        if critical_vendor or pii_access:
            return VendorTier.TIER_1
        if annual_spend > Decimal("1000000") or data_access:
            return VendorTier.TIER_2
        if annual_spend > Decimal("100000") or system_access:
            return VendorTier.TIER_3
        return VendorTier.TIER_4

    async def register_vendor(
        self,
        vendor_name: str,
        legal_name: str,
        service_category: ServiceCategory,
        services_provided: List[str],
        primary_contact: str,
        contact_email: str,
        contact_phone: str,
        address: str,
        country: str,
        relationship_owner: str,
        business_unit: str,
        annual_spend: Decimal = Decimal("0"),
        payment_terms: str = "Net 30",
        data_access: bool = False,
        pii_access: bool = False,
        system_access: bool = False,
        critical_vendor: bool = False
    ) -> Vendor:
        tier = self._calculate_tier(annual_spend, data_access, pii_access, system_access, critical_vendor)

        vendor = Vendor(
            vendor_code=self._generate_vendor_code(),
            vendor_name=vendor_name,
            legal_name=legal_name,
            vendor_tier=tier,
            service_category=service_category,
            services_provided=services_provided,
            primary_contact=primary_contact,
            contact_email=contact_email,
            contact_phone=contact_phone,
            address=address,
            country=country,
            relationship_owner=relationship_owner,
            business_unit=business_unit,
            annual_spend=annual_spend,
            payment_terms=payment_terms,
            data_access=data_access,
            pii_access=pii_access,
            system_access=system_access,
            critical_vendor=critical_vendor
        )

        await self.repository.save_vendor(vendor)
        return vendor

    async def get_vendor(self, vendor_id: UUID) -> Optional[Vendor]:
        return await self.repository.find_vendor_by_id(vendor_id)

    async def get_vendor_by_code(self, vendor_code: str) -> Optional[Vendor]:
        return await self.repository.find_vendor_by_code(vendor_code)

    async def list_vendors(
        self,
        status: Optional[VendorStatus] = None,
        tier: Optional[VendorTier] = None,
        category: Optional[ServiceCategory] = None,
        critical_only: bool = False
    ) -> List[Vendor]:
        vendors = await self.repository.find_all_vendors()

        if status:
            vendors = [v for v in vendors if v.status == status]
        if tier:
            vendors = [v for v in vendors if v.vendor_tier == tier]
        if category:
            vendors = [v for v in vendors if v.service_category == category]
        if critical_only:
            vendors = [v for v in vendors if v.critical_vendor]

        return vendors

    async def update_vendor_status(
        self,
        vendor_id: UUID,
        new_status: VendorStatus
    ) -> Optional[Vendor]:
        vendor = await self.repository.find_vendor_by_id(vendor_id)
        if not vendor:
            return None

        vendor.status = new_status
        if new_status == VendorStatus.ACTIVE and not vendor.onboarding_date:
            vendor.onboarding_date = date.today()

        await self.repository.update_vendor(vendor)
        return vendor

    async def create_contract(
        self,
        vendor_id: UUID,
        contract_number: str,
        contract_name: str,
        contract_type: str,
        effective_date: date,
        expiration_date: date,
        contract_value: Decimal,
        currency: str,
        payment_frequency: str,
        termination_notice_days: int,
        owner: str,
        approved_by: str,
        document_location: str,
        auto_renewal: bool = False,
        sla_attached: bool = False,
        audit_rights: bool = False
    ) -> VendorContract:
        contract = VendorContract(
            vendor_id=vendor_id,
            contract_number=contract_number,
            contract_name=contract_name,
            contract_type=contract_type,
            effective_date=effective_date,
            expiration_date=expiration_date,
            contract_value=contract_value,
            currency=currency,
            payment_frequency=payment_frequency,
            termination_notice_days=termination_notice_days,
            owner=owner,
            approved_by=approved_by,
            approval_date=date.today(),
            document_location=document_location,
            auto_renewal=auto_renewal,
            sla_attached=sla_attached,
            audit_rights=audit_rights
        )

        await self.repository.save_contract(contract)

        vendor = await self.repository.find_vendor_by_id(vendor_id)
        if vendor:
            vendor.contract_end_date = expiration_date
            await self.repository.update_vendor(vendor)

        return contract

    async def get_vendor_contracts(self, vendor_id: UUID) -> List[VendorContract]:
        return await self.repository.find_contracts_by_vendor(vendor_id)

    async def get_expiring_contracts(self, days: int = 90) -> List[VendorContract]:
        contracts = await self.repository.find_all_contracts()
        cutoff = date.today()
        cutoff_end = date(cutoff.year, cutoff.month, cutoff.day)

        from datetime import timedelta
        cutoff_end = cutoff + timedelta(days=days)

        return [c for c in contracts if cutoff <= c.expiration_date <= cutoff_end]

    async def perform_assessment(
        self,
        vendor_id: UUID,
        assessment_type: AssessmentType,
        assessor: str,
        financial_risk_rating: RiskRating,
        operational_risk_rating: RiskRating,
        compliance_risk_rating: RiskRating,
        security_risk_rating: RiskRating,
        reputational_risk_rating: RiskRating,
        financial_stability: str,
        years_in_business: int,
        certifications: List[str],
        audit_reports: List[str],
        insurance_coverage: Dict[str, Decimal],
        findings: List[str] = None,
        recommendations: List[str] = None
    ) -> VendorAssessment:
        ratings = [
            financial_risk_rating, operational_risk_rating,
            compliance_risk_rating, security_risk_rating, reputational_risk_rating
        ]
        rating_scores = {RiskRating.LOW: 1, RiskRating.MEDIUM: 2, RiskRating.HIGH: 3, RiskRating.CRITICAL: 4}
        avg_score = sum(rating_scores[r] for r in ratings) / len(ratings)

        if avg_score >= 3.5:
            overall = RiskRating.CRITICAL
        elif avg_score >= 2.5:
            overall = RiskRating.HIGH
        elif avg_score >= 1.5:
            overall = RiskRating.MEDIUM
        else:
            overall = RiskRating.LOW

        inherent_score = int(avg_score * 25)
        residual_score = int(inherent_score * 0.7)

        assessment = VendorAssessment(
            vendor_id=vendor_id,
            assessment_type=assessment_type,
            assessment_date=date.today(),
            assessor=assessor,
            status="completed",
            financial_risk_rating=financial_risk_rating,
            operational_risk_rating=operational_risk_rating,
            compliance_risk_rating=compliance_risk_rating,
            security_risk_rating=security_risk_rating,
            reputational_risk_rating=reputational_risk_rating,
            overall_risk_rating=overall,
            inherent_risk_score=inherent_score,
            residual_risk_score=residual_score,
            financial_stability=financial_stability,
            years_in_business=years_in_business,
            certifications=certifications,
            audit_reports=audit_reports,
            insurance_coverage=insurance_coverage,
            findings=findings or [],
            recommendations=recommendations or []
        )

        await self.repository.save_assessment(assessment)

        vendor = await self.repository.find_vendor_by_id(vendor_id)
        if vendor:
            vendor.overall_risk_rating = overall
            vendor.last_assessment_date = date.today()
            vendor.next_assessment_date = self._calculate_next_assessment(vendor.vendor_tier)
            await self.repository.update_vendor(vendor)

        return assessment

    def _calculate_next_assessment(self, tier: VendorTier) -> date:
        from datetime import timedelta
        if tier == VendorTier.TIER_1:
            return date.today() + timedelta(days=180)
        elif tier == VendorTier.TIER_2:
            return date.today() + timedelta(days=365)
        elif tier == VendorTier.TIER_3:
            return date.today() + timedelta(days=730)
        return date.today() + timedelta(days=1095)

    async def get_vendor_assessments(self, vendor_id: UUID) -> List[VendorAssessment]:
        return await self.repository.find_assessments_by_vendor(vendor_id)

    async def initiate_due_diligence(
        self,
        vendor_id: UUID,
        due_diligence_type: str,
        performed_by: str,
        background_check: bool = True,
        financial_review: bool = True,
        reference_check: bool = True,
        security_assessment: bool = True,
        compliance_verification: bool = True,
        sanctions_screening: bool = True,
        adverse_media_check: bool = True
    ) -> VendorDueDiligence:
        dd = VendorDueDiligence(
            vendor_id=vendor_id,
            due_diligence_type=due_diligence_type,
            request_date=date.today(),
            performed_by=performed_by,
            background_check=background_check,
            financial_review=financial_review,
            reference_check=reference_check,
            security_assessment=security_assessment,
            compliance_verification=compliance_verification,
            sanctions_screening=sanctions_screening,
            adverse_media_check=adverse_media_check
        )

        await self.repository.save_due_diligence(dd)
        return dd

    async def complete_due_diligence(
        self,
        dd_id: UUID,
        findings: Dict[str, Any],
        risk_flags: List[str],
        recommendation: str,
        reviewed_by: str
    ) -> Optional[VendorDueDiligence]:
        dd = await self.repository.find_due_diligence_by_id(dd_id)
        if not dd:
            return None

        dd.completion_date = date.today()
        dd.status = "completed"
        dd.findings = findings
        dd.risk_flags = risk_flags
        dd.recommendation = recommendation
        dd.reviewed_by = reviewed_by

        return dd

    async def report_incident(
        self,
        vendor_id: UUID,
        incident_type: str,
        severity: str,
        description: str,
        impact_description: str,
        service_affected: str,
        sla_breached: bool = False
    ) -> VendorIncident:
        incident = VendorIncident(
            vendor_id=vendor_id,
            incident_date=datetime.utcnow(),
            reported_date=datetime.utcnow(),
            incident_type=incident_type,
            severity=severity,
            description=description,
            impact_description=impact_description,
            service_affected=service_affected,
            sla_breached=sla_breached
        )

        await self.repository.save_incident(incident)
        return incident

    async def resolve_incident(
        self,
        incident_id: UUID,
        root_cause: str,
        vendor_response: str,
        remediation_actions: List[str],
        credit_applied: Optional[Decimal] = None
    ) -> Optional[VendorIncident]:
        incident = await self.repository.find_incident_by_id(incident_id)
        if not incident:
            return None

        incident.root_cause = root_cause
        incident.vendor_response = vendor_response
        incident.remediation_actions = remediation_actions
        incident.resolution_date = datetime.utcnow()
        incident.status = "resolved"
        incident.credit_applied = credit_applied

        return incident

    async def get_vendor_incidents(self, vendor_id: UUID) -> List[VendorIncident]:
        return await self.repository.find_incidents_by_vendor(vendor_id)

    async def record_performance(
        self,
        vendor_id: UUID,
        review_period: str,
        period_start: date,
        period_end: date,
        sla_metrics: Dict[str, Decimal],
        quality_score: Decimal,
        delivery_score: Decimal,
        responsiveness_score: Decimal,
        cost_performance: Decimal,
        issues_reported: int,
        issues_resolved: int,
        strengths: List[str],
        areas_for_improvement: List[str],
        reviewer: str
    ) -> VendorPerformance:
        overall_sla = sum(sla_metrics.values()) / len(sla_metrics) if sla_metrics else Decimal("0")
        overall_score = (quality_score + delivery_score + responsiveness_score + cost_performance) / 4

        incidents = await self.repository.find_incidents_by_vendor(vendor_id)
        incidents_count = len([i for i in incidents if period_start <= i.incident_date.date() <= period_end])

        performance = VendorPerformance(
            vendor_id=vendor_id,
            review_period=review_period,
            period_start=period_start,
            period_end=period_end,
            sla_metrics=sla_metrics,
            overall_sla_compliance=overall_sla,
            quality_score=quality_score,
            delivery_score=delivery_score,
            responsiveness_score=responsiveness_score,
            cost_performance=cost_performance,
            overall_score=overall_score,
            issues_reported=issues_reported,
            issues_resolved=issues_resolved,
            incidents_count=incidents_count,
            strengths=strengths,
            areas_for_improvement=areas_for_improvement,
            action_items=[],
            reviewer=reviewer,
            review_date=date.today()
        )

        await self.repository.save_performance(performance)
        return performance

    async def get_vendor_performance(self, vendor_id: UUID) -> List[VendorPerformance]:
        return await self.repository.find_performance_by_vendor(vendor_id)

    async def generate_metrics(self) -> VendorRiskMetrics:
        vendors = await self.repository.find_all_vendors()

        total = len(vendors)
        active = len([v for v in vendors if v.status == VendorStatus.ACTIVE])
        critical = len([v for v in vendors if v.critical_vendor])

        tier_counts = {
            VendorTier.TIER_1: 0,
            VendorTier.TIER_2: 0,
            VendorTier.TIER_3: 0,
            VendorTier.TIER_4: 0
        }
        for v in vendors:
            tier_counts[v.vendor_tier] += 1

        high_risk = len([v for v in vendors if v.overall_risk_rating in [RiskRating.HIGH, RiskRating.CRITICAL]])
        total_spend = sum(v.annual_spend for v in vendors)

        assessments_due = len([v for v in vendors if v.next_assessment_date and v.next_assessment_date <= date.today()])
        assessments_overdue = len([
            v for v in vendors
            if v.next_assessment_date and v.next_assessment_date < date.today()
        ])

        expiring = await self.get_expiring_contracts(90)

        incidents = await self.repository.find_all_incidents()
        open_incidents = len([i for i in incidents if i.status == "open"])

        performances = await self.repository.find_all_performances()
        avg_score = sum(p.overall_score for p in performances) / len(performances) if performances else Decimal("0")

        concentration = len([v for v in vendors if v.concentration_risk])
        data_access = len([v for v in vendors if v.data_access])

        metrics = VendorRiskMetrics(
            metrics_date=date.today(),
            total_vendors=total,
            active_vendors=active,
            critical_vendors=critical,
            tier_1_count=tier_counts[VendorTier.TIER_1],
            tier_2_count=tier_counts[VendorTier.TIER_2],
            tier_3_count=tier_counts[VendorTier.TIER_3],
            tier_4_count=tier_counts[VendorTier.TIER_4],
            high_risk_vendors=high_risk,
            total_spend=total_spend,
            assessments_due=assessments_due,
            assessments_overdue=assessments_overdue,
            contracts_expiring_90_days=len(expiring),
            open_incidents=open_incidents,
            average_performance_score=avg_score,
            concentration_risk_vendors=concentration,
            data_access_vendors=data_access
        )

        await self.repository.save_metrics(metrics)
        return metrics

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


vendor_risk_service = VendorRiskService()
