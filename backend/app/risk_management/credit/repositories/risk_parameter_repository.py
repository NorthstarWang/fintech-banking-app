"""Risk Parameter Repository - Data access layer for risk parameters"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from ..models.risk_parameter_models import (
    PDModel, LGDModel, EADModel, RiskParameterEstimate,
    ExpectedLossCalculation, UnexpectedLossCalculation,
    ParameterBacktest, ParameterStressTest, ParameterType
)


class RiskParameterRepository:
    def __init__(self):
        self._pd_models: Dict[UUID, PDModel] = {}
        self._lgd_models: Dict[UUID, LGDModel] = {}
        self._ead_models: Dict[UUID, EADModel] = {}
        self._estimates: Dict[UUID, RiskParameterEstimate] = {}
        self._el_calculations: Dict[UUID, ExpectedLossCalculation] = {}
        self._ul_calculations: Dict[UUID, UnexpectedLossCalculation] = {}
        self._backtests: Dict[UUID, ParameterBacktest] = {}
        self._stress_tests: Dict[UUID, ParameterStressTest] = {}

    async def save_pd_model(self, model: PDModel) -> PDModel:
        self._pd_models[model.model_id] = model
        return model

    async def find_pd_model_by_id(self, model_id: UUID) -> Optional[PDModel]:
        return self._pd_models.get(model_id)

    async def find_pd_models_by_segment(self, segment: str) -> List[PDModel]:
        return [m for m in self._pd_models.values() if m.segment == segment]

    async def find_active_pd_models(self) -> List[PDModel]:
        return [m for m in self._pd_models.values() if m.status == "active"]

    async def save_lgd_model(self, model: LGDModel) -> LGDModel:
        self._lgd_models[model.model_id] = model
        return model

    async def find_lgd_model_by_id(self, model_id: UUID) -> Optional[LGDModel]:
        return self._lgd_models.get(model_id)

    async def find_lgd_models_by_segment(self, segment: str) -> List[LGDModel]:
        return [m for m in self._lgd_models.values() if m.segment == segment]

    async def find_active_lgd_models(self) -> List[LGDModel]:
        return [m for m in self._lgd_models.values() if m.status == "active"]

    async def save_ead_model(self, model: EADModel) -> EADModel:
        self._ead_models[model.model_id] = model
        return model

    async def find_ead_model_by_id(self, model_id: UUID) -> Optional[EADModel]:
        return self._ead_models.get(model_id)

    async def find_ead_models_by_product(self, product_type: str) -> List[EADModel]:
        return [m for m in self._ead_models.values() if m.product_type == product_type]

    async def find_active_ead_models(self) -> List[EADModel]:
        return [m for m in self._ead_models.values() if m.status == "active"]

    async def save_estimate(self, estimate: RiskParameterEstimate) -> RiskParameterEstimate:
        self._estimates[estimate.estimate_id] = estimate
        return estimate

    async def find_estimate_by_id(self, estimate_id: UUID) -> Optional[RiskParameterEstimate]:
        return self._estimates.get(estimate_id)

    async def find_estimates_by_entity(self, entity_id: str) -> List[RiskParameterEstimate]:
        return [e for e in self._estimates.values() if e.entity_id == entity_id]

    async def find_estimates_by_type(self, param_type: ParameterType) -> List[RiskParameterEstimate]:
        return [e for e in self._estimates.values() if e.parameter_type == param_type]

    async def save_el_calculation(self, calculation: ExpectedLossCalculation) -> ExpectedLossCalculation:
        self._el_calculations[calculation.calculation_id] = calculation
        return calculation

    async def find_el_by_entity(self, entity_id: str) -> List[ExpectedLossCalculation]:
        return [c for c in self._el_calculations.values() if c.entity_id == entity_id]

    async def save_ul_calculation(self, calculation: UnexpectedLossCalculation) -> UnexpectedLossCalculation:
        self._ul_calculations[calculation.calculation_id] = calculation
        return calculation

    async def find_ul_by_entity(self, entity_id: str) -> List[UnexpectedLossCalculation]:
        return [c for c in self._ul_calculations.values() if c.entity_id == entity_id]

    async def save_backtest(self, backtest: ParameterBacktest) -> ParameterBacktest:
        self._backtests[backtest.backtest_id] = backtest
        return backtest

    async def find_backtests_by_model(self, model_id: UUID) -> List[ParameterBacktest]:
        return [b for b in self._backtests.values() if b.model_id == model_id]

    async def find_failed_backtests(self) -> List[ParameterBacktest]:
        return [b for b in self._backtests.values() if b.pass_fail == "fail"]

    async def save_stress_test(self, stress_test: ParameterStressTest) -> ParameterStressTest:
        self._stress_tests[stress_test.stress_test_id] = stress_test
        return stress_test

    async def find_stress_tests_by_type(self, param_type: ParameterType) -> List[ParameterStressTest]:
        return [s for s in self._stress_tests.values() if s.parameter_type == param_type]

    async def get_statistics(self) -> Dict[str, Any]:
        total_el = sum(c.expected_loss for c in self._el_calculations.values())
        total_rwa = sum(c.risk_weighted_assets for c in self._el_calculations.values())
        return {
            "total_pd_models": len(self._pd_models),
            "total_lgd_models": len(self._lgd_models),
            "total_ead_models": len(self._ead_models),
            "total_estimates": len(self._estimates),
            "total_expected_loss": total_el,
            "total_rwa": total_rwa
        }


risk_parameter_repository = RiskParameterRepository()
