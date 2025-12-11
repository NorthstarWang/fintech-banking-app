"""Fraud Pattern Repository - Data access layer for fraud patterns"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from ..models.fraud_pattern_models import (
    FraudPattern, PatternMatch, PatternCategory, PatternStatus, RiskLevel
)


class FraudPatternRepository:
    def __init__(self):
        self._patterns: Dict[UUID, FraudPattern] = {}
        self._matches: List[PatternMatch] = []
        self._code_index: Dict[str, UUID] = {}
        self._category_index: Dict[PatternCategory, List[UUID]] = {}

    async def save_pattern(self, pattern: FraudPattern) -> FraudPattern:
        self._patterns[pattern.pattern_id] = pattern
        self._code_index[pattern.pattern_code] = pattern.pattern_id
        if pattern.category not in self._category_index:
            self._category_index[pattern.category] = []
        if pattern.pattern_id not in self._category_index[pattern.category]:
            self._category_index[pattern.category].append(pattern.pattern_id)
        return pattern

    async def find_pattern_by_id(self, pattern_id: UUID) -> Optional[FraudPattern]:
        return self._patterns.get(pattern_id)

    async def find_pattern_by_code(self, pattern_code: str) -> Optional[FraudPattern]:
        pattern_id = self._code_index.get(pattern_code)
        if pattern_id:
            return self._patterns.get(pattern_id)
        return None

    async def find_patterns_by_category(self, category: PatternCategory) -> List[FraudPattern]:
        pattern_ids = self._category_index.get(category, [])
        return [self._patterns[pid] for pid in pattern_ids if pid in self._patterns]

    async def find_active_patterns(self) -> List[FraudPattern]:
        return [p for p in self._patterns.values() if p.status == PatternStatus.ACTIVE]

    async def find_patterns_by_risk_level(self, risk_level: RiskLevel) -> List[FraudPattern]:
        return [p for p in self._patterns.values() if p.risk_level == risk_level]

    async def find_high_risk_patterns(self) -> List[FraudPattern]:
        return [p for p in self._patterns.values() if p.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]

    async def update_pattern(self, pattern: FraudPattern) -> FraudPattern:
        pattern.updated_at = datetime.utcnow()
        self._patterns[pattern.pattern_id] = pattern
        return pattern

    async def delete_pattern(self, pattern_id: UUID) -> bool:
        if pattern_id in self._patterns:
            pattern = self._patterns[pattern_id]
            del self._patterns[pattern_id]
            if pattern.pattern_code in self._code_index:
                del self._code_index[pattern.pattern_code]
            return True
        return False

    async def save_match(self, match: PatternMatch) -> PatternMatch:
        self._matches.append(match)
        pattern = self._patterns.get(match.pattern_id)
        if pattern:
            pattern.match_count += 1
            pattern.last_match_at = datetime.utcnow()
        return match

    async def find_matches_by_pattern(self, pattern_id: UUID, limit: int = 100) -> List[PatternMatch]:
        matches = [m for m in self._matches if m.pattern_id == pattern_id]
        return sorted(matches, key=lambda x: x.matched_at, reverse=True)[:limit]

    async def find_matches_by_entity(self, entity_type: str, entity_id: str, limit: int = 100) -> List[PatternMatch]:
        matches = [m for m in self._matches if m.entity_type == entity_type and m.entity_id == entity_id]
        return sorted(matches, key=lambda x: x.matched_at, reverse=True)[:limit]

    async def find_matches_by_confidence(self, min_confidence: float, limit: int = 100) -> List[PatternMatch]:
        matches = [m for m in self._matches if m.confidence_score >= min_confidence]
        return sorted(matches, key=lambda x: x.confidence_score, reverse=True)[:limit]

    async def find_recent_matches(self, hours: int = 24, limit: int = 500) -> List[PatternMatch]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        matches = [m for m in self._matches if m.matched_at >= cutoff]
        return sorted(matches, key=lambda x: x.matched_at, reverse=True)[:limit]

    async def find_unreviewed_matches(self, limit: int = 100) -> List[PatternMatch]:
        matches = [m for m in self._matches if not m.reviewed]
        return sorted(matches, key=lambda x: x.matched_at, reverse=True)[:limit]

    async def update_match(self, match: PatternMatch) -> PatternMatch:
        for i, m in enumerate(self._matches):
            if m.match_id == match.match_id:
                self._matches[i] = match
                break
        return match

    async def get_pattern_statistics(self) -> Dict[str, Any]:
        total_patterns = len(self._patterns)
        active_patterns = len([p for p in self._patterns.values() if p.status == PatternStatus.ACTIVE])
        by_category = {}
        for pattern in self._patterns.values():
            cat_key = pattern.category.value
            by_category[cat_key] = by_category.get(cat_key, 0) + 1
        by_risk_level = {}
        for pattern in self._patterns.values():
            risk_key = pattern.risk_level.value
            by_risk_level[risk_key] = by_risk_level.get(risk_key, 0) + 1
        today = datetime.utcnow().date()
        matches_today = len([m for m in self._matches if m.matched_at.date() == today])
        return {
            "total_patterns": total_patterns,
            "active_patterns": active_patterns,
            "by_category": by_category,
            "by_risk_level": by_risk_level,
            "total_matches": len(self._matches),
            "matches_today": matches_today
        }

    async def get_all_patterns(self, limit: int = 200, offset: int = 0) -> List[FraudPattern]:
        patterns = sorted(self._patterns.values(), key=lambda x: x.created_at, reverse=True)
        return patterns[offset:offset + limit]

    async def count_patterns(self) -> int:
        return len(self._patterns)


fraud_pattern_repository = FraudPatternRepository()
