"""Market Risk Routes Package"""

from .commodity_routes import router as commodity_router
from .equity_risk_routes import router as equity_risk_router
from .fx_risk_routes import router as fx_risk_router
from .greeks_routes import router as greeks_router
from .interest_rate_routes import router as interest_rate_router
from .position_routes import router as position_router
from .stress_test_routes import router as stress_test_router
from .var_routes import router as var_router

__all__ = [
    "commodity_router",
    "equity_risk_router",
    "fx_risk_router",
    "greeks_router",
    "interest_rate_router",
    "position_router",
    "stress_test_router",
    "var_router",
]
