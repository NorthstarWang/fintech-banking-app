"""FX Risk Service - Foreign exchange risk management service"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from ..models.fx_risk_models import (
    FXPosition, FXExposure, FXRate, FXVolatilitySurface,
    FXScenario, FXRiskStatistics, FXPositionType
)


class FXRiskService:
    def __init__(self):
        self._positions: Dict[UUID, FXPosition] = {}
        self._exposures: Dict[UUID, FXExposure] = {}
        self._rates: Dict[UUID, FXRate] = {}
        self._vol_surfaces: Dict[UUID, FXVolatilitySurface] = {}
        self._scenarios: Dict[UUID, FXScenario] = {}

    async def create_position(
        self, position_type: FXPositionType, currency_pair: str,
        notional_amount: float, direction: str, spot_rate: float,
        portfolio_id: UUID, value_date: date
    ) -> FXPosition:
        base_ccy, quote_ccy = currency_pair[:3], currency_pair[3:]
        position = FXPosition(
            position_type=position_type,
            currency_pair=currency_pair,
            base_currency=base_ccy,
            quote_currency=quote_ccy,
            notional_amount=notional_amount,
            direction=direction,
            spot_rate=spot_rate,
            value_date=value_date,
            portfolio_id=portfolio_id,
            delta=1.0 if position_type == FXPositionType.SPOT else 0.95
        )
        self._positions[position.position_id] = position
        return position

    async def get_position(self, position_id: UUID) -> Optional[FXPosition]:
        return self._positions.get(position_id)

    async def calculate_exposure(self, currency: str) -> FXExposure:
        long_amount = sum(
            p.notional_amount for p in self._positions.values()
            if p.base_currency == currency and p.direction == "long"
        )
        short_amount = sum(
            p.notional_amount for p in self._positions.values()
            if p.base_currency == currency and p.direction == "short"
        )

        exposure = FXExposure(
            currency=currency,
            gross_long=long_amount,
            gross_short=short_amount,
            net_position=long_amount - short_amount,
            spot_equivalent=long_amount - short_amount,
            delta_equivalent=(long_amount - short_amount) * 0.95,
            var_contribution=abs(long_amount - short_amount) * 0.02,
            stress_loss=abs(long_amount - short_amount) * 0.1,
            as_of_date=date.today()
        )
        self._exposures[exposure.exposure_id] = exposure
        return exposure

    async def update_rate(
        self, currency_pair: str, spot_rate: float,
        bid_rate: float, ask_rate: float, source: str
    ) -> FXRate:
        base_ccy, quote_ccy = currency_pair[:3], currency_pair[3:]
        rate = FXRate(
            currency_pair=currency_pair,
            base_currency=base_ccy,
            quote_currency=quote_ccy,
            spot_rate=spot_rate,
            bid_rate=bid_rate,
            ask_rate=ask_rate,
            mid_rate=(bid_rate + ask_rate) / 2,
            volatility=0.1,
            rate_date=date.today(),
            rate_time=datetime.utcnow(),
            source=source
        )
        self._rates[rate.rate_id] = rate

        # Update position MTM
        for position in self._positions.values():
            if position.currency_pair == currency_pair:
                position.mtm_value = position.notional_amount * (spot_rate - position.spot_rate)
                if position.direction == "short":
                    position.mtm_value = -position.mtm_value
                position.unrealized_pnl = position.mtm_value

        return rate

    async def create_vol_surface(
        self, currency_pair: str, tenors: List[str],
        deltas: List[float], volatilities: List[List[float]]
    ) -> FXVolatilitySurface:
        atm_vols = {t: vols[len(vols) // 2] for t, vols in zip(tenors, volatilities)}

        surface = FXVolatilitySurface(
            currency_pair=currency_pair,
            surface_date=date.today(),
            tenors=tenors,
            deltas=deltas,
            volatilities=volatilities,
            atm_vols=atm_vols
        )
        self._vol_surfaces[surface.surface_id] = surface
        return surface

    async def run_scenario(
        self, scenario_name: str, scenario_type: str,
        rate_shocks: Dict[str, float], vol_shocks: Dict[str, float]
    ) -> FXScenario:
        pnl_impact = 0
        for position in self._positions.values():
            shock = rate_shocks.get(position.currency_pair, 0)
            pnl = position.notional_amount * shock
            if position.direction == "short":
                pnl = -pnl
            pnl_impact += pnl

        scenario = FXScenario(
            scenario_name=scenario_name,
            scenario_type=scenario_type,
            rate_shocks=rate_shocks,
            vol_shocks=vol_shocks,
            pnl_impact=pnl_impact,
            var_impact=pnl_impact * 0.1
        )
        self._scenarios[scenario.scenario_id] = scenario
        return scenario

    async def get_portfolio_positions(self, portfolio_id: UUID) -> List[FXPosition]:
        return [p for p in self._positions.values() if p.portfolio_id == portfolio_id]

    async def get_statistics(self) -> FXRiskStatistics:
        stats = FXRiskStatistics(
            total_positions=len(self._positions),
            total_notional=sum(p.notional_amount for p in self._positions.values()),
            net_fx_exposure=sum(
                p.notional_amount if p.direction == "long" else -p.notional_amount
                for p in self._positions.values()
            )
        )
        for position in self._positions.values():
            stats.by_currency[position.base_currency] = stats.by_currency.get(
                position.base_currency, 0
            ) + position.notional_amount
        return stats


fx_risk_service = FXRiskService()
