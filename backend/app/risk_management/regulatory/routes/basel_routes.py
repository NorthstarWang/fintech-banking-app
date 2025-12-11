"""Basel III/IV Compliance API Routes"""

from typing import List, Optional
from datetime import date
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..models.basel_models import (
    RiskWeightedAsset, CapitalRequirement, LiquidityCoverageRatio,
    NetStableFundingRatio, LeverageRatio, CounterpartyCreditRisk,
    LargeExposure, BaselReport, RWARiskType
)
from ..services.basel_service import basel_service

router = APIRouter(prefix="/basel", tags=["Basel Compliance"])


class RWACalculationRequest(BaseModel):
    exposure_id: str
    exposure_type: str
    asset_class: str
    exposure_amount: Decimal
    risk_type: RWARiskType
    entity_id: str


class CapitalRequirementRequest(BaseModel):
    entity_id: str
    entity_name: str
    reporting_date: date
    cet1_required: Decimal
    tier1_required: Decimal
    total_capital_required: Decimal
    countercyclical_buffer: Decimal
    systemic_buffer: Decimal


class LCRCalculationRequest(BaseModel):
    entity_id: str
    total_hqla: Decimal
    level1_assets: Decimal
    level2a_assets: Decimal
    level2b_assets: Decimal
    total_outflows: Decimal
    total_inflows: Decimal


class NSFRCalculationRequest(BaseModel):
    entity_id: str
    available_stable_funding: Decimal
    required_stable_funding: Decimal


class LeverageRatioRequest(BaseModel):
    entity_id: str
    tier1_capital: Decimal
    total_exposure: Decimal


class CCRRequest(BaseModel):
    counterparty_id: str
    counterparty_name: str
    counterparty_type: str
    approach: str
    exposure_type: str
    gross_exposure: Decimal
    netting_benefit: Decimal
    collateral_held: Decimal


class LargeExposureRequest(BaseModel):
    counterparty_id: str
    counterparty_name: str
    entity_id: str
    gross_exposure: Decimal
    net_exposure: Decimal


@router.post("/rwa/calculate", response_model=dict)
async def calculate_rwa(request: RWACalculationRequest):
    """Calculate Risk-Weighted Assets for an exposure"""
    rwa = await basel_service.calculate_rwa(
        exposure_id=request.exposure_id, exposure_type=request.exposure_type,
        asset_class=request.asset_class, exposure_amount=request.exposure_amount,
        risk_type=request.risk_type, entity_id=request.entity_id
    )
    return {"rwa_id": str(rwa.rwa_id), "rwa_amount": float(rwa.rwa_amount), "risk_weight": float(rwa.risk_weight)}


@router.get("/rwa", response_model=List[dict])
async def list_rwas(
    risk_type: Optional[str] = None,
    reporting_date: Optional[date] = None
):
    """List all Risk-Weighted Asset calculations"""
    if risk_type:
        rwas = await basel_service.repository.find_rwas_by_type(risk_type)
    elif reporting_date:
        rwas = await basel_service.repository.find_rwas_by_date(reporting_date)
    else:
        rwas = await basel_service.repository.find_all_rwas()
    return [{"rwa_id": str(r.rwa_id), "exposure_id": r.exposure_id, "rwa_amount": float(r.rwa_amount)} for r in rwas]


@router.post("/capital-requirements", response_model=dict)
async def record_capital_requirement(request: CapitalRequirementRequest):
    """Record capital requirements for an entity"""
    req = await basel_service.record_capital_requirement(
        entity_id=request.entity_id, entity_name=request.entity_name,
        reporting_date=request.reporting_date, cet1_required=request.cet1_required,
        tier1_required=request.tier1_required, total_capital_required=request.total_capital_required,
        countercyclical_buffer=request.countercyclical_buffer, systemic_buffer=request.systemic_buffer
    )
    return {"requirement_id": str(req.requirement_id), "total_buffer": float(req.total_buffer)}


@router.get("/capital-requirements/{entity_id}", response_model=dict)
async def get_capital_requirement(entity_id: str):
    """Get latest capital requirement for an entity"""
    req = await basel_service.repository.find_latest_capital_requirement(entity_id)
    if not req:
        raise HTTPException(status_code=404, detail="Capital requirement not found")
    return {
        "requirement_id": str(req.requirement_id),
        "cet1_required": float(req.cet1_required),
        "tier1_required": float(req.tier1_required),
        "total_capital_required": float(req.total_capital_required)
    }


