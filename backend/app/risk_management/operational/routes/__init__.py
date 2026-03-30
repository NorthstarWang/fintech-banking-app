"""Operational Risk Routes Package"""

from .business_continuity_routes import router as bcp_router
from .control_routes import router as control_router
from .incident_routes import router as incident_router
from .kri_routes import router as kri_router
from .loss_event_routes import router as loss_event_router
from .rcsa_routes import router as rcsa_router
from .technology_risk_routes import router as tech_risk_router
from .vendor_risk_routes import router as vendor_router

__all__ = [
    "bcp_router",
    "control_router",
    "incident_router",
    "kri_router",
    "loss_event_router",
    "rcsa_router",
    "tech_risk_router",
    "vendor_router",
]
