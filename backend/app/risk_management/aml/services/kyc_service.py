"""
KYC Service

Handles Know Your Customer operations and customer due diligence.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID, uuid4

from ..models.kyc_models import (
    KYCStatus, KYCLevel, DocumentType, VerificationMethod,
    IdentityDocument, AddressVerification, BiometricVerification,
    SourceOfFunds, SourceOfWealth, BeneficialOwner, KYCCheck,
    KYCProfile, EDDRequest, OnboardingWorkflow, KYCStatistics
)


class KYCService:
    """Service for KYC and customer due diligence operations"""

    def __init__(self):
        self._profiles: Dict[UUID, KYCProfile] = {}
        self._edd_requests: Dict[UUID, EDDRequest] = {}
        self._onboarding_workflows: Dict[UUID, OnboardingWorkflow] = {}

    async def create_profile(
        self, customer_id: str, customer_type: str, full_name: str, **kwargs
    ) -> KYCProfile:
        """Create a new KYC profile"""
        profile = KYCProfile(
            customer_id=customer_id,
            customer_type=customer_type,
            full_name=full_name,
            **kwargs
        )
        self._profiles[profile.profile_id] = profile
        return profile

    async def get_profile(self, profile_id: UUID) -> Optional[KYCProfile]:
        """Get KYC profile by ID"""
        return self._profiles.get(profile_id)

    async def get_profile_by_customer(self, customer_id: str) -> Optional[KYCProfile]:
        """Get KYC profile by customer ID"""
        for profile in self._profiles.values():
            if profile.customer_id == customer_id:
                return profile
        return None

    async def update_profile_status(
        self, profile_id: UUID, status: KYCStatus, updated_by: str
    ) -> Optional[KYCProfile]:
        """Update KYC profile status"""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        profile.kyc_status = status
        profile.updated_at = datetime.utcnow()

        if status == KYCStatus.APPROVED:
            profile.approved_by = updated_by
            profile.approved_at = datetime.utcnow()
            # Set next review date based on risk level
            review_months = self._get_review_months(profile.risk_level)
            profile.next_review_date = (datetime.utcnow() + timedelta(days=review_months * 30)).date()

        return profile

    def _get_review_months(self, risk_level: str) -> int:
        """Get review frequency in months based on risk level"""
        frequencies = {
            "low": 36,
            "medium": 12,
            "high": 6,
            "very_high": 3
        }
        return frequencies.get(risk_level, 12)

    async def add_identity_document(
        self, profile_id: UUID, document: IdentityDocument
    ) -> Optional[KYCProfile]:
        """Add identity document to profile"""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        profile.identity_documents.append(document)
        profile.updated_at = datetime.utcnow()

        # Update status if pending documents
        if profile.kyc_status == KYCStatus.PENDING_DOCUMENTS:
            profile.kyc_status = KYCStatus.IN_PROGRESS

        return profile

    async def verify_document(
        self, profile_id: UUID, document_id: UUID, verified_by: str, is_verified: bool, rejection_reason: Optional[str] = None
    ) -> Optional[IdentityDocument]:
        """Verify an identity document"""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        for doc in profile.identity_documents:
            if doc.document_id == document_id:
                doc.verification_status = "verified" if is_verified else "rejected"
                doc.verified_by = verified_by
                doc.verified_at = datetime.utcnow()
                if rejection_reason:
                    doc.rejection_reason = rejection_reason
                profile.updated_at = datetime.utcnow()
                return doc

        return None

    async def add_address_verification(
        self, profile_id: UUID, address: AddressVerification
    ) -> Optional[KYCProfile]:
        """Add address verification to profile"""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        profile.address_verifications.append(address)
        profile.updated_at = datetime.utcnow()
        return profile

    async def add_biometric_verification(
        self, profile_id: UUID, biometric: BiometricVerification
    ) -> Optional[KYCProfile]:
        """Add biometric verification to profile"""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        profile.biometric_verifications.append(biometric)
        profile.updated_at = datetime.utcnow()
        return profile

    async def add_source_of_funds(
        self, profile_id: UUID, source: SourceOfFunds
    ) -> Optional[KYCProfile]:
        """Add source of funds declaration"""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        profile.sources_of_funds.append(source)
        profile.updated_at = datetime.utcnow()
        return profile

    async def add_source_of_wealth(
        self, profile_id: UUID, source: SourceOfWealth
    ) -> Optional[KYCProfile]:
        """Add source of wealth declaration"""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        profile.sources_of_wealth.append(source)
        profile.updated_at = datetime.utcnow()
        return profile

    async def add_beneficial_owner(
        self, profile_id: UUID, owner: BeneficialOwner
    ) -> Optional[KYCProfile]:
        """Add beneficial owner (for corporate customers)"""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        profile.beneficial_owners.append(owner)
        profile.updated_at = datetime.utcnow()
        return profile

    async def run_kyc_check(
        self, profile_id: UUID, check_type: str, check_name: str, provider: Optional[str] = None
    ) -> Optional[KYCCheck]:
        """Run a KYC check"""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        check = KYCCheck(
            check_type=check_type,
            check_name=check_name,
            provider=provider,
            status="completed",
            result="pass",
            completed_at=datetime.utcnow()
        )

        # Simulate check results based on type
        if check_type == "sanctions":
            check.result = "pass" if not profile.sanctions_hit else "fail"
            check.risk_level = "high" if profile.sanctions_hit else "low"
        elif check_type == "pep":
            check.result = "review_required" if profile.is_pep else "pass"
            check.risk_level = "high" if profile.is_pep else "low"
        elif check_type == "adverse_media":
            check.result = "pass" if not profile.adverse_media_hit else "review_required"
            check.risk_level = "medium" if profile.adverse_media_hit else "low"
        elif check_type == "identity":
            verified_docs = [d for d in profile.identity_documents if d.verification_status == "verified"]
            check.result = "pass" if verified_docs else "fail"

        profile.checks.append(check)
        profile.updated_at = datetime.utcnow()
        return check

    async def calculate_risk_score(self, profile_id: UUID) -> Optional[float]:
        """Calculate customer risk score"""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        score = 0.0

        # PEP status
        if profile.is_pep:
            score += 30.0

        # Sanctions
        if profile.sanctions_hit:
            score += 50.0

        # Adverse media
        if profile.adverse_media_hit:
            score += 20.0

        # High-risk country (simplified)
        high_risk_countries = ["AF", "IR", "KP", "SY", "YE"]
        if profile.nationality in high_risk_countries:
            score += 25.0

        # Risk factors
        score += len(profile.risk_factors) * 5.0

        # Cap at 100
        score = min(score, 100.0)

        # Update profile
        profile.risk_score = score
        profile.risk_level = self._score_to_level(score)
        profile.requires_edd = score >= 70.0
        profile.updated_at = datetime.utcnow()

        return score

    def _score_to_level(self, score: float) -> str:
        """Convert risk score to risk level"""
        if score >= 80:
            return "very_high"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        return "low"

    async def request_edd(
        self, profile_id: UUID, trigger_reason: str, trigger_type: str, triggered_by: str
    ) -> Optional[EDDRequest]:
        """Request Enhanced Due Diligence"""
        profile = self._profiles.get(profile_id)
        if not profile:
            return None

        edd = EDDRequest(
            customer_id=profile.customer_id,
            kyc_profile_id=profile_id,
            trigger_reason=trigger_reason,
            trigger_type=trigger_type,
            triggered_by=triggered_by,
            due_date=datetime.utcnow() + timedelta(days=30)
        )

        # Set required documents and checks based on trigger type
        if trigger_type == "pep":
            edd.required_documents = [DocumentType.SOURCE_OF_FUNDS, DocumentType.SOURCE_OF_WEALTH]
            edd.required_checks = ["enhanced_pep_screening", "adverse_media_deep_dive"]
        elif trigger_type == "high_risk_country":
            edd.required_documents = [DocumentType.PROOF_OF_ADDRESS, DocumentType.SOURCE_OF_FUNDS]
            edd.required_checks = ["country_risk_assessment", "sanctions_enhanced"]
        elif trigger_type == "high_value":
            edd.required_documents = [DocumentType.SOURCE_OF_WEALTH, DocumentType.FINANCIAL_STATEMENT]
            edd.required_checks = ["wealth_verification"]

        self._edd_requests[edd.edd_id] = edd

        # Update profile
        profile.requires_edd = True
        profile.edd_reason = trigger_reason
        profile.updated_at = datetime.utcnow()

        return edd

    async def complete_edd(
        self, edd_id: UUID, findings: List[Dict[str, Any]], recommendation: str, completed_by: str
    ) -> Optional[EDDRequest]:
        """Complete an EDD request"""
        edd = self._edd_requests.get(edd_id)
        if not edd:
            return None

        edd.findings = findings
        edd.recommendation = recommendation
        edd.status = "completed"
        edd.completed_at = datetime.utcnow()

        # Update profile
        profile = self._profiles.get(edd.kyc_profile_id)
        if profile:
            profile.edd_completed = True
            profile.edd_completed_at = datetime.utcnow()
            profile.updated_at = datetime.utcnow()

        return edd

    async def start_onboarding(
        self, customer_id: str, customer_type: str, product_type: str
    ) -> OnboardingWorkflow:
        """Start customer onboarding workflow"""
        # Determine required KYC level based on product type
        kyc_level_map = {
            "basic_account": KYCLevel.BASIC,
            "savings_account": KYCLevel.STANDARD,
            "investment_account": KYCLevel.ENHANCED,
            "business_account": KYCLevel.ENHANCED
        }
        required_level = kyc_level_map.get(product_type, KYCLevel.STANDARD)

        # Determine required documents
        required_docs = [DocumentType.PASSPORT, DocumentType.PROOF_OF_ADDRESS]
        if required_level == KYCLevel.ENHANCED:
            required_docs.extend([DocumentType.SOURCE_OF_FUNDS])
        if customer_type == "corporate":
            required_docs.extend([
                DocumentType.COMPANY_REGISTRATION,
                DocumentType.ARTICLES_OF_INCORPORATION,
                DocumentType.SHAREHOLDER_REGISTER
            ])

        workflow = OnboardingWorkflow(
            customer_id=customer_id,
            status="initiated",
            current_step="document_collection",
            pending_steps=["document_collection", "document_verification", "kyc_checks", "risk_assessment", "approval"],
            customer_type=customer_type,
            product_type=product_type,
            required_kyc_level=required_level,
            required_documents=required_docs,
            required_checks=["identity", "sanctions", "pep", "adverse_media"],
            documents_required=len(required_docs),
            checks_required=4,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )

        self._onboarding_workflows[workflow.workflow_id] = workflow
        return workflow

    async def advance_onboarding(
        self, workflow_id: UUID, completed_step: str
    ) -> Optional[OnboardingWorkflow]:
        """Advance onboarding workflow to next step"""
        workflow = self._onboarding_workflows.get(workflow_id)
        if not workflow:
            return None

        if completed_step in workflow.pending_steps:
            workflow.pending_steps.remove(completed_step)
            workflow.completed_steps.append(completed_step)

        if workflow.pending_steps:
            workflow.current_step = workflow.pending_steps[0]
        else:
            workflow.status = "completed"
            workflow.completed_at = datetime.utcnow()
            workflow.current_step = "completed"

        return workflow

    async def get_statistics(self) -> KYCStatistics:
        """Get KYC statistics"""
        stats = KYCStatistics()
        stats.total_profiles = len(self._profiles)

        for profile in self._profiles.values():
            # By status
            status_key = profile.kyc_status.value
            stats.by_status[status_key] = stats.by_status.get(status_key, 0) + 1

            # By KYC level
            level_key = profile.kyc_level.value
            stats.by_kyc_level[level_key] = stats.by_kyc_level.get(level_key, 0) + 1

            # By risk level
            stats.by_risk_level[profile.risk_level] = stats.by_risk_level.get(profile.risk_level, 0) + 1

            # Special counts
            if profile.kyc_status == KYCStatus.PENDING_REVIEW:
                stats.pending_review += 1
            if profile.kyc_status == KYCStatus.EXPIRED:
                stats.expired_profiles += 1
            if profile.requires_edd:
                stats.requiring_edd += 1
            if profile.is_pep:
                stats.pep_count += 1
            if profile.risk_level in ["high", "very_high"]:
                stats.high_risk_count += 1

        # Onboarding stats
        stats.onboarding_in_progress = len([
            w for w in self._onboarding_workflows.values()
            if w.status == "initiated"
        ])

        return stats


# Global service instance
kyc_service = KYCService()
