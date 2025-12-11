"""Credit Risk Routes"""

from .credit_score_routes import router as credit_score_router
from .loan_routes import router as loan_router
from .portfolio_routes import router as portfolio_router
from .exposure_routes import router as exposure_router
from .collateral_routes import router as collateral_router
from .credit_limit_routes import router as credit_limit_router
from .rating_routes import router as rating_router
from .risk_parameter_routes import router as risk_parameter_router

__all__ = [
    "credit_score_router",
    "loan_router",
    "portfolio_router",
    "exposure_router",
    "collateral_router",
    "credit_limit_router",
    "rating_router",
    "risk_parameter_router",
]
