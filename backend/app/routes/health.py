"""
Health check endpoints for monitoring and load balancers.
"""
import os
from datetime import datetime

import psutil
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 if the service is running.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "bankflow-api",
            "version": os.getenv("APP_VERSION", "1.0.0")
        }
    )


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    Checks if the application is ready to serve requests.
    """
    checks = {
        "database": True,  # Check database connection
        "cache": True,     # Check cache connection if applicable
        "dependencies": True  # Check external dependencies
    }

    # Perform actual checks here
    try:
        from ..storage.memory_adapter import memory_storage
        _ = memory_storage.get_users()  # Simple database check
        checks["database"] = True
    except Exception:
        checks["database"] = False

    all_healthy = all(checks.values())

    return JSONResponse(
        status_code=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "ready" if all_healthy else "not ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        }
    )


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check endpoint.
    Returns basic system metrics.
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "alive",
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_mb": memory.available / (1024 * 1024)
                }
            }
        )
    except Exception:
        # If we can't get metrics, still return alive
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "alive",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
