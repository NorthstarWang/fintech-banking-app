"""Equity Risk Service - Equity risk management service"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from ..models.equity_risk_models import (
    EquityPosition, EquityExposure, BetaAnalysis,
    EquityFactorExposure, EquityScenario, EquityRiskStatistics,
    EquityPositionType
)


class EquityRiskService:
    def __init__(self):
        self._positions: Dict[UUID, EquityPosition] = {}
        self._exposures: Dict[UUID, EquityExposure] = {}
        self._beta_analyses: Dict[UUID, BetaAnalysis] = {}
        self._factor_exposures: Dict[UUID, EquityFactorExposure] = {}
        self._scenarios: Dict[UUID, EquityScenario] = {}

    async def create_position(
        self, position_type: EquityPositionType, ticker: str, exchange: str,
        quantity: float, direction: str, entry_price: float, current_price: float,
        sector: str, country: str, currency: str, portfolio_id: UUID
    ) -> EquityPosition:
        market_value = quantity * current_price
        cost_basis = quantity * entry_price
        pnl = market_value - cost_basis if direction == "long" else cost_basis - market_value

        position = EquityPosition(
            position_type=position_type,
            ticker=ticker,
            exchange=exchange,
            quantity=quantity,
            direction=direction,
            entry_price=entry_price,
            current_price=current_price,
            market_value=market_value,
            unrealized_pnl=pnl,
            sector=sector,
            country=country,
            currency=currency,
            portfolio_id=portfolio_id
        )
        self._positions[position.position_id] = position
        return position

    async def get_position(self, position_id: UUID) -> Optional[EquityPosition]:
        return self._positions.get(position_id)

    async def calculate_exposure(
        self, exposure_type: str, exposure_key: str, portfolio_id: UUID
    ) -> EquityExposure:
        positions = [p for p in self._positions.values() if p.portfolio_id == portfolio_id]

        if exposure_type == "sector":
            filtered = [p for p in positions if p.sector == exposure_key]
        elif exposure_type == "country":
            filtered = [p for p in positions if p.country == exposure_key]
        else:
            filtered = positions

        long_exp = sum(p.market_value for p in filtered if p.direction == "long")
        short_exp = sum(p.market_value for p in filtered if p.direction == "short")
        total_portfolio = sum(p.market_value for p in positions)

        exposure = EquityExposure(
            exposure_type=exposure_type,
            exposure_key=exposure_key,
            gross_exposure=long_exp + short_exp,
            net_exposure=long_exp - short_exp,
            long_exposure=long_exp,
            short_exposure=short_exp,
            percentage_of_portfolio=(long_exp - short_exp) / total_portfolio * 100 if total_portfolio > 0 else 0,
            beta_adjusted_exposure=(long_exp - short_exp) * 1.1,
            var_contribution=abs(long_exp - short_exp) * 0.02,
            as_of_date=date.today()
        )
        self._exposures[exposure.exposure_id] = exposure
        return exposure

    async def perform_beta_analysis(
        self, portfolio_id: UUID, benchmark_ticker: str,
        portfolio_returns: List[float], benchmark_returns: List[float]
    ) -> BetaAnalysis:
        # Simplified beta calculation
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            beta = 1.0
            correlation = 0.8
        else:
            mean_p = sum(portfolio_returns) / len(portfolio_returns)
            mean_b = sum(benchmark_returns) / len(benchmark_returns)
            cov = sum((p - mean_p) * (b - mean_b) for p, b in zip(portfolio_returns, benchmark_returns)) / len(portfolio_returns)
            var_b = sum((b - mean_b) ** 2 for b in benchmark_returns) / len(benchmark_returns)
            beta = cov / var_b if var_b > 0 else 1.0
            std_p = (sum((p - mean_p) ** 2 for p in portfolio_returns) / len(portfolio_returns)) ** 0.5
            std_b = var_b ** 0.5
            correlation = cov / (std_p * std_b) if std_p > 0 and std_b > 0 else 0

        analysis = BetaAnalysis(
            portfolio_id=portfolio_id,
            analysis_date=date.today(),
            portfolio_beta=beta,
            benchmark_ticker=benchmark_ticker,
            correlation=correlation,
            r_squared=correlation ** 2,
            tracking_error=(1 - correlation ** 2) ** 0.5 * 0.1,
            information_ratio=0.5,
            treynor_ratio=0.02 / beta if beta > 0 else 0,
            jensen_alpha=0.01,
            systematic_risk=beta * 0.15,
            idiosyncratic_risk=0.1
        )
        self._beta_analyses[analysis.analysis_id] = analysis
        return analysis

    async def calculate_factor_exposure(self, portfolio_id: UUID) -> EquityFactorExposure:
        exposure = EquityFactorExposure(
            portfolio_id=portfolio_id,
            analysis_date=date.today(),
            market_factor=1.05,
            size_factor=-0.2,
            value_factor=0.3,
            momentum_factor=0.15,
            quality_factor=0.25,
            volatility_factor=-0.1,
            residual_risk=0.05
        )
        self._factor_exposures[exposure.exposure_id] = exposure
        return exposure

    async def run_scenario(
        self, scenario_name: str, market_shock: float,
        sector_shocks: Dict[str, float], volatility_shock: float
    ) -> EquityScenario:
        pnl_impact = 0
        for position in self._positions.values():
            sector_shock = sector_shocks.get(position.sector, 0)
            total_shock = market_shock + sector_shock
            impact = position.market_value * total_shock
            if position.direction == "short":
                impact = -impact
            pnl_impact += impact

        scenario = EquityScenario(
            scenario_name=scenario_name,
            scenario_type="hypothetical",
            market_shock=market_shock,
            sector_shocks=sector_shocks,
            volatility_shock=volatility_shock,
            correlation_change=0,
            pnl_impact=pnl_impact,
            beta_impact=market_shock
        )
        self._scenarios[scenario.scenario_id] = scenario
        return scenario

    async def get_portfolio_positions(self, portfolio_id: UUID) -> List[EquityPosition]:
        return [p for p in self._positions.values() if p.portfolio_id == portfolio_id]

    async def get_statistics(self) -> EquityRiskStatistics:
        stats = EquityRiskStatistics(
            total_positions=len(self._positions),
            total_market_value=sum(p.market_value for p in self._positions.values())
        )
        if self._beta_analyses:
            stats.portfolio_beta = sum(b.portfolio_beta for b in self._beta_analyses.values()) / len(self._beta_analyses)
        for position in self._positions.values():
            stats.by_sector[position.sector] = stats.by_sector.get(position.sector, 0) + position.market_value
        return stats


equity_risk_service = EquityRiskService()
