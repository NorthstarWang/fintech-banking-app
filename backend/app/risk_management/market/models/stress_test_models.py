"""Stress Test Models - Market risk stress testing models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field


class ScenarioType(str, Enum):
    HISTORICAL = "historical"
    HYPOTHETICAL = "hypothetical"
    REVERSE = "reverse"
    SENSITIVITY = "sensitivity"


class ScenarioSeverity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"


class StressScenario(BaseModel):
    scenario_id: UUID = Field(default_factory=uuid4)
    scenario_name: str
    scenario_type: ScenarioType
    severity: ScenarioSeverity
    description: str
    equity_shocks: Dict[str, float] = {}
    fx_shocks: Dict[str, float] = {}
    ir_shocks: Dict[str, float] = {}
    credit_spread_shocks: Dict[str, float] = {}
    commodity_shocks: Dict[str, float] = {}
    volatility_shocks: Dict[str, float] = {}
    correlation_adjustments: Dict[str, float] = {}
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StressTestResult(BaseModel):
    result_id: UUID = Field(default_factory=uuid4)
    scenario_id: UUID
    portfolio_id: UUID
    test_date: date
    portfolio_value_before: float
    portfolio_value_after: float
    pnl_impact: float
    pnl_impact_percentage: float
    var_before: float
    var_after: float
    var_change: float
    risk_factor_contributions: Dict[str, float] = {}
    position_level_impacts: List[Dict[str, Any]] = []
    breach_limits: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HistoricalScenario(BaseModel):
    scenario_id: UUID = Field(default_factory=uuid4)
    scenario_name: str
    event_name: str
    event_date: date
    event_duration_days: int
    description: str
    market_data_changes: Dict[str, Dict[str, float]] = {}
    max_drawdown: float
    recovery_days: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SensitivityAnalysis(BaseModel):
    analysis_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    analysis_date: date
    risk_factor: str
    shock_sizes: List[float] = []
    pnl_impacts: List[float] = []
    sensitivity: float
    convexity: float
    breakeven_point: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReverseStressTest(BaseModel):
    test_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    test_date: date
    target_loss: float
    identified_scenarios: List[Dict[str, Any]] = []
    probability_assessment: str
    risk_factors_required: List[str] = []
    plausibility_score: float = Field(ge=0, le=100)
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StressTestStatistics(BaseModel):
    total_scenarios: int = 0
    total_tests_run: int = 0
    average_pnl_impact: float = 0.0
    worst_case_loss: float = 0.0
    by_severity: Dict[str, int] = {}
