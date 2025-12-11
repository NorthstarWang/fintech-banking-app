"""Credit Score Repository - Data access layer for credit scores"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from ..models.credit_score_models import (
    CreditScore, CreditScoreHistory, CreditScoreRequest,
    ScoreType, ScoreCategory
)


class CreditScoreRepository:
    def __init__(self):
        self._scores: Dict[UUID, CreditScore] = {}
        self._customer_index: Dict[str, List[UUID]] = {}
        self._requests: Dict[UUID, CreditScoreRequest] = {}

    async def save(self, score: CreditScore) -> CreditScore:
        self._scores[score.score_id] = score
        if score.customer_id not in self._customer_index:
            self._customer_index[score.customer_id] = []
        self._customer_index[score.customer_id].append(score.score_id)
        return score

    async def find_by_id(self, score_id: UUID) -> Optional[CreditScore]:
        return self._scores.get(score_id)

    async def find_by_customer(self, customer_id: str, limit: int = 100) -> List[CreditScore]:
        score_ids = self._customer_index.get(customer_id, [])
        scores = [self._scores[sid] for sid in score_ids if sid in self._scores]
        return sorted(scores, key=lambda x: x.score_date, reverse=True)[:limit]

    async def find_latest_by_customer(self, customer_id: str) -> Optional[CreditScore]:
        scores = await self.find_by_customer(customer_id, limit=1)
        return scores[0] if scores else None

    async def find_by_category(self, category: ScoreCategory, limit: int = 100) -> List[CreditScore]:
        scores = [s for s in self._scores.values() if s.score_category == category]
        return sorted(scores, key=lambda x: x.score_date, reverse=True)[:limit]

    async def find_by_score_range(self, min_score: int, max_score: int, limit: int = 100) -> List[CreditScore]:
        scores = [s for s in self._scores.values() if min_score <= s.score_value <= max_score]
        return sorted(scores, key=lambda x: x.score_value, reverse=True)[:limit]

    async def find_expired(self) -> List[CreditScore]:
        now = datetime.utcnow()
        return [s for s in self._scores.values() if s.valid_until and s.valid_until < now]

    async def update(self, score: CreditScore) -> CreditScore:
        score.updated_at = datetime.utcnow()
        self._scores[score.score_id] = score
        return score

    async def delete(self, score_id: UUID) -> bool:
        if score_id in self._scores:
            del self._scores[score_id]
            return True
        return False

    async def save_request(self, request: CreditScoreRequest) -> CreditScoreRequest:
        self._requests[request.request_id] = request
        return request

    async def find_request_by_id(self, request_id: UUID) -> Optional[CreditScoreRequest]:
        return self._requests.get(request_id)

    async def get_statistics(self) -> Dict[str, Any]:
        total = len(self._scores)
        by_category = {}
        score_sum = 0
        for score in self._scores.values():
            by_category[score.score_category.value] = by_category.get(score.score_category.value, 0) + 1
            score_sum += score.score_value
        return {
            "total_scores": total,
            "by_category": by_category,
            "average_score": score_sum / total if total > 0 else 0
        }

    async def count(self) -> int:
        return len(self._scores)


credit_score_repository = CreditScoreRepository()
