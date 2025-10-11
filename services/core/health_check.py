"""Health check utilities for microservices."""
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HealthCheck:
    """Base class for service health checks."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.last_check: Optional[datetime] = None
        self.is_healthy: bool = True
        self.error_message: str = ""

    async def check(self) -> bool:
        """Override this method to implement health check logic."""
        return True

    async def run(self) -> Dict[str, Any]:
        """Run the health check and return results."""
        try:
            self.is_healthy = await self.check()
            self.error_message = ""
            logger.debug(f"Health check '{self.name}' passed")
        except Exception as e:
            self.is_healthy = False
            self.error_message = str(e)
            logger.error(f"Health check '{self.name}' failed: {e}")

        self.last_check = datetime.utcnow()

        return {
            "name": self.name,
            "description": self.description,
            "is_healthy": self.is_healthy,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "error": self.error_message
        }


class ServiceHealthChecker:
    """Manages health checks for a service."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.checks: Dict[str, HealthCheck] = {}
        self.is_service_healthy: bool = True

    def register_check(self, check: HealthCheck):
        """Register a health check."""
        self.checks[check.name] = check

    def register_callable_check(
        self,
        name: str,
        check_func: Callable,
        description: str = ""
    ):
        """Register a health check from a callable."""
        class CallableHealthCheck(HealthCheck):
            async def check(self) -> bool:
                return await check_func()

        check = CallableHealthCheck(name, description)
        self.register_check(check)

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = []
        all_healthy = True

        for check in self.checks.values():
            result = await check.run()
            results.append(result)
            if not result["is_healthy"]:
                all_healthy = False

        self.is_service_healthy = all_healthy

        return {
            "service": self.service_name,
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results
        }

    async def check_service_health(self) -> bool:
        """Quick check if service is healthy."""
        health_status = await self.run_all_checks()
        return health_status["status"] == "healthy"


# Common health checks
class DatabaseHealthCheck(HealthCheck):
    """Check database connectivity."""

    def __init__(self, db_connector):
        super().__init__("database", "Check database connectivity")
        self.db_connector = db_connector

    async def check(self) -> bool:
        """Check if database is accessible."""
        try:
            # This would depend on your database implementation
            # For example, execute a simple query
            if hasattr(self.db_connector, 'execute'):
                await self.db_connector.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            raise


class ExternalServiceHealthCheck(HealthCheck):
    """Check external service availability."""

    def __init__(self, service_name: str, service_client):
        super().__init__(
            f"external_{service_name}",
            f"Check {service_name} availability"
        )
        self.service_name = service_name
        self.service_client = service_client

    async def check(self) -> bool:
        """Check if external service is available."""
        try:
            result = await self.service_client.get("/health")
            return result.get("status") == "success"
        except Exception as e:
            logger.error(f"External service {self.service_name} check failed: {e}")
            raise


class MemoryHealthCheck(HealthCheck):
    """Check memory usage."""

    def __init__(self, threshold_percent: float = 90.0):
        super().__init__("memory", "Check memory usage")
        self.threshold_percent = threshold_percent

    async def check(self) -> bool:
        """Check if memory usage is within threshold."""
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > self.threshold_percent:
                raise Exception(f"Memory usage at {memory_percent}%")
            return True
        except ImportError:
            # psutil not available, skip check
            return True
        except Exception as e:
            logger.error(f"Memory health check failed: {e}")
            raise


class DiskHealthCheck(HealthCheck):
    """Check disk usage."""

    def __init__(self, threshold_percent: float = 90.0):
        super().__init__("disk", "Check disk usage")
        self.threshold_percent = threshold_percent

    async def check(self) -> bool:
        """Check if disk usage is within threshold."""
        try:
            import psutil
            disk_percent = psutil.disk_usage("/").percent
            if disk_percent > self.threshold_percent:
                raise Exception(f"Disk usage at {disk_percent}%")
            return True
        except ImportError:
            # psutil not available, skip check
            return True
        except Exception as e:
            logger.error(f"Disk health check failed: {e}")
            raise
