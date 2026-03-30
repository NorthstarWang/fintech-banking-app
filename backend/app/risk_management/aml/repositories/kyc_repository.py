"""
KYC Repository

Data access layer for KYC profiles and documents.
"""

from datetime import UTC, date, datetime
from uuid import UUID

from ..models.kyc_models import EDDRequest, KYCLevel, KYCProfile, KYCStatus, OnboardingWorkflow


class KYCRepository:
    """Repository for KYC data access"""

    def __init__(self):
        self._profiles: dict[UUID, KYCProfile] = {}
        self._edd_requests: dict[UUID, EDDRequest] = {}
        self._workflows: dict[UUID, OnboardingWorkflow] = {}

    async def create_profile(self, profile: KYCProfile) -> KYCProfile:
        """Create a new KYC profile"""
        self._profiles[profile.profile_id] = profile
        return profile

    async def get_profile(self, profile_id: UUID) -> KYCProfile | None:
        """Get profile by ID"""
        return self._profiles.get(profile_id)

    async def get_profile_by_customer(self, customer_id: str) -> KYCProfile | None:
        """Get profile by customer ID"""
        for profile in self._profiles.values():
            if profile.customer_id == customer_id:
                return profile
        return None

    async def update_profile(self, profile: KYCProfile) -> KYCProfile:
        """Update an existing profile"""
        self._profiles[profile.profile_id] = profile
        return profile

    async def delete_profile(self, profile_id: UUID) -> bool:
        """Delete a profile"""
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            return True
        return False

    async def find_by_status(self, statuses: list[KYCStatus]) -> list[KYCProfile]:
        """Find profiles by status"""
        return [p for p in self._profiles.values() if p.kyc_status in statuses]

    async def find_by_level(self, levels: list[KYCLevel]) -> list[KYCProfile]:
        """Find profiles by KYC level"""
        return [p for p in self._profiles.values() if p.kyc_level in levels]

    async def find_pending_review(self) -> list[KYCProfile]:
        """Find profiles pending review"""
        return await self.find_by_status([KYCStatus.PENDING_REVIEW])

    async def find_expired(self) -> list[KYCProfile]:
        """Find expired profiles"""
        now = datetime.now(UTC)
        return [
            p for p in self._profiles.values()
            if p.expires_at and p.expires_at < now
        ]

    async def find_requiring_review(self) -> list[KYCProfile]:
        """Find profiles requiring periodic review"""
        today = date.today()
        return [
            p for p in self._profiles.values()
            if p.next_review_date and p.next_review_date <= today
        ]

    async def find_requiring_edd(self) -> list[KYCProfile]:
        """Find profiles requiring EDD"""
        return [
            p for p in self._profiles.values()
            if p.requires_edd and not p.edd_completed
        ]

    async def find_peps(self) -> list[KYCProfile]:
        """Find PEP profiles"""
        return [p for p in self._profiles.values() if p.is_pep]

    async def create_edd_request(self, edd: EDDRequest) -> EDDRequest:
        """Create EDD request"""
        self._edd_requests[edd.edd_id] = edd
        return edd

    async def get_edd_request(self, edd_id: UUID) -> EDDRequest | None:
        """Get EDD request by ID"""
        return self._edd_requests.get(edd_id)

    async def find_open_edd_requests(self) -> list[EDDRequest]:
        """Find open EDD requests"""
        return [e for e in self._edd_requests.values() if e.status == "open"]

    async def create_workflow(self, workflow: OnboardingWorkflow) -> OnboardingWorkflow:
        """Create onboarding workflow"""
        self._workflows[workflow.workflow_id] = workflow
        return workflow

    async def get_workflow(self, workflow_id: UUID) -> OnboardingWorkflow | None:
        """Get workflow by ID"""
        return self._workflows.get(workflow_id)

    async def find_active_workflows(self) -> list[OnboardingWorkflow]:
        """Find active onboarding workflows"""
        return [w for w in self._workflows.values() if w.status == "initiated"]

    async def count_by_status(self) -> dict[str, int]:
        """Count profiles by status"""
        counts: dict[str, int] = {}
        for profile in self._profiles.values():
            key = profile.kyc_status.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    async def get_all_profiles(self, limit: int = 100, offset: int = 0) -> list[KYCProfile]:
        """Get all profiles with pagination"""
        profiles = list(self._profiles.values())
        return profiles[offset:offset + limit]

    async def count_profiles(self) -> int:
        """Count total profiles"""
        return len(self._profiles)


# Global repository instance
kyc_repository = KYCRepository()
