"""Fraud Detection Routes"""

from .fraud_alert_routes import router as fraud_alert_router
from .fraud_case_routes import router as fraud_case_router
from .fraud_rule_routes import router as fraud_rule_router
from .device_routes import router as device_router
from .behavior_routes import router as behavior_router
from .ml_model_routes import router as ml_model_router
from .investigation_routes import router as investigation_router
from .fraud_pattern_routes import router as fraud_pattern_router

__all__ = [
    "fraud_alert_router",
    "fraud_case_router",
    "fraud_rule_router",
    "device_router",
    "behavior_router",
    "ml_model_router",
    "investigation_router",
    "fraud_pattern_router",
]
