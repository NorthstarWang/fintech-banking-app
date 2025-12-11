"""Greeks Service - Options greeks calculation service"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
import math
from ..models.greeks_models import (
    OptionPosition, GreeksCalculation, PortfolioGreeks,
    GreeksLimit, GreeksSensitivity, GreeksStatistics,
    OptionType, OptionStyle
)


class GreeksService:
    def __init__(self):
        self._positions: Dict[UUID, OptionPosition] = {}
        self._calculations: Dict[UUID, GreeksCalculation] = {}
        self._portfolio_greeks: Dict[UUID, PortfolioGreeks] = {}
        self._limits: Dict[UUID, GreeksLimit] = {}
        self._sensitivities: Dict[UUID, GreeksSensitivity] = {}

    def _black_scholes_greeks(
        self, S: float, K: float, T: float, r: float, sigma: float, option_type: OptionType
    ) -> Dict[str, float]:
        """Calculate Black-Scholes greeks"""
        if T <= 0 or sigma <= 0:
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}

        d1 = (math.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        # Normal CDF approximation
        def norm_cdf(x):
            return 0.5 * (1 + math.erf(x / math.sqrt(2)))

        def norm_pdf(x):
            return math.exp(-x ** 2 / 2) / math.sqrt(2 * math.pi)

        if option_type == OptionType.CALL:
            delta = norm_cdf(d1)
            rho = K * T * math.exp(-r * T) * norm_cdf(d2) / 100
        else:
            delta = norm_cdf(d1) - 1
            rho = -K * T * math.exp(-r * T) * norm_cdf(-d2) / 100

        gamma = norm_pdf(d1) / (S * sigma * math.sqrt(T))
        vega = S * norm_pdf(d1) * math.sqrt(T) / 100
        theta = -(S * norm_pdf(d1) * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * (
            norm_cdf(d2) if option_type == OptionType.CALL else norm_cdf(-d2)
        )
        theta = theta / 365  # Daily theta

        return {
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "rho": rho
        }

    async def create_position(
        self, underlying: str, underlying_type: str, option_type: OptionType,
        option_style: OptionStyle, strike_price: float, expiry_date: date,
        quantity: float, direction: str, premium: float, underlying_price: float,
        implied_volatility: float, portfolio_id: UUID
    ) -> OptionPosition:
        time_to_expiry = (expiry_date - date.today()).days / 365
        intrinsic = max(0, underlying_price - strike_price) if option_type == OptionType.CALL else max(0, strike_price - underlying_price)
        time_value = premium - intrinsic

        position = OptionPosition(
            underlying=underlying,
            underlying_type=underlying_type,
            option_type=option_type,
            option_style=option_style,
            strike_price=strike_price,
            expiry_date=expiry_date,
            quantity=quantity,
            direction=direction,
            premium=premium,
            current_price=premium,
            intrinsic_value=intrinsic,
            time_value=max(0, time_value),
            underlying_price=underlying_price,
            implied_volatility=implied_volatility,
            portfolio_id=portfolio_id
        )
        self._positions[position.position_id] = position
        return position

    async def calculate_greeks(
        self, position_id: UUID, risk_free_rate: float = 0.05
    ) -> Optional[GreeksCalculation]:
        position = self._positions.get(position_id)
        if not position:
            return None

        time_to_expiry = max(0.001, (position.expiry_date - date.today()).days / 365)

        greeks = self._black_scholes_greeks(
            S=position.underlying_price,
            K=position.strike_price,
            T=time_to_expiry,
            r=risk_free_rate,
            sigma=position.implied_volatility,
            option_type=position.option_type
        )

        multiplier = position.quantity if position.direction == "long" else -position.quantity

        calculation = GreeksCalculation(
            position_id=position_id,
            calculation_date=date.today(),
            delta=greeks["delta"] * multiplier,
            gamma=greeks["gamma"] * multiplier,
            theta=greeks["theta"] * multiplier,
            vega=greeks["vega"] * multiplier,
            rho=greeks["rho"] * multiplier,
            dollar_delta=greeks["delta"] * position.underlying_price * position.quantity,
            dollar_gamma=greeks["gamma"] * position.underlying_price ** 2 * 0.01 * position.quantity,
            dollar_theta=greeks["theta"] * position.quantity,
            dollar_vega=greeks["vega"] * position.quantity
        )
        self._calculations[calculation.calculation_id] = calculation
        return calculation

    async def calculate_portfolio_greeks(self, portfolio_id: UUID) -> PortfolioGreeks:
        positions = [p for p in self._positions.values() if p.portfolio_id == portfolio_id]

        total_delta = total_gamma = total_theta = total_vega = total_rho = 0
        by_underlying = {}

        for position in positions:
            calc = await self.calculate_greeks(position.position_id)
            if calc:
                total_delta += calc.delta
                total_gamma += calc.gamma
                total_theta += calc.theta
                total_vega += calc.vega
                total_rho += calc.rho

                if position.underlying not in by_underlying:
                    by_underlying[position.underlying] = {"delta": 0, "gamma": 0, "vega": 0}
                by_underlying[position.underlying]["delta"] += calc.delta
                by_underlying[position.underlying]["gamma"] += calc.gamma
                by_underlying[position.underlying]["vega"] += calc.vega

        portfolio_greeks = PortfolioGreeks(
            portfolio_id=portfolio_id,
            calculation_date=date.today(),
            total_delta=total_delta,
            total_gamma=total_gamma,
            total_theta=total_theta,
            total_vega=total_vega,
            total_rho=total_rho,
            net_delta=total_delta,
            net_gamma=total_gamma,
            gamma_exposure=abs(total_gamma) * 100,
            vega_exposure=abs(total_vega) * 100,
            theta_decay=total_theta,
            by_underlying=by_underlying
        )
        self._portfolio_greeks[portfolio_id] = portfolio_greeks
        return portfolio_greeks

    async def set_limit(
        self, portfolio_id: UUID, greek_type: str,
        limit_amount: float, approved_by: str
    ) -> GreeksLimit:
        limit = GreeksLimit(
            portfolio_id=portfolio_id,
            greek_type=greek_type,
            limit_amount=limit_amount,
            current_value=0,
            utilization_percentage=0,
            effective_date=date.today(),
            approved_by=approved_by
        )
        self._limits[limit.limit_id] = limit
        return limit

    async def calculate_sensitivity(
        self, portfolio_id: UUID, underlying_move_pct: float,
        vol_move_pct: float, time_decay_days: int
    ) -> GreeksSensitivity:
        greeks = self._portfolio_greeks.get(portfolio_id)
        if not greeks:
            greeks = await self.calculate_portfolio_greeks(portfolio_id)

        delta_pnl = greeks.total_delta * underlying_move_pct
        gamma_pnl = 0.5 * greeks.total_gamma * underlying_move_pct ** 2
        vega_pnl = greeks.total_vega * vol_move_pct
        theta_pnl = greeks.total_theta * time_decay_days

        sensitivity = GreeksSensitivity(
            portfolio_id=portfolio_id,
            analysis_date=date.today(),
            underlying_move_percentage=underlying_move_pct,
            delta_pnl=delta_pnl,
            gamma_pnl=gamma_pnl,
            total_pnl=delta_pnl + gamma_pnl,
            vol_move_percentage=vol_move_pct,
            vega_pnl=vega_pnl,
            time_decay_days=time_decay_days,
            theta_pnl=theta_pnl
        )
        self._sensitivities[sensitivity.sensitivity_id] = sensitivity
        return sensitivity

    async def get_statistics(self) -> GreeksStatistics:
        stats = GreeksStatistics(total_option_positions=len(self._positions))
        if self._portfolio_greeks:
            stats.net_portfolio_delta = sum(g.total_delta for g in self._portfolio_greeks.values())
            stats.net_portfolio_gamma = sum(g.total_gamma for g in self._portfolio_greeks.values())
            stats.total_vega_exposure = sum(abs(g.total_vega) for g in self._portfolio_greeks.values())
            stats.daily_theta_decay = sum(g.total_theta for g in self._portfolio_greeks.values())
        return stats


greeks_service = GreeksService()
