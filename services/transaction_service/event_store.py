"""Event sourcing store for transaction events."""
import logging
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of transaction events."""
    TRANSACTION_INITIATED = "transaction_initiated"
    TRANSACTION_AUTHORIZED = "transaction_authorized"
    TRANSACTION_CLEARED = "transaction_cleared"
    TRANSACTION_SETTLED = "transaction_settled"
    TRANSACTION_FAILED = "transaction_failed"
    TRANSACTION_REVERSED = "transaction_reversed"


@dataclass
class Event:
    """Represents an event in the event store."""
    event_id: str
    event_type: EventType
    aggregate_id: str  # Transaction ID
    timestamp: datetime
    data: Dict[str, Any]
    version: int
    correlation_id: str = None
    service_name: str = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "version": self.version,
            "correlation_id": self.correlation_id,
            "service_name": self.service_name
        }


class EventStore:
    """In-memory event store for transaction events."""

    def __init__(self):
        self.events: List[Event] = []
        self.snapshots: Dict[str, Any] = {}
        self.version_counter: Dict[str, int] = {}

    def append_event(
        self,
        event_type: EventType,
        aggregate_id: str,
        data: Dict[str, Any],
        correlation_id: str = None,
        service_name: str = None
    ) -> Event:
        """Append an event to the store."""
        import uuid

        version = self.version_counter.get(aggregate_id, 0) + 1
        self.version_counter[aggregate_id] = version

        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            aggregate_id=aggregate_id,
            timestamp=datetime.utcnow(),
            data=data,
            version=version,
            correlation_id=correlation_id,
            service_name=service_name
        )

        self.events.append(event)
        logger.info(
            f"Event appended to store",
            extra={
                "event_type": event_type.value,
                "aggregate_id": aggregate_id,
                "version": version,
                "correlation_id": correlation_id
            }
        )

        return event

    def get_events_for_aggregate(self, aggregate_id: str) -> List[Event]:
        """Get all events for an aggregate."""
        return [e for e in self.events if e.aggregate_id == aggregate_id]

    def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """Get all events of a specific type."""
        return [e for e in self.events if e.event_type == event_type]

    def get_events_since(self, timestamp: datetime) -> List[Event]:
        """Get all events since timestamp."""
        return [e for e in self.events if e.timestamp >= timestamp]

    def replay_events(self, aggregate_id: str) -> Dict[str, Any]:
        """Replay events to reconstruct current state."""
        events = self.get_events_for_aggregate(aggregate_id)
        state = {"transaction_id": aggregate_id, "status": "unknown", "events": []}

        for event in events:
            if event.event_type == EventType.TRANSACTION_INITIATED:
                state.update(event.data)
                state["status"] = "initiated"

            elif event.event_type == EventType.TRANSACTION_AUTHORIZED:
                state["status"] = "authorized"
                state["authorized_at"] = event.timestamp.isoformat()

            elif event.event_type == EventType.TRANSACTION_CLEARED:
                state["status"] = "cleared"
                state["cleared_at"] = event.timestamp.isoformat()

            elif event.event_type == EventType.TRANSACTION_SETTLED:
                state["status"] = "settled"
                state["settled_at"] = event.timestamp.isoformat()

            elif event.event_type == EventType.TRANSACTION_FAILED:
                state["status"] = "failed"
                state["failure_reason"] = event.data.get("reason")

            elif event.event_type == EventType.TRANSACTION_REVERSED:
                state["status"] = "reversed"
                state["reversed_at"] = event.timestamp.isoformat()

            state["events"].append(event.to_dict())

        return state

    def create_snapshot(self, aggregate_id: str, state: Dict[str, Any]):
        """Create a snapshot of current state."""
        self.snapshots[aggregate_id] = {
            "state": state,
            "created_at": datetime.utcnow().isoformat(),
            "version": self.version_counter.get(aggregate_id, 0)
        }
        logger.info(f"Snapshot created for {aggregate_id}")

    def get_snapshot(self, aggregate_id: str) -> Dict[str, Any]:
        """Get latest snapshot."""
        return self.snapshots.get(aggregate_id)

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all events as list of dictionaries."""
        return [event.to_dict() for event in self.events]


# Global event store
_event_store: EventStore = None


def get_event_store() -> EventStore:
    """Get or create global event store."""
    global _event_store
    if _event_store is None:
        _event_store = EventStore()
    return _event_store


def init_event_store() -> EventStore:
    """Initialize global event store."""
    global _event_store
    _event_store = EventStore()
    return _event_store
