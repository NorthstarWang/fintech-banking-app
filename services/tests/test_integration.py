"""Integration tests for microservices communication."""
import pytest
import asyncio
from datetime import datetime

from services.core.service_registry import ServiceRegistry, ServiceInstance
from services.core.api_client import ServiceClient, RetryConfig, ServiceClientFactory
from services.core.correlation_id import CorrelationContext, get_correlation_id, get_service_name
from services.core.health_check import ServiceHealthChecker, HealthCheck


class TestServiceRegistry:
    """Test service registry functionality."""

    def test_register_service(self):
        """Test registering a service instance."""
        registry = ServiceRegistry()

        instance = registry.register(
            service_name="auth-service",
            instance_id="auth-1",
            host="localhost",
            port=8001,
            health_check_url="/health",
            api_key="auth-key-123"
        )

        assert instance.service_name == "auth-service"
        assert instance.instance_id == "auth-1"
        assert instance.base_url == "http://localhost:8001"

    def test_get_service_instance(self):
        """Test retrieving a service instance."""
        registry = ServiceRegistry()

        registry.register(
            service_name="auth-service",
            instance_id="auth-1",
            host="localhost",
            port=8001,
            health_check_url="/health",
            api_key="auth-key-123"
        )

        instance = registry.get_instance("auth-service")
        assert instance is not None
        assert instance.instance_id == "auth-1"

    def test_deregister_service(self):
        """Test deregistering a service."""
        registry = ServiceRegistry()

        registry.register(
            service_name="auth-service",
            instance_id="auth-1",
            host="localhost",
            port=8001,
            health_check_url="/health",
            api_key="auth-key-123"
        )

        success = registry.deregister("auth-service", "auth-1")
        assert success is True

        instance = registry.get_instance("auth-service")
        assert instance is None

    def test_mark_unhealthy(self):
        """Test marking a service as unhealthy."""
        registry = ServiceRegistry()

        registry.register(
            service_name="auth-service",
            instance_id="auth-1",
            host="localhost",
            port=8001,
            health_check_url="/health",
            api_key="auth-key-123"
        )

        registry.mark_unhealthy("auth-service", "auth-1")

        instance = registry.get_instance("auth-service")
        assert instance is None  # Unhealthy instances are not returned

    def test_multiple_instances(self):
        """Test registering multiple instances of same service."""
        registry = ServiceRegistry()

        registry.register(
            service_name="auth-service",
            instance_id="auth-1",
            host="localhost",
            port=8001,
            health_check_url="/health",
            api_key="auth-key-1"
        )

        registry.register(
            service_name="auth-service",
            instance_id="auth-2",
            host="localhost",
            port=8011,
            health_check_url="/health",
            api_key="auth-key-2"
        )

        instances = registry.get_all_instances("auth-service")
        assert len(instances) == 2

    def test_registry_status(self):
        """Test getting registry status."""
        registry = ServiceRegistry()

        registry.register(
            service_name="auth-service",
            instance_id="auth-1",
            host="localhost",
            port=8001,
            health_check_url="/health",
            api_key="auth-key-123"
        )

        status = registry.get_registry_status()
        assert "auth-service" in status
        assert status["auth-service"]["total_instances"] == 1
        assert status["auth-service"]["healthy_instances"] == 1


class TestCorrelationID:
    """Test correlation ID tracking."""

    def test_correlation_context(self):
        """Test correlation context manager."""
        with CorrelationContext("test-service", "test-correlation-123"):
            assert get_service_name() == "test-service"
            assert get_correlation_id() == "test-correlation-123"

    def test_correlation_generation(self):
        """Test automatic correlation ID generation."""
        with CorrelationContext("test-service"):
            correlation_id = get_correlation_id()
            assert correlation_id is not None
            assert len(correlation_id) > 0


class TestRetryConfig:
    """Test retry configuration."""

    def test_retry_delay_calculation(self):
        """Test exponential backoff calculation."""
        config = RetryConfig(
            max_retries=3,
            initial_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0
        )

        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0

    def test_retry_delay_max_cap(self):
        """Test that retry delay is capped at max_delay."""
        config = RetryConfig(
            max_retries=5,
            initial_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0
        )

        delay = config.get_delay(10)
        assert delay == 10.0  # Capped at max_delay


