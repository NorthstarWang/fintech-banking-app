"""VaR Models - Value at Risk calculation models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field


class VaRMethod(str, Enum):
    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"


class ConfidenceLevel(str, Enum):
    CL_95 = "95"
    CL_99 = "99"
    CL_99_5 = "99.5"


class VaRCalculation(BaseModel):
    calculation_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    calculation_date: date
    method: VaRMethod
    confidence_level: ConfidenceLevel
    time_horizon_days: int = 1
    var_amount: float
    var_percentage: float
    portfolio_value: float
    expected_shortfall: Optional[float] = None
    component_var: Dict[str, float] = {}
    marginal_var: Dict[str, float] = {}
    incremental_var: Dict[str, float] = {}
    diversification_benefit: float = 0.0
    undiversified_var: float = 0.0
    model_parameters: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VaRBacktest(BaseModel):
    backtest_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    backtest_start: date
    backtest_end: date
    method: VaRMethod
    confidence_level: ConfidenceLevel
    total_observations: int
    exceptions: int
    exception_rate: float
    expected_exceptions: float
    kupiec_test_stat: float
    kupiec_p_value: float
    christoffersen_test_stat: Optional[float] = None
    traffic_light_zone: str  # green, yellow, red
    pass_fail: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VaRLimit(BaseModel):
    limit_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    limit_type: str  # var, expected_shortfall
    limit_amount: float
    current_var: float
    utilization_percentage: float
    warning_threshold: float = 80.0
    breach_status: bool = False
    effective_date: date
    expiry_date: Optional[date] = None
    approved_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VaRException(BaseModel):
    exception_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    exception_date: date
    predicted_var: float
    actual_loss: float
    exception_amount: float
    exception_multiplier: float
    explanation: Optional[str] = None
    market_conditions: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VaRStatistics(BaseModel):
    total_calculations: int = 0
    average_var: float = 0.0
    total_exceptions: int = 0
    average_exception_rate: float = 0.0
    by_method: Dict[str, int] = {}
