"""VaR Repository - Data access layer for VaR calculations"""

from typing import Any
from uuid import UUID

from ..models.var_models import VaRBacktest, VaRCalculation, VaRException, VaRLimit, VaRMethod


class VaRRepository:
    def __init__(self):
        self._calculations: dict[UUID, VaRCalculation] = {}
        self._backtests: dict[UUID, VaRBacktest] = {}
        self._limits: dict[UUID, VaRLimit] = {}
        self._exceptions: list[VaRException] = []
        self._portfolio_index: dict[UUID, list[UUID]] = {}

    async def save_calculation(self, calc: VaRCalculation) -> VaRCalculation:
        self._calculations[calc.calculation_id] = calc
        if calc.portfolio_id not in self._portfolio_index:
            self._portfolio_index[calc.portfolio_id] = []
        self._portfolio_index[calc.portfolio_id].append(calc.calculation_id)
        return calc

    async def find_calculation_by_id(self, calc_id: UUID) -> VaRCalculation | None:
        return self._calculations.get(calc_id)

    async def find_calculations_by_portfolio(self, portfolio_id: UUID, limit: int = 100) -> list[VaRCalculation]:
        calc_ids = self._portfolio_index.get(portfolio_id, [])
        calcs = [self._calculations[cid] for cid in calc_ids if cid in self._calculations]
        return sorted(calcs, key=lambda x: x.calculation_date, reverse=True)[:limit]

    async def find_calculations_by_method(self, method: VaRMethod) -> list[VaRCalculation]:
        return [c for c in self._calculations.values() if c.method == method]

    async def save_backtest(self, backtest: VaRBacktest) -> VaRBacktest:
        self._backtests[backtest.backtest_id] = backtest
        return backtest

    async def find_backtest_by_id(self, bt_id: UUID) -> VaRBacktest | None:
        return self._backtests.get(bt_id)

    async def find_backtests_by_portfolio(self, portfolio_id: UUID) -> list[VaRBacktest]:
        return [b for b in self._backtests.values() if b.portfolio_id == portfolio_id]

    async def save_limit(self, limit: VaRLimit) -> VaRLimit:
        self._limits[limit.limit_id] = limit
        return limit

    async def find_limit_by_portfolio(self, portfolio_id: UUID) -> VaRLimit | None:
        for limit in self._limits.values():
            if limit.portfolio_id == portfolio_id:
                return limit
        return None

    async def save_exception(self, exception: VaRException) -> VaRException:
        self._exceptions.append(exception)
        return exception

    async def find_exceptions_by_portfolio(self, portfolio_id: UUID) -> list[VaRException]:
        return [e for e in self._exceptions if e.portfolio_id == portfolio_id]

    async def get_statistics(self) -> dict[str, Any]:
        return {
            "total_calculations": len(self._calculations),
            "total_backtests": len(self._backtests),
            "total_exceptions": len(self._exceptions)
        }


var_repository = VaRRepository()
