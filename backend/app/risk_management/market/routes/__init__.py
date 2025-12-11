"""Market Risk Routes Package"""

from .var_routes import router as var_router
from .interest_rate_routes import router as interest_rate_router
from .fx_risk_routes import router as fx_risk_router
from .equity_risk_routes import router as equity_risk_router
from .commodity_routes import router as commodity_router
from .stress_test_routes import router as stress_test_router
from .greeks_routes import router as greeks_router
from .position_routes import router as position_router

__all__ = [
    "var_router",
    "interest_rate_router",
    "fx_risk_router",
    "equity_risk_router",
    "commodity_router",
    "stress_test_router",
    "greeks_router",
    "position_router",
]
