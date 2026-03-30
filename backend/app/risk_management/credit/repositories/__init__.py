"""Credit Risk Repositories"""

from .collateral_repository import collateral_repository
from .credit_limit_repository import credit_limit_repository
from .credit_score_repository import credit_score_repository
from .exposure_repository import exposure_repository
from .loan_repository import loan_repository
from .portfolio_repository import portfolio_repository
from .rating_repository import rating_repository
from .risk_parameter_repository import risk_parameter_repository

__all__ = [
    "collateral_repository",
    "credit_limit_repository",
    "credit_score_repository",
    "exposure_repository",
    "loan_repository",
    "portfolio_repository",
    "rating_repository",
    "risk_parameter_repository",
]
