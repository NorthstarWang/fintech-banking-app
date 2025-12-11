"""FX Risk Models - Foreign exchange risk management models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field


class FXPositionType(str, Enum):
    SPOT = "spot"
    FORWARD = "forward"
    SWAP = "swap"
    OPTION = "option"
    NDF = "ndf"


class FXPosition(BaseModel):
    position_id: UUID = Field(default_factory=uuid4)
    position_type: FXPositionType
    currency_pair: str
    base_currency: str
    quote_currency: str
    notional_amount: float
    direction: str  # long, short
    spot_rate: float
    forward_rate: Optional[float] = None
    value_date: date
    maturity_date: Optional[date] = None
    mtm_value: float = 0.0
    unrealized_pnl: float = 0.0
    delta: float = 0.0
    portfolio_id: UUID
    counterparty_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FXExposure(BaseModel):
    exposure_id: UUID = Field(default_factory=uuid4)
    currency: str
    gross_long: float
    gross_short: float
    net_position: float
    spot_equivalent: float
    delta_equivalent: float
    var_contribution: float
    stress_loss: float
    hedge_ratio: float = 0.0
    as_of_date: date
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FXRate(BaseModel):
    rate_id: UUID = Field(default_factory=uuid4)
    currency_pair: str
    base_currency: str
    quote_currency: str
    spot_rate: float
    bid_rate: float
    ask_rate: float
    mid_rate: float
    forward_points: Dict[str, float] = {}
    volatility: float
    rate_date: date
    rate_time: datetime
    source: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FXVolatilitySurface(BaseModel):
    surface_id: UUID = Field(default_factory=uuid4)
    currency_pair: str
    surface_date: date
    tenors: List[str] = []
    deltas: List[float] = []
    volatilities: List[List[float]] = []
    atm_vols: Dict[str, float] = {}
    risk_reversals: Dict[str, float] = {}
    butterflies: Dict[str, float] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FXScenario(BaseModel):
    scenario_id: UUID = Field(default_factory=uuid4)
    scenario_name: str
    scenario_type: str  # historical, hypothetical
    rate_shocks: Dict[str, float] = {}
    vol_shocks: Dict[str, float] = {}
    correlation_shocks: Dict[str, float] = {}
    pnl_impact: float
    var_impact: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FXRiskStatistics(BaseModel):
    total_positions: int = 0
    total_notional: float = 0.0
    net_fx_exposure: float = 0.0
    fx_var: float = 0.0
    by_currency: Dict[str, float] = {}
