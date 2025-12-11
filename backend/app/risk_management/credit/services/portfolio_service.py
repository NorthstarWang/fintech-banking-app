"""Portfolio Service - Credit portfolio risk management"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from ..models.portfolio_models import (
    CreditPortfolio, PortfolioSegment, ConcentrationRisk,
    PortfolioMigration, PortfolioStressTest, VintageAnalysis,
    PortfolioStatistics, PortfolioType, PortfolioStatus, ConcentrationRiskType
)


class PortfolioService:
    def __init__(self):
        self._portfolios: Dict[UUID, CreditPortfolio] = {}
        self._segments: Dict[UUID, PortfolioSegment] = {}
        self._concentrations: Dict[UUID, ConcentrationRisk] = {}
        self._migrations: Dict[UUID, PortfolioMigration] = {}
        self._stress_tests: Dict[UUID, PortfolioStressTest] = {}
        self._vintages: Dict[UUID, VintageAnalysis] = {}

    async def create_portfolio(
        self, name: str, portfolio_type: PortfolioType,
        description: str, manager: str
    ) -> CreditPortfolio:
        portfolio = CreditPortfolio(
            portfolio_name=name,
            portfolio_type=portfolio_type,
            description=description,
            portfolio_manager=manager
        )
        self._portfolios[portfolio.portfolio_id] = portfolio
        return portfolio

    async def get_portfolio(self, portfolio_id: UUID) -> Optional[CreditPortfolio]:
        return self._portfolios.get(portfolio_id)

    async def update_portfolio_metrics(
        self, portfolio_id: UUID, metrics: Dict[str, Any]
    ) -> Optional[CreditPortfolio]:
        portfolio = self._portfolios.get(portfolio_id)
        if portfolio:
            for key, value in metrics.items():
                if hasattr(portfolio, key):
                    setattr(portfolio, key, value)
            portfolio.updated_at = datetime.utcnow()
        return portfolio

    async def add_segment(
        self, portfolio_id: UUID, segment_name: str,
        segment_type: str, exposure_amount: float
    ) -> Optional[PortfolioSegment]:
        portfolio = self._portfolios.get(portfolio_id)
        if not portfolio:
            return None

        segment = PortfolioSegment(
            portfolio_id=portfolio_id,
            segment_name=segment_name,
            segment_type=segment_type,
            exposure_amount=exposure_amount,
            exposure_percentage=(exposure_amount / portfolio.total_exposure * 100) if portfolio.total_exposure > 0 else 0,
            number_of_accounts=0,
            average_rating="BBB",
            average_pd=0.02,
            expected_loss=exposure_amount * 0.02 * 0.45
        )
        self._segments[segment.segment_id] = segment
        return segment

    async def get_portfolio_segments(self, portfolio_id: UUID) -> List[PortfolioSegment]:
        return [s for s in self._segments.values() if s.portfolio_id == portfolio_id]

    async def assess_concentration_risk(
        self, portfolio_id: UUID, concentration_type: ConcentrationRiskType,
        dimension_name: str, dimension_value: str, exposure_amount: float,
        limit_percentage: float = None
    ) -> Optional[ConcentrationRisk]:
        portfolio = self._portfolios.get(portfolio_id)
        if not portfolio:
            return None

        exposure_pct = (exposure_amount / portfolio.total_exposure * 100) if portfolio.total_exposure > 0 else 0
        breach = limit_percentage and exposure_pct > limit_percentage

        concentration = ConcentrationRisk(
            portfolio_id=portfolio_id,
            concentration_type=concentration_type,
            dimension_name=dimension_name,
            dimension_value=dimension_value,
            exposure_amount=exposure_amount,
            exposure_percentage=exposure_pct,
            limit_percentage=limit_percentage,
            breach_status=breach,
            breach_amount=exposure_amount - (portfolio.total_exposure * limit_percentage / 100) if breach else None,
            risk_score=min(100, exposure_pct * 2)
        )
        self._concentrations[concentration.concentration_id] = concentration
        return concentration

    async def get_concentration_risks(self, portfolio_id: UUID) -> List[ConcentrationRisk]:
        return [c for c in self._concentrations.values() if c.portfolio_id == portfolio_id]

    async def calculate_migration_matrix(
        self, portfolio_id: UUID, period_start: date, period_end: date
    ) -> Optional[PortfolioMigration]:
        portfolio = self._portfolios.get(portfolio_id)
        if not portfolio:
            return None

        # Sample migration matrix
        migration_matrix = {
            "AAA": {"AAA": 0.90, "AA": 0.08, "A": 0.02},
            "AA": {"AAA": 0.02, "AA": 0.88, "A": 0.08, "BBB": 0.02},
            "A": {"AA": 0.03, "A": 0.87, "BBB": 0.08, "BB": 0.02},
            "BBB": {"A": 0.02, "BBB": 0.85, "BB": 0.10, "B": 0.03},
        }

        migration = PortfolioMigration(
            portfolio_id=portfolio_id,
            period_start=period_start,
            period_end=period_end,
            migration_matrix=migration_matrix,
            upgrade_rate=0.05,
            downgrade_rate=0.12,
            stable_rate=0.82,
            default_rate=0.01
        )
        self._migrations[migration.migration_id] = migration
        return migration

    async def run_stress_test(
        self, portfolio_id: UUID, scenario_name: str, scenario_type: str,
        economic_assumptions: Dict[str, float], created_by: str
    ) -> Optional[PortfolioStressTest]:
        portfolio = self._portfolios.get(portfolio_id)
        if not portfolio:
            return None

        # Calculate stressed parameters
        stress_multiplier = 2.0 if scenario_type == "severely_adverse" else (1.5 if scenario_type == "adverse" else 1.0)
        stressed_pd = portfolio.weighted_average_pd * stress_multiplier
        stressed_lgd = min(1.0, portfolio.weighted_average_lgd * 1.2)
        stressed_el = portfolio.total_exposure * stressed_pd * stressed_lgd

        stress_test = PortfolioStressTest(
            portfolio_id=portfolio_id,
            scenario_name=scenario_name,
            scenario_description=f"{scenario_type} economic scenario",
            scenario_type=scenario_type,
            economic_assumptions=economic_assumptions,
            stressed_pd=stressed_pd,
            stressed_lgd=stressed_lgd,
            stressed_ead=portfolio.total_exposure,
            stressed_expected_loss=stressed_el,
            stressed_unexpected_loss=stressed_el * 2.5,
            loss_increase_percentage=((stressed_el - portfolio.expected_loss) / portfolio.expected_loss * 100) if portfolio.expected_loss > 0 else 0,
            capital_impact=stressed_el * 0.08,
            created_by=created_by
        )
        self._stress_tests[stress_test.stress_test_id] = stress_test
        return stress_test

    async def analyze_vintage(
        self, portfolio_id: UUID, vintage_period: str,
        origination_amount: float, current_balance: float
    ) -> Optional[VintageAnalysis]:
        analysis = VintageAnalysis(
            portfolio_id=portfolio_id,
            vintage_period=vintage_period,
            origination_amount=origination_amount,
            current_balance=current_balance,
            cumulative_default_rate=0.02,
            cumulative_loss_rate=0.01,
            months_on_book=12,
            performance_status="performing"
        )
        self._vintages[analysis.analysis_id] = analysis
        return analysis

    async def get_statistics(self) -> PortfolioStatistics:
        stats = PortfolioStatistics(
            total_portfolios=len(self._portfolios),
            total_exposure=sum(p.total_exposure for p in self._portfolios.values()),
            total_expected_loss=sum(p.expected_loss for p in self._portfolios.values())
        )
        for portfolio in self._portfolios.values():
            stats.by_type[portfolio.portfolio_type.value] = stats.by_type.get(portfolio.portfolio_type.value, 0) + 1
        if self._portfolios:
            stats.average_pd = sum(p.weighted_average_pd for p in self._portfolios.values()) / len(self._portfolios)
            stats.average_lgd = sum(p.weighted_average_lgd for p in self._portfolios.values()) / len(self._portfolios)
        return stats


portfolio_service = PortfolioService()
