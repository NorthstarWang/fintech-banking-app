"""Regulatory Compliance Services Package"""

from .basel_service import basel_service
from .gdpr_service import gdpr_service
from .kyc_service import kyc_service
from .capital_service import capital_service
from .reporting_service import reporting_service
from .sanctions_service import sanctions_service
from .consumer_protection_service import consumer_protection_service
from .sox_service import sox_service

__all__ = [
    "basel_service",
    "gdpr_service",
    "kyc_service",
    "capital_service",
    "reporting_service",
    "sanctions_service",
    "consumer_protection_service",
    "sox_service",
]
