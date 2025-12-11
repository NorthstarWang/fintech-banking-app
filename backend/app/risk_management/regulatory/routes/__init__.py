"""Regulatory Compliance Routes"""

from .basel_routes import router as basel_router
from .gdpr_routes import router as gdpr_router
from .kyc_routes import router as kyc_router
from .capital_routes import router as capital_router
from .reporting_routes import router as reporting_router
from .sanctions_routes import router as sanctions_router
from .consumer_protection_routes import router as consumer_protection_router
from .sox_routes import router as sox_router

__all__ = [
    "basel_router",
    "gdpr_router",
    "kyc_router",
    "capital_router",
    "reporting_router",
    "sanctions_router",
    "consumer_protection_router",
    "sox_router",
]
