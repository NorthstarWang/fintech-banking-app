"""Collateral Repository - Data access layer for collateral"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from ..models.collateral_models import (
    Collateral, CollateralValuation, CollateralAllocation,
    CollateralHaircut, CollateralMonitoring, Guarantee,
    CollateralType, CollateralStatus
)


class CollateralRepository:
    def __init__(self):
        self._collaterals: Dict[UUID, Collateral] = {}
        self._valuations: Dict[UUID, CollateralValuation] = {}
        self._allocations: Dict[UUID, CollateralAllocation] = {}
        self._haircuts: Dict[UUID, CollateralHaircut] = {}
        self._monitoring: Dict[UUID, CollateralMonitoring] = {}
        self._guarantees: Dict[UUID, Guarantee] = {}
        self._owner_index: Dict[str, List[UUID]] = {}
        self._code_index: Dict[str, UUID] = {}

    async def save(self, collateral: Collateral) -> Collateral:
        self._collaterals[collateral.collateral_id] = collateral
        self._code_index[collateral.collateral_code] = collateral.collateral_id
        if collateral.owner_id not in self._owner_index:
            self._owner_index[collateral.owner_id] = []
        if collateral.collateral_id not in self._owner_index[collateral.owner_id]:
            self._owner_index[collateral.owner_id].append(collateral.collateral_id)
        return collateral

    async def find_by_id(self, collateral_id: UUID) -> Optional[Collateral]:
        return self._collaterals.get(collateral_id)

    async def find_by_code(self, code: str) -> Optional[Collateral]:
        cid = self._code_index.get(code)
        if cid:
            return self._collaterals.get(cid)
        return None

    async def find_by_owner(self, owner_id: str) -> List[Collateral]:
        cids = self._owner_index.get(owner_id, [])
        return [self._collaterals[cid] for cid in cids if cid in self._collaterals]

    async def find_by_type(self, col_type: CollateralType) -> List[Collateral]:
        return [c for c in self._collaterals.values() if c.collateral_type == col_type]

    async def find_by_status(self, status: CollateralStatus) -> List[Collateral]:
        return [c for c in self._collaterals.values() if c.status == status]

    async def find_requiring_valuation(self) -> List[Collateral]:
        today = date.today()
        return [c for c in self._collaterals.values() if c.next_valuation_date and c.next_valuation_date <= today]

    async def update(self, collateral: Collateral) -> Collateral:
        collateral.updated_at = datetime.utcnow()
        self._collaterals[collateral.collateral_id] = collateral
        return collateral

    async def save_valuation(self, valuation: CollateralValuation) -> CollateralValuation:
        self._valuations[valuation.valuation_id] = valuation
        return valuation

    async def find_valuations_by_collateral(self, collateral_id: UUID) -> List[CollateralValuation]:
        valuations = [v for v in self._valuations.values() if v.collateral_id == collateral_id]
        return sorted(valuations, key=lambda x: x.valuation_date, reverse=True)

    async def find_latest_valuation(self, collateral_id: UUID) -> Optional[CollateralValuation]:
        valuations = await self.find_valuations_by_collateral(collateral_id)
        return valuations[0] if valuations else None

    async def save_allocation(self, allocation: CollateralAllocation) -> CollateralAllocation:
        self._allocations[allocation.allocation_id] = allocation
        return allocation

    async def find_allocations_by_collateral(self, collateral_id: UUID) -> List[CollateralAllocation]:
        return [a for a in self._allocations.values() if a.collateral_id == collateral_id]

    async def find_allocations_by_facility(self, facility_id: UUID) -> List[CollateralAllocation]:
        return [a for a in self._allocations.values() if a.facility_id == facility_id]

    async def save_haircut(self, haircut: CollateralHaircut) -> CollateralHaircut:
        self._haircuts[haircut.haircut_id] = haircut
        return haircut

    async def find_haircut_by_type(self, col_type: CollateralType) -> Optional[CollateralHaircut]:
        for h in self._haircuts.values():
            if h.collateral_type == col_type:
                return h
        return None

    async def save_monitoring(self, monitoring: CollateralMonitoring) -> CollateralMonitoring:
        self._monitoring[monitoring.monitoring_id] = monitoring
        return monitoring

    async def find_monitoring_by_collateral(self, collateral_id: UUID) -> List[CollateralMonitoring]:
        return [m for m in self._monitoring.values() if m.collateral_id == collateral_id]

    async def save_guarantee(self, guarantee: Guarantee) -> Guarantee:
        self._guarantees[guarantee.guarantee_id] = guarantee
        return guarantee

    async def find_guarantees_by_facility(self, facility_id: UUID) -> List[Guarantee]:
        return [g for g in self._guarantees.values() if g.guaranteed_facility_id == facility_id]

    async def get_statistics(self) -> Dict[str, Any]:
        total_value = sum(c.current_value for c in self._collaterals.values())
        by_type = {}
        for col in self._collaterals.values():
            by_type[col.collateral_type.value] = by_type.get(col.collateral_type.value, 0) + col.current_value
        return {
            "total_collaterals": len(self._collaterals),
            "total_value": total_value,
            "by_type": by_type
        }

    async def count(self) -> int:
        return len(self._collaterals)


collateral_repository = CollateralRepository()
