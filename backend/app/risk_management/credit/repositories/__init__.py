"""Credit Risk Repositories"""

from .credit_score_repository import credit_score_repository
from .loan_repository import loan_repository
from .portfolio_repository import portfolio_repository
from .exposure_repository import exposure_repository
from .collateral_repository import collateral_repository
from .credit_limit_repository import credit_limit_repository
from .rating_repository import rating_repository
from .risk_parameter_repository import risk_parameter_repository

__all__ = [
    "credit_score_repository",
    "loan_repository",
    "portfolio_repository",
    "exposure_repository",
    "collateral_repository",
    "credit_limit_repository",
    "rating_repository",
    "risk_parameter_repository",
]
