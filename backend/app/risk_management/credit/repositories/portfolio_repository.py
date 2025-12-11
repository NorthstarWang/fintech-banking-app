"""Portfolio Repository - Data access layer for credit portfolios"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from ..models.portfolio_models import (
    CreditPortfolio, PortfolioSegment, ConcentrationRisk,
    PortfolioMigration, PortfolioStressTest, VintageAnalysis,
    PortfolioType, PortfolioStatus
)


class PortfolioRepository:
    def __init__(self):
        self._portfolios: Dict[UUID, CreditPortfolio] = {}
        self._segments: Dict[UUID, PortfolioSegment] = {}
        self._concentrations: Dict[UUID, ConcentrationRisk] = {}
        self._migrations: Dict[UUID, PortfolioMigration] = {}
        self._stress_tests: Dict[UUID, PortfolioStressTest] = {}
        self._vintages: Dict[UUID, VintageAnalysis] = {}

    async def save_portfolio(self, portfolio: CreditPortfolio) -> CreditPortfolio:
        self._portfolios[portfolio.portfolio_id] = portfolio
        return portfolio

    async def find_portfolio_by_id(self, portfolio_id: UUID) -> Optional[CreditPortfolio]:
        return self._portfolios.get(portfolio_id)

    async def find_portfolios_by_type(self, portfolio_type: PortfolioType) -> List[CreditPortfolio]:
        return [p for p in self._portfolios.values() if p.portfolio_type == portfolio_type]

    async def find_portfolios_by_status(self, status: PortfolioStatus) -> List[CreditPortfolio]:
        return [p for p in self._portfolios.values() if p.status == status]

    async def find_portfolios_by_manager(self, manager: str) -> List[CreditPortfolio]:
        return [p for p in self._portfolios.values() if p.portfolio_manager == manager]

    async def update_portfolio(self, portfolio: CreditPortfolio) -> CreditPortfolio:
        portfolio.updated_at = datetime.utcnow()
        self._portfolios[portfolio.portfolio_id] = portfolio
        return portfolio

    async def save_segment(self, segment: PortfolioSegment) -> PortfolioSegment:
        self._segments[segment.segment_id] = segment
        return segment

    async def find_segments_by_portfolio(self, portfolio_id: UUID) -> List[PortfolioSegment]:
        return [s for s in self._segments.values() if s.portfolio_id == portfolio_id]

    async def save_concentration(self, concentration: ConcentrationRisk) -> ConcentrationRisk:
        self._concentrations[concentration.concentration_id] = concentration
        return concentration

    async def find_concentrations_by_portfolio(self, portfolio_id: UUID) -> List[ConcentrationRisk]:
        return [c for c in self._concentrations.values() if c.portfolio_id == portfolio_id]

    async def find_breach_concentrations(self) -> List[ConcentrationRisk]:
        return [c for c in self._concentrations.values() if c.breach_status]

    async def save_migration(self, migration: PortfolioMigration) -> PortfolioMigration:
        self._migrations[migration.migration_id] = migration
        return migration

    async def find_migrations_by_portfolio(self, portfolio_id: UUID) -> List[PortfolioMigration]:
        return [m for m in self._migrations.values() if m.portfolio_id == portfolio_id]

    async def save_stress_test(self, stress_test: PortfolioStressTest) -> PortfolioStressTest:
        self._stress_tests[stress_test.stress_test_id] = stress_test
        return stress_test

    async def find_stress_tests_by_portfolio(self, portfolio_id: UUID) -> List[PortfolioStressTest]:
        return [s for s in self._stress_tests.values() if s.portfolio_id == portfolio_id]

    async def save_vintage(self, vintage: VintageAnalysis) -> VintageAnalysis:
        self._vintages[vintage.analysis_id] = vintage
        return vintage

    async def find_vintages_by_portfolio(self, portfolio_id: UUID) -> List[VintageAnalysis]:
        return [v for v in self._vintages.values() if v.portfolio_id == portfolio_id]

    async def get_all_portfolios(self) -> List[CreditPortfolio]:
        return list(self._portfolios.values())

    async def get_statistics(self) -> Dict[str, Any]:
        total = len(self._portfolios)
        total_exposure = sum(p.total_exposure for p in self._portfolios.values())
        by_type = {}
        for portfolio in self._portfolios.values():
            by_type[portfolio.portfolio_type.value] = by_type.get(portfolio.portfolio_type.value, 0) + 1
        return {
            "total_portfolios": total,
            "total_exposure": total_exposure,
            "by_type": by_type
        }


portfolio_repository = PortfolioRepository()
