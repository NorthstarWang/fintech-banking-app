"""Operational Risk Routes Package"""

from .incident_routes import router as incident_router
from .loss_event_routes import router as loss_event_router
from .rcsa_routes import router as rcsa_router
from .kri_routes import router as kri_router
from .control_routes import router as control_router
from .business_continuity_routes import router as bcp_router
from .vendor_risk_routes import router as vendor_router
from .technology_risk_routes import router as tech_risk_router

__all__ = [
    "incident_router",
    "loss_event_router",
    "rcsa_router",
    "kri_router",
    "control_router",
    "bcp_router",
    "vendor_router",
    "tech_risk_router",
]
