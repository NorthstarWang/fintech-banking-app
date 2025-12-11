"""Interest Rate Models - Interest rate risk management models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field


class RateType(str, Enum):
    OVERNIGHT = "overnight"
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"


class CurveType(str, Enum):
    YIELD = "yield"
    DISCOUNT = "discount"
    FORWARD = "forward"
    ZERO = "zero"


class InterestRateCurve(BaseModel):
    curve_id: UUID = Field(default_factory=uuid4)
    curve_name: str
    curve_type: CurveType
    currency: str
    reference_date: date
    tenors: List[str] = []
    rates: List[float] = []
    interpolation_method: str = "linear"
    source: str
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DurationAnalysis(BaseModel):
    analysis_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    analysis_date: date
    modified_duration: float
    macaulay_duration: float
    effective_duration: float
    dollar_duration: float
    dv01: float  # Dollar Value of 01 basis point
    convexity: float
    portfolio_value: float
    yield_to_maturity: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GapAnalysis(BaseModel):
    analysis_id: UUID = Field(default_factory=uuid4)
    analysis_date: date
    time_buckets: List[str] = []
    rate_sensitive_assets: List[float] = []
    rate_sensitive_liabilities: List[float] = []
    gap_amounts: List[float] = []
    cumulative_gap: List[float] = []
    gap_ratio: List[float] = []
    net_interest_income_impact: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RateShockScenario(BaseModel):
    scenario_id: UUID = Field(default_factory=uuid4)
    scenario_name: str
    scenario_type: str  # parallel, twist, steepening, flattening
    shock_amounts: Dict[str, float] = {}
    base_curve_id: UUID
    stressed_rates: Dict[str, float] = {}
    pnl_impact: float
    duration_impact: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InterestRateRisk(BaseModel):
    risk_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    assessment_date: date
    repricing_risk: float
    yield_curve_risk: float
    basis_risk: float
    optionality_risk: float
    total_ir_risk: float
    economic_value_sensitivity: float
    earnings_at_risk: float
    net_interest_income_at_risk: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InterestRateStatistics(BaseModel):
    total_curves: int = 0
    average_duration: float = 0.0
    total_dv01: float = 0.0
    by_currency: Dict[str, float] = {}
