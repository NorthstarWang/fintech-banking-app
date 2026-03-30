"""KYC Repository - Data access for Know Your Customer compliance"""

from datetime import date
from typing import Any
from uuid import UUID

from ..models.kyc_models import (
    AdverseMedia,
    BeneficialOwner,
    CustomerProfile,
    CustomerVerification,
    EnhancedDueDiligence,
    KYCReport,
    PEPScreening,
    PeriodicReview,
)


class KYCRepository:
    def __init__(self):
        self._profiles: dict[UUID, CustomerProfile] = {}
        self._verifications: dict[UUID, CustomerVerification] = {}
        self._edds: dict[UUID, EnhancedDueDiligence] = {}
        self._reviews: dict[UUID, PeriodicReview] = {}
        self._beneficial_owners: dict[UUID, BeneficialOwner] = {}
        self._pep_screenings: dict[UUID, PEPScreening] = {}
        self._adverse_media: dict[UUID, AdverseMedia] = {}
        self._reports: dict[UUID, KYCReport] = {}

    async def save_profile(self, profile: CustomerProfile) -> None:
        self._profiles[profile.profile_id] = profile

    async def find_profile_by_id(self, profile_id: UUID) -> CustomerProfile | None:
        return self._profiles.get(profile_id)

    async def find_profile_by_customer_id(self, customer_id: str) -> CustomerProfile | None:
        for p in self._profiles.values():
            if p.customer_id == customer_id:
                return p
        return None

    async def find_all_profiles(self) -> list[CustomerProfile]:
        return list(self._profiles.values())

    async def find_profiles_by_risk_rating(self, risk_rating: str) -> list[CustomerProfile]:
        return [p for p in self._profiles.values() if p.risk_rating == risk_rating]

    async def find_profiles_due_for_review(self, before_date: date) -> list[CustomerProfile]:
        return [p for p in self._profiles.values() if p.next_review_date and p.next_review_date <= before_date]

    async def save_verification(self, verification: CustomerVerification) -> None:
        self._verifications[verification.verification_id] = verification

    async def find_verification_by_id(self, verification_id: UUID) -> CustomerVerification | None:
        return self._verifications.get(verification_id)

    async def find_all_verifications(self) -> list[CustomerVerification]:
        return list(self._verifications.values())

    async def find_verifications_by_customer(self, customer_id: str) -> list[CustomerVerification]:
        return [v for v in self._verifications.values() if v.customer_id == customer_id]

    async def find_pending_verifications(self) -> list[CustomerVerification]:
        return [v for v in self._verifications.values() if v.verification_status == "pending"]

    async def save_edd(self, edd: EnhancedDueDiligence) -> None:
        self._edds[edd.edd_id] = edd

    async def find_edd_by_id(self, edd_id: UUID) -> EnhancedDueDiligence | None:
        return self._edds.get(edd_id)

    async def find_all_edds(self) -> list[EnhancedDueDiligence]:
        return list(self._edds.values())

    async def find_edds_by_customer(self, customer_id: str) -> list[EnhancedDueDiligence]:
        return [e for e in self._edds.values() if e.customer_id == customer_id]

    async def find_pending_edd_approvals(self) -> list[EnhancedDueDiligence]:
        return [e for e in self._edds.values() if e.approval_status == "pending"]

    async def save_review(self, review: PeriodicReview) -> None:
        self._reviews[review.review_id] = review

    async def find_review_by_id(self, review_id: UUID) -> PeriodicReview | None:
        return self._reviews.get(review_id)

    async def find_all_reviews(self) -> list[PeriodicReview]:
        return list(self._reviews.values())

    async def find_reviews_by_customer(self, customer_id: str) -> list[PeriodicReview]:
        return [r for r in self._reviews.values() if r.customer_id == customer_id]

    async def find_overdue_reviews(self) -> list[PeriodicReview]:
        return [r for r in self._reviews.values() if r.review_status == "overdue"]

    async def save_beneficial_owner(self, owner: BeneficialOwner) -> None:
        self._beneficial_owners[owner.owner_id] = owner

    async def find_beneficial_owner_by_id(self, owner_id: UUID) -> BeneficialOwner | None:
        return self._beneficial_owners.get(owner_id)

    async def find_all_beneficial_owners(self) -> list[BeneficialOwner]:
        return list(self._beneficial_owners.values())

    async def find_beneficial_owners_by_customer(self, customer_id: str) -> list[BeneficialOwner]:
        return [o for o in self._beneficial_owners.values() if o.customer_id == customer_id]

    async def save_pep_screening(self, screening: PEPScreening) -> None:
        self._pep_screenings[screening.screening_id] = screening

    async def find_pep_screening_by_id(self, screening_id: UUID) -> PEPScreening | None:
        return self._pep_screenings.get(screening_id)

    async def find_all_pep_screenings(self) -> list[PEPScreening]:
        return list(self._pep_screenings.values())

    async def find_pep_matches(self) -> list[PEPScreening]:
        return [s for s in self._pep_screenings.values() if s.pep_match]

    async def save_adverse_media(self, media: AdverseMedia) -> None:
        self._adverse_media[media.media_id] = media

    async def find_adverse_media_by_id(self, media_id: UUID) -> AdverseMedia | None:
        return self._adverse_media.get(media_id)

    async def find_all_adverse_media(self) -> list[AdverseMedia]:
        return list(self._adverse_media.values())

    async def find_adverse_media_by_customer(self, customer_id: str) -> list[AdverseMedia]:
        return [m for m in self._adverse_media.values() if m.customer_id == customer_id]

    async def save_report(self, report: KYCReport) -> None:
        self._reports[report.report_id] = report

    async def find_report_by_id(self, report_id: UUID) -> KYCReport | None:
        return self._reports.get(report_id)

    async def find_all_reports(self) -> list[KYCReport]:
        return list(self._reports.values())

    async def get_statistics(self) -> dict[str, Any]:
        return {
            "total_profiles": len(self._profiles),
            "high_risk_profiles": len([p for p in self._profiles.values() if p.risk_rating == "high"]),
            "total_verifications": len(self._verifications),
            "pending_verifications": len([v for v in self._verifications.values() if v.verification_status == "pending"]),
            "total_edds": len(self._edds),
            "total_reviews": len(self._reviews),
            "overdue_reviews": len([r for r in self._reviews.values() if r.review_status == "overdue"]),
            "total_beneficial_owners": len(self._beneficial_owners),
            "pep_matches": len([s for s in self._pep_screenings.values() if s.pep_match]),
            "total_reports": len(self._reports),
        }


kyc_repository = KYCRepository()
