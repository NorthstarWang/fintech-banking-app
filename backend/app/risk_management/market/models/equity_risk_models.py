"""Equity Risk Models - Equity risk management models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field


class EquityPositionType(str, Enum):
    STOCK = "stock"
    ETF = "etf"
    INDEX = "index"
    OPTION = "option"
    FUTURE = "future"
    WARRANT = "warrant"


class EquityPosition(BaseModel):
    position_id: UUID = Field(default_factory=uuid4)
    position_type: EquityPositionType
    ticker: str
    exchange: str
    quantity: float
    direction: str  # long, short
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    beta: float = 1.0
    sector: str
    country: str
    currency: str
    portfolio_id: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EquityExposure(BaseModel):
    exposure_id: UUID = Field(default_factory=uuid4)
    exposure_type: str  # sector, country, market_cap, style
    exposure_key: str
    gross_exposure: float
    net_exposure: float
    long_exposure: float
    short_exposure: float
    percentage_of_portfolio: float
    beta_adjusted_exposure: float
    var_contribution: float
    as_of_date: date
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BetaAnalysis(BaseModel):
    analysis_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    analysis_date: date
    portfolio_beta: float
    benchmark_ticker: str
    correlation: float
    r_squared: float
    tracking_error: float
    information_ratio: float
    treynor_ratio: float
    jensen_alpha: float
    systematic_risk: float
    idiosyncratic_risk: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EquityFactorExposure(BaseModel):
    exposure_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    analysis_date: date
    market_factor: float
    size_factor: float
    value_factor: float
    momentum_factor: float
    quality_factor: float
    volatility_factor: float
    factor_var: Dict[str, float] = {}
    residual_risk: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EquityScenario(BaseModel):
    scenario_id: UUID = Field(default_factory=uuid4)
    scenario_name: str
    scenario_type: str
    market_shock: float
    sector_shocks: Dict[str, float] = {}
    volatility_shock: float
    correlation_change: float
    pnl_impact: float
    beta_impact: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EquityRiskStatistics(BaseModel):
    total_positions: int = 0
    total_market_value: float = 0.0
    portfolio_beta: float = 0.0
    equity_var: float = 0.0
    by_sector: Dict[str, float] = {}