@router.post("/lcr/calculate", response_model=dict)
async def calculate_lcr(request: LCRCalculationRequest):
    """Calculate Liquidity Coverage Ratio"""
    lcr = await basel_service.calculate_lcr(
        entity_id=request.entity_id, total_hqla=request.total_hqla,
        level1_assets=request.level1_assets, level2a_assets=request.level2a_assets,
        level2b_assets=request.level2b_assets, total_outflows=request.total_outflows,
        total_inflows=request.total_inflows
    )
    return {"lcr_id": str(lcr.lcr_id), "lcr_ratio": float(lcr.lcr_ratio), "compliant": lcr.compliant}


@router.get("/lcr/{entity_id}", response_model=List[dict])
async def get_entity_lcrs(entity_id: str):
    """Get LCR history for an entity"""
    lcrs = await basel_service.repository.find_lcrs_by_entity(entity_id)
    return [{"lcr_id": str(l.lcr_id), "lcr_ratio": float(l.lcr_ratio), "reporting_date": str(l.reporting_date)} for l in lcrs]


@router.post("/nsfr/calculate", response_model=dict)
async def calculate_nsfr(request: NSFRCalculationRequest):
    """Calculate Net Stable Funding Ratio"""
    nsfr = await basel_service.calculate_nsfr(
        entity_id=request.entity_id, available_stable_funding=request.available_stable_funding,
        required_stable_funding=request.required_stable_funding
    )
    return {"nsfr_id": str(nsfr.nsfr_id), "nsfr_ratio": float(nsfr.nsfr_ratio), "compliant": nsfr.compliant}


@router.post("/leverage-ratio/calculate", response_model=dict)
async def calculate_leverage_ratio(request: LeverageRatioRequest):
    """Calculate Leverage Ratio"""
    ratio = await basel_service.calculate_leverage_ratio(
        entity_id=request.entity_id, tier1_capital=request.tier1_capital,
        total_exposure=request.total_exposure
    )
    return {"leverage_id": str(ratio.leverage_id), "leverage_ratio": float(ratio.leverage_ratio), "compliant": ratio.compliant}


@router.post("/ccr/calculate", response_model=dict)
async def calculate_ccr(request: CCRRequest):
    """Calculate Counterparty Credit Risk"""
    ccr = await basel_service.calculate_ccr(
        counterparty_id=request.counterparty_id, counterparty_name=request.counterparty_name,
        counterparty_type=request.counterparty_type, approach=request.approach,
        exposure_type=request.exposure_type, gross_exposure=request.gross_exposure,
        netting_benefit=request.netting_benefit, collateral_held=request.collateral_held
    )
    return {"ccr_id": str(ccr.ccr_id), "ead": float(ccr.ead), "rwa": float(ccr.rwa)}


@router.post("/large-exposures", response_model=dict)
async def record_large_exposure(request: LargeExposureRequest):
    """Record a large exposure"""
    exposure = await basel_service.record_large_exposure(
        counterparty_id=request.counterparty_id, counterparty_name=request.counterparty_name,
        entity_id=request.entity_id, gross_exposure=request.gross_exposure,
        net_exposure=request.net_exposure
    )
    return {"exposure_id": str(exposure.exposure_id), "limit_breach": exposure.limit_breach}


@router.get("/large-exposures/breached", response_model=List[dict])
async def list_breached_exposures():
    """List all large exposures that breach limits"""
    exposures = await basel_service.repository.find_large_exposures_breached()
    return [{"exposure_id": str(e.exposure_id), "counterparty_name": e.counterparty_name, "utilization": float(e.limit_utilization)} for e in exposures]


@router.post("/reports/generate", response_model=dict)
async def generate_basel_report(
    entity_id: str = Query(...),
    generated_by: str = Query(...)
):
    """Generate a comprehensive Basel compliance report"""
    report = await basel_service.generate_report(entity_id=entity_id, generated_by=generated_by)
    return {"report_id": str(report.report_id), "report_date": str(report.report_date)}


@router.get("/statistics", response_model=dict)
async def get_basel_statistics():
    """Get Basel compliance statistics"""
    return await basel_service.get_statistics()
