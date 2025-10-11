"""
API Gateway - Routes requests to microservices with API key validation.
"""
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from typing import Optional

from ..core.correlation_id import CorrelationIDMiddleware, StructuredLogger
from ..core.api_client import get_client_factory, ServiceClient
from ..core.service_registry import get_registry, init_registry
from ..core.health_check import ServiceHealthChecker

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger_instance = logging.getLogger(__name__)
logger = StructuredLogger(logger_instance)

# Initialize service
app = FastAPI(
    title="API Gateway",
    description="Routes requests to microservices",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware, service_name="api-gateway")

# Initialize service components
registry = init_registry()
client_factory = get_client_factory()
health_checker = ServiceHealthChecker("api-gateway")

# API key validation
GATEWAY_API_KEY = os.getenv("GATEWAY_API_KEY", "gateway-key-dev")
ALLOWED_API_KEYS = os.getenv("ALLOWED_API_KEYS", "client-key-1,client-key-2").split(",")


def validate_api_key(request: Request) -> str:
    """Validate API key from request."""
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header"
        )

    if api_key not in ALLOWED_API_KEYS and api_key != GATEWAY_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )

    return api_key


@app.on_event("startup")
async def startup():
    """Initialize gateway on startup."""
    logger.info("API Gateway starting up", service="api-gateway")

    # Register this gateway instance
    registry.register(
        service_name="api-gateway",
        instance_id=os.getenv("GATEWAY_INSTANCE_ID", "gateway-1"),
        host=os.getenv("GATEWAY_HOST", "localhost"),
        port=int(os.getenv("GATEWAY_PORT", "8000")),
        health_check_url="/health",
        api_key=GATEWAY_API_KEY,
        metadata={"version": "1.0.0"}
    )


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    logger.info("API Gateway shutting down", service="api-gateway")
    registry.deregister(
        "api-gateway",
        os.getenv("GATEWAY_INSTANCE_ID", "gateway-1")
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check all registered services
    status_data = registry.get_registry_status()

    # Check local health
    health_status = await health_checker.run_all_checks()

    all_healthy = (
        health_status["status"] == "healthy" and
        all(
            s["healthy_instances"] > 0
            for s in status_data.values()
        )
    )

    status_code = 200 if all_healthy else 503

    return JSONResponse({
        "service": "api-gateway",
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": health_status["timestamp"],
        "services": status_data
    }, status_code=status_code)


@app.get("/registry")
async def get_registry_status(api_key: str = Depends(validate_api_key)):
    """Get service registry status."""
    return registry.get_registry_status()


# ============== AUTH SERVICE ROUTES ==============

@app.post("/auth/register")
async def register(request: Request, api_key: str = Depends(validate_api_key)):
    """Proxy to auth service - register user."""
    client = await client_factory.get_client("auth-service")
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )

    body = await request.json()
    result = await client.post("/register", json=body)

    if result["status"] == "error":
        raise HTTPException(
            status_code=result["error_code"],
            detail=result["error_message"]
        )

    return result["data"]


@app.post("/auth/login")
async def login(request: Request, api_key: str = Depends(validate_api_key)):
    """Proxy to auth service - login user."""
    client = await client_factory.get_client("auth-service")
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )

    body = await request.json()
    result = await client.post("/login", json=body)

    if result["status"] == "error":
        raise HTTPException(
            status_code=result["error_code"],
            detail=result["error_message"]
        )

    return result["data"]


@app.get("/auth/me")
async def get_current_user(request: Request, api_key: str = Depends(validate_api_key)):
    """Proxy to auth service - get current user."""
    client = await client_factory.get_client("auth-service")
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )

    # Pass through authorization header
    auth_header = request.headers.get("Authorization")
    headers = {"Authorization": auth_header} if auth_header else {}

    result = await client.get("/me", headers=headers)

    if result["status"] == "error":
        raise HTTPException(
            status_code=result["error_code"],
            detail=result["error_message"]
        )

    return result["data"]


# ============== NOTIFICATION SERVICE ROUTES ==============

@app.post("/notifications/send")
async def send_notification(request: Request, api_key: str = Depends(validate_api_key)):
    """Proxy to notification service - send notification."""
    client = await client_factory.get_client("notification-service")
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification service unavailable"
        )

    body = await request.json()
    result = await client.post("/send", json=body)

    if result["status"] == "error":
        raise HTTPException(
            status_code=result["error_code"],
            detail=result["error_message"]
        )

    return result["data"]


@app.get("/notifications/user/{user_id}")
async def get_user_notifications(
    user_id: int,
    limit: int = 20,
    offset: int = 0,
    api_key: str = Depends(validate_api_key)
):
    """Proxy to notification service - get user notifications."""
    client = await client_factory.get_client("notification-service")
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification service unavailable"
        )

    result = await client.get(
        f"/user/{user_id}",
        params={"limit": limit, "offset": offset}
    )

    if result["status"] == "error":
        raise HTTPException(
            status_code=result["error_code"],
            detail=result["error_message"]
        )

    return result["data"]


# ============== ANALYTICS SERVICE ROUTES ==============

@app.post("/analytics/query")
async def query_analytics(request: Request, api_key: str = Depends(validate_api_key)):
    """Proxy to analytics service - query analytics."""
    client = await client_factory.get_client("analytics-service")
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics service unavailable"
        )

    body = await request.json()
    result = await client.post("/query", json=body)

    if result["status"] == "error":
        raise HTTPException(
            status_code=result["error_code"],
            detail=result["error_message"]
        )

    return result["data"]


@app.get("/analytics/health/detailed")
async def analytics_detailed_health(api_key: str = Depends(validate_api_key)):
    """Get detailed analytics service health."""
    client = await client_factory.get_client("analytics-service")
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics service unavailable"
        )

    result = await client.get("/health/detailed")

    if result["status"] == "error":
        raise HTTPException(
            status_code=result["error_code"],
            detail=result["error_message"]
        )

    return result["data"]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("GATEWAY_HOST", "0.0.0.0"),
        port=int(os.getenv("GATEWAY_PORT", "8000"))
    )
