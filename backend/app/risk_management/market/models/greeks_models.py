"""Greeks Models - Options greeks and sensitivities"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field


class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"


class OptionStyle(str, Enum):
    EUROPEAN = "european"
    AMERICAN = "american"
    BERMUDAN = "bermudan"
    ASIAN = "asian"
    BARRIER = "barrier"


class OptionPosition(BaseModel):
    position_id: UUID = Field(default_factory=uuid4)
    underlying: str
    underlying_type: str  # equity, fx, commodity, rate
    option_type: OptionType
    option_style: OptionStyle
    strike_price: float
    expiry_date: date
    quantity: float
    direction: str  # long, short
    premium: float
    current_price: float
    intrinsic_value: float
    time_value: float
    underlying_price: float
    implied_volatility: float
    portfolio_id: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GreeksCalculation(BaseModel):
    calculation_id: UUID = Field(default_factory=uuid4)
    position_id: UUID
    calculation_date: date
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    vanna: float = 0.0
    volga: float = 0.0
    charm: float = 0.0
    dollar_delta: float
    dollar_gamma: float
    dollar_theta: float
    dollar_vega: float
    model_used: str = "black_scholes"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PortfolioGreeks(BaseModel):
    portfolio_id: UUID
    calculation_date: date
    total_delta: float
    total_gamma: float
    total_theta: float
    total_vega: float
    total_rho: float
    net_delta: float
    net_gamma: float
    gamma_exposure: float
    vega_exposure: float
    theta_decay: float
    by_underlying: Dict[str, Dict[str, float]] = {}
    by_expiry: Dict[str, Dict[str, float]] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GreeksLimit(BaseModel):
    limit_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    greek_type: str
    limit_amount: float
    current_value: float
    utilization_percentage: float
    breach_status: bool = False
    effective_date: date
    approved_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GreeksSensitivity(BaseModel):
    sensitivity_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    analysis_date: date
    underlying_move_percentage: float
    delta_pnl: float
    gamma_pnl: float
    total_pnl: float
    vol_move_percentage: float
    vega_pnl: float
    time_decay_days: int
    theta_pnl: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GreeksStatistics(BaseModel):
    total_option_positions: int = 0
    net_portfolio_delta: float = 0.0
    net_portfolio_gamma: float = 0.0
    total_vega_exposure: float = 0.0
    daily_theta_decay: float = 0.0
