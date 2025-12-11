"""Behavior Service - Behavioral analysis for fraud detection"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from ..models.behavior_models import (
    BehaviorPattern, BehaviorEvent, BehaviorAnomaly,
    BehaviorScore, BehaviorCategory, AnomalyType, BehaviorStatistics
)


class BehaviorService:
    def __init__(self):
        self._patterns: Dict[str, BehaviorPattern] = {}
        self._events: List[BehaviorEvent] = []
        self._anomalies: Dict[UUID, BehaviorAnomaly] = {}
        self._scores: Dict[str, BehaviorScore] = {}

    async def create_pattern(self, customer_id: str) -> BehaviorPattern:
        pattern = BehaviorPattern(
            customer_id=customer_id,
            pattern_type="baseline",
            profile_start_date=datetime.utcnow() - timedelta(days=90),
            profile_end_date=datetime.utcnow()
        )
        self._patterns[customer_id] = pattern
        return pattern

    async def get_pattern(self, customer_id: str) -> Optional[BehaviorPattern]:
        return self._patterns.get(customer_id)

    async def record_event(self, customer_id: str, event_type: str, category: BehaviorCategory, event_data: Dict[str, Any]) -> BehaviorEvent:
        event = BehaviorEvent(
            customer_id=customer_id,
            event_type=event_type,
            category=category,
            event_data=event_data
        )
        anomaly_result = await self._check_for_anomalies(customer_id, event)
        event.is_anomalous = anomaly_result["is_anomalous"]
        event.anomaly_score = anomaly_result["score"]
        event.anomaly_types = anomaly_result["types"]
        self._events.append(event)
        return event

    async def _check_for_anomalies(self, customer_id: str, event: BehaviorEvent) -> Dict[str, Any]:
        pattern = self._patterns.get(customer_id)
        if not pattern:
            return {"is_anomalous": False, "score": 0.0, "types": []}
        anomaly_types = []
        score = 0.0
        hour = event.timestamp.hour
        if pattern.typical_login_times and hour not in pattern.typical_login_times:
            anomaly_types.append(AnomalyType.TIME_ANOMALY)
            score += 20.0
        if event.device_id and pattern.typical_devices:
            if event.device_id not in pattern.typical_devices:
                anomaly_types.append(AnomalyType.DEVICE_ANOMALY)
                score += 25.0
        return {
            "is_anomalous": len(anomaly_types) > 0,
            "score": min(score, 100.0),
            "types": anomaly_types
        }

    async def record_anomaly(self, customer_id: str, event_id: UUID, anomaly_type: AnomalyType, description: str) -> BehaviorAnomaly:
        anomaly = BehaviorAnomaly(
            customer_id=customer_id,
            event_id=event_id,
            anomaly_type=anomaly_type,
            description=description,
            severity="medium"
        )
        self._anomalies[anomaly.anomaly_id] = anomaly
        return anomaly

    async def calculate_behavior_score(self, customer_id: str) -> BehaviorScore:
        now = datetime.utcnow()
        customer_anomalies = [a for a in self._anomalies.values() if a.customer_id == customer_id]
        recent_anomalies_24h = len([a for a in customer_anomalies if (now - a.detected_at).total_seconds() < 86400])
        recent_anomalies_7d = len([a for a in customer_anomalies if (now - a.detected_at).total_seconds() < 604800])
        score = 100.0 - (recent_anomalies_24h * 10) - (recent_anomalies_7d * 2)
        score = max(score, 0.0)
        behavior_score = BehaviorScore(
            customer_id=customer_id,
            overall_score=score,
            anomaly_count_24h=recent_anomalies_24h,
            anomaly_count_7d=recent_anomalies_7d,
            risk_level="high" if score < 50 else "medium" if score < 70 else "low",
            valid_until=now + timedelta(hours=24)
        )
        self._scores[customer_id] = behavior_score
        return behavior_score

    async def get_statistics(self) -> BehaviorStatistics:
        return BehaviorStatistics(
            total_profiles=len(self._patterns),
            anomalies_detected_today=len([a for a in self._anomalies.values() if a.detected_at.date() == datetime.utcnow().date()]),
            average_behavior_score=sum(s.overall_score for s in self._scores.values()) / max(len(self._scores), 1)
        )


behavior_service = BehaviorService()
