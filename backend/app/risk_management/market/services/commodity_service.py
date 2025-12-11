"""Commodity Service - Commodity risk management service"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from ..models.commodity_models import (
    CommodityPosition, CommodityCurve, CommodityExposure,
    CommodityScenario, CommodityRiskStatistics,
    CommodityType, CommodityPositionType
)


class CommodityService:
    def __init__(self):
        self._positions: Dict[UUID, CommodityPosition] = {}
        self._curves: Dict[UUID, CommodityCurve] = {}
        self._exposures: Dict[UUID, CommodityExposure] = {}
        self._scenarios: Dict[UUID, CommodityScenario] = {}

    async def create_position(
        self, commodity_type: CommodityType, position_type: CommodityPositionType,
        commodity_name: str, contract_code: str, quantity: float, unit: str,
        direction: str, entry_price: float, current_price: float, portfolio_id: UUID
    ) -> CommodityPosition:
        market_value = quantity * current_price
        pnl = quantity * (current_price - entry_price)
        if direction == "short":
            pnl = -pnl

        position = CommodityPosition(
            commodity_type=commodity_type,
            position_type=position_type,
            commodity_name=commodity_name,
            contract_code=contract_code,
            quantity=quantity,
            unit=unit,
            direction=direction,
            entry_price=entry_price,
            current_price=current_price,
            market_value=market_value,
            unrealized_pnl=pnl,
            portfolio_id=portfolio_id
        )
        self._positions[position.position_id] = position
        return position

    async def get_position(self, position_id: UUID) -> Optional[CommodityPosition]:
        return self._positions.get(position_id)

    async def create_curve(
        self, commodity_name: str, commodity_type: CommodityType,
        contract_months: List[str], prices: List[float]
    ) -> CommodityCurve:
        # Determine curve shape
        if len(prices) >= 2:
            if prices[-1] > prices[0]:
                shape = "contango"
            elif prices[-1] < prices[0]:
                shape = "backwardation"
            else:
                shape = "flat"
        else:
            shape = "flat"

        curve = CommodityCurve(
            commodity_name=commodity_name,
            commodity_type=commodity_type,
            curve_date=date.today(),
            contract_months=contract_months,
            prices=prices,
            curve_shape=shape,
            roll_yield=(prices[0] - prices[1]) / prices[0] if len(prices) >= 2 and prices[0] > 0 else 0,
            convenience_yield=0.02,
            storage_cost=0.01
        )
        self._curves[curve.curve_id] = curve
        return curve

    async def calculate_exposure(
        self, commodity_type: CommodityType, commodity_name: str
    ) -> CommodityExposure:
        positions = [
            p for p in self._positions.values()
            if p.commodity_type == commodity_type and p.commodity_name == commodity_name
        ]

        long_amount = sum(p.market_value for p in positions if p.direction == "long")
        short_amount = sum(p.market_value for p in positions if p.direction == "short")

        exposure = CommodityExposure(
            commodity_type=commodity_type,
            commodity_name=commodity_name,
            gross_long=long_amount,
            gross_short=short_amount,
            net_position=long_amount - short_amount,
            notional_value=long_amount + short_amount,
            delta_equivalent=(long_amount - short_amount) * 0.95,
            var_contribution=abs(long_amount - short_amount) * 0.03,
            stress_loss=abs(long_amount - short_amount) * 0.15,
            as_of_date=date.today()
        )
        self._exposures[exposure.exposure_id] = exposure
        return exposure

    async def run_scenario(
        self, scenario_name: str, scenario_type: str,
        price_shocks: Dict[str, float], volatility_shocks: Dict[str, float]
    ) -> CommodityScenario:
        pnl_impact = 0
        for position in self._positions.values():
            shock = price_shocks.get(position.commodity_name, 0)
            impact = position.market_value * shock
            if position.direction == "short":
                impact = -impact
            pnl_impact += impact

        scenario = CommodityScenario(
            scenario_name=scenario_name,
            scenario_type=scenario_type,
            price_shocks=price_shocks,
            volatility_shocks=volatility_shocks,
            pnl_impact=pnl_impact,
            var_impact=pnl_impact * 0.1
        )
        self._scenarios[scenario.scenario_id] = scenario
        return scenario

    async def get_portfolio_positions(self, portfolio_id: UUID) -> List[CommodityPosition]:
        return [p for p in self._positions.values() if p.portfolio_id == portfolio_id]

    async def get_statistics(self) -> CommodityRiskStatistics:
        stats = CommodityRiskStatistics(
            total_positions=len(self._positions),
            total_notional=sum(p.market_value for p in self._positions.values())
        )
        for position in self._positions.values():
            stats.by_type[position.commodity_type.value] = stats.by_type.get(
                position.commodity_type.value, 0
            ) + position.market_value
        return stats


commodity_service = CommodityService()
