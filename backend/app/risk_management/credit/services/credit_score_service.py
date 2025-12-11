"""Credit Score Service - Credit scoring and assessment"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from ..models.credit_score_models import (
    CreditScore, CreditScoreFactor, CreditScoreHistory,
    CreditScoreRequest, ScoreSimulation, CreditScoreStatistics,
    ScoreType, ScoreCategory, CreditScoreSource
)


class CreditScoreService:
    def __init__(self):
        self._scores: Dict[UUID, CreditScore] = {}
        self._customer_scores: Dict[str, List[UUID]] = {}
        self._requests: Dict[UUID, CreditScoreRequest] = {}
        self._score_factors = self._initialize_factors()

    def _initialize_factors(self) -> Dict[str, CreditScoreFactor]:
        return {
            "payment_history": CreditScoreFactor(
                factor_code="PAY_HIST",
                factor_name="Payment History",
                factor_category="payment",
                impact_type="positive",
                impact_weight=35.0,
                factor_value=None,
                factor_description="History of on-time payments"
            ),
            "credit_utilization": CreditScoreFactor(
                factor_code="UTIL",
                factor_name="Credit Utilization",
                factor_category="utilization",
                impact_type="negative",
                impact_weight=30.0,
                factor_value=None,
                factor_description="Ratio of used credit to available credit"
            ),
            "credit_history_length": CreditScoreFactor(
                factor_code="HIST_LEN",
                factor_name="Credit History Length",
                factor_category="history",
                impact_type="positive",
                impact_weight=15.0,
                factor_value=None,
                factor_description="Length of credit history"
            ),
        }

    def _calculate_category(self, score: int) -> ScoreCategory:
        if score >= 800:
            return ScoreCategory.EXCELLENT
        elif score >= 740:
            return ScoreCategory.GOOD
        elif score >= 670:
            return ScoreCategory.FAIR
        elif score >= 580:
            return ScoreCategory.POOR
        else:
            return ScoreCategory.VERY_POOR

    async def calculate_score(self, customer_id: str, score_type: ScoreType = ScoreType.INTERNAL) -> CreditScore:
        # Simulate score calculation
        base_score = 700
        import random
        score_value = min(850, max(300, base_score + random.randint(-100, 100)))

        score = CreditScore(
            customer_id=customer_id,
            score_type=score_type,
            score_value=score_value,
            score_category=self._calculate_category(score_value),
            positive_factors=["On-time payments", "Low credit utilization"],
            negative_factors=["Short credit history"],
            valid_until=datetime.utcnow() + timedelta(days=30)
        )

        self._scores[score.score_id] = score
        if customer_id not in self._customer_scores:
            self._customer_scores[customer_id] = []
        self._customer_scores[customer_id].append(score.score_id)

        return score

    async def get_score(self, score_id: UUID) -> Optional[CreditScore]:
        return self._scores.get(score_id)

    async def get_customer_score(self, customer_id: str) -> Optional[CreditScore]:
        score_ids = self._customer_scores.get(customer_id, [])
        if score_ids:
            latest_id = score_ids[-1]
            return self._scores.get(latest_id)
        return None

    async def get_score_history(self, customer_id: str) -> CreditScoreHistory:
        score_ids = self._customer_scores.get(customer_id, [])
        scores = [self._scores[sid] for sid in score_ids if sid in self._scores]

        if not scores:
            return CreditScoreHistory(customer_id=customer_id)

        score_values = [s.score_value for s in scores]
        history = CreditScoreHistory(
            customer_id=customer_id,
            scores=scores,
            average_score=sum(score_values) / len(score_values),
            highest_score=max(score_values),
            lowest_score=min(score_values),
            trend="stable" if len(scores) < 2 else (
                "improving" if scores[-1].score_value > scores[-2].score_value else "declining"
            )
        )
        return history

    async def request_score(self, customer_id: str, purpose: str, requested_by: str) -> CreditScoreRequest:
        request = CreditScoreRequest(
            customer_id=customer_id,
            request_type="score_pull",
            purpose=purpose,
            requested_by=requested_by
        )
        self._requests[request.request_id] = request
        return request

    async def simulate_score(self, customer_id: str, scenarios: List[Dict[str, Any]], created_by: str) -> ScoreSimulation:
        current_score = await self.get_customer_score(customer_id)
        current_value = current_score.score_value if current_score else 700

        # Simulate impact
        simulated_change = 0
        for scenario in scenarios:
            if scenario.get("action") == "pay_down_debt":
                simulated_change += 20
            elif scenario.get("action") == "close_account":
                simulated_change -= 10

        simulated_value = min(850, max(300, current_value + simulated_change))

        simulation = ScoreSimulation(
            customer_id=customer_id,
            current_score=current_value,
            simulated_score=simulated_value,
            score_change=simulated_value - current_value,
            simulation_scenarios=scenarios,
            created_by=created_by
        )
        return simulation

    async def get_statistics(self) -> CreditScoreStatistics:
        stats = CreditScoreStatistics(total_scores=len(self._scores))
        for score in self._scores.values():
            stats.by_category[score.score_category.value] = stats.by_category.get(score.score_category.value, 0) + 1
            stats.by_source[score.score_source.value] = stats.by_source.get(score.score_source.value, 0) + 1
        if self._scores:
            stats.average_score = sum(s.score_value for s in self._scores.values()) / len(self._scores)
        return stats


credit_score_service = CreditScoreService()
