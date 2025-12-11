"""Dimension Weights Configuration"""

from typing import Dict, List, Optional
from decimal import Decimal
from dataclasses import dataclass


@dataclass
class DimensionWeight:
    dimension: str
    weight: Decimal
    description: str
    is_active: bool = True


class DimensionWeights:
    def __init__(self):
        self._weights = {
            "completeness": DimensionWeight(
                dimension="completeness",
                weight=Decimal("0.20"),
                description="Measures whether all required data is present",
            ),
            "accuracy": DimensionWeight(
                dimension="accuracy",
                weight=Decimal("0.25"),
                description="Measures how well data reflects the real world",
            ),
            "consistency": DimensionWeight(
                dimension="consistency",
                weight=Decimal("0.20"),
                description="Measures data uniformity across systems",
            ),
            "timeliness": DimensionWeight(
                dimension="timeliness",
                weight=Decimal("0.15"),
                description="Measures how current and up-to-date data is",
            ),
            "uniqueness": DimensionWeight(
                dimension="uniqueness",
                weight=Decimal("0.10"),
                description="Measures absence of duplicates",
            ),
            "validity": DimensionWeight(
                dimension="validity",
                weight=Decimal("0.10"),
                description="Measures conformance to defined formats and ranges",
            ),
        }
        self._domain_weights: Dict[str, Dict[str, Decimal]] = {}

    def get_weight(self, dimension: str) -> Decimal:
        weight_obj = self._weights.get(dimension)
        return weight_obj.weight if weight_obj else Decimal("0")

    def set_weight(self, dimension: str, weight: Decimal, description: str = "") -> None:
        if dimension in self._weights:
            self._weights[dimension].weight = weight
            if description:
                self._weights[dimension].description = description
        else:
            self._weights[dimension] = DimensionWeight(
                dimension=dimension,
                weight=weight,
                description=description or f"Custom dimension: {dimension}",
            )
        self._normalize_weights()

    def _normalize_weights(self) -> None:
        total = sum(w.weight for w in self._weights.values() if w.is_active)
        if total > 0 and total != Decimal("1"):
            for dimension in self._weights:
                if self._weights[dimension].is_active:
                    self._weights[dimension].weight = self._weights[dimension].weight / total

    def calculate_weighted_score(self, dimension_scores: Dict[str, Decimal]) -> Decimal:
        weighted_sum = Decimal("0")
        total_weight = Decimal("0")

        for dimension, score in dimension_scores.items():
            weight_obj = self._weights.get(dimension)
            if weight_obj and weight_obj.is_active:
                weighted_sum += score * weight_obj.weight
                total_weight += weight_obj.weight

        return weighted_sum / total_weight if total_weight > 0 else Decimal("0")

    def set_domain_weights(self, domain: str, weights: Dict[str, Decimal]) -> None:
        self._domain_weights[domain] = weights

    def get_domain_weights(self, domain: str) -> Optional[Dict[str, Decimal]]:
        return self._domain_weights.get(domain)

    def calculate_domain_score(
        self, domain: str, dimension_scores: Dict[str, Decimal]
    ) -> Decimal:
        domain_weights = self._domain_weights.get(domain)
        if not domain_weights:
            return self.calculate_weighted_score(dimension_scores)

        weighted_sum = Decimal("0")
        total_weight = Decimal("0")

        for dimension, score in dimension_scores.items():
            weight = domain_weights.get(dimension, self.get_weight(dimension))
            weighted_sum += score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else Decimal("0")

    def toggle_dimension(self, dimension: str, is_active: bool) -> None:
        if dimension in self._weights:
            self._weights[dimension].is_active = is_active
            self._normalize_weights()

    def get_active_dimensions(self) -> List[str]:
        return [dim for dim, w in self._weights.items() if w.is_active]

    def get_all_weights(self) -> Dict[str, DimensionWeight]:
        return self._weights.copy()

    def export_config(self) -> Dict[str, Dict[str, any]]:
        return {
            dim: {
                "weight": float(w.weight),
                "description": w.description,
                "is_active": w.is_active,
            }
            for dim, w in self._weights.items()
        }


dimension_weights = DimensionWeights()
