"""
Customer Risk Repository

Data access layer for customer risk profiles and assessments.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID

from ..models.customer_risk_models import (
    CustomerRiskProfile, CustomerRiskAssessment, CustomerRiskLevel,
    RiskOverrideRequest
)


class CustomerRiskRepository:
    """Repository for customer risk data access"""

    def __init__(self):
        self._profiles: Dict[str, CustomerRiskProfile] = {}
        self._assessments: Dict[UUID, CustomerRiskAssessment] = {}
        self._overrides: Dict[UUID, RiskOverrideRequest] = {}

    async def create_profile(self, profile: CustomerRiskProfile) -> CustomerRiskProfile:
        """Create a new risk profile"""
        self._profiles[profile.customer_id] = profile
        return profile

    async def get_profile(self, customer_id: str) -> Optional[CustomerRiskProfile]:
        """Get risk profile by customer ID"""
        return self._profiles.get(customer_id)

    async def update_profile(self, profile: CustomerRiskProfile) -> CustomerRiskProfile:
        """Update an existing profile"""
        self._profiles[profile.customer_id] = profile
        return profile

    async def delete_profile(self, customer_id: str) -> bool:
        """Delete a risk profile"""
        if customer_id in self._profiles:
            del self._profiles[customer_id]
            return True
        return False

    async def find_by_risk_level(self, levels: List[CustomerRiskLevel]) -> List[CustomerRiskProfile]:
        """Find profiles by risk level"""
        return [p for p in self._profiles.values() if p.current_risk_level in levels]

    async def find_high_risk(self) -> List[CustomerRiskProfile]:
        """Find high and very high risk profiles"""
        return await self.find_by_risk_level([
            CustomerRiskLevel.HIGH, CustomerRiskLevel.VERY_HIGH
        ])

    async def find_requiring_review(self) -> List[CustomerRiskProfile]:
        """Find profiles requiring review"""
        today = date.today()
        return [
            p for p in self._profiles.values()
            if p.next_review_date and p.next_review_date <= today
        ]

    async def find_requiring_edd(self) -> List[CustomerRiskProfile]:
        """Find profiles requiring EDD"""
        return [p for p in self._profiles.values() if p.requires_edd]

    async def find_peps(self) -> List[CustomerRiskProfile]:
        """Find PEP profiles"""
        from ..models.customer_risk_models import PEPStatus
        return [
            p for p in self._profiles.values()
            if p.pep_status != PEPStatus.NOT_PEP
        ]

    async def find_sanctions_matches(self) -> List[CustomerRiskProfile]:
        """Find profiles with sanctions matches"""
        return [p for p in self._profiles.values() if p.sanctions_match]

    async def create_assessment(self, assessment: CustomerRiskAssessment) -> CustomerRiskAssessment:
        """Create a new risk assessment"""
        self._assessments[assessment.assessment_id] = assessment
        return assessment

    async def get_assessment(self, assessment_id: UUID) -> Optional[CustomerRiskAssessment]:
        """Get assessment by ID"""
        return self._assessments.get(assessment_id)

    async def get_assessments_for_customer(self, customer_id: str) -> List[CustomerRiskAssessment]:
        """Get all assessments for a customer"""
        return [a for a in self._assessments.values() if a.customer_id == customer_id]

    async def create_override(self, override: RiskOverrideRequest) -> RiskOverrideRequest:
        """Create a risk override request"""
        self._overrides[override.override_id] = override
        return override

    async def get_override(self, override_id: UUID) -> Optional[RiskOverrideRequest]:
        """Get override by ID"""
        return self._overrides.get(override_id)

    async def get_pending_overrides(self) -> List[RiskOverrideRequest]:
        """Get pending override requests"""
        return [o for o in self._overrides.values() if o.status == "pending"]

    async def count_by_risk_level(self) -> Dict[str, int]:
        """Count profiles by risk level"""
        counts: Dict[str, int] = {}
        for profile in self._profiles.values():
            key = profile.current_risk_level.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    async def get_all_profiles(self, limit: int = 100, offset: int = 0) -> List[CustomerRiskProfile]:
        """Get all profiles with pagination"""
        profiles = list(self._profiles.values())
        return profiles[offset:offset + limit]

    async def count_profiles(self) -> int:
        """Count total profiles"""
        return len(self._profiles)


# Global repository instance
customer_risk_repository = CustomerRiskRepository()
