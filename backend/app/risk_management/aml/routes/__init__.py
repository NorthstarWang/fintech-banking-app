"""AML Routes Package"""

from .alert_routes import router as alert_router
from .case_routes import router as case_router
from .kyc_routes import router as kyc_router
from .monitoring_routes import router as monitoring_router
from .risk_routes import router as risk_router
from .sanctions_routes import router as sanctions_router
from .sar_routes import router as sar_router
from .watchlist_routes import router as watchlist_router

__all__ = [
    "alert_router",
    "case_router",
    "kyc_router",
    "monitoring_router",
    "risk_router",
    "sanctions_router",
    "sar_router",
    "watchlist_router",
]
