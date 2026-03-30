"""Credit Limit Repository - Data access layer for credit limits"""

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from ..models.credit_limit_models import (
    CreditLimit,
    LimitBreach,
    LimitCovenant,
    LimitRequest,
    LimitReview,
    LimitStatus,
    LimitType,
    LimitUtilization,
    UtilizationStatus,
)


class CreditLimitRepository:
    def __init__(self):
        self._limits: dict[UUID, CreditLimit] = {}
        self._requests: dict[UUID, LimitRequest] = {}
        self._utilizations: list[LimitUtilization] = []
        self._reviews: dict[UUID, LimitReview] = {}
        self._breaches: dict[UUID, LimitBreach] = {}
        self._covenants: dict[UUID, LimitCovenant] = {}
        self._entity_index: dict[str, list[UUID]] = {}
        self._number_index: dict[str, UUID] = {}

    async def save(self, limit: CreditLimit) -> CreditLimit:
        self._limits[limit.limit_id] = limit
        self._number_index[limit.limit_number] = limit.limit_id
        if limit.entity_id not in self._entity_index:
            self._entity_index[limit.entity_id] = []
        if limit.limit_id not in self._entity_index[limit.entity_id]:
            self._entity_index[limit.entity_id].append(limit.limit_id)
        return limit

    async def find_by_id(self, limit_id: UUID) -> CreditLimit | None:
        return self._limits.get(limit_id)

    async def find_by_number(self, limit_number: str) -> CreditLimit | None:
        lid = self._number_index.get(limit_number)
        if lid:
            return self._limits.get(lid)
        return None

    async def find_by_entity(self, entity_id: str) -> list[CreditLimit]:
        lids = self._entity_index.get(entity_id, [])
        return [self._limits[lid] for lid in lids if lid in self._limits]

    async def find_active_by_entity(self, entity_id: str) -> list[CreditLimit]:
        limits = await self.find_by_entity(entity_id)
        return [l for l in limits if l.status == LimitStatus.ACTIVE]

    async def find_by_type(self, limit_type: LimitType) -> list[CreditLimit]:
        return [l for l in self._limits.values() if l.limit_type == limit_type]

    async def find_by_status(self, status: LimitStatus) -> list[CreditLimit]:
        return [l for l in self._limits.values() if l.status == status]

    async def find_expiring(self, days: int = 30) -> list[CreditLimit]:
        from datetime import timedelta
        cutoff = date.today() + timedelta(days=days)
        return [l for l in self._limits.values() if l.expiry_date <= cutoff and l.status == LimitStatus.ACTIVE]

    async def find_for_review(self) -> list[CreditLimit]:
        today = date.today()
        return [l for l in self._limits.values() if l.review_date <= today and l.status == LimitStatus.ACTIVE]

    async def find_by_utilization_status(self, status: UtilizationStatus) -> list[CreditLimit]:
        return [l for l in self._limits.values() if l.utilization_status == status]

    async def update(self, limit: CreditLimit) -> CreditLimit:
        limit.updated_at = datetime.now(UTC)
        self._limits[limit.limit_id] = limit
        return limit

    async def save_request(self, request: LimitRequest) -> LimitRequest:
        self._requests[request.request_id] = request
        return request

    async def find_request_by_id(self, request_id: UUID) -> LimitRequest | None:
        return self._requests.get(request_id)

    async def find_pending_requests(self) -> list[LimitRequest]:
        return [r for r in self._requests.values() if r.status == "pending"]

    async def save_utilization(self, utilization: LimitUtilization) -> LimitUtilization:
        self._utilizations.append(utilization)
        return utilization

    async def find_utilizations_by_limit(self, limit_id: UUID) -> list[LimitUtilization]:
        return [u for u in self._utilizations if u.limit_id == limit_id]

    async def save_review(self, review: LimitReview) -> LimitReview:
        self._reviews[review.review_id] = review
        return review

    async def find_reviews_by_limit(self, limit_id: UUID) -> list[LimitReview]:
        return [r for r in self._reviews.values() if r.limit_id == limit_id]

    async def save_breach(self, breach: LimitBreach) -> LimitBreach:
        self._breaches[breach.breach_id] = breach
        return breach

    async def find_breaches_by_limit(self, limit_id: UUID) -> list[LimitBreach]:
        return [b for b in self._breaches.values() if b.limit_id == limit_id]

    async def find_unresolved_breaches(self) -> list[LimitBreach]:
        return [b for b in self._breaches.values() if not b.resolved]

    async def save_covenant(self, covenant: LimitCovenant) -> LimitCovenant:
        self._covenants[covenant.covenant_id] = covenant
        return covenant

    async def find_covenants_by_limit(self, limit_id: UUID) -> list[LimitCovenant]:
        return [c for c in self._covenants.values() if c.limit_id == limit_id]

    async def get_statistics(self) -> dict[str, Any]:
        total_amount = sum(l.limit_amount for l in self._limits.values())
        total_utilized = sum(l.utilized_amount for l in self._limits.values())
        by_type = {}
        for limit in self._limits.values():
            by_type[limit.limit_type.value] = by_type.get(limit.limit_type.value, 0) + 1
        return {
            "total_limits": len(self._limits),
            "total_limit_amount": total_amount,
            "total_utilized": total_utilized,
            "by_type": by_type
        }

    async def count(self) -> int:
        return len(self._limits)


credit_limit_repository = CreditLimitRepository()
