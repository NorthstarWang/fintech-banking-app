# SQLAlchemy imports removed - using memory adapter
import random
import string
from datetime import date, datetime, timedelta
from typing import Any

from app.models.entities.insurance_models import (
    ClaimStatus,
    ClaimTimelineEvent,
    InsuranceClaimCreate,
    InsuranceClaimResponse,
    InsurancePolicyCreate,
    InsurancePolicyResponse,
    InsuranceProviderResponse,
    InsuranceQuoteRequest,
    InsuranceQuoteResponse,
    InsuranceSummaryResponse,
    InsuranceType,
    PolicyStatus,
    PremiumFrequency,
)
from app.models.memory_models import MemoryModel


class InsuranceManager:
    def __init__(self, db):
        self.db = db

    def _generate_policy_number(self) -> str:
        """Generate unique policy number."""
        prefix = "POL"
        random_part = ''.join(random.choices(string.digits, k=8))
        return f"{prefix}-{random_part}"

    def _generate_claim_number(self) -> str:
        """Generate unique claim number."""
        prefix = "CLM"
        timestamp = datetime.now().strftime("%Y%m%d")
        random_part = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}-{timestamp}-{random_part}"

    def get_user_insurance_summary(self, user_id: int) -> InsuranceSummaryResponse:
        """Get comprehensive insurance summary for a user."""
        # Get all policies
        policies = self.db.query(MemoryModel).filter(
            and_(
                MemoryModel.user_id == user_id,
                MemoryModel.memory_type == "insurance_policy"
            )
        ).all()

        active_policies = [p for p in policies if p.data.get("status") == PolicyStatus.ACTIVE.value]

        # Calculate totals
        total_monthly = sum(
            float(p.data.get("premium_amount", 0))
            for p in active_policies
            if p.data.get("premium_frequency") == PremiumFrequency.MONTHLY.value
        )

        total_annual = sum(
            float(p.data.get("premium_amount", 0))
            for p in active_policies
            if p.data.get("premium_frequency") == PremiumFrequency.ANNUAL.value
        )

        # Convert other frequencies to monthly
        for p in active_policies:
            if p.data.get("premium_frequency") == PremiumFrequency.QUARTERLY.value:
                total_monthly += float(p.data.get("premium_amount", 0)) / 3
            elif p.data.get("premium_frequency") == PremiumFrequency.SEMI_ANNUAL.value:
                total_monthly += float(p.data.get("premium_amount", 0)) / 6

        total_annual += total_monthly * 12

        # Group by type
        policies_by_type = {}
        for p in active_policies:
            insurance_type = p.data.get("insurance_type", "unknown")
            policies_by_type[insurance_type] = policies_by_type.get(insurance_type, 0) + 1

        # Get upcoming renewals (within 60 days)
        upcoming_renewals = []
        today = date.today()
        for p in active_policies:
            end_date_str = p.data.get("end_date")
            if end_date_str:
                end_date = date.fromisoformat(end_date_str)
                days_until = (end_date - today).days
                if 0 <= days_until <= 60:
                    upcoming_renewals.append({
                        "policy_id": p.id,
                        "policy_number": p.data.get("policy_number"),
                        "insurance_type": p.data.get("insurance_type"),
                        "end_date": end_date_str,
                        "days_until_renewal": days_until
                    })

        # Get recent claims
        claims = self.db.query(MemoryModel).filter(
            and_(
                MemoryModel.user_id == user_id,
                MemoryModel.memory_type == "insurance_claim"
            )
        ).order_by(MemoryModel.created_at.desc()).limit(5).all()

        recent_claims = []
        for c in claims:
            recent_claims.append({
                "claim_id": c.id,
                "claim_number": c.data.get("claim_number"),
                "status": c.data.get("status"),
                "amount_claimed": c.data.get("amount_claimed"),
                "filed_date": c.data.get("filed_date")
            })

        # Analyze coverage gaps
        coverage_gaps = self._analyze_coverage_gaps(active_policies)

        total_coverage = sum(float(p.data.get("coverage_amount", 0)) for p in active_policies)

        return InsuranceSummaryResponse(
            total_policies=len(policies),
            active_policies=len(active_policies),
            total_monthly_premiums=total_monthly,
            total_annual_premiums=total_annual,
            total_coverage_amount=total_coverage,
            policies_by_type=policies_by_type,
            upcoming_renewals=upcoming_renewals,
            recent_claims=recent_claims,
            coverage_gaps=coverage_gaps
        )

    def _analyze_coverage_gaps(self, policies: list[MemoryModel]) -> list[str]:
        """Analyze insurance coverage and identify gaps."""
        gaps = []
        covered_types = {p.data.get("insurance_type") for p in policies}

        # Essential insurance types everyone should consider
        essential_types = {
            InsuranceType.HEALTH.value: "Health insurance",
            InsuranceType.AUTO.value: "Auto insurance (if you own a vehicle)",
            InsuranceType.HOME.value: "Homeowners/Renters insurance",
            InsuranceType.LIFE.value: "Life insurance (if you have dependents)",
            InsuranceType.DISABILITY.value: "Disability insurance"
        }

        for ins_type, description in essential_types.items():
            if ins_type not in covered_types:
                gaps.append(f"Missing {description}")

        # Check for adequate coverage amounts
        for p in policies:
            if p.data.get("insurance_type") == InsuranceType.LIFE.value:
                coverage = float(p.data.get("coverage_amount", 0))
                if coverage < 500000:  # General recommendation: 10x annual income
                    gaps.append("Life insurance coverage may be insufficient")

        return gaps

    def get_user_policies(
        self,
        user_id: int,
        insurance_type: InsuranceType | None = None,
        status: PolicyStatus | None = None
    ) -> list[InsurancePolicyResponse]:
        """Get all insurance policies for a user."""
        query = self.db.query(MemoryModel).filter(
            and_(
                MemoryModel.user_id == user_id,
                MemoryModel.memory_type == "insurance_policy"
            )
        )

        policies = query.all()
        results = []

        for policy in policies:
            # Apply filters
            if insurance_type and policy.data.get("insurance_type") != insurance_type.value:
                continue
            if status and policy.data.get("status") != status.value:
                continue

            results.append(self._memory_to_policy_response(policy))

        return results

    def get_policy(self, policy_id: int, user_id: int) -> InsurancePolicyResponse | None:
        """Get specific insurance policy."""
        policy = self.db.query(MemoryModel).filter(
            and_(
                MemoryModel.id == policy_id,
                MemoryModel.user_id == user_id,
                MemoryModel.memory_type == "insurance_policy"
            )
        ).first()

        if not policy:
            return None

        return self._memory_to_policy_response(policy)

    def create_policy(self, user_id: int, policy_data: InsurancePolicyCreate) -> InsurancePolicyResponse:
        """Create new insurance policy."""
        # Calculate next premium date
        today = date.today()
        if policy_data.premium_frequency == PremiumFrequency.MONTHLY:
            next_premium = today + timedelta(days=30)
        elif policy_data.premium_frequency == PremiumFrequency.QUARTERLY:
            next_premium = today + timedelta(days=90)
        elif policy_data.premium_frequency == PremiumFrequency.SEMI_ANNUAL:
            next_premium = today + timedelta(days=180)
        else:  # Annual
            next_premium = today + timedelta(days=365)

        policy_dict = policy_data.model_dump()
        policy_dict.update({
            "status": PolicyStatus.ACTIVE.value,
            "next_premium_date": next_premium.isoformat(),
            "documents": [],
            "out_of_pocket_max": policy_dict.get("out_of_pocket_max")
        })

        # Convert dates to strings
        policy_dict["start_date"] = policy_dict["start_date"].isoformat()
        policy_dict["end_date"] = policy_dict["end_date"].isoformat()

        memory = MemoryModel(
            user_id=user_id,
            memory_type="insurance_policy",
            title=f"{policy_data.insurance_type.value.title()} Insurance - {policy_data.provider_name}",
            content=f"Policy #{policy_data.policy_number}",
            data=policy_dict,
            importance_score=0.8
        )

        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)

        return self._memory_to_policy_response(memory)

    def update_policy(
        self,
        policy_id: int,
        user_id: int,
        policy_data: InsurancePolicyCreate
    ) -> InsurancePolicyResponse | None:
        """Update existing insurance policy."""
        policy = self.db.query(MemoryModel).filter(
            and_(
                MemoryModel.id == policy_id,
                MemoryModel.user_id == user_id,
                MemoryModel.memory_type == "insurance_policy"
            )
        ).first()

        if not policy:
            return None

        # Update policy data
        policy_dict = policy_data.model_dump()
        policy_dict["start_date"] = policy_dict["start_date"].isoformat()
        policy_dict["end_date"] = policy_dict["end_date"].isoformat()

        # Preserve existing fields
        policy_dict["status"] = policy.data.get("status", PolicyStatus.ACTIVE.value)
        policy_dict["documents"] = policy.data.get("documents", [])
        policy_dict["next_premium_date"] = policy.data.get("next_premium_date")

        policy.data = policy_dict
        policy.title = f"{policy_data.insurance_type.value.title()} Insurance - {policy_data.provider_name}"
        policy.content = f"Policy #{policy_data.policy_number}"
        policy.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(policy)

        return self._memory_to_policy_response(policy)

    def delete_policy(self, policy_id: int, user_id: int) -> bool:
        """Delete insurance policy."""
        policy = self.db.query(MemoryModel).filter(
            and_(
                MemoryModel.id == policy_id,
                MemoryModel.user_id == user_id,
                MemoryModel.memory_type == "insurance_policy"
            )
        ).first()

        if not policy:
            return False

        self.db.delete(policy)
        self.db.commit()
        return True

    def cancel_policy(
        self,
        policy_id: int,
        user_id: int,
        cancellation_date: date,
        reason: str
    ) -> bool:
        """Cancel an insurance policy."""
        policy = self.db.query(MemoryModel).filter(
            and_(
                MemoryModel.id == policy_id,
                MemoryModel.user_id == user_id,
                MemoryModel.memory_type == "insurance_policy"
            )
        ).first()

        if not policy:
            return False

        policy.data["status"] = PolicyStatus.CANCELLED.value
        policy.data["cancellation_date"] = cancellation_date.isoformat()
        policy.data["cancellation_reason"] = reason
        policy.updated_at = datetime.utcnow()

        self.db.commit()
        return True

    def get_user_claims(
        self,
        user_id: int,
        policy_id: int | None = None,
        status: ClaimStatus | None = None
    ) -> list[InsuranceClaimResponse]:
        """Get all claims for a user."""
        query = self.db.query(MemoryModel).filter(
            and_(
                MemoryModel.user_id == user_id,
                MemoryModel.memory_type == "insurance_claim"
            )
        )

        claims = query.all()
        results = []

        for claim in claims:
            # Apply filters
            if policy_id and claim.data.get("policy_id") != policy_id:
                continue
            if status and claim.data.get("status") != status.value:
                continue

            results.append(self._memory_to_claim_response(claim))

        return results

    def get_claim(self, claim_id: int, user_id: int) -> InsuranceClaimResponse | None:
        """Get specific claim."""
        claim = self.db.query(MemoryModel).filter(
            and_(
                MemoryModel.id == claim_id,
                MemoryModel.user_id == user_id,
                MemoryModel.memory_type == "insurance_claim"
            )
        ).first()

        if not claim:
            return None

        return self._memory_to_claim_response(claim)

    def create_claim(self, claim_data: InsuranceClaimCreate) -> InsuranceClaimResponse:
        """Create new insurance claim."""
        claim_number = self._generate_claim_number()

        # Get policy to determine user_id
        policy = self.db.query(MemoryModel).filter(
            and_(
                MemoryModel.id == claim_data.policy_id,
                MemoryModel.memory_type == "insurance_policy"
            )
        ).first()

        if not policy:
            raise ValueError("Policy not found")

        claim_dict = claim_data.model_dump()
        claim_dict.update({
            "claim_number": claim_number,
            "status": ClaimStatus.SUBMITTED.value,
            "filed_date": datetime.utcnow().isoformat(),
            "documents": claim_dict.get("supporting_documents", []),
            "status_history": [{
                "status": ClaimStatus.SUBMITTED.value,
                "date": datetime.utcnow().isoformat(),
                "notes": "Claim submitted"
            }]
        })

        # Convert date to string
        claim_dict["incident_date"] = claim_dict["incident_date"].isoformat()

        memory = MemoryModel(
            user_id=policy.user_id,
            memory_type="insurance_claim",
            title=f"Insurance Claim - {claim_data.claim_type}",
            content=f"Claim #{claim_number} - ${claim_data.amount_claimed}",
            data=claim_dict,
            importance_score=0.9
        )

        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)

        return self._memory_to_claim_response(memory)

    def update_claim_status(
        self,
        claim_id: int,
        user_id: int,
        status: ClaimStatus,
        notes: str | None = None
    ) -> InsuranceClaimResponse | None:
        """Update claim status."""
        claim = self.db.query(MemoryModel).filter(
            and_(
                MemoryModel.id == claim_id,
                MemoryModel.user_id == user_id,
                MemoryModel.memory_type == "insurance_claim"
            )
        ).first()

        if not claim:
            return None

        # Update status
        claim.data["status"] = status.value

        # Add to status history
        history_entry = {
            "status": status.value,
            "date": datetime.utcnow().isoformat(),
            "notes": notes or f"Status changed to {status.value}"
        }

        if "status_history" not in claim.data:
            claim.data["status_history"] = []
        claim.data["status_history"].append(history_entry)

        # Update specific fields based on status
        if status == ClaimStatus.APPROVED:
            if notes and "approved_amount" in notes:
                # Extract approved amount from notes if provided
                try:
                    approved_amount = float(notes.split("approved_amount:")[1].split()[0])
                    claim.data["amount_approved"] = approved_amount
                except:
                    claim.data["amount_approved"] = claim.data.get("amount_claimed")
        elif status == ClaimStatus.PAID:
            claim.data["payment_date"] = datetime.utcnow().isoformat()
            claim.data["amount_paid"] = claim.data.get("amount_approved", claim.data.get("amount_claimed"))

        claim.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(claim)

        return self._memory_to_claim_response(claim)

    def get_claim_timeline(self, claim_id: int, user_id: int) -> list[ClaimTimelineEvent] | None:
        """Get timeline of events for a claim."""
        claim = self.db.query(MemoryModel).filter(
            and_(
                MemoryModel.id == claim_id,
                MemoryModel.user_id == user_id,
                MemoryModel.memory_type == "insurance_claim"
            )
        ).first()

        if not claim:
            return None

        timeline = []

        # Add submission event
        timeline.append(ClaimTimelineEvent(
            event_date=datetime.fromisoformat(claim.data.get("filed_date")),
            event_type="Claim Submitted",
            description=f"Claim #{claim.data.get('claim_number')} submitted",
            performed_by="User"
        ))

        # Add status history events
        for event in claim.data.get("status_history", []):
            timeline.append(ClaimTimelineEvent(
                event_date=datetime.fromisoformat(event["date"]),
                event_type=f"Status: {event['status']}",
                description=event.get("notes", ""),
                performed_by="System"
            ))

        # Add document uploads
        for doc in claim.data.get("documents", []):
            if "upload_date" in doc:
                timeline.append(ClaimTimelineEvent(
                    event_date=datetime.fromisoformat(doc["upload_date"]),
                    event_type="Document Uploaded",
                    description=f"{doc.get('document_type', 'Document')} uploaded",
                    performed_by="User"
                ))

        # Sort by date
        timeline.sort(key=lambda x: x.event_date)

        return timeline

    def add_claim_document(
        self,
        claim_id: int,
        user_id: int,
        document_url: str,
        document_type: str
    ) -> bool:
        """Add document to claim."""
        claim = self.db.query(MemoryModel).filter(
            and_(
                MemoryModel.id == claim_id,
                MemoryModel.user_id == user_id,
                MemoryModel.memory_type == "insurance_claim"
            )
        ).first()

        if not claim:
            return False

        if "documents" not in claim.data:
            claim.data["documents"] = []

        claim.data["documents"].append({
            "url": document_url,
            "document_type": document_type,
            "upload_date": datetime.utcnow().isoformat()
        })

        claim.updated_at = datetime.utcnow()
        self.db.commit()

        return True

    def get_providers(
        self,
        insurance_type: InsuranceType | None = None,
        min_rating: float | None = None
    ) -> list[InsuranceProviderResponse]:
        """Get list of insurance providers."""
        # In a real implementation, this would query a providers table
        # For now, return mock data
        providers = [
            {
                "id": 1,
                "name": "SecureHealth Insurance",
                "insurance_types": [InsuranceType.HEALTH, InsuranceType.DENTAL, InsuranceType.VISION],
                "rating": 4.5,
                "customer_service_phone": "1-800-HEALTH-1",
                "customer_service_email": "support@securehealth.com",
                "website": "https://securehealth.com",
                "claim_phone": "1-800-CLAIMS-1",
                "network_size": 50000,
                "financial_strength_rating": "A+",
                "complaint_ratio": 0.02
            },
            {
                "id": 2,
                "name": "AutoGuard Insurance",
                "insurance_types": [InsuranceType.AUTO, InsuranceType.HOME],
                "rating": 4.3,
                "customer_service_phone": "1-800-AUTO-123",
                "customer_service_email": "help@autoguard.com",
                "website": "https://autoguard.com",
                "claim_phone": "1-800-CLAIMS-2",
                "financial_strength_rating": "A",
                "complaint_ratio": 0.03
            },
            {
                "id": 3,
                "name": "LifeProtect Insurance",
                "insurance_types": [InsuranceType.LIFE, InsuranceType.DISABILITY],
                "rating": 4.7,
                "customer_service_phone": "1-800-LIFE-456",
                "website": "https://lifeprotect.com",
                "claim_phone": "1-800-CLAIMS-3",
                "financial_strength_rating": "A++",
                "complaint_ratio": 0.01
            },
            {
                "id": 4,
                "name": "CryptoShield",
                "insurance_types": [InsuranceType.CRYPTO, InsuranceType.CYBER],
                "rating": 4.1,
                "customer_service_phone": "1-800-CRYPTO-1",
                "customer_service_email": "support@cryptoshield.io",
                "website": "https://cryptoshield.io",
                "claim_phone": "1-800-CRYPTO-2",
                "financial_strength_rating": "B+",
                "complaint_ratio": 0.04
            }
        ]

        results = []
        for provider in providers:
            # Apply filters
            if insurance_type:
                if insurance_type not in provider["insurance_types"]:
                    continue
            if min_rating and provider["rating"] < min_rating:
                continue

            results.append(InsuranceProviderResponse(**provider))

        return results

    def get_quotes(
        self,
        user_id: int,
        quote_request: InsuranceQuoteRequest
    ) -> list[InsuranceQuoteResponse]:
        """Get insurance quotes from multiple providers."""
        # In a real implementation, this would call provider APIs
        # For now, generate mock quotes
        providers = self.get_providers(quote_request.insurance_type)
        quotes = []

        for provider in providers:
            # Base premium calculation (mock)
            base_premium = quote_request.coverage_amount * 0.002  # 0.2% of coverage

            # Adjust based on deductible
            deductible_factor = 1 - (quote_request.deductible / quote_request.coverage_amount * 0.5)
            base_premium *= deductible_factor

            # Random variation between providers
            provider_factor = random.uniform(0.8, 1.2)
            monthly_premium = base_premium * provider_factor / 12

            # Apply discounts
            discounts = []
            if quote_request.insurance_type == InsuranceType.AUTO:
                if quote_request.personal_info.get("safe_driver", True):
                    monthly_premium *= 0.9
                    discounts.append("Safe driver discount")
                if quote_request.personal_info.get("multi_policy", False):
                    monthly_premium *= 0.95
                    discounts.append("Multi-policy discount")

            quote_id = f"QUOTE-{provider.name[:3].upper()}-{random.randint(100000, 999999)}"

            quotes.append(InsuranceQuoteResponse(
                provider_name=provider.name,
                monthly_premium=round(monthly_premium, 2),
                annual_premium=round(monthly_premium * 12, 2),
                coverage_amount=quote_request.coverage_amount,
                deductible=quote_request.deductible,
                coverage_details=quote_request.coverage_options or {},
                discounts_applied=discounts,
                quote_id=quote_id,
                valid_until=datetime.utcnow() + timedelta(days=30)
            ))

        return quotes

    def analyze_coverage_gaps(self, user_id: int) -> dict[str, Any]:
        """Analyze user's insurance coverage and identify gaps."""
        policies = self.get_user_policies(user_id)
        active_policies = [p for p in policies if p.status == PolicyStatus.ACTIVE]

        gaps = self._analyze_coverage_gaps([
            self.db.query(MemoryModel).filter(MemoryModel.id == p.id).first()
            for p in active_policies
        ])

        recommendations = []

        # Generate specific recommendations
        covered_types = {p.insurance_type for p in active_policies}

        if InsuranceType.HEALTH not in covered_types:
            recommendations.append({
                "type": "health",
                "priority": "high",
                "reason": "Health insurance is essential for medical expenses",
                "estimated_cost": "$300-500/month"
            })

        if InsuranceType.DISABILITY not in covered_types:
            recommendations.append({
                "type": "disability",
                "priority": "medium",
                "reason": "Protects income if unable to work due to illness/injury",
                "estimated_cost": "$50-150/month"
            })

        # Check for underinsured policies
        for policy in active_policies:
            if policy.insurance_type == InsuranceType.LIFE and policy.coverage_amount < 500000:
                recommendations.append({
                    "type": "life_increase",
                    "priority": "medium",
                    "reason": f"Current life insurance ({policy.coverage_amount}) may be insufficient",
                    "estimated_cost": "Additional $50-100/month"
                })

        return {
            "coverage_gaps": gaps,
            "recommendations": recommendations,
            "coverage_score": max(0, 100 - len(gaps) * 15),  # Simple scoring
            "next_steps": [
                "Review recommended insurance types",
                "Get quotes for missing coverage",
                "Schedule annual insurance review"
            ]
        }

    def get_renewal_options(self, policy_id: int) -> dict[str, Any]:
        """Get renewal options for an expiring policy."""
        policy = self.db.query(MemoryModel).filter(
            and_(
                MemoryModel.id == policy_id,
                MemoryModel.memory_type == "insurance_policy"
            )
        ).first()

        if not policy:
            return {}

        # Generate renewal options
        current_premium = float(policy.data.get("premium_amount", 0))

        options = [
            {
                "option": "Renew with same coverage",
                "premium_change": 0,
                "new_premium": current_premium,
                "benefits": ["No changes to coverage", "Simple renewal process"]
            },
            {
                "option": "Increase coverage by 20%",
                "premium_change": current_premium * 0.15,
                "new_premium": current_premium * 1.15,
                "benefits": ["Better protection", "Keep pace with inflation"]
            },
            {
                "option": "Add additional riders",
                "premium_change": current_premium * 0.1,
                "new_premium": current_premium * 1.1,
                "benefits": ["Enhanced coverage options", "Customized protection"]
            },
            {
                "option": "Switch to competitor offer",
                "premium_change": -current_premium * 0.1,
                "new_premium": current_premium * 0.9,
                "benefits": ["Lower premium", "New customer discounts"]
            }
        ]

        return {
            "current_policy": {
                "policy_number": policy.data.get("policy_number"),
                "current_premium": current_premium,
                "coverage_amount": policy.data.get("coverage_amount"),
                "end_date": policy.data.get("end_date")
            },
            "renewal_options": options,
            "recommendation": "Consider increasing coverage to account for inflation"
        }

    def get_claims_analytics(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None
    ) -> dict[str, Any]:
        """Get analytics on user's insurance claims."""
        claims = self.get_user_claims(user_id)

        # Filter by date if provided
        if start_date or end_date:
            filtered_claims = []
            for claim in claims:
                claim_date = date.fromisoformat(claim.incident_date.isoformat()[:10])
                if start_date and claim_date < start_date:
                    continue
                if end_date and claim_date > end_date:
                    continue
                filtered_claims.append(claim)
            claims = filtered_claims

        # Calculate analytics
        total_claims = len(claims)
        total_claimed = sum(claim.amount_claimed for claim in claims)
        total_approved = sum(claim.amount_approved or 0 for claim in claims if claim.amount_approved)
        total_paid = sum(claim.amount_paid or 0 for claim in claims if claim.amount_paid)

        # Group by status
        status_breakdown = {}
        for claim in claims:
            status = claim.status
            if status not in status_breakdown:
                status_breakdown[status] = {"count": 0, "total_amount": 0}
            status_breakdown[status]["count"] += 1
            status_breakdown[status]["total_amount"] += claim.amount_claimed

        # Calculate approval rate
        completed_claims = [c for c in claims if c.status in [ClaimStatus.APPROVED, ClaimStatus.DENIED, ClaimStatus.PAID]]
        approval_rate = 0
        if completed_claims:
            approved_claims = [c for c in completed_claims if c.status in [ClaimStatus.APPROVED, ClaimStatus.PAID]]
            approval_rate = len(approved_claims) / len(completed_claims) * 100

        # Average processing time
        processing_times = []
        for claim in completed_claims:
            if claim.status == ClaimStatus.PAID and claim.payment_date:
                filed_date = datetime.fromisoformat(claim.filed_date.isoformat()[:19])
                paid_date = datetime.fromisoformat(claim.payment_date.isoformat()[:19])
                processing_times.append((paid_date - filed_date).days)

        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

        return {
            "total_claims": total_claims,
            "total_claimed_amount": total_claimed,
            "total_approved_amount": total_approved,
            "total_paid_amount": total_paid,
            "approval_rate": round(approval_rate, 2),
            "average_processing_days": round(avg_processing_time, 1),
            "status_breakdown": status_breakdown,
            "claim_trends": {
                "most_common_type": max(
                    [(c.claim_type, sum(1 for cl in claims if cl.claim_type == c.claim_type))
                     for c in claims],
                    key=lambda x: x[1]
                )[0] if claims else None,
                "average_claim_amount": round(total_claimed / total_claims, 2) if total_claims else 0
            }
        }

    def _memory_to_policy_response(self, memory: MemoryModel) -> InsurancePolicyResponse:
        """Convert MemoryModel to InsurancePolicyResponse."""
        data = memory.data
        return InsurancePolicyResponse(
            id=memory.id,
            user_id=memory.user_id,
            insurance_type=InsuranceType(data.get("insurance_type")),
            provider_name=data.get("provider_name"),
            policy_number=data.get("policy_number"),
            status=PolicyStatus(data.get("status", PolicyStatus.ACTIVE.value)),
            coverage_amount=float(data.get("coverage_amount", 0)),
            deductible=float(data.get("deductible", 0)),
            out_of_pocket_max=float(data.get("out_of_pocket_max")) if data.get("out_of_pocket_max") else None,
            premium_amount=float(data.get("premium_amount", 0)),
            premium_frequency=PremiumFrequency(data.get("premium_frequency")),
            next_premium_date=date.fromisoformat(data.get("next_premium_date")),
            start_date=date.fromisoformat(data.get("start_date")),
            end_date=date.fromisoformat(data.get("end_date")),
            renewal_date=date.fromisoformat(data.get("renewal_date")) if data.get("renewal_date") else None,
            beneficiaries=data.get("beneficiaries"),
            coverage_details=data.get("coverage_details", {}),
            documents=data.get("documents", []),
            created_at=memory.created_at,
            updated_at=memory.updated_at
        )

    def _memory_to_claim_response(self, memory: MemoryModel) -> InsuranceClaimResponse:
        """Convert MemoryModel to InsuranceClaimResponse."""
        data = memory.data
        return InsuranceClaimResponse(
            id=memory.id,
            policy_id=data.get("policy_id"),
            claim_number=data.get("claim_number"),
            claim_type=data.get("claim_type"),
            status=ClaimStatus(data.get("status")),
            incident_date=date.fromisoformat(data.get("incident_date")),
            filed_date=datetime.fromisoformat(data.get("filed_date")),
            amount_claimed=float(data.get("amount_claimed", 0)),
            amount_approved=float(data.get("amount_approved")) if data.get("amount_approved") else None,
            amount_paid=float(data.get("amount_paid")) if data.get("amount_paid") else None,
            deductible_applied=float(data.get("deductible_applied")) if data.get("deductible_applied") else None,
            description=data.get("description"),
            adjuster_name=data.get("adjuster_name"),
            adjuster_notes=data.get("adjuster_notes"),
            denial_reason=data.get("denial_reason"),
            documents=data.get("documents", []),
            status_history=data.get("status_history", []),
            payment_date=datetime.fromisoformat(data.get("payment_date")) if data.get("payment_date") else None,
            appeal_deadline=date.fromisoformat(data.get("appeal_deadline")) if data.get("appeal_deadline") else None,
            created_at=memory.created_at,
            updated_at=memory.updated_at
        )
