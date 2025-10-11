"""Data models for analytics service."""
from pydantic import BaseModel
from typing import Optional, Dict, Any


class AnalyticsQueryRequest(BaseModel):
    """Request to query analytics data."""
    user_id: int
    metric: str  # e.g., "cash_flow", "spending_trends", "investment_performance"
    period_days: Optional[int] = 30
    filters: Optional[Dict[str, Any]] = None


class CashFlowResponse(BaseModel):
    """Cash flow analytics."""
    period_days: int
    money_in: float
    money_out: float
    net_flow: float
    savings_rate: float
    categories: list[Dict[str, Any]]


class SpendingTrendResponse(BaseModel):
    """Spending trend analytics."""
    period_months: int
    total_categories: int
    trends: list[Dict[str, Any]]


class HealthScoreResponse(BaseModel):
    """Financial health score."""
    overall_score: int
    rating: str
    factors: list[Dict[str, Any]]
    recommendations: list[str]


class AnomalyResponse(BaseModel):
    """Anomaly detection results."""
    anomalies: list[Dict[str, Any]]
    timestamp: str
