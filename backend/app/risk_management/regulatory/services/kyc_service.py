"""KYC Service - Business logic for Know Your Customer compliance"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID
from decimal import Decimal
from ..models.kyc_models import (
    CustomerProfile, CorporateCustomer, IdentityVerification, EnhancedDueDiligence,
    PeriodicReview, BeneficialOwner, KYCReport, CustomerType, RiskRating,
    VerificationStatus, DocumentType
)
from ..repositories.kyc_repository import kyc_repository


class KYCService:
    def __init__(self):
        self.repository = kyc_repository

    def _calculate_risk_score(self, profile: CustomerProfile) -> int:
        score = 50
        if profile.pep_status: score += 30
        if profile.sanctions_status: score += 50
        if profile.adverse_media: score += 20
        high_risk_countries = ["AF", "KP", "IR", "SY"]
        if profile.country_of_residence in high_risk_countries: score += 25
        if profile.expected_monthly_volume > Decimal("100000"): score += 15
        return min(score, 100)

    def _determine_rating(self, score: int) -> RiskRating:
        if score >= 80: return RiskRating.HIGH
        if score >= 50: return RiskRating.MEDIUM
        return RiskRating.LOW

    async def create_customer_profile(
        self, customer_id: str, customer_type: CustomerType, full_name: str,
        country_of_residence: str, address: str, source_of_funds: str,
        expected_activity: str, expected_monthly_volume: Decimal, **kwargs
    ) -> CustomerProfile:
        profile = CustomerProfile(
            customer_id=customer_id, customer_type=customer_type, full_name=full_name,
            country_of_residence=country_of_residence, address=address, source_of_funds=source_of_funds,
            expected_activity=expected_activity, expected_monthly_volume=expected_monthly_volume,
            onboarding_date=date.today(), **kwargs
        )
        profile.risk_score = self._calculate_risk_score(profile)
        profile.risk_rating = self._determine_rating(profile.risk_score)

        review_months = 12 if profile.risk_rating == RiskRating.LOW else 6 if profile.risk_rating == RiskRating.MEDIUM else 3
        profile.next_review_date = date.today() + timedelta(days=review_months * 30)

        await self.repository.save_profile(profile)
        return profile

    async def get_profile(self, profile_id: UUID) -> Optional[CustomerProfile]:
        return await self.repository.find_profile_by_id(profile_id)

    async def verify_identity(
        self, profile_id: UUID, verification_type: str, document_type: DocumentType,
        document_number: str, issuing_country: str, document_location: str,
        verification_method: str = "manual", **kwargs
    ) -> IdentityVerification:
        verification = IdentityVerification(
            profile_id=profile_id, verification_type=verification_type, document_type=document_type,
            document_number=document_number, issuing_country=issuing_country,
            verification_method=verification_method, document_location=document_location, **kwargs
        )
        await self.repository.save_verification(verification)
        return verification

    async def complete_verification(
        self, verification_id: UUID, verified_by: str, passed: bool, failure_reason: Optional[str] = None
    ) -> Optional[IdentityVerification]:
        verification = await self.repository.find_verification_by_id(verification_id)
        if verification:
            verification.status = VerificationStatus.VERIFIED if passed else VerificationStatus.FAILED
            verification.verification_date = datetime.utcnow()
            verification.verified_by = verified_by
            verification.failure_reason = failure_reason
        return verification

    async def perform_edd(
        self, profile_id: UUID, trigger_reason: str, conducted_by: str,
        business_relationship_purpose: str, expected_transactions: str,
        geographical_exposure: List[str], next_review_date: date
    ) -> EnhancedDueDiligence:
        edd = EnhancedDueDiligence(
            profile_id=profile_id, trigger_reason=trigger_reason, edd_date=date.today(),
            conducted_by=conducted_by, business_relationship_purpose=business_relationship_purpose,
            expected_transactions=expected_transactions, geographical_exposure=geographical_exposure,
            next_review_date=next_review_date
        )
        await self.repository.save_edd(edd)
        return edd

    async def perform_periodic_review(
        self, profile_id: UUID, review_type: str, reviewer: str
    ) -> PeriodicReview:
        profile = await self.repository.find_profile_by_id(profile_id)
        if not profile:
            raise ValueError("Profile not found")

        previous_rating = profile.risk_rating
        new_score = self._calculate_risk_score(profile)
        new_rating = self._determine_rating(new_score)

        review_months = 12 if new_rating == RiskRating.LOW else 6 if new_rating == RiskRating.MEDIUM else 3

        review = PeriodicReview(
            profile_id=profile_id, review_type=review_type, review_date=date.today(), reviewer=reviewer,
            previous_risk_rating=previous_rating, new_risk_rating=new_rating,
            risk_score_change=new_score - profile.risk_score, changes_identified=[], documents_updated=[],
            screening_results={}, transaction_review={}, recommendations=[],
            action_items=[], next_review_date=date.today() + timedelta(days=review_months * 30)
        )

        profile.risk_score = new_score
        profile.risk_rating = new_rating
        profile.last_review_date = date.today()
        profile.next_review_date = review.next_review_date

        await self.repository.save_review(review)
        return review

    async def add_beneficial_owner(
        self, profile_id: UUID, full_name: str, date_of_birth: date, nationality: str,
        country_of_residence: str, ownership_percentage: Decimal, ownership_type: str
    ) -> BeneficialOwner:
        owner = BeneficialOwner(
            profile_id=profile_id, full_name=full_name, date_of_birth=date_of_birth,
            nationality=nationality, country_of_residence=country_of_residence,
            ownership_percentage=ownership_percentage, ownership_type=ownership_type
        )
        await self.repository.save_beneficial_owner(owner)
        return owner

    async def generate_report(self, reporting_period: str, generated_by: str) -> KYCReport:
        profiles = await self.repository.find_all_profiles()
        report = KYCReport(
            report_date=date.today(), reporting_period=reporting_period,
            total_customers=len(profiles), new_customers=0,
            high_risk_customers=len([p for p in profiles if p.risk_rating == RiskRating.HIGH]),
            medium_risk_customers=len([p for p in profiles if p.risk_rating == RiskRating.MEDIUM]),
            low_risk_customers=len([p for p in profiles if p.risk_rating == RiskRating.LOW]),
            pep_customers=len([p for p in profiles if p.pep_status]),
            verifications_completed=0, verifications_failed=0, edd_conducted=0,
            periodic_reviews_completed=0, periodic_reviews_overdue=0, sars_filed=0,
            accounts_closed=0, average_onboarding_time=0, compliance_score=90.0, generated_by=generated_by
        )
        await self.repository.save_report(report)
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


kyc_service = KYCService()
