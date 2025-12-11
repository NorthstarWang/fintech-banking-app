"""Consumer Protection Service - Business logic for consumer protection compliance"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID
from decimal import Decimal
from ..models.consumer_protection_models import (
    ConsumerComplaint, FairLendingAnalysis, TILADisclosure, RESPADisclosure,
    UDAPReview, ServicememberProtection, ConsumerProtectionReport,
    ComplaintCategory, ComplaintStatus, FairLendingProtectedClass
)
from ..repositories.consumer_protection_repository import consumer_protection_repository


class ConsumerProtectionService:
    def __init__(self):
        self.repository = consumer_protection_repository
        self._complaint_counter = 0

    async def create_complaint(
        self, customer_id: str, customer_name: str, contact_method: str,
        category: ComplaintCategory, product_type: str, description: str,
        amount_disputed: Optional[Decimal] = None, regulatory_complaint: bool = False,
        regulator_reference: Optional[str] = None
    ) -> ConsumerComplaint:
        self._complaint_counter += 1
        sla_days = 30 if regulatory_complaint else 15

        complaint = ConsumerComplaint(
            complaint_reference=f"CMP-{date.today().strftime('%Y%m')}-{self._complaint_counter:05d}",
            customer_id=customer_id, customer_name=customer_name, contact_method=contact_method,
            received_date=datetime.utcnow(), category=category, product_type=product_type,
            description=description, amount_disputed=amount_disputed,
            sla_due_date=date.today() + timedelta(days=sla_days),
            regulatory_complaint=regulatory_complaint, regulator_reference=regulator_reference,
            priority="high" if regulatory_complaint else "normal"
        )
        await self.repository.save_complaint(complaint)
        return complaint

    async def resolve_complaint(
        self, complaint_id: UUID, resolution: str, resolution_amount: Optional[Decimal],
        root_cause: str, systemic_issue: bool = False
    ) -> Optional[ConsumerComplaint]:
        complaint = await self.repository.find_complaint_by_id(complaint_id)
        if complaint:
            complaint.resolution = resolution
            complaint.resolution_amount = resolution_amount
            complaint.resolution_date = datetime.utcnow()
            complaint.root_cause = root_cause
            complaint.systemic_issue = systemic_issue
            complaint.status = ComplaintStatus.RESOLVED
        return complaint

    async def perform_fair_lending_analysis(
        self, analysis_type: str, product_type: str, period_start: date, period_end: date,
        protected_class: FairLendingProtectedClass, total_applications: int,
        approved_count: int, denied_count: int, control_group_approval_rate: Decimal,
        protected_group_approval_rate: Decimal, analyst: str
    ) -> FairLendingAnalysis:
        rate_disparity = control_group_approval_rate - protected_group_approval_rate
        statistical_significance = abs(rate_disparity) > Decimal("5")

        analysis = FairLendingAnalysis(
            analysis_date=date.today(), analysis_type=analysis_type, product_type=product_type,
            analysis_period_start=period_start, analysis_period_end=period_end,
            total_applications=total_applications, approved_count=approved_count, denied_count=denied_count,
            withdrawn_count=total_applications - approved_count - denied_count,
            protected_class=protected_class, control_group_approval_rate=control_group_approval_rate,
            protected_group_approval_rate=protected_group_approval_rate, rate_disparity=rate_disparity,
            statistical_significance=statistical_significance, analyst=analyst
        )
        await self.repository.save_fair_lending(analysis)
        return analysis

    async def create_tila_disclosure(
        self, loan_id: str, customer_id: str, disclosure_type: str, product_type: str,
        loan_amount: Decimal, apr: Decimal, finance_charge: Decimal, amount_financed: Decimal,
        total_of_payments: Decimal, payment_amount: Decimal, payment_frequency: str,
        number_of_payments: int, delivery_method: str
    ) -> TILADisclosure:
        disclosure = TILADisclosure(
            loan_id=loan_id, customer_id=customer_id, disclosure_type=disclosure_type,
            disclosure_date=date.today(), product_type=product_type, loan_amount=loan_amount,
            apr=apr, finance_charge=finance_charge, amount_financed=amount_financed,
            total_of_payments=total_of_payments, payment_amount=payment_amount,
            payment_frequency=payment_frequency, number_of_payments=number_of_payments,
            delivered_date=date.today(), delivery_method=delivery_method
        )
        await self.repository.save_tila(disclosure)
        return disclosure

    async def create_respa_disclosure(
        self, loan_id: str, disclosure_type: str, loan_amount: Decimal, interest_rate: Decimal,
        monthly_principal_interest: Decimal, closing_costs: Decimal, cash_to_close: Decimal,
        origination_charges: Decimal, delivery_method: str
    ) -> RESPADisclosure:
        disclosure = RESPADisclosure(
            loan_id=loan_id, disclosure_type=disclosure_type, disclosure_date=date.today(),
            loan_amount=loan_amount, interest_rate=interest_rate,
            monthly_principal_interest=monthly_principal_interest, closing_costs=closing_costs,
            cash_to_close=cash_to_close, origination_charges=origination_charges,
            services_you_cannot_shop=Decimal("0"), services_you_can_shop=Decimal("0"),
            taxes_and_insurance=Decimal("0"), other_costs=Decimal("0"), lender_credits=Decimal("0"),
            deposit=Decimal("0"), seller_credits=Decimal("0"),
            delivered_date=date.today(), delivery_method=delivery_method
        )
        await self.repository.save_respa(disclosure)
        return disclosure

    async def perform_udap_review(
        self, product_service: str, review_type: str, reviewer: str,
        unfair_assessment: str, deceptive_assessment: str, abusive_assessment: str,
        issues_identified: List[Dict[str, Any]], recommendations: List[str]
    ) -> UDAPReview:
        risk_rating = "high" if issues_identified else "low"

        review = UDAPReview(
            review_date=date.today(), product_service=product_service, review_type=review_type,
            reviewer=reviewer, unfair_assessment=unfair_assessment, deceptive_assessment=deceptive_assessment,
            abusive_assessment=abusive_assessment, issues_identified=issues_identified,
            risk_rating=risk_rating, recommendations=recommendations,
            remediation_required=len(issues_identified) > 0
        )
        await self.repository.save_udap(review)
        return review

    async def register_servicemember(
        self, customer_id: str, account_id: str, military_status: str,
        verification_method: str, protections_applied: List[str],
        interest_rate_reduction: Optional[Decimal] = None
    ) -> ServicememberProtection:
        protection = ServicememberProtection(
            customer_id=customer_id, account_id=account_id, military_status=military_status,
            verification_date=date.today(), verification_method=verification_method,
            scra_benefits_applied="scra" in [p.lower() for p in protections_applied],
            mla_benefits_applied="mla" in [p.lower() for p in protections_applied],
            interest_rate_reduction=interest_rate_reduction,
            effective_date=date.today() if interest_rate_reduction else None,
            protections_applied=protections_applied
        )
        await self.repository.save_servicemember(protection)
        return protection

    async def generate_report(self, reporting_period: str, generated_by: str) -> ConsumerProtectionReport:
        complaints = await self.repository.find_all_complaints()
        fair_lending = await self.repository.find_all_fair_lending()
        udap = await self.repository.find_all_udap()
        servicemember = await self.repository.find_all_servicemember()

        by_category = {}
        by_status = {}
        for c in complaints:
            by_category[c.category.value] = by_category.get(c.category.value, 0) + 1
            by_status[c.status.value] = by_status.get(c.status.value, 0) + 1

        resolved = [c for c in complaints if c.resolution_date]
        avg_days = sum((c.resolution_date - c.received_date).days for c in resolved) / len(resolved) if resolved else 0

        report = ConsumerProtectionReport(
            report_date=date.today(), reporting_period=reporting_period, total_complaints=len(complaints),
            complaints_by_category=by_category, complaints_by_status=by_status,
            average_resolution_days=avg_days,
            sla_compliance_rate=Decimal("95"), regulatory_complaints=len([c for c in complaints if c.regulatory_complaint]),
            escalated_complaints=len([c for c in complaints if c.status == ComplaintStatus.ESCALATED]),
            customer_satisfaction_avg=4.2, fair_lending_reviews=len(fair_lending),
            fair_lending_findings=len([f for f in fair_lending if f.statistical_significance]),
            disclosure_reviews=0, disclosure_compliance_rate=Decimal("98"),
            udap_reviews=len(udap), udap_issues_found=len([u for u in udap if u.remediation_required]),
            servicemember_accounts=len(servicemember), training_completion_rate=Decimal("95"),
            generated_by=generated_by
        )
        await self.repository.save_report(report)
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


consumer_protection_service = ConsumerProtectionService()
