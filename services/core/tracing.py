"""Distributed tracing with OpenTelemetry span management."""
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from enum import Enum
import contextvars
import time

logger = logging.getLogger(__name__)


class SpanKind(Enum):
    """Type of span."""
    INTERNAL = "INTERNAL"
    SERVER = "SERVER"
    CLIENT = "CLIENT"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"


class SpanStatus(Enum):
    """Span status."""
    UNSET = "UNSET"
    OK = "OK"
    ERROR = "ERROR"


@dataclass
class SpanContext:
    """Context for a span in a trace."""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: Optional[str] = None
    is_remote: bool = False


@dataclass
class SpanEvent:
    """Event recorded during span execution."""
    name: str
    timestamp: float
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """Represents a unit of work in distributed tracing."""
    name: str
    context: SpanContext
    start_time: float
    kind: SpanKind = SpanKind.INTERNAL
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    status: SpanStatus = SpanStatus.UNSET
    status_message: str = ""
    end_time: Optional[float] = None

    @property
    def duration_ms(self) -> float:
        """Get span duration in milliseconds."""
        if self.end_time is None:
            return (time.time() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add event to span."""
        event = SpanEvent(
            name=name,
            timestamp=time.time(),
            attributes=attributes or {}
        )
        self.events.append(event)

    def set_attribute(self, key: str, value: Any):
        """Set span attribute."""
        self.attributes[key] = value

    def set_status(self, status: SpanStatus, message: str = ""):
        """Set span status."""
        self.status = status
        self.status_message = message

    def end(self):
        """End the span."""
        self.end_time = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for serialization."""
        return {
            "name": self.name,
            "trace_id": self.context.trace_id,
            "span_id": self.context.span_id,
            "parent_span_id": self.context.parent_span_id,
            "kind": self.kind.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "status_message": self.status_message,
            "attributes": self.attributes,
            "events": [
                {
                    "name": event.name,
                    "timestamp": event.timestamp,
                    "attributes": event.attributes
                }
                for event in self.events
            ]
        }


# Context variables for tracing
current_span_context = contextvars.ContextVar('span_context', default=None)
current_span = contextvars.ContextVar('span', default=None)


class Tracer:
    """Manages spans and trace propagation."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.spans: List[Span] = []
        self._lock = None  # For thread safety if needed

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
        parent_context: Optional[SpanContext] = None
    ) -> Span:
        """Start a new span."""
        if parent_context is None:
            parent_context = current_span_context.get()

        span_context = SpanContext(
            parent_span_id=parent_context.span_id if parent_context else None,
            is_remote=False
        )

        span = Span(
            name=name,
            context=span_context,
            start_time=time.time(),
            kind=kind,
            attributes=attributes or {}
        )

        # Add service attribute
        span.set_attribute("service.name", self.service_name)

        logger.debug(f"Span started: {name} (trace_id={span_context.trace_id}, span_id={span_context.span_id})")

        return span

    def end_span(self, span: Span):
        """End a span."""
        span.end()
        self.spans.append(span)
        logger.debug(f"Span ended: {span.name} (duration={span.duration_ms:.2f}ms)")

    def create_remote_span_context(self, trace_id: str, span_id: str) -> SpanContext:
        """Create span context from remote service."""
        return SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            is_remote=True
        )

    def get_trace(self, trace_id: str) -> List[Span]:
        """Get all spans in a trace."""
        return [s for s in self.spans if s.context.trace_id == trace_id]

    def get_all_spans(self) -> List[Dict[str, Any]]:
        """Get all recorded spans as dictionaries."""
        return [span.to_dict() for span in self.spans]


class TracingContext:
    """Context manager for span lifecycle."""

    def __init__(
        self,
        tracer: Tracer,
        span_name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ):
        self.tracer = tracer
        self.span_name = span_name
        self.kind = kind
        self.attributes = attributes
        self.span: Optional[Span] = None
        self.token = None

    def __enter__(self) -> Span:
        """Enter tracing context."""
        self.span = self.tracer.start_span(
            self.span_name,
            kind=self.kind,
            attributes=self.attributes
        )
        self.token = current_span.set(self.span)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit tracing context."""
        if exc_type is not None:
            self.span.set_status(SpanStatus.ERROR, f"{exc_type.__name__}: {exc_val}")
        else:
            self.span.set_status(SpanStatus.OK)

        self.tracer.end_span(self.span)
        if self.token:
            current_span.reset(self.token)


class AsyncTracingContext:
    """Async context manager for span lifecycle."""

    def __init__(
        self,
        tracer: Tracer,
        span_name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ):
        self.tracer = tracer
        self.span_name = span_name
        self.kind = kind
        self.attributes = attributes
        self.span: Optional[Span] = None
        self.token = None

    async def __aenter__(self) -> Span:
        """Enter async tracing context."""
        self.span = self.tracer.start_span(
            self.span_name,
            kind=self.kind,
            attributes=self.attributes
        )
        self.token = current_span.set(self.span)
        return self.span

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async tracing context."""
        if exc_type is not None:
            self.span.set_status(SpanStatus.ERROR, f"{exc_type.__name__}: {exc_val}")
        else:
            self.span.set_status(SpanStatus.OK)

        self.tracer.end_span(self.span)
        if self.token:
            current_span.reset(self.token)


def get_current_span() -> Optional[Span]:
    """Get current active span."""
    return current_span.get()


def get_current_span_context() -> Optional[SpanContext]:
    """Get current span context."""
    span = current_span.get()
    return span.context if span else None


# Global tracer instance
_tracer: Optional[Tracer] = None


def get_tracer(service_name: str = "unknown") -> Tracer:
    """Get or create global tracer."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer(service_name)
    return _tracer


def init_tracer(service_name: str) -> Tracer:
    """Initialize global tracer."""
    global _tracer
    _tracer = Tracer(service_name)
    return _tracer
