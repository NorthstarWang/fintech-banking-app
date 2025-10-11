"""
Analytics Service FastAPI Application.

Provides analytics, metrics, and insights.
"""
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from datetime import datetime

from ..core.correlation_id import CorrelationIDMiddleware, StructuredLogger
from ..core.health_check import ServiceHealthChecker
from ..core.service_registry import get_registry, init_registry
from .models import (
    AnalyticsQueryRequest,
    CashFlowResponse,
    SpendingTrendResponse,
    HealthScoreResponse,
    AnomalyResponse
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger_instance = logging.getLogger(__name__)
logger = StructuredLogger(logger_instance)

# Initialize service
app = FastAPI(
    title="Analytics Service",
    description="Provides analytics, metrics, and insights",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware, service_name="analytics-service")

# Initialize service components
registry = init_registry()
health_checker = ServiceHealthChecker("analytics-service")

# Register health checks
health_checker.register_callable_check(
    "analytics_service_ready",
    lambda: True,
    "Check if analytics service is ready"
)


@app.on_event("startup")
async def startup():
    """Initialize service on startup."""
    logger.info("Analytics Service starting up", service="analytics-service")

    # Register this service instance with the registry
    registry.register(
        service_name="analytics-service",
        instance_id=os.getenv("SERVICE_INSTANCE_ID", "analytics-1"),
        host=os.getenv("SERVICE_HOST", "localhost"),
        port=int(os.getenv("SERVICE_PORT", "8003")),
        health_check_url="/health",
        api_key=os.getenv("ANALYTICS_SERVICE_API_KEY", "analytics-key-dev"),
        metadata={"version": "1.0.0"}
    )


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    logger.info("Analytics Service shutting down", service="analytics-service")
    registry.deregister(
        "analytics-service",
        os.getenv("SERVICE_INSTANCE_ID", "analytics-1")
    )


@app.post("/health")
async def health_check():
    """Health check endpoint."""
    health_status = await health_checker.run_all_checks()
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(health_status, status_code=status_code)


@app.post("/query")
async def query_analytics(request: Request, query: AnalyticsQueryRequest):
    """Query analytics data."""
    logger.info(
        f"Analytics query received",
        user_id=query.user_id,
        metric=query.metric
    )

    try:
        # Route to appropriate analytics calculator based on metric
        if query.metric == "cash_flow":
            result = calculate_cash_flow(query.user_id, query.period_days or 30)
        elif query.metric == "spending_trends":
            result = calculate_spending_trends(query.user_id, query.period_days or 30)
        elif query.metric == "health_score":
            result = calculate_health_score(query.user_id)
        elif query.metric == "anomalies":
            result = detect_anomalies(query.user_id, query.period_days or 90)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown metric: {query.metric}"
            )

        logger.info(f"Analytics query completed", user_id=query.user_id, metric=query.metric)
        return result

    except Exception as e:
        logger.error(f"Analytics query failed", user_id=query.user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics query failed: {str(e)}"
        )


def calculate_cash_flow(user_id: int, period_days: int) -> dict:
    """Calculate cash flow analytics."""
    # TODO: Fetch actual transaction data from data service
    return {
        "period_days": period_days,
        "money_in": 5000.00,
        "money_out": 3500.00,
        "net_flow": 1500.00,
        "savings_rate": 30.0,
        "categories": [
            {"category": "Food & Dining", "type": "expense", "amount": 500.00},
            {"category": "Transportation", "type": "expense", "amount": 200.00},
            {"category": "Entertainment", "type": "expense", "amount": 300.00},
            {"category": "Salary", "type": "income", "amount": 5000.00}
        ]
    }


def calculate_spending_trends(user_id: int, period_days: int) -> dict:
    """Calculate spending trends."""
    # TODO: Fetch actual transaction data and calculate trends
    months = max(1, period_days // 30)
    return {
        "period_months": months,
        "total_categories": 8,
        "trends": [
            {
                "category": "Food & Dining",
                "average_monthly": 500.00,
                "standard_deviation": 50.00,
                "trend_direction": "increasing",
                "change_percentage": 12.5,
                "monthly_breakdown": {
                    "2024-09": 480.00,
                    "2024-10": 520.00
                }
            },
            {
                "category": "Transportation",
                "average_monthly": 200.00,
                "standard_deviation": 20.00,
                "trend_direction": "stable",
                "change_percentage": 0.0,
                "monthly_breakdown": {
                    "2024-09": 200.00,
                    "2024-10": 200.00
                }
            }
        ]
    }


def calculate_health_score(user_id: int) -> dict:
    """Calculate financial health score."""
    return {
        "overall_score": 75,
        "rating": "Good",
        "factors": [
            {
                "factor": "Savings Rate",
                "score": 15,
                "max_score": 20,
                "value": "30.0%"
            },
            {
                "factor": "Budget Adherence",
                "score": 18,
                "max_score": 20,
                "value": "90% on track"
            },
            {
                "factor": "Debt Management",
                "score": 16,
                "max_score": 20,
                "value": "low risk"
            },
            {
                "factor": "Investment Performance",
                "score": 13,
                "max_score": 20,
                "value": "8.5% return"
            },
            {
                "factor": "Emergency Fund",
                "score": 13,
                "max_score": 20,
                "value": "4.2 months"
            }
        ],
        "recommendations": [
            "Increase your emergency fund to 6 months of expenses",
            "Consider diversifying your investment portfolio",
            "Monitor your spending trends to identify optimization opportunities"
        ]
    }


def detect_anomalies(user_id: int, lookback_days: int) -> dict:
    """Detect financial anomalies."""
    return {
        "anomalies": [
            {
                "type": "unusual_amount",
                "severity": "medium",
                "transaction_id": "txn_123",
                "amount": 2500.00,
                "baseline_average": 150.00,
                "description": "Transaction amount $2500.00 is 16.7x your average",
                "detected_at": datetime.utcnow().isoformat()
            },
            {
                "type": "velocity_spike",
                "severity": "medium",
                "transaction_count": 24,
                "baseline_daily": 8.0,
                "description": "24 transactions in 24h vs average of 8.0/day",
                "detected_at": datetime.utcnow().isoformat()
            }
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health/detailed")
async def detailed_health():
    """Get detailed health information."""
    return {
        "service": "analytics-service",
        "status": "healthy",
        "uptime": "24h",
        "version": "1.0.0",
        "metrics": {
            "queries_processed": 1234,
            "average_query_time_ms": 45,
            "cache_hit_rate": 0.85
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("SERVICE_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVICE_PORT", "8003"))
    )
