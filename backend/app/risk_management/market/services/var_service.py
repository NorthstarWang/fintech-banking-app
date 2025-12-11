"""VaR Service - Value at Risk calculation service"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
import math
from ..models.var_models import (
    VaRCalculation, VaRBacktest, VaRLimit, VaRException,
    VaRStatistics, VaRMethod, ConfidenceLevel
)


class VaRService:
    def __init__(self):
        self._calculations: Dict[UUID, VaRCalculation] = {}
        self._backtests: Dict[UUID, VaRBacktest] = {}
        self._limits: Dict[UUID, VaRLimit] = {}
        self._exceptions: List[VaRException] = []

    async def calculate_var(
        self, portfolio_id: UUID, portfolio_value: float,
        method: VaRMethod, confidence_level: ConfidenceLevel,
        time_horizon: int = 1, returns: List[float] = None
    ) -> VaRCalculation:
        # Simplified VaR calculation
        cl_map = {"95": 1.645, "99": 2.326, "99.5": 2.576}
        z_score = cl_map.get(confidence_level.value, 2.326)

        if method == VaRMethod.PARAMETRIC:
            volatility = 0.02  # Simplified
            var_amount = portfolio_value * volatility * z_score * math.sqrt(time_horizon)
        elif method == VaRMethod.HISTORICAL and returns:
            sorted_returns = sorted(returns)
            index = int(len(sorted_returns) * (1 - float(confidence_level.value) / 100))
            var_amount = abs(sorted_returns[index]) * portfolio_value
        else:
            var_amount = portfolio_value * 0.05  # Simplified Monte Carlo

        calculation = VaRCalculation(
            portfolio_id=portfolio_id,
            calculation_date=date.today(),
            method=method,
            confidence_level=confidence_level,
            time_horizon_days=time_horizon,
            var_amount=var_amount,
            var_percentage=(var_amount / portfolio_value * 100),
            portfolio_value=portfolio_value,
            expected_shortfall=var_amount * 1.2,
            undiversified_var=var_amount * 1.3,
            diversification_benefit=var_amount * 0.3
        )
        self._calculations[calculation.calculation_id] = calculation
        return calculation

    async def get_calculation(self, calculation_id: UUID) -> Optional[VaRCalculation]:
        return self._calculations.get(calculation_id)

    async def run_backtest(
        self, portfolio_id: UUID, method: VaRMethod,
        confidence_level: ConfidenceLevel,
        var_predictions: List[float], actual_pnl: List[float]
    ) -> VaRBacktest:
        exceptions = sum(1 for v, p in zip(var_predictions, actual_pnl) if abs(p) > v)
        total = len(var_predictions)
        exception_rate = exceptions / total if total > 0 else 0
        expected_rate = 1 - float(confidence_level.value) / 100
        expected_exceptions = total * expected_rate

        # Kupiec test
        if exceptions > 0 and total > exceptions:
            kupiec_stat = -2 * (
                math.log((1 - expected_rate) ** (total - exceptions) * expected_rate ** exceptions) -
                math.log((1 - exception_rate) ** (total - exceptions) * exception_rate ** exceptions)
            )
        else:
            kupiec_stat = 0

        # Traffic light
        if exception_rate <= expected_rate * 1.5:
            zone = "green"
        elif exception_rate <= expected_rate * 2:
            zone = "yellow"
        else:
            zone = "red"

        backtest = VaRBacktest(
            portfolio_id=portfolio_id,
            backtest_start=date.today(),
            backtest_end=date.today(),
            method=method,
            confidence_level=confidence_level,
            total_observations=total,
            exceptions=exceptions,
            exception_rate=exception_rate,
            expected_exceptions=expected_exceptions,
            kupiec_test_stat=kupiec_stat,
            kupiec_p_value=0.05,
            traffic_light_zone=zone,
            pass_fail="pass" if zone != "red" else "fail"
        )
        self._backtests[backtest.backtest_id] = backtest
        return backtest

    async def set_limit(
        self, portfolio_id: UUID, limit_amount: float, approved_by: str
    ) -> VaRLimit:
        limit = VaRLimit(
            portfolio_id=portfolio_id,
            limit_type="var",
            limit_amount=limit_amount,
            current_var=0,
            utilization_percentage=0,
            effective_date=date.today(),
            approved_by=approved_by
        )
        self._limits[limit.limit_id] = limit
        return limit

    async def check_limit(self, limit_id: UUID, current_var: float) -> Dict[str, Any]:
        limit = self._limits.get(limit_id)
        if not limit:
            return {"status": "error", "message": "Limit not found"}

        utilization = (current_var / limit.limit_amount * 100) if limit.limit_amount > 0 else 0
        limit.current_var = current_var
        limit.utilization_percentage = utilization
        limit.breach_status = utilization >= 100

        return {
            "status": "breach" if limit.breach_status else "ok",
            "utilization": utilization,
            "available": max(0, limit.limit_amount - current_var)
        }

    async def record_exception(
        self, portfolio_id: UUID, predicted_var: float, actual_loss: float
    ) -> VaRException:
        exception = VaRException(
            portfolio_id=portfolio_id,
            exception_date=date.today(),
            predicted_var=predicted_var,
            actual_loss=actual_loss,
            exception_amount=actual_loss - predicted_var,
            exception_multiplier=actual_loss / predicted_var if predicted_var > 0 else 0
        )
        self._exceptions.append(exception)
        return exception

    async def get_statistics(self) -> VaRStatistics:
        stats = VaRStatistics(
            total_calculations=len(self._calculations),
            total_exceptions=len(self._exceptions)
        )
        if self._calculations:
            stats.average_var = sum(c.var_amount for c in self._calculations.values()) / len(self._calculations)
        for calc in self._calculations.values():
            stats.by_method[calc.method.value] = stats.by_method.get(calc.method.value, 0) + 1
        return stats


var_service = VaRService()
