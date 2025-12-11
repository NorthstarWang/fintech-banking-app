"""Behavior Repository - Data access layer for behavioral analysis"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from ..models.behavior_models import (
    BehaviorPattern, BehaviorEvent, BehaviorAnomaly,
    BehaviorScore, BehaviorCategory, AnomalyType
)


class BehaviorRepository:
    def __init__(self):
        self._patterns: Dict[str, BehaviorPattern] = {}
        self._events: List[BehaviorEvent] = []
        self._anomalies: Dict[UUID, BehaviorAnomaly] = {}
        self._scores: Dict[str, BehaviorScore] = {}
        self._customer_event_index: Dict[str, List[int]] = {}

    async def save_pattern(self, pattern: BehaviorPattern) -> BehaviorPattern:
        self._patterns[pattern.customer_id] = pattern
        return pattern

    async def find_pattern_by_customer(self, customer_id: str) -> Optional[BehaviorPattern]:
        return self._patterns.get(customer_id)

    async def update_pattern(self, pattern: BehaviorPattern) -> BehaviorPattern:
        pattern.last_updated = datetime.utcnow()
        self._patterns[pattern.customer_id] = pattern
        return pattern

    async def delete_pattern(self, customer_id: str) -> bool:
        if customer_id in self._patterns:
            del self._patterns[customer_id]
            return True
        return False

    async def save_event(self, event: BehaviorEvent) -> BehaviorEvent:
        event_index = len(self._events)
        self._events.append(event)
        if event.customer_id not in self._customer_event_index:
            self._customer_event_index[event.customer_id] = []
        self._customer_event_index[event.customer_id].append(event_index)
        return event

    async def find_events_by_customer(self, customer_id: str, limit: int = 100) -> List[BehaviorEvent]:
        event_indices = self._customer_event_index.get(customer_id, [])
        events = [self._events[i] for i in event_indices if i < len(self._events)]
        return sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def find_events_by_category(self, category: BehaviorCategory, limit: int = 100) -> List[BehaviorEvent]:
        events = [e for e in self._events if e.category == category]
        return sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def find_anomalous_events(self, limit: int = 100) -> List[BehaviorEvent]:
        events = [e for e in self._events if e.is_anomalous]
        return sorted(events, key=lambda x: x.anomaly_score, reverse=True)[:limit]

    async def find_recent_events(self, hours: int = 24, limit: int = 500) -> List[BehaviorEvent]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        events = [e for e in self._events if e.timestamp >= cutoff]
        return sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def save_anomaly(self, anomaly: BehaviorAnomaly) -> BehaviorAnomaly:
        self._anomalies[anomaly.anomaly_id] = anomaly
        return anomaly

    async def find_anomaly_by_id(self, anomaly_id: UUID) -> Optional[BehaviorAnomaly]:
        return self._anomalies.get(anomaly_id)

    async def find_anomalies_by_customer(self, customer_id: str, limit: int = 100) -> List[BehaviorAnomaly]:
        anomalies = [a for a in self._anomalies.values() if a.customer_id == customer_id]
        return sorted(anomalies, key=lambda x: x.detected_at, reverse=True)[:limit]

    async def find_anomalies_by_type(self, anomaly_type: AnomalyType, limit: int = 100) -> List[BehaviorAnomaly]:
        anomalies = [a for a in self._anomalies.values() if a.anomaly_type == anomaly_type]
        return sorted(anomalies, key=lambda x: x.detected_at, reverse=True)[:limit]

    async def find_unresolved_anomalies(self, limit: int = 100) -> List[BehaviorAnomaly]:
        anomalies = [a for a in self._anomalies.values() if not a.resolved]
        return sorted(anomalies, key=lambda x: x.detected_at, reverse=True)[:limit]

    async def find_recent_anomalies(self, hours: int = 24, limit: int = 100) -> List[BehaviorAnomaly]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        anomalies = [a for a in self._anomalies.values() if a.detected_at >= cutoff]
        return sorted(anomalies, key=lambda x: x.detected_at, reverse=True)[:limit]

    async def update_anomaly(self, anomaly: BehaviorAnomaly) -> BehaviorAnomaly:
        self._anomalies[anomaly.anomaly_id] = anomaly
        return anomaly

    async def resolve_anomaly(self, anomaly_id: UUID, resolution: str, resolved_by: str) -> Optional[BehaviorAnomaly]:
        anomaly = self._anomalies.get(anomaly_id)
        if anomaly:
            anomaly.resolved = True
            anomaly.resolution = resolution
            anomaly.resolved_by = resolved_by
            anomaly.resolved_at = datetime.utcnow()
        return anomaly

    async def save_score(self, score: BehaviorScore) -> BehaviorScore:
        self._scores[score.customer_id] = score
        return score

    async def find_score_by_customer(self, customer_id: str) -> Optional[BehaviorScore]:
        return self._scores.get(customer_id)

    async def find_high_risk_scores(self, threshold: float = 50.0) -> List[BehaviorScore]:
        return [s for s in self._scores.values() if s.overall_score < threshold]

    async def get_behavior_statistics(self) -> Dict[str, Any]:
        now = datetime.utcnow()
        today_cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return {
            "total_patterns": len(self._patterns),
            "total_events": len(self._events),
            "events_today": len([e for e in self._events if e.timestamp >= today_cutoff]),
            "total_anomalies": len(self._anomalies),
            "unresolved_anomalies": len([a for a in self._anomalies.values() if not a.resolved]),
            "anomalies_today": len([a for a in self._anomalies.values() if a.detected_at >= today_cutoff])
        }

    async def count_patterns(self) -> int:
        return len(self._patterns)


behavior_repository = BehaviorRepository()
