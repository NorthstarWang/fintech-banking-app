"""Correlation ID tracking for distributed request tracing."""
import contextvars
import uuid
from datetime import datetime
from typing import Optional
import logging

correlation_id_var = contextvars.ContextVar('correlation_id', default=None)
service_name_var = contextvars.ContextVar('service_name', default=None)

logger = logging.getLogger(__name__)


class CorrelationContext:
    """Context manager for correlation IDs and structured logging."""

    def __init__(self, service_name: str, correlation_id: Optional[str] = None):
        self.service_name = service_name
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.token_correlation = None
        self.token_service = None

    def __enter__(self):
        """Enter context and set correlation variables."""
        self.token_correlation = correlation_id_var.set(self.correlation_id)
        self.token_service = service_name_var.set(self.service_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and reset correlation variables."""
        if self.token_correlation:
            correlation_id_var.reset(self.token_correlation)
        if self.token_service:
            service_name_var.reset(self.token_service)


def get_correlation_id() -> str:
    """Get current correlation ID."""
    cid = correlation_id_var.get()
    return cid if cid else str(uuid.uuid4())


def get_service_name() -> str:
    """Get current service name."""
    return service_name_var.get() or "unknown"


def set_correlation_id(correlation_id: str):
    """Set correlation ID for current context."""
    correlation_id_var.set(correlation_id)


def set_service_name(service_name: str):
    """Set service name for current context."""
    service_name_var.set(service_name)


class CorrelationIDMiddleware:
    """FastAPI middleware for correlation ID tracking."""

    def __init__(self, app, service_name: str):
        self.app = app
        self.service_name = service_name

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract or generate correlation ID from headers
        headers = dict(scope.get("headers", []))
        correlation_id = headers.get(b"x-correlation-id", b"").decode() or str(uuid.uuid4())

        with CorrelationContext(self.service_name, correlation_id):
            await self.app(scope, receive, send)


class StructuredLogger:
    """Logger with structured context (service name, correlation ID, etc.)."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def _get_context(self) -> dict:
        """Build context dictionary with service and correlation info."""
        return {
            "service": get_service_name(),
            "correlation_id": get_correlation_id(),
            "timestamp": datetime.utcnow().isoformat()
        }

    def info(self, message: str, **extra):
        """Log info with context."""
        context = self._get_context()
        context.update(extra)
        self.logger.info(f"{message} | {context}")

    def error(self, message: str, **extra):
        """Log error with context."""
        context = self._get_context()
        context.update(extra)
        self.logger.error(f"{message} | {context}")

    def warning(self, message: str, **extra):
        """Log warning with context."""
        context = self._get_context()
        context.update(extra)
        self.logger.warning(f"{message} | {context}")

    def debug(self, message: str, **extra):
        """Log debug with context."""
        context = self._get_context()
        context.update(extra)
        self.logger.debug(f"{message} | {context}")
