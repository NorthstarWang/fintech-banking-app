"""Data Quality & MDM Routes"""

from .data_quality_routes import router as data_quality_router
from .data_profiling_routes import router as data_profiling_router
from .data_lineage_routes import router as data_lineage_router
from .master_data_routes import router as master_data_router
from .data_governance_routes import router as data_governance_router
from .data_catalog_routes import router as data_catalog_router
from .data_validation_routes import router as data_validation_router

__all__ = [
    "data_quality_router",
    "data_profiling_router",
    "data_lineage_router",
    "master_data_router",
    "data_governance_router",
    "data_catalog_router",
    "data_validation_router",
]