class TestHealthChecker:
    """Test service health checking."""

    @pytest.mark.asyncio
    async def test_health_checker_initialization(self):
        """Test health checker initialization."""
        checker = ServiceHealthChecker("test-service")
        assert checker.service_name == "test-service"

    @pytest.mark.asyncio
    async def test_register_check(self):
        """Test registering a health check."""
        checker = ServiceHealthChecker("test-service")

        async def dummy_check():
            return True

        checker.register_callable_check("dummy", dummy_check, "Dummy check")
        assert "dummy" in checker.checks

    @pytest.mark.asyncio
    async def test_run_all_checks(self):
        """Test running all health checks."""
        checker = ServiceHealthChecker("test-service")

        async def dummy_check():
            return True

        checker.register_callable_check("dummy", dummy_check, "Dummy check")
        result = await checker.run_all_checks()

        assert result["service"] == "test-service"
        assert result["status"] == "healthy"
        assert len(result["checks"]) == 1

    @pytest.mark.asyncio
    async def test_failing_health_check(self):
        """Test health check failure handling."""
        checker = ServiceHealthChecker("test-service")

        async def failing_check():
            raise Exception("Health check failed")

        checker.register_callable_check("failing", failing_check, "Failing check")
        result = await checker.run_all_checks()

        assert result["status"] == "unhealthy"


class TestServiceCommunication:
    """Test service-to-service communication."""

    def test_service_instance_base_url(self):
        """Test service instance URL generation."""
        instance = ServiceInstance(
            service_name="test-service",
            instance_id="test-1",
            host="localhost",
            port=8000,
            health_check_url="/health",
            api_key="test-key"
        )

        assert instance.base_url == "http://localhost:8000"


class TestScenarios:
    """Test realistic scenarios."""

    def test_scenario_multiple_services_registration(self):
        """Test scenario: Multiple services registering."""
        registry = ServiceRegistry()

        # Register auth service
        registry.register(
            service_name="auth-service",
            instance_id="auth-1",
            host="localhost",
            port=8001,
            health_check_url="/health",
            api_key="auth-key-123"
        )

        # Register notification service
        registry.register(
            service_name="notification-service",
            instance_id="notif-1",
            host="localhost",
            port=8002,
            health_check_url="/health",
            api_key="notif-key-123"
        )

        # Register analytics service
        registry.register(
            service_name="analytics-service",
            instance_id="analytics-1",
            host="localhost",
            port=8003,
            health_check_url="/health",
            api_key="analytics-key-123"
        )

        status = registry.get_registry_status()
        assert len(status) == 3
        assert all(status[service]["healthy_instances"] == 1 for service in status)

    def test_scenario_service_failure_and_recovery(self):
        """Test scenario: Service failure and recovery."""
        registry = ServiceRegistry()

        instance = registry.register(
            service_name="auth-service",
            instance_id="auth-1",
            host="localhost",
            port=8001,
            health_check_url="/health",
            api_key="auth-key-123"
        )

        assert instance.is_healthy is True

        # Service fails
        registry.mark_unhealthy("auth-service", "auth-1")
        instance = registry.get_instance("auth-service")
        assert instance is None

        # Service recovers (heartbeat)
        registry.heartbeat("auth-service", "auth-1")
        instance = registry.get_instance("auth-service")
        assert instance is not None

    def test_scenario_correlation_tracking_across_services(self):
        """Test scenario: Correlation ID tracking across services."""
        correlation_ids = []

        # Service 1
        with CorrelationContext("service-1", "req-123"):
            cid_1 = get_correlation_id()
            correlation_ids.append(cid_1)

        # Service 2
        with CorrelationContext("service-2", "req-123"):
            cid_2 = get_correlation_id()
            correlation_ids.append(cid_2)

        # Both should have same correlation ID
        assert correlation_ids[0] == correlation_ids[1] == "req-123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
