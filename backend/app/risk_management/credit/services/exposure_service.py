"""Exposure Service - Credit exposure calculation and management"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from ..models.exposure_models import (
    CreditExposure, ExposureAggregate, ExposureLimit, LargeExposure,
    CounterpartyExposure, ExposureMovement, ExposureStatistics,
    ExposureType, ExposureCategory
)


class ExposureService:
    def __init__(self):
        self._exposures: Dict[UUID, CreditExposure] = {}
        self._aggregates: Dict[UUID, ExposureAggregate] = {}
        self._limits: Dict[UUID, ExposureLimit] = {}
        self._large_exposures: Dict[UUID, LargeExposure] = {}
        self._counterparties: Dict[UUID, CounterpartyExposure] = {}
        self._movements: List[ExposureMovement] = []

    async def create_exposure(
        self, customer_id: str, customer_name: str,
        exposure_type: ExposureType, exposure_category: ExposureCategory,
        gross_exposure: float, limit_amount: float,
        collateral_value: float = 0.0
    ) -> CreditExposure:
        net_exposure = max(0, gross_exposure - collateral_value)
        ccf = 1.0 if exposure_type == ExposureType.FUNDED else 0.5
        ead = gross_exposure * ccf
        utilization = (gross_exposure / limit_amount * 100) if limit_amount > 0 else 0

        exposure = CreditExposure(
            customer_id=customer_id,
            customer_name=customer_name,
            exposure_type=exposure_type,
            exposure_category=exposure_category,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            collateral_value=collateral_value,
            credit_conversion_factor=ccf,
            exposure_at_default=ead,
            drawn_amount=gross_exposure if exposure_type == ExposureType.FUNDED else 0,
            undrawn_amount=limit_amount - gross_exposure,
            limit_amount=limit_amount,
            limit_utilization=utilization,
            risk_weighted_assets=ead * 1.0,
            expected_loss=ead * 0.02 * 0.45
        )
        self._exposures[exposure.exposure_id] = exposure
        return exposure

    async def get_exposure(self, exposure_id: UUID) -> Optional[CreditExposure]:
        return self._exposures.get(exposure_id)

    async def update_exposure(
        self, exposure_id: UUID, updates: Dict[str, Any]
    ) -> Optional[CreditExposure]:
        exposure = self._exposures.get(exposure_id)
        if exposure:
            for key, value in updates.items():
                if hasattr(exposure, key):
                    setattr(exposure, key, value)
            exposure.updated_at = datetime.utcnow()
        return exposure

    async def get_customer_exposures(self, customer_id: str) -> List[CreditExposure]:
        return [e for e in self._exposures.values() if e.customer_id == customer_id]

    async def calculate_aggregate(
        self, aggregation_level: str, aggregation_key: str, aggregation_name: str
    ) -> ExposureAggregate:
        # Filter exposures by aggregation criteria
        filtered_exposures = [
            e for e in self._exposures.values()
            if (aggregation_level == "customer" and e.customer_id == aggregation_key)
        ]

        total_gross = sum(e.gross_exposure for e in filtered_exposures)
        total_net = sum(e.net_exposure for e in filtered_exposures)
        total_ead = sum(e.exposure_at_default for e in filtered_exposures)
        total_rwa = sum(e.risk_weighted_assets for e in filtered_exposures)

        aggregate = ExposureAggregate(
            aggregation_level=aggregation_level,
            aggregation_key=aggregation_key,
            aggregation_name=aggregation_name,
            total_gross_exposure=total_gross,
            total_net_exposure=total_net,
            total_ead=total_ead,
            total_rwa=total_rwa,
            number_of_exposures=len(filtered_exposures),
            weighted_average_pd=0.02,
            weighted_average_lgd=0.45,
            expected_loss=total_ead * 0.02 * 0.45
        )
        self._aggregates[aggregate.aggregate_id] = aggregate
        return aggregate

    async def set_limit(
        self, limit_type: str, limit_key: str, limit_name: str,
        limit_amount: float, approved_by: str
    ) -> ExposureLimit:
        current_exposure = sum(
            e.gross_exposure for e in self._exposures.values()
            if e.customer_id == limit_key
        )
        utilization = (current_exposure / limit_amount * 100) if limit_amount > 0 else 0

        limit = ExposureLimit(
            limit_type=limit_type,
            limit_key=limit_key,
            limit_name=limit_name,
            limit_amount=limit_amount,
            current_exposure=current_exposure,
            available_amount=max(0, limit_amount - current_exposure),
            utilization_percentage=utilization,
            status="breach" if utilization >= 100 else ("warning" if utilization >= 80 else "active"),
            effective_date=date.today(),
            approved_by=approved_by,
            approved_date=datetime.utcnow()
        )
        self._limits[limit.limit_id] = limit
        return limit

    async def get_limit(self, limit_id: UUID) -> Optional[ExposureLimit]:
        return self._limits.get(limit_id)

    async def check_limit(self, limit_id: UUID, proposed_exposure: float) -> Dict[str, Any]:
        limit = self._limits.get(limit_id)
        if not limit:
            return {"allowed": False, "reason": "Limit not found"}

        new_utilization = (limit.current_exposure + proposed_exposure) / limit.limit_amount * 100
        if new_utilization >= 100:
            return {
                "allowed": False,
                "reason": "Would breach limit",
                "available": limit.available_amount,
                "proposed": proposed_exposure
            }
        return {
            "allowed": True,
            "new_utilization": new_utilization,
            "available_after": limit.limit_amount - limit.current_exposure - proposed_exposure
        }

    async def identify_large_exposures(self, capital_base: float) -> List[LargeExposure]:
        large_exposures = []
        customer_exposures: Dict[str, float] = {}

        for exposure in self._exposures.values():
            customer_exposures[exposure.customer_id] = customer_exposures.get(
                exposure.customer_id, 0
            ) + exposure.gross_exposure

        for customer_id, total_exposure in customer_exposures.items():
            pct_of_capital = (total_exposure / capital_base * 100) if capital_base > 0 else 0
            if pct_of_capital >= 10:  # Large exposure threshold
                large_exp = LargeExposure(
                    customer_id=customer_id,
                    customer_name=customer_id,
                    total_exposure=total_exposure,
                    exposure_as_percentage_of_capital=pct_of_capital,
                    breach_status=pct_of_capital > 25,
                    breach_amount=total_exposure - (capital_base * 0.25) if pct_of_capital > 25 else None,
                    reporting_date=date.today()
                )
                large_exposures.append(large_exp)
                self._large_exposures[large_exp.exposure_id] = large_exp

        return large_exposures

    async def record_movement(
        self, exposure_id: UUID, movement_type: str,
        change_amount: float, change_reason: str
    ) -> Optional[ExposureMovement]:
        exposure = self._exposures.get(exposure_id)
        if not exposure:
            return None

        movement = ExposureMovement(
            exposure_id=exposure_id,
            movement_date=date.today(),
            movement_type=movement_type,
            previous_exposure=exposure.gross_exposure,
            new_exposure=exposure.gross_exposure + change_amount,
            change_amount=change_amount,
            change_reason=change_reason
        )
        self._movements.append(movement)
        return movement

    async def get_statistics(self) -> ExposureStatistics:
        stats = ExposureStatistics(
            total_gross_exposure=sum(e.gross_exposure for e in self._exposures.values()),
            total_net_exposure=sum(e.net_exposure for e in self._exposures.values()),
            total_ead=sum(e.exposure_at_default for e in self._exposures.values()),
            total_rwa=sum(e.risk_weighted_assets for e in self._exposures.values()),
            number_of_exposures=len(self._exposures)
        )
        for exposure in self._exposures.values():
            stats.by_type[exposure.exposure_type.value] = stats.by_type.get(
                exposure.exposure_type.value, 0
            ) + exposure.gross_exposure
            stats.by_category[exposure.exposure_category.value] = stats.by_category.get(
                exposure.exposure_category.value, 0
            ) + exposure.gross_exposure
        return stats


exposure_service = ExposureService()
