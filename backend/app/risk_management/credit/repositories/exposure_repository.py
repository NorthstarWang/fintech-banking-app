"""Exposure Repository - Data access layer for credit exposures"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from ..models.exposure_models import (
    CreditExposure, ExposureAggregate, ExposureLimit,
    LargeExposure, CounterpartyExposure, ExposureMovement,
    ExposureType, ExposureCategory
)


class ExposureRepository:
    def __init__(self):
        self._exposures: Dict[UUID, CreditExposure] = {}
        self._aggregates: Dict[UUID, ExposureAggregate] = {}
        self._limits: Dict[UUID, ExposureLimit] = {}
        self._large_exposures: Dict[UUID, LargeExposure] = {}
        self._counterparties: Dict[UUID, CounterpartyExposure] = {}
        self._movements: List[ExposureMovement] = []
        self._customer_index: Dict[str, List[UUID]] = {}

    async def save(self, exposure: CreditExposure) -> CreditExposure:
        self._exposures[exposure.exposure_id] = exposure
        if exposure.customer_id not in self._customer_index:
            self._customer_index[exposure.customer_id] = []
        if exposure.exposure_id not in self._customer_index[exposure.customer_id]:
            self._customer_index[exposure.customer_id].append(exposure.exposure_id)
        return exposure

    async def find_by_id(self, exposure_id: UUID) -> Optional[CreditExposure]:
        return self._exposures.get(exposure_id)

    async def find_by_customer(self, customer_id: str) -> List[CreditExposure]:
        exposure_ids = self._customer_index.get(customer_id, [])
        return [self._exposures[eid] for eid in exposure_ids if eid in self._exposures]

    async def find_by_type(self, exposure_type: ExposureType) -> List[CreditExposure]:
        return [e for e in self._exposures.values() if e.exposure_type == exposure_type]

    async def find_by_category(self, category: ExposureCategory) -> List[CreditExposure]:
        return [e for e in self._exposures.values() if e.exposure_category == category]

    async def update(self, exposure: CreditExposure) -> CreditExposure:
        exposure.updated_at = datetime.utcnow()
        self._exposures[exposure.exposure_id] = exposure
        return exposure

    async def save_aggregate(self, aggregate: ExposureAggregate) -> ExposureAggregate:
        self._aggregates[aggregate.aggregate_id] = aggregate
        return aggregate

    async def find_aggregates_by_level(self, level: str) -> List[ExposureAggregate]:
        return [a for a in self._aggregates.values() if a.aggregation_level == level]

    async def save_limit(self, limit: ExposureLimit) -> ExposureLimit:
        self._limits[limit.limit_id] = limit
        return limit

    async def find_limit_by_id(self, limit_id: UUID) -> Optional[ExposureLimit]:
        return self._limits.get(limit_id)

    async def find_limits_by_type(self, limit_type: str) -> List[ExposureLimit]:
        return [l for l in self._limits.values() if l.limit_type == limit_type]

    async def find_breached_limits(self) -> List[ExposureLimit]:
        return [l for l in self._limits.values() if l.status == "breach"]

    async def save_large_exposure(self, large_exp: LargeExposure) -> LargeExposure:
        self._large_exposures[large_exp.exposure_id] = large_exp
        return large_exp

    async def find_large_exposures(self) -> List[LargeExposure]:
        return list(self._large_exposures.values())

    async def save_counterparty(self, counterparty: CounterpartyExposure) -> CounterpartyExposure:
        self._counterparties[counterparty.counterparty_id] = counterparty
        return counterparty

    async def find_counterparty_by_id(self, counterparty_id: UUID) -> Optional[CounterpartyExposure]:
        return self._counterparties.get(counterparty_id)

    async def save_movement(self, movement: ExposureMovement) -> ExposureMovement:
        self._movements.append(movement)
        return movement

    async def find_movements_by_exposure(self, exposure_id: UUID) -> List[ExposureMovement]:
        return [m for m in self._movements if m.exposure_id == exposure_id]

    async def get_statistics(self) -> Dict[str, Any]:
        total_gross = sum(e.gross_exposure for e in self._exposures.values())
        total_net = sum(e.net_exposure for e in self._exposures.values())
        by_type = {}
        for exp in self._exposures.values():
            by_type[exp.exposure_type.value] = by_type.get(exp.exposure_type.value, 0) + exp.gross_exposure
        return {
            "total_gross_exposure": total_gross,
            "total_net_exposure": total_net,
            "number_of_exposures": len(self._exposures),
            "by_type": by_type
        }

    async def count(self) -> int:
        return len(self._exposures)


exposure_repository = ExposureRepository()
