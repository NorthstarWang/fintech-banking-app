"""
Health check endpoints for monitoring and load balancers.
Provides comprehensive health monitoring for all backend systems independently.
"""
import os
from datetime import datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from ..services.health_service import (
    AuthenticationHealthAdapter,
    CacheHealthAdapter,
    DatabaseHealthAdapter,
    HealthMonitor,
    HealthStatus,
    SystemMetricsAdapter,
)
from ..storage.memory_adapter import db

router = APIRouter()

# Initialize health monitor with adapters
_health_monitor = HealthMonitor()
_health_monitor.register_adapter(DatabaseHealthAdapter(db))
_health_monitor.register_adapter(AuthenticationHealthAdapter())
_health_monitor.register_adapter(CacheHealthAdapter())
_health_monitor.register_adapter(SystemMetricsAdapter())


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.
    Returns 200 if healthy, 503 if any critical system is unhealthy.
    Includes detailed response times for all critical services.
    """
    # Check all systems
    health_results = await _health_monitor.check_all_systems()

    # Convert results to dict format
    systems_health = {
        name: health.to_dict()
        for name, health in health_results.items()
    }

    # Determine overall status
    overall_status = _health_monitor.get_overall_status()

    # Calculate total response time
    total_response_time = sum(
        health.response_time_ms for health in health_results.values()
    )

    status_code = status.HTTP_200_OK
    if overall_status == HealthStatus.UNHEALTHY:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif overall_status == HealthStatus.DEGRADED:
        status_code = status.HTTP_200_OK  # Still serve but indicate degradation

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "bankflow-api",
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "systems": systems_health,
            "performance": {
                "total_check_time_ms": round(total_response_time, 2),
                "system_count": len(systems_health)
            }
        }
    )


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    Checks if the application is ready to serve requests.
    Returns 503 if any critical system is not ready.
    """
    # Check all systems
    health_results = await _health_monitor.check_all_systems()

    # Determine readiness - all critical systems must be healthy
    critical_systems = ["database", "authentication"]
    is_ready = all(
        health_results.get(system, HealthStatus.UNHEALTHY).status == HealthStatus.HEALTHY
        for system in critical_systems
        if system in health_results
    )

    systems_health = {
        name: health.to_dict()
        for name, health in health_results.items()
    }

    return JSONResponse(
        status_code=status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "ready" if is_ready else "not ready",
            "timestamp": datetime.utcnow().isoformat(),
            "systems": systems_health,
            "critical_systems": {
                system: systems_health.get(system, {}).get("status", "unknown")
                for system in critical_systems
            }
        }
    )


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check endpoint.
    Returns basic system metrics and confirms service is running.
    Always returns 200 unless there's a critical system failure.
    """
    # Check all systems
    health_results = await _health_monitor.check_all_systems()

    # Get system resources health
    system_resources = health_results.get("system_resources", {})

    systems_health = {
        name: health.to_dict()
        for name, health in health_results.items()
    }

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": system_resources.get("details", {}) if hasattr(system_resources, "details") else
                       systems_health.get("system_resources", {}).get("details", {}),
            "systems": systems_health
        }
    )


@router.get("/health/systems/{system_name}")
async def system_health_check(system_name: str):
    """
    Check health of a specific system.
    Returns detailed health information for a single system.
    This allows monitoring systems independently.
    """
    # Get the specific system's last known health
    system_health = _health_monitor.get_system_health(system_name)

    if system_health is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": f"System '{system_name}' not found",
                "available_systems": list(_health_monitor.last_results.keys()),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    status_code = (
        status.HTTP_200_OK
        if system_health.status == HealthStatus.HEALTHY
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "system": system_health.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
