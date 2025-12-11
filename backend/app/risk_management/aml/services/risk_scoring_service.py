"""
Risk Scoring Service

Handles customer and transaction risk scoring calculations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from ..models.customer_risk_models import (
    CustomerRiskLevel, CustomerType, PEPStatus, RiskFactorCategory,
    GeographicRisk, RiskFactor, BehaviorProfile, CustomerRiskAssessment,
    CustomerRiskProfile, RiskScoreCalculation, RiskOverrideRequest
)


class RiskScoringService:
    """Service for calculating and managing risk scores"""

    def __init__(self):
        self._risk_profiles: Dict[str, CustomerRiskProfile] = {}
        self._assessments: Dict[UUID, CustomerRiskAssessment] = {}
        self._override_requests: Dict[UUID, RiskOverrideRequest] = {}
        self._country_risks: Dict[str, GeographicRisk] = {}
        self._initialize_country_risks()

    def _initialize_country_risks(self):
        """Initialize country risk data"""
        # High-risk jurisdictions
        high_risk = [
            ("AF", "Afghanistan", 95.0, True, True),
            ("IR", "Iran", 90.0, True, True),
            ("KP", "North Korea", 100.0, True, True),
            ("SY", "Syria", 90.0, True, True),
            ("YE", "Yemen", 85.0, False, True),
            ("MM", "Myanmar", 80.0, False, True),
        ]

        # Medium-risk jurisdictions
        medium_risk = [
            ("PA", "Panama", 65.0, False, True),
            ("AE", "United Arab Emirates", 50.0, False, False),
            ("CN", "China", 45.0, False, False),
            ("RU", "Russia", 70.0, True, True),
        ]

        # Low-risk jurisdictions
        low_risk = [
            ("US", "United States", 20.0, False, False),
            ("GB", "United Kingdom", 15.0, False, False),
            ("DE", "Germany", 10.0, False, False),
            ("JP", "Japan", 10.0, False, False),
            ("CA", "Canada", 15.0, False, False),
        ]

        for code, name, score, sanctioned, high_risk_flag in high_risk + medium_risk + low_risk:
            self._country_risks[code] = GeographicRisk(
                country_code=code,
                country_name=name,
                risk_level="high" if score >= 70 else "medium" if score >= 40 else "low",
                risk_score=score,
                is_sanctioned=sanctioned,
                is_high_risk_jurisdiction=high_risk_flag
            )

    async def create_risk_profile(
        self, customer_id: str, customer_type: CustomerType, customer_name: str, **kwargs
    ) -> CustomerRiskProfile:
        """Create a new customer risk profile"""
        profile = CustomerRiskProfile(
            customer_id=customer_id,
            customer_type=customer_type,
            customer_name=customer_name,
            customer_since=kwargs.get("customer_since", datetime.utcnow()),
            current_risk_level=CustomerRiskLevel.MEDIUM,
            current_risk_score=50.0,
            last_assessment_date=datetime.utcnow(),
            next_review_date=datetime.utcnow().date(),
            country_of_residence=kwargs.get("country_of_residence", "US"),
            **{k: v for k, v in kwargs.items() if k not in ["customer_since", "country_of_residence"]}
        )

        self._risk_profiles[customer_id] = profile
        return profile

    async def get_risk_profile(self, customer_id: str) -> Optional[CustomerRiskProfile]:
        """Get customer risk profile"""
        return self._risk_profiles.get(customer_id)

    async def assess_customer_risk(
        self, customer_id: str, assessment_type: str = "periodic"
    ) -> CustomerRiskAssessment:
        """Perform customer risk assessment"""
        profile = self._risk_profiles.get(customer_id)
        if not profile:
            raise ValueError(f"Risk profile not found for customer {customer_id}")

        assessment = CustomerRiskAssessment(
            customer_id=customer_id,
            assessment_type=assessment_type
        )

        # Calculate component scores
        assessment.geography_risk_score = await self._calculate_geography_risk(profile)
        assessment.product_risk_score = await self._calculate_product_risk(profile)
        assessment.channel_risk_score = await self._calculate_channel_risk(profile)
        assessment.customer_risk_score = await self._calculate_customer_inherent_risk(profile)
        assessment.transaction_risk_score = await self._calculate_transaction_risk(profile)
        assessment.industry_risk_score = await self._calculate_industry_risk(profile)

        # Calculate inherent risk score
        weights = {
            "geography": 0.25,
            "product": 0.15,
            "channel": 0.10,
            "customer": 0.20,
            "transaction": 0.20,
            "industry": 0.10
        }

        assessment.inherent_risk_score = (
            assessment.geography_risk_score * weights["geography"] +
            assessment.product_risk_score * weights["product"] +
            assessment.channel_risk_score * weights["channel"] +
            assessment.customer_risk_score * weights["customer"] +
            assessment.transaction_risk_score * weights["transaction"] +
            assessment.industry_risk_score * weights["industry"]
        )

        # Apply control effectiveness (simplified)
        assessment.control_effectiveness_score = 70.0  # Assume 70% control effectiveness
        assessment.residual_risk_score = assessment.inherent_risk_score * (1 - assessment.control_effectiveness_score / 100)

        # Overall risk score
        assessment.overall_risk_score = assessment.inherent_risk_score

        # Add risk factors
        assessment.risk_factors = await self._identify_risk_factors(profile)

        # Set special statuses
        assessment.pep_status = profile.pep_status
        assessment.sanctions_status = profile.sanctions_match
        assessment.adverse_media_flag = profile.adverse_media

        # Determine risk level
        assessment.risk_level = self._score_to_level(assessment.overall_risk_score)

        # Set review schedule
        assessment.review_frequency_months = self._get_review_frequency(assessment.risk_level)
        assessment.next_review_date = datetime.utcnow().date()

        # Store assessment
        self._assessments[assessment.assessment_id] = assessment

        # Update profile
        profile.current_risk_score = assessment.overall_risk_score
        profile.current_risk_level = assessment.risk_level
        profile.last_assessment_date = datetime.utcnow()
        profile.risk_assessment_history.append(assessment)

        return assessment

    async def _calculate_geography_risk(self, profile: CustomerRiskProfile) -> float:
        """Calculate geographic risk score"""
        score = 0.0

        # Country of residence
        country = profile.country_of_residence
        if country in self._country_risks:
            score = self._country_risks[country].risk_score
        else:
            score = 30.0  # Default for unknown countries

        # Countries of operation
        for op_country in profile.countries_of_operation:
            if op_country in self._country_risks:
                country_score = self._country_risks[op_country].risk_score
                score = max(score, country_score * 0.8)

        return min(score, 100.0)

    async def _calculate_product_risk(self, profile: CustomerRiskProfile) -> float:
        """Calculate product risk score"""
        # Simplified product risk scoring
        high_risk_products = ["wire_transfer", "correspondent_banking", "trade_finance"]
        medium_risk_products = ["investment", "foreign_exchange", "credit_card"]

        score = 20.0
        if profile.behavior_profile:
            for product in profile.behavior_profile.product_types_used:
                if product in high_risk_products:
                    score = max(score, 70.0)
                elif product in medium_risk_products:
                    score = max(score, 45.0)

        return score

    async def _calculate_channel_risk(self, profile: CustomerRiskProfile) -> float:
        """Calculate channel risk score"""
        high_risk_channels = ["non_face_to_face", "third_party", "agent"]
        medium_risk_channels = ["online", "mobile"]

        score = 20.0
        if profile.behavior_profile:
            for channel in profile.behavior_profile.primary_channels:
                if channel in high_risk_channels:
                    score = max(score, 65.0)
                elif channel in medium_risk_channels:
                    score = max(score, 40.0)

        return score

    async def _calculate_customer_inherent_risk(self, profile: CustomerRiskProfile) -> float:
        """Calculate customer inherent risk score"""
        score = 20.0

        # PEP status
        if profile.pep_status == PEPStatus.PEP:
            score += 40.0
        elif profile.pep_status in [PEPStatus.PEP_FAMILY, PEPStatus.PEP_ASSOCIATE]:
            score += 25.0

        # Sanctions
        if profile.sanctions_match:
            score += 50.0

        # Adverse media
        if profile.adverse_media:
            score += 20.0

        # Customer type
        high_risk_types = [CustomerType.TRUST, CustomerType.FINANCIAL_INSTITUTION]
        if profile.customer_type in high_risk_types:
            score += 15.0

        return min(score, 100.0)

    async def _calculate_transaction_risk(self, profile: CustomerRiskProfile) -> float:
        """Calculate transaction behavior risk score"""
        score = 20.0

        if profile.behavior_profile:
            bp = profile.behavior_profile

            # High velocity
            if bp.velocity_score > 70:
                score += 20.0

            # Low consistency (erratic behavior)
            if bp.consistency_score < 30:
                score += 15.0

            # High-risk country exposure
            if bp.high_risk_country_exposure > 0.2:
                score += 25.0

        # Active alerts and cases
        if profile.open_alerts_count > 0:
            score += profile.open_alerts_count * 5

        if profile.open_cases_count > 0:
            score += profile.open_cases_count * 10

        # Previous SARs
        if profile.total_sars_filed > 0:
            score += profile.total_sars_filed * 15

        return min(score, 100.0)

    async def _calculate_industry_risk(self, profile: CustomerRiskProfile) -> float:
        """Calculate industry risk score"""
        # High-risk industries
        high_risk_industries = [
            "casino", "gambling", "money_service_business", "crypto",
            "precious_metals", "arms_dealer", "adult_entertainment"
        ]
        medium_risk_industries = [
            "real_estate", "legal_services", "accounting", "art_dealer"
        ]

        # This would normally come from the customer profile
        customer_industry = profile.metadata.get("industry", "")

        if customer_industry in high_risk_industries:
            return 80.0
        elif customer_industry in medium_risk_industries:
            return 50.0
        return 25.0

    async def _identify_risk_factors(self, profile: CustomerRiskProfile) -> List[RiskFactor]:
        """Identify active risk factors for a customer"""
        factors = []

        # PEP factor
        if profile.pep_status != PEPStatus.NOT_PEP:
            factors.append(RiskFactor(
                category=RiskFactorCategory.CUSTOMER,
                factor_code="PEP_STATUS",
                factor_name="Politically Exposed Person",
                description=f"Customer has PEP status: {profile.pep_status.value}",
                weight=2.0,
                score=40.0
            ))

        # Sanctions factor
        if profile.sanctions_match:
            factors.append(RiskFactor(
                category=RiskFactorCategory.CUSTOMER,
                factor_code="SANCTIONS_MATCH",
                factor_name="Sanctions List Match",
                description="Customer matches a sanctions list entry",
                weight=3.0,
                score=50.0
            ))

        # High-risk country
        if profile.country_of_residence in self._country_risks:
            country_risk = self._country_risks[profile.country_of_residence]
            if country_risk.is_high_risk_jurisdiction:
                factors.append(RiskFactor(
                    category=RiskFactorCategory.GEOGRAPHY,
                    factor_code="HIGH_RISK_COUNTRY",
                    factor_name="High-Risk Country",
                    description=f"Customer resides in high-risk jurisdiction: {country_risk.country_name}",
                    weight=1.5,
                    score=country_risk.risk_score
                ))

        # Previous SARs
        if profile.total_sars_filed > 0:
            factors.append(RiskFactor(
                category=RiskFactorCategory.TRANSACTION,
                factor_code="PRIOR_SAR",
                factor_name="Prior SAR Filing",
                description=f"{profile.total_sars_filed} previous SAR(s) filed",
                weight=2.0,
                score=30.0 * profile.total_sars_filed
            ))

        return factors

    def _score_to_level(self, score: float) -> CustomerRiskLevel:
        """Convert risk score to risk level"""
        if score >= 80:
            return CustomerRiskLevel.VERY_HIGH
        elif score >= 60:
            return CustomerRiskLevel.HIGH
        elif score >= 40:
            return CustomerRiskLevel.MEDIUM
        return CustomerRiskLevel.LOW

    def _get_review_frequency(self, risk_level: CustomerRiskLevel) -> int:
        """Get review frequency in months based on risk level"""
        frequencies = {
            CustomerRiskLevel.LOW: 36,
            CustomerRiskLevel.MEDIUM: 12,
            CustomerRiskLevel.HIGH: 6,
            CustomerRiskLevel.VERY_HIGH: 3,
            CustomerRiskLevel.PROHIBITED: 0
        }
        return frequencies.get(risk_level, 12)

    async def request_risk_override(
        self, customer_id: str, requested_level: CustomerRiskLevel, reason: str, justification: str, requested_by: str
    ) -> RiskOverrideRequest:
        """Request to override customer risk level"""
        profile = self._risk_profiles.get(customer_id)
        if not profile:
            raise ValueError(f"Risk profile not found for customer {customer_id}")

        override = RiskOverrideRequest(
            customer_id=customer_id,
            current_risk_level=profile.current_risk_level,
            requested_risk_level=requested_level,
            reason=reason,
            justification=justification,
            requested_by=requested_by,
            review_deadline=datetime.utcnow()
        )

        self._override_requests[override.override_id] = override
        return override

    async def approve_override(
        self, override_id: UUID, approved_by: str, notes: str
    ) -> Optional[RiskOverrideRequest]:
        """Approve a risk override request"""
        override = self._override_requests.get(override_id)
        if not override:
            return None

        override.status = "approved"
        override.approvals.append({
            "approved_by": approved_by,
            "approved_at": datetime.utcnow().isoformat(),
            "notes": notes
        })

        # Apply override to profile
        profile = self._risk_profiles.get(override.customer_id)
        if profile:
            profile.current_risk_level = override.requested_risk_level
            profile.updated_at = datetime.utcnow()

        return override

    async def get_country_risk(self, country_code: str) -> Optional[GeographicRisk]:
        """Get risk information for a country"""
        return self._country_risks.get(country_code)

    async def get_high_risk_countries(self) -> List[GeographicRisk]:
        """Get list of high-risk countries"""
        return [
            cr for cr in self._country_risks.values()
            if cr.is_high_risk_jurisdiction
        ]


# Global service instance
risk_scoring_service = RiskScoringService()
