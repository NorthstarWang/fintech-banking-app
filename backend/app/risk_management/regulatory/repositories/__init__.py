"""Regulatory Compliance Repositories"""

from .basel_repository import basel_repository
from .gdpr_repository import gdpr_repository
from .kyc_repository import kyc_repository
from .capital_repository import capital_repository
from .reporting_repository import reporting_repository
from .sanctions_repository import sanctions_repository
from .consumer_protection_repository import consumer_protection_repository
from .sox_repository import sox_repository

__all__ = [
    "basel_repository",
    "gdpr_repository",
    "kyc_repository",
    "capital_repository",
    "reporting_repository",
    "sanctions_repository",
    "consumer_protection_repository",
    "sox_repository",
]
