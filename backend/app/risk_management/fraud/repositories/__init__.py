"""Fraud Detection Repositories"""

from .fraud_alert_repository import fraud_alert_repository
from .fraud_case_repository import fraud_case_repository
from .fraud_rule_repository import fraud_rule_repository
from .device_repository import device_repository
from .behavior_repository import behavior_repository
from .ml_model_repository import ml_model_repository
from .investigation_repository import investigation_repository
from .fraud_pattern_repository import fraud_pattern_repository

__all__ = [
    "fraud_alert_repository",
    "fraud_case_repository",
    "fraud_rule_repository",
    "device_repository",
    "behavior_repository",
    "ml_model_repository",
    "investigation_repository",
    "fraud_pattern_repository",
]
