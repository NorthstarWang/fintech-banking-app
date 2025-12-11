"""Risk Parameter Service - PD, LGD, EAD modeling"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from ..models.risk_parameter_models import (
    PDModel, LGDModel, EADModel, RiskParameterEstimate,
    ExpectedLossCalculation, UnexpectedLossCalculation,
    ParameterBacktest, ParameterStressTest, RiskParameterStatistics,
    ParameterType, ModelApproach
)


class RiskParameterService:
    def __init__(self):
        self._pd_models: Dict[UUID, PDModel] = {}
        self._lgd_models: Dict[UUID, LGDModel] = {}
        self._ead_models: Dict[UUID, EADModel] = {}
        self._estimates: Dict[UUID, RiskParameterEstimate] = {}
        self._el_calculations: Dict[UUID, ExpectedLossCalculation] = {}
        self._ul_calculations: Dict[UUID, UnexpectedLossCalculation] = {}
        self._backtests: Dict[UUID, ParameterBacktest] = {}
        self._stress_tests: Dict[UUID, ParameterStressTest] = []

    async def register_pd_model(
        self, model_name: str, segment: str, approach: ModelApproach,
        methodology: str, ttc_pd: float, pit_pd: float, created_by: str
    ) -> PDModel:
        model = PDModel(
            model_name=model_name,
            segment=segment,
            model_approach=approach,
            version="1.0",
            methodology=methodology,
            calibration_date=date.today(),
            through_the_cycle_pd=ttc_pd,
            point_in_time_pd=pit_pd,
            long_run_average_pd=(ttc_pd + pit_pd) / 2,
            created_by=created_by
        )
        self._pd_models[model.model_id] = model
        return model

    async def get_pd_model(self, model_id: UUID) -> Optional[PDModel]:
        return self._pd_models.get(model_id)

    async def register_lgd_model(
        self, model_name: str, segment: str, collateral_type: str,
        approach: ModelApproach, methodology: str,
        downturn_lgd: float, recovery_rate: float, created_by: str
    ) -> LGDModel:
        model = LGDModel(
            model_name=model_name,
            segment=segment,
            collateral_type=collateral_type,
            model_approach=approach,
            version="1.0",
            methodology=methodology,
            calibration_date=date.today(),
            downturn_lgd=downturn_lgd,
            long_run_average_lgd=downturn_lgd * 0.85,
            recovery_rate=recovery_rate,
            cure_rate=1 - downturn_lgd - recovery_rate,
            workout_lgd=downturn_lgd * 0.9,
            created_by=created_by
        )
        self._lgd_models[model.model_id] = model
        return model

    async def get_lgd_model(self, model_id: UUID) -> Optional[LGDModel]:
        return self._lgd_models.get(model_id)

    async def register_ead_model(
        self, model_name: str, product_type: str, approach: ModelApproach,
        methodology: str, ccf: float, created_by: str
    ) -> EADModel:
        model = EADModel(
            model_name=model_name,
            product_type=product_type,
            model_approach=approach,
            version="1.0",
            methodology=methodology,
            calibration_date=date.today(),
            credit_conversion_factor=ccf,
            utilization_at_default=0.75,
            limit_at_default=1.0,
            undrawn_at_default=0.25,
            additional_drawdown_factor=ccf * 0.25,
            created_by=created_by
        )
        self._ead_models[model.model_id] = model
        return model

    async def estimate_parameters(
        self, entity_id: str, entity_type: str, segment: str,
        pd_model_id: UUID, lgd_model_id: UUID, ead_model_id: UUID,
        input_factors: Dict[str, Any]
    ) -> Dict[str, RiskParameterEstimate]:
        estimates = {}

        # PD Estimate
        pd_model = self._pd_models.get(pd_model_id)
        if pd_model:
            pd_estimate = RiskParameterEstimate(
                entity_id=entity_id,
                entity_type=entity_type,
                segment=segment,
                parameter_type=ParameterType.PD,
                point_estimate=pd_model.point_in_time_pd,
                lower_bound=pd_model.point_in_time_pd * 0.8,
                upper_bound=pd_model.point_in_time_pd * 1.2,
                estimation_date=date.today(),
                model_id=pd_model_id,
                model_version=pd_model.version,
                input_factors=input_factors,
                final_estimate=max(pd_model.point_in_time_pd, pd_model.regulatory_floor)
            )
            self._estimates[pd_estimate.estimate_id] = pd_estimate
            estimates["pd"] = pd_estimate

        # LGD Estimate
        lgd_model = self._lgd_models.get(lgd_model_id)
        if lgd_model:
            lgd_estimate = RiskParameterEstimate(
                entity_id=entity_id,
                entity_type=entity_type,
                segment=segment,
                parameter_type=ParameterType.LGD,
                point_estimate=lgd_model.downturn_lgd,
                lower_bound=lgd_model.downturn_lgd * 0.85,
                upper_bound=lgd_model.downturn_lgd * 1.15,
                estimation_date=date.today(),
                model_id=lgd_model_id,
                model_version=lgd_model.version,
                input_factors=input_factors,
                final_estimate=lgd_model.downturn_lgd
            )
            self._estimates[lgd_estimate.estimate_id] = lgd_estimate
            estimates["lgd"] = lgd_estimate

        # EAD Estimate
        ead_model = self._ead_models.get(ead_model_id)
        if ead_model:
            exposure = input_factors.get("exposure", 100000)
            ead_value = exposure * ead_model.credit_conversion_factor
            ead_estimate = RiskParameterEstimate(
                entity_id=entity_id,
                entity_type=entity_type,
                segment=segment,
                parameter_type=ParameterType.EAD,
                point_estimate=ead_value,
                lower_bound=ead_value * 0.9,
                upper_bound=ead_value * 1.1,
                estimation_date=date.today(),
                model_id=ead_model_id,
                model_version=ead_model.version,
                input_factors=input_factors,
                final_estimate=ead_value
            )
            self._estimates[ead_estimate.estimate_id] = ead_estimate
            estimates["ead"] = ead_estimate

        return estimates

    async def calculate_expected_loss(
        self, entity_id: str, exposure: float,
        pd: float, lgd: float, approach: ModelApproach = ModelApproach.STANDARDIZED
    ) -> ExpectedLossCalculation:
        ead = exposure
        el = ead * pd * lgd
        el_pct = pd * lgd * 100

        # Risk weight calculation (simplified Basel approach)
        correlation = 0.12 * (1 - 2.718 ** (-50 * pd)) / (1 - 2.718 ** (-50))
        rwa = ead * 12.5 * el_pct / 100  # Simplified

        calculation = ExpectedLossCalculation(
            entity_id=entity_id,
            calculation_date=date.today(),
            exposure_at_default=ead,
            probability_of_default=pd,
            loss_given_default=lgd,
            expected_loss=el,
            expected_loss_percentage=el_pct,
            provision_required=el,
            risk_weighted_assets=rwa,
            capital_requirement=rwa * 0.08,
            calculation_approach=approach
        )
        self._el_calculations[calculation.calculation_id] = calculation
        return calculation

    async def calculate_unexpected_loss(
        self, entity_id: str, portfolio_id: UUID,
        expected_loss: float, pd: float, lgd: float,
        confidence_level: float = 0.999
    ) -> UnexpectedLossCalculation:
        # Simplified UL calculation
        import math

        # Asset correlation (Basel formula)
        correlation = 0.12 * (1 - math.exp(-50 * pd)) / (1 - math.exp(-50))
        correlation += 0.24 * (1 - (1 - math.exp(-50 * pd)) / (1 - math.exp(-50)))

        # Maturity adjustment
        maturity_adjustment = 1.0

        # VaR calculation (simplified)
        var_multiplier = 2.5  # Approximate for 99.9%
        ul = expected_loss * var_multiplier
        var = ul * 1.5

        calculation = UnexpectedLossCalculation(
            entity_id=entity_id,
            portfolio_id=portfolio_id,
            calculation_date=date.today(),
            unexpected_loss=ul,
            value_at_risk=var,
            confidence_level=confidence_level,
            correlation_factor=correlation,
            asset_correlation=correlation,
            maturity_adjustment=maturity_adjustment,
            economic_capital=ul * 1.2,
            regulatory_capital=ul * 1.0
        )
        self._ul_calculations[calculation.calculation_id] = calculation
        return calculation

    async def run_backtest(
        self, model_id: UUID, parameter_type: ParameterType,
        period_start: date, period_end: date,
        predicted: List[float], actual: List[float],
        backtested_by: str
    ) -> ParameterBacktest:
        # Calculate accuracy metrics
        if predicted and actual and len(predicted) == len(actual):
            accuracy = 1 - sum(abs(p - a) for p, a in zip(predicted, actual)) / len(predicted)
        else:
            accuracy = 0.0

        backtest = ParameterBacktest(
            model_id=model_id,
            parameter_type=parameter_type,
            backtest_period_start=period_start,
            backtest_period_end=period_end,
            predicted_values=predicted,
            actual_values=actual,
            accuracy_ratio=accuracy,
            binomial_test_result="pass" if accuracy > 0.8 else "fail",
            pass_fail="pass" if accuracy > 0.75 else "fail",
            observations=f"Accuracy: {accuracy:.2%}",
            backtested_by=backtested_by
        )
        self._backtests[backtest.backtest_id] = backtest
        return backtest

    async def run_stress_test(
        self, parameter_type: ParameterType, scenario_name: str,
        base_value: float, stress_factors: Dict[str, float],
        tested_by: str
    ) -> ParameterStressTest:
        stress_multiplier = 1.0 + sum(stress_factors.values())
        stressed_value = base_value * stress_multiplier

        stress_test = ParameterStressTest(
            parameter_type=parameter_type,
            scenario_name=scenario_name,
            base_value=base_value,
            stressed_value=stressed_value,
            stress_multiplier=stress_multiplier,
            stress_factors=stress_factors,
            impact_assessment=f"Parameter increases by {(stress_multiplier - 1) * 100:.1f}%",
            tested_by=tested_by
        )
        self._stress_tests[stress_test.stress_test_id] = stress_test
        return stress_test

    async def get_statistics(self) -> RiskParameterStatistics:
        stats = RiskParameterStatistics(
            total_pd_models=len(self._pd_models),
            total_lgd_models=len(self._lgd_models),
            total_ead_models=len(self._ead_models)
        )

        if self._pd_models:
            stats.average_pd = sum(m.point_in_time_pd for m in self._pd_models.values()) / len(self._pd_models)
        if self._lgd_models:
            stats.average_lgd = sum(m.downturn_lgd for m in self._lgd_models.values()) / len(self._lgd_models)

        stats.total_expected_loss = sum(c.expected_loss for c in self._el_calculations.values())
        stats.total_rwa = sum(c.risk_weighted_assets for c in self._el_calculations.values())

        return stats


risk_parameter_service = RiskParameterService()
