"""HTTP client for service-to-service communication with retry logic."""
import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime
import httpx

from .correlation_id import get_correlation_id, get_service_name
from .service_registry import get_registry, ServiceInstance

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        retry_on_status_codes: Optional[list] = None
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_on_status_codes = retry_on_status_codes or [408, 429, 500, 502, 503, 504]

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt with exponential backoff."""
        delay = self.initial_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


class ServiceClient:
    """Client for making requests to other services."""

    def __init__(
        self,
        service_name: str,
        instance: ServiceInstance,
        retry_config: Optional[RetryConfig] = None,
        timeout: float = 10.0
    ):
        self.service_name = service_name
        self.instance = instance
        self.retry_config = retry_config or RetryConfig()
        self.timeout = timeout
        self._last_call_timestamp = None

    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make an HTTP request to the service with retry logic."""
        url = f"{self.instance.base_url}{endpoint}"
        headers = kwargs.pop("headers", {})

        # Add service-to-service authentication and correlation ID
        headers["X-API-Key"] = self.instance.api_key
        headers["X-Correlation-ID"] = get_correlation_id()
        headers["X-Service-From"] = get_service_name()

        for attempt in range(self.retry_config.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method,
                        url,
                        headers=headers,
                        **kwargs
                    )

                    self._last_call_timestamp = datetime.utcnow()

                    # Success
                    if response.status_code < 400:
                        logger.info(
                            f"Request to {self.service_name} successful",
                            status_code=response.status_code,
                            endpoint=endpoint
                        )
                        return {
                            "status": "success",
                            "data": response.json() if response.text else None,
                            "status_code": response.status_code
                        }

                    # Check if we should retry
                    if response.status_code not in self.retry_config.retry_on_status_codes:
                        logger.error(
                            f"Request to {self.service_name} failed",
                            status_code=response.status_code,
                            endpoint=endpoint
                        )
                        return {
                            "status": "error",
                            "error_code": response.status_code,
                            "error_message": response.text
                        }

                    # Retry on specific status codes
                    if attempt < self.retry_config.max_retries - 1:
                        delay = self.retry_config.get_delay(attempt)
                        logger.warning(
                            f"Retrying request to {self.service_name}",
                            attempt=attempt + 1,
                            delay=delay,
                            status_code=response.status_code
                        )
                        await asyncio.sleep(delay)
                        continue

                    # Max retries exceeded
                    logger.error(
                        f"Request to {self.service_name} failed after retries",
                        status_code=response.status_code,
                        endpoint=endpoint
                    )
                    return {
                        "status": "error",
                        "error_code": response.status_code,
                        "error_message": response.text
                    }

            except asyncio.TimeoutError:
                logger.warning(
                    f"Request to {self.service_name} timed out",
                    attempt=attempt + 1
                )
                if attempt < self.retry_config.max_retries - 1:
                    delay = self.retry_config.get_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    return {
                        "status": "error",
                        "error_code": 408,
                        "error_message": "Request timeout"
                    }

            except Exception as e:
                logger.error(
                    f"Request to {self.service_name} failed with exception",
                    error=str(e),
                    attempt=attempt + 1
                )
                if attempt < self.retry_config.max_retries - 1:
                    delay = self.retry_config.get_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    return {
                        "status": "error",
                        "error_code": 500,
                        "error_message": str(e)
                    }

        return {
            "status": "error",
            "error_code": 500,
            "error_message": "All retries exhausted"
        }

    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a GET request."""
        return await self.request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a POST request."""
        return await self.request("POST", endpoint, **kwargs)

    async def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a PUT request."""
        return await self.request("PUT", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a DELETE request."""
        return await self.request("DELETE", endpoint, **kwargs)

    def is_healthy(self) -> bool:
        """Check if service instance is healthy based on last call."""
        if self._last_call_timestamp is None:
            return True  # No calls made yet

        # Simple health check: if last call was recent, assume healthy
        from datetime import timedelta
        return (datetime.utcnow() - self._last_call_timestamp) < timedelta(minutes=5)


class ServiceClientFactory:
    """Factory for creating service clients with service discovery."""

    def __init__(self, service_timeout: float = 10.0):
        self.registry = get_registry()
        self.service_timeout = service_timeout
        self._clients_cache: Dict[str, ServiceClient] = {}

    async def get_client(self, service_name: str) -> Optional[ServiceClient]:
        """Get a client for a service using service discovery."""
        instance = self.registry.get_instance(service_name)

        if not instance:
            logger.error(f"No available instance for service: {service_name}")
            return None

        cache_key = f"{service_name}:{instance.instance_id}"

        if cache_key not in self._clients_cache:
            self._clients_cache[cache_key] = ServiceClient(
                service_name,
                instance,
                timeout=self.service_timeout
            )

        return self._clients_cache[cache_key]

    def get_all_clients(self, service_name: str) -> list[ServiceClient]:
        """Get clients for all instances of a service."""
        instances = self.registry.get_all_instances(service_name)
        clients = []

        for instance in instances:
            if instance.is_healthy:
                cache_key = f"{service_name}:{instance.instance_id}"
                if cache_key not in self._clients_cache:
                    self._clients_cache[cache_key] = ServiceClient(
                        service_name,
                        instance,
                        timeout=self.service_timeout
                    )
                clients.append(self._clients_cache[cache_key])

        return clients

    def clear_cache(self):
        """Clear the client cache."""
        self._clients_cache.clear()


# Global factory instance
_factory: Optional[ServiceClientFactory] = None


def get_client_factory() -> ServiceClientFactory:
    """Get or create the global service client factory."""
    global _factory
    if _factory is None:
        _factory = ServiceClientFactory()
    return _factory
