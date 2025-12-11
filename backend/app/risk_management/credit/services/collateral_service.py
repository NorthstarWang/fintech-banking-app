"""Collateral Service - Collateral and security management"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID
from ..models.collateral_models import (
    Collateral, CollateralValuation, CollateralAllocation,
    CollateralHaircut, CollateralMonitoring, Guarantee,
    CollateralStatistics, CollateralType, CollateralStatus, ValuationType
)


class CollateralService:
    def __init__(self):
        self._collaterals: Dict[UUID, Collateral] = {}
        self._valuations: Dict[UUID, CollateralValuation] = {}
        self._allocations: Dict[UUID, CollateralAllocation] = {}
        self._haircuts: Dict[UUID, CollateralHaircut] = {}
        self._monitoring: Dict[UUID, CollateralMonitoring] = {}
        self._guarantees: Dict[UUID, Guarantee] = {}
        self._counter = 0
        self._initialize_haircuts()

    def _initialize_haircuts(self):
        default_haircuts = [
            (CollateralType.CASH, 0.0, 0.0),
            (CollateralType.SECURITIES, 15.0, 25.0),
            (CollateralType.REAL_ESTATE, 30.0, 40.0),
            (CollateralType.VEHICLE, 35.0, 50.0),
            (CollateralType.EQUIPMENT, 40.0, 55.0),
            (CollateralType.INVENTORY, 50.0, 65.0),
            (CollateralType.RECEIVABLES, 25.0, 40.0),
        ]
        for col_type, standard, stressed in default_haircuts:
            haircut = CollateralHaircut(
                collateral_type=col_type,
                standard_haircut=standard,
                stressed_haircut=stressed,
                total_haircut=standard,
                effective_date=date.today(),
                review_date=date.today() + timedelta(days=365),
                approved_by="system"
            )
            self._haircuts[haircut.haircut_id] = haircut

    def _generate_code(self) -> str:
        self._counter += 1
        return f"COL-{datetime.utcnow().strftime('%Y%m%d')}-{self._counter:06d}"

    def _get_haircut(self, col_type: CollateralType) -> float:
        for haircut in self._haircuts.values():
            if haircut.collateral_type == col_type:
                return haircut.standard_haircut
        return 50.0

    async def register_collateral(
        self, collateral_type: CollateralType, description: str,
        owner_id: str, owner_name: str, original_value: float
    ) -> Collateral:
        haircut = self._get_haircut(collateral_type)
        adjusted_value = original_value * (1 - haircut / 100)

        collateral = Collateral(
            collateral_code=self._generate_code(),
            collateral_type=collateral_type,
            description=description,
            owner_id=owner_id,
            owner_name=owner_name,
            original_value=original_value,
            current_value=original_value,
            haircut_percentage=haircut,
            adjusted_value=adjusted_value,
            available_value=adjusted_value
        )
        self._collaterals[collateral.collateral_id] = collateral
        return collateral

    async def get_collateral(self, collateral_id: UUID) -> Optional[Collateral]:
        return self._collaterals.get(collateral_id)

    async def update_collateral(
        self, collateral_id: UUID, updates: Dict[str, Any]
    ) -> Optional[Collateral]:
        collateral = self._collaterals.get(collateral_id)
        if collateral:
            for key, value in updates.items():
                if hasattr(collateral, key):
                    setattr(collateral, key, value)
            collateral.updated_at = datetime.utcnow()
        return collateral

    async def record_valuation(
        self, collateral_id: UUID, valuation_type: ValuationType,
        market_value: float, forced_sale_value: float,
        valuer_name: str, methodology: str
    ) -> Optional[CollateralValuation]:
        collateral = self._collaterals.get(collateral_id)
        if not collateral:
            return None

        valuation = CollateralValuation(
            collateral_id=collateral_id,
            valuation_type=valuation_type,
            valuation_date=date.today(),
            valuer_name=valuer_name,
            market_value=market_value,
            forced_sale_value=forced_sale_value,
            valuation_methodology=methodology,
            expiry_date=date.today() + timedelta(days=365)
        )
        self._valuations[valuation.valuation_id] = valuation

        # Update collateral value
        collateral.current_value = market_value
        collateral.adjusted_value = market_value * (1 - collateral.haircut_percentage / 100)
        collateral.available_value = collateral.adjusted_value - collateral.total_allocation
        collateral.last_valuation_date = date.today()
        collateral.next_valuation_date = date.today() + timedelta(days=365)

        return valuation

    async def allocate_collateral(
        self, collateral_id: UUID, facility_id: UUID,
        allocation_amount: float, priority_ranking: int = 1
    ) -> Optional[CollateralAllocation]:
        collateral = self._collaterals.get(collateral_id)
        if not collateral:
            return None

        if allocation_amount > collateral.available_value:
            return None

        allocation = CollateralAllocation(
            collateral_id=collateral_id,
            facility_id=facility_id,
            allocation_amount=allocation_amount,
            allocation_percentage=(allocation_amount / collateral.adjusted_value * 100),
            priority_ranking=priority_ranking,
            effective_date=date.today()
        )
        self._allocations[allocation.allocation_id] = allocation

        collateral.linked_facilities.append(facility_id)
        collateral.total_allocation += allocation_amount
        collateral.available_value -= allocation_amount

        return allocation

    async def release_allocation(self, allocation_id: UUID) -> bool:
        allocation = self._allocations.get(allocation_id)
        if not allocation:
            return False

        collateral = self._collaterals.get(allocation.collateral_id)
        if collateral:
            collateral.total_allocation -= allocation.allocation_amount
            collateral.available_value += allocation.allocation_amount
            if allocation.facility_id in collateral.linked_facilities:
                collateral.linked_facilities.remove(allocation.facility_id)

        allocation.status = "released"
        return True

    async def monitor_collateral(
        self, collateral_id: UUID, monitored_by: str
    ) -> Optional[CollateralMonitoring]:
        collateral = self._collaterals.get(collateral_id)
        if not collateral:
            return None

        value_change = 0.0
        if collateral.original_value > 0:
            value_change = ((collateral.current_value - collateral.original_value) / collateral.original_value) * 100

        ltv = (collateral.total_allocation / collateral.current_value * 100) if collateral.current_value > 0 else 0
        margin_call = ltv > 80

        monitoring = CollateralMonitoring(
            collateral_id=collateral_id,
            monitoring_date=date.today(),
            value_change_percentage=value_change,
            ltv_ratio=ltv,
            margin_call_triggered=margin_call,
            margin_call_amount=(collateral.total_allocation - collateral.current_value * 0.8) if margin_call else None,
            insurance_status="valid" if collateral.insurance_expiry and collateral.insurance_expiry > date.today() else "expired",
            monitored_by=monitored_by
        )
        self._monitoring[monitoring.monitoring_id] = monitoring
        return monitoring

    async def register_guarantee(
        self, guarantee_type: str, guarantor_id: str, guarantor_name: str,
        guaranteed_facility_id: UUID, guarantee_amount: float,
        effective_date: date, expiry_date: date
    ) -> Guarantee:
        guarantee = Guarantee(
            guarantee_type=guarantee_type,
            guarantor_id=guarantor_id,
            guarantor_name=guarantor_name,
            guaranteed_facility_id=guaranteed_facility_id,
            guarantee_amount=guarantee_amount,
            guarantee_percentage=100.0,
            effective_date=effective_date,
            expiry_date=expiry_date
        )
        self._guarantees[guarantee.guarantee_id] = guarantee
        return guarantee

    async def get_customer_collaterals(self, customer_id: str) -> List[Collateral]:
        return [c for c in self._collaterals.values() if c.owner_id == customer_id]

    async def get_statistics(self) -> CollateralStatistics:
        stats = CollateralStatistics(
            total_collateral_count=len(self._collaterals),
            total_original_value=sum(c.original_value for c in self._collaterals.values()),
            total_current_value=sum(c.current_value for c in self._collaterals.values()),
            total_adjusted_value=sum(c.adjusted_value for c in self._collaterals.values())
        )
        for collateral in self._collaterals.values():
            stats.by_type[collateral.collateral_type.value] = stats.by_type.get(
                collateral.collateral_type.value, 0
            ) + collateral.current_value
            stats.by_status[collateral.status.value] = stats.by_status.get(
                collateral.status.value, 0
            ) + 1
        if self._collaterals:
            stats.average_haircut = sum(c.haircut_percentage for c in self._collaterals.values()) / len(self._collaterals)
        return stats


collateral_service = CollateralService()
