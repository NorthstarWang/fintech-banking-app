"""Risk Parameter Routes - API endpoints for PD/LGD/EAD modeling"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..models.risk_parameter_models import (
    PDModel, LGDModel, EADModel, RiskParameterEstimate,
    ExpectedLossCalculation, UnexpectedLossCalculation,
    ParameterType, ModelApproach
)
from ..services.risk_parameter_service import risk_parameter_service

router = APIRouter(prefix="/credit/risk-parameters", tags=["Credit Risk Parameters"])


class RegisterPDModelRequest(BaseModel):
    model_name: str
    segment: str
    approach: ModelApproach
    methodology: str
    ttc_pd: float = Field(ge=0, le=1)
    pit_pd: float = Field(ge=0, le=1)
    created_by: str


class RegisterLGDModelRequest(BaseModel):
    model_name: str
    segment: str
    collateral_type: str
    approach: ModelApproach
    methodology: str
    downturn_lgd: float = Field(ge=0, le=1)
    recovery_rate: float = Field(ge=0, le=1)
    created_by: str


class RegisterEADModelRequest(BaseModel):
    model_name: str
    product_type: str
    approach: ModelApproach
    methodology: str
    ccf: float = Field(ge=0, le=1)
    created_by: str


class EstimateParametersRequest(BaseModel):
    entity_id: str
    entity_type: str
    segment: str
    pd_model_id: UUID
    lgd_model_id: UUID
    ead_model_id: UUID
    input_factors: Dict[str, Any]


class CalculateELRequest(BaseModel):
    entity_id: str
    exposure: float = Field(gt=0)
    pd: float = Field(ge=0, le=1)
    lgd: float = Field(ge=0, le=1)
    approach: ModelApproach = ModelApproach.STANDARDIZED


class CalculateULRequest(BaseModel):
    entity_id: str
    portfolio_id: UUID
    expected_loss: float = Field(ge=0)
    pd: float = Field(ge=0, le=1)
    lgd: float = Field(ge=0, le=1)
    confidence_level: float = Field(default=0.999, ge=0.9, le=1)


class BacktestRequest(BaseModel):
    model_id: UUID
    parameter_type: ParameterType
    period_start: date
    period_end: date
    predicted: List[float]
    actual: List[float]
    backtested_by: str


class StressTestRequest(BaseModel):
    parameter_type: ParameterType
    scenario_name: str
    base_value: float
    stress_factors: Dict[str, float]
    tested_by: str


@router.post("/pd-models", response_model=PDModel)
async def register_pd_model(request: RegisterPDModelRequest):
    """Register a PD model"""
    model = await risk_parameter_service.register_pd_model(
        request.model_name, request.segment, request.approach,
        request.methodology, request.ttc_pd, request.pit_pd, request.created_by
    )
    return model


@router.get("/pd-models/{model_id}", response_model=PDModel)
async def get_pd_model(model_id: UUID):
    """Get PD model by ID"""
    model = await risk_parameter_service.get_pd_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="PD model not found")
    return model


@router.post("/lgd-models", response_model=LGDModel)
async def register_lgd_model(request: RegisterLGDModelRequest):
    """Register an LGD model"""
    model = await risk_parameter_service.register_lgd_model(
        request.model_name, request.segment, request.collateral_type,
        request.approach, request.methodology, request.downturn_lgd,
        request.recovery_rate, request.created_by
    )
    return model


@router.get("/lgd-models/{model_id}", response_model=LGDModel)
async def get_lgd_model(model_id: UUID):
    """Get LGD model by ID"""
    model = await risk_parameter_service.get_lgd_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="LGD model not found")
    return model


@router.post("/ead-models", response_model=EADModel)
async def register_ead_model(request: RegisterEADModelRequest):
    """Register an EAD model"""
    model = await risk_parameter_service.register_ead_model(
        request.model_name, request.product_type, request.approach,
        request.methodology, request.ccf, request.created_by
    )
    return model


@router.post("/estimate")
async def estimate_parameters(request: EstimateParametersRequest):
    """Estimate risk parameters for an entity"""
    estimates = await risk_parameter_service.estimate_parameters(
        request.entity_id, request.entity_type, request.segment,
        request.pd_model_id, request.lgd_model_id, request.ead_model_id,
        request.input_factors
    )
    return estimates


@router.post("/expected-loss", response_model=ExpectedLossCalculation)
async def calculate_expected_loss(request: CalculateELRequest):
    """Calculate expected loss"""
    return await risk_parameter_service.calculate_expected_loss(
        request.entity_id, request.exposure, request.pd, request.lgd, request.approach
    )


@router.post("/unexpected-loss", response_model=UnexpectedLossCalculation)
async def calculate_unexpected_loss(request: CalculateULRequest):
    """Calculate unexpected loss"""
    return await risk_parameter_service.calculate_unexpected_loss(
        request.entity_id, request.portfolio_id, request.expected_loss,
        request.pd, request.lgd, request.confidence_level
    )


@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """Run parameter backtest"""
    return await risk_parameter_service.run_backtest(
        request.model_id, request.parameter_type, request.period_start,
        request.period_end, request.predicted, request.actual, request.backtested_by
    )


@router.post("/stress-test")
async def run_stress_test(request: StressTestRequest):
    """Run parameter stress test"""
    return await risk_parameter_service.run_stress_test(
        request.parameter_type, request.scenario_name, request.base_value,
        request.stress_factors, request.tested_by
    )


@router.get("/statistics/summary")
async def get_parameter_statistics():
    """Get risk parameter statistics"""
    return await risk_parameter_service.get_statistics()
