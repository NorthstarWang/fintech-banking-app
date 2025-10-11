"""Circuit breaker pattern implementation for resilient service communication."""
import time
import logging
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any, Optional
import threading

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerException(Exception):
    """Raised when circuit is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker for handling transient failures.

    Implements Hystrix pattern:
    - CLOSED: Normal operation
    - OPEN: Too many failures, reject requests
    - HALF_OPEN: Test if service recovered
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        max_concurrent_calls: Optional[int] = None
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker name
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before trying half-open
            expected_exception: Exception type to catch
            max_concurrent_calls: Maximum concurrent calls (None = unlimited)
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.max_concurrent_calls = max_concurrent_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._last_state_change = datetime.utcnow()
        self._concurrent_calls = 0
        self._lock = threading.RLock()

        logger.info(f"Circuit breaker '{name}' initialized")

    @property
    def state(self) -> CircuitState:
        """Get current state."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
                    return CircuitState.HALF_OPEN
            return self._state

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return False
        time_since_failure = (datetime.utcnow() - self._last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerException: If circuit is open
            Original exception from func if failure
        """
        current_state = self.state

        if current_state == CircuitState.OPEN:
            logger.warning(f"Circuit breaker '{self.name}' is OPEN, rejecting call")
            raise CircuitBreakerException(f"Circuit breaker '{self.name}' is OPEN")

        # Check concurrent calls limit
        with self._lock:
            if self.max_concurrent_calls and self._concurrent_calls >= self.max_concurrent_calls:
                raise CircuitBreakerException(
                    f"Circuit breaker '{self.name}' max concurrent calls exceeded"
                )
            self._concurrent_calls += 1

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise

        finally:
            with self._lock:
                self._concurrent_calls -= 1

    def _on_success(self):
        """Handle successful call."""
        with self._lock:
            self._failure_count = 0

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= 2:  # 2 successful calls to fully close
                    self._state = CircuitState.CLOSED
                    self._last_state_change = datetime.utcnow()
                    logger.info(f"Circuit breaker '{self.name}' is CLOSED (recovered)")

    def _on_failure(self):
        """Handle failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.utcnow()

            if self._state == CircuitState.HALF_OPEN:
                # Failure in half-open state reopens circuit
                self._state = CircuitState.OPEN
                self._last_state_change = datetime.utcnow()
                logger.warning(f"Circuit breaker '{self.name}' is OPEN (recovery failed)")

            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._last_state_change = datetime.utcnow()
                logger.warning(
                    f"Circuit breaker '{self.name}' is OPEN "
                    f"({self._failure_count} failures >= {self.failure_threshold})"
                )

    def get_state_info(self) -> dict:
        """Get circuit breaker state information."""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "concurrent_calls": self._concurrent_calls,
                "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None,
                "last_state_change": self._last_state_change.isoformat(),
                "time_to_retry_seconds": (
                    self.recovery_timeout - (datetime.utcnow() - self._last_failure_time).total_seconds()
                ) if self._last_failure_time else 0
            }


class CircuitBreakerManager:
    """Manages multiple circuit breakers."""

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        max_concurrent_calls: Optional[int] = None
    ) -> CircuitBreaker:
        """Get existing or create new circuit breaker."""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    name,
                    failure_threshold,
                    recovery_timeout,
                    expected_exception,
                    max_concurrent_calls
                )
            return self._breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get existing circuit breaker."""
        return self._breakers.get(name)

    def get_all_states(self) -> dict:
        """Get state info for all circuit breakers."""
        return {
            name: breaker.get_state_info()
            for name, breaker in self._breakers.items()
        }

    def reset(self, name: str) -> bool:
        """Manually reset circuit breaker."""
        with self._lock:
            if name in self._breakers:
                self._breakers[name]._state = CircuitState.CLOSED
                self._breakers[name]._failure_count = 0
                logger.info(f"Circuit breaker '{name}' manually reset to CLOSED")
                return True
            return False

    def reset_all(self):
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker._state = CircuitState.CLOSED
                breaker._failure_count = 0
            logger.info("All circuit breakers reset to CLOSED")


# Global circuit breaker manager
_breaker_manager: Optional[CircuitBreakerManager] = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get or create global circuit breaker manager."""
    global _breaker_manager
    if _breaker_manager is None:
        _breaker_manager = CircuitBreakerManager()
    return _breaker_manager


def init_circuit_breaker_manager() -> CircuitBreakerManager:
    """Initialize global circuit breaker manager."""
    global _breaker_manager
    _breaker_manager = CircuitBreakerManager()
    return _breaker_manager
