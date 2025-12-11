"""Credit Limit Service - Credit limit management"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID
from ..models.credit_limit_models import (
    CreditLimit, LimitRequest, LimitUtilization, LimitReview,
    LimitBreach, LimitCovenant, LimitStatistics,
    LimitType, LimitStatus, UtilizationStatus
)


class CreditLimitService:
    def __init__(self):
        self._limits: Dict[UUID, CreditLimit] = {}
        self._requests: Dict[UUID, LimitRequest] = {}
        self._utilizations: List[LimitUtilization] = []
        self._reviews: Dict[UUID, LimitReview] = {}
        self._breaches: Dict[UUID, LimitBreach] = {}
        self._covenants: Dict[UUID, LimitCovenant] = {}
        self._counter = 0

    def _generate_number(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}-{datetime.utcnow().strftime('%Y%m%d')}-{self._counter:06d}"

    def _calculate_utilization_status(self, utilization_pct: float, warning: float, breach: float) -> UtilizationStatus:
        if utilization_pct >= breach:
            return UtilizationStatus.BREACH
        elif utilization_pct >= warning:
            return UtilizationStatus.WARNING
        return UtilizationStatus.NORMAL

    async def create_limit(
        self, limit_type: LimitType, entity_id: str, entity_name: str,
        limit_amount: float, tenor_months: int, approved_by: str,
        conditions: List[str] = None
    ) -> CreditLimit:
        today = date.today()
        limit = CreditLimit(
            limit_number=self._generate_number("LMT"),
            limit_type=limit_type,
            entity_id=entity_id,
            entity_name=entity_name,
            limit_amount=limit_amount,
            available_amount=limit_amount,
            effective_date=today,
            expiry_date=today + timedelta(days=30 * tenor_months),
            review_date=today + timedelta(days=365),
            approved_by=approved_by,
            approved_date=datetime.utcnow(),
            approval_authority="credit_committee",
            conditions=conditions or []
        )
        self._limits[limit.limit_id] = limit
        return limit

    async def get_limit(self, limit_id: UUID) -> Optional[CreditLimit]:
        return self._limits.get(limit_id)

    async def get_entity_limit(self, entity_id: str, limit_type: LimitType = None) -> Optional[CreditLimit]:
        for limit in self._limits.values():
            if limit.entity_id == entity_id and limit.status == LimitStatus.ACTIVE:
                if limit_type is None or limit.limit_type == limit_type:
                    return limit
        return None

    async def update_limit(
        self, limit_id: UUID, updates: Dict[str, Any]
    ) -> Optional[CreditLimit]:
        limit = self._limits.get(limit_id)
        if limit:
            for key, value in updates.items():
                if hasattr(limit, key):
                    setattr(limit, key, value)
            limit.updated_at = datetime.utcnow()
        return limit

    async def utilize_limit(
        self, limit_id: UUID, amount: float, utilization_type: str,
        transaction_reference: str = None
    ) -> Optional[LimitUtilization]:
        limit = self._limits.get(limit_id)
        if not limit:
            return None

        if utilization_type == "drawdown" and amount > limit.available_amount:
            # Record potential breach
            await self._record_breach(limit, amount)
            return None

        change = amount if utilization_type == "drawdown" else -amount
        new_utilized = limit.utilized_amount + change
        new_utilized = max(0, min(new_utilized, limit.limit_amount))

        utilization = LimitUtilization(
            limit_id=limit_id,
            utilization_date=date.today(),
            utilized_amount=change,
            utilization_type=utilization_type,
            transaction_reference=transaction_reference,
            balance_after=new_utilized,
            utilization_percentage_after=(new_utilized / limit.limit_amount * 100)
        )
        self._utilizations.append(utilization)

        # Update limit
        limit.utilized_amount = new_utilized
        limit.available_amount = limit.limit_amount - new_utilized
        limit.utilization_percentage = (new_utilized / limit.limit_amount * 100)
        limit.utilization_status = self._calculate_utilization_status(
            limit.utilization_percentage, limit.warning_threshold, limit.breach_threshold
        )
        limit.updated_at = datetime.utcnow()

        return utilization

    async def _record_breach(self, limit: CreditLimit, attempted_amount: float) -> LimitBreach:
        breach = LimitBreach(
            limit_id=limit.limit_id,
            breach_date=datetime.utcnow(),
            breach_type="limit",
            limit_amount=limit.limit_amount,
            utilized_amount=limit.utilized_amount,
            breach_amount=attempted_amount - limit.available_amount,
            breach_percentage=((limit.utilized_amount + attempted_amount) / limit.limit_amount * 100),
            breach_reason="Attempted utilization exceeds available limit"
        )
        self._breaches[breach.breach_id] = breach
        return breach

    async def submit_limit_request(
        self, request_type: str, limit_type: LimitType,
        entity_id: str, entity_name: str, requested_limit: float,
        tenor_months: int, purpose: str, justification: str,
        requested_by: str
    ) -> LimitRequest:
        current_limit = await self.get_entity_limit(entity_id, limit_type)

        request = LimitRequest(
            request_number=self._generate_number("REQ"),
            request_type=request_type,
            limit_type=limit_type,
            entity_id=entity_id,
            entity_name=entity_name,
            current_limit=current_limit.limit_amount if current_limit else None,
            requested_limit=requested_limit,
            requested_tenor_months=tenor_months,
            purpose=purpose,
            justification=justification,
            requested_by=requested_by
        )
        self._requests[request.request_id] = request
        return request

    async def approve_request(
        self, request_id: UUID, approved_amount: float,
        conditions: List[str], approved_by: str
    ) -> Optional[LimitRequest]:
        request = self._requests.get(request_id)
        if not request:
            return None

        request.status = "approved"
        request.decision = "approved"
        request.decision_date = datetime.utcnow()
        request.approved_amount = approved_amount
        request.conditions = conditions
        request.approval_history.append({
            "approver": approved_by,
            "action": "approved",
            "amount": approved_amount,
            "date": datetime.utcnow().isoformat()
        })

        # Create the limit
        await self.create_limit(
            limit_type=request.limit_type,
            entity_id=request.entity_id,
            entity_name=request.entity_name,
            limit_amount=approved_amount,
            tenor_months=request.requested_tenor_months,
            approved_by=approved_by,
            conditions=conditions
        )

        return request

    async def create_review(
        self, limit_id: UUID, review_type: str,
        recommended_limit: float, recommendation: str,
        reviewed_by: str
    ) -> Optional[LimitReview]:
        limit = self._limits.get(limit_id)
        if not limit:
            return None

        review = LimitReview(
            limit_id=limit_id,
            review_date=date.today(),
            review_type=review_type,
            current_limit=limit.limit_amount,
            recommended_limit=recommended_limit,
            limit_change=recommended_limit - limit.limit_amount,
            change_reason="Annual review",
            recommendation=recommendation,
            reviewed_by=reviewed_by
        )
        self._reviews[review.review_id] = review
        return review

    async def add_covenant(
        self, limit_id: UUID, covenant_type: str, covenant_name: str,
        description: str, threshold_value: float, measurement_frequency: str
    ) -> Optional[LimitCovenant]:
        limit = self._limits.get(limit_id)
        if not limit:
            return None

        covenant = LimitCovenant(
            limit_id=limit_id,
            covenant_type=covenant_type,
            covenant_name=covenant_name,
            covenant_description=description,
            threshold_value=threshold_value,
            measurement_frequency=measurement_frequency,
            next_measurement_date=date.today() + timedelta(days=90)
        )
        self._covenants[covenant.covenant_id] = covenant
        limit.covenants.append(covenant.model_dump())
        return covenant

    async def get_breaches(self, limit_id: UUID = None) -> List[LimitBreach]:
        if limit_id:
            return [b for b in self._breaches.values() if b.limit_id == limit_id]
        return list(self._breaches.values())

    async def get_statistics(self) -> LimitStatistics:
        stats = LimitStatistics(
            total_limits=len(self._limits),
            total_limit_amount=sum(l.limit_amount for l in self._limits.values()),
            total_utilized=sum(l.utilized_amount for l in self._limits.values())
        )
        for limit in self._limits.values():
            stats.by_type[limit.limit_type.value] = stats.by_type.get(limit.limit_type.value, 0) + 1
            stats.by_status[limit.status.value] = stats.by_status.get(limit.status.value, 0) + 1
            if limit.utilization_status == UtilizationStatus.BREACH:
                stats.breaches_count += 1
            elif limit.utilization_status == UtilizationStatus.WARNING:
                stats.warnings_count += 1
        if self._limits:
            stats.average_utilization = sum(l.utilization_percentage for l in self._limits.values()) / len(self._limits)
        return stats


credit_limit_service = CreditLimitService()
