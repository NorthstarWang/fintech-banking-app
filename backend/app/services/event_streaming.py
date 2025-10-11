"""
Event streaming infrastructure with deduplication, ordering, and late-arriving data handling.
"""
import asyncio
import hashlib
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from .event_schemas import BaseEvent, EVENT_SCHEMA_MAP, EventType

logger = logging.getLogger(__name__)


class EventBuffer:
    """Handles out-of-order and late-arriving events with proper ordering."""

    def __init__(self, window_seconds: int = 300):  # 5 minute window
        self.window_seconds = window_seconds
        self.buffer: dict[int, list[BaseEvent]] = defaultdict(list)  # user_id -> events
        self.sequence_trackers: dict[int, int] = {}  # user_id -> last_sequence
        self.watermarks: dict[int, datetime] = {}  # user_id -> watermark timestamp

    def add_event(self, event: BaseEvent) -> tuple[bool, str | None]:
        """
        Add event to buffer with ordering and deduplication.
        Returns (should_process, skip_reason)
        """
        user_id = event.user_id

        # Check if event is too old (beyond window)
        now = datetime.utcnow()
        if event.timestamp < now - timedelta(seconds=self.window_seconds * 2):
            return False, "event_too_old"

        # Add to buffer
        self.buffer[user_id].append(event)

        # Update watermark
        if user_id not in self.watermarks:
            self.watermarks[user_id] = event.timestamp
        else:
            self.watermarks[user_id] = max(self.watermarks[user_id], event.timestamp)

        return True, None

    def get_ordered_events(self, user_id: int, limit: int = 100) -> list[BaseEvent]:
        """Get events in order for a user."""
        if user_id not in self.buffer:
            return []

        # Sort by timestamp then sequence number
        events = sorted(
            self.buffer[user_id],
            key=lambda e: (e.timestamp, e.sequence_number or 0)
        )

        # Return and remove processed events
        result = events[:limit]
        self.buffer[user_id] = events[limit:]

        return result

    def cleanup_old_events(self):
        """Remove events older than the window."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds * 2)

        for user_id in list(self.buffer.keys()):
            self.buffer[user_id] = [
                e for e in self.buffer[user_id]
                if e.timestamp >= cutoff
            ]
            if not self.buffer[user_id]:
                del self.buffer[user_id]


class EventDeduplicator:
    """Handles event deduplication using event IDs and content hashing."""

    def __init__(self, ttl_seconds: int = 3600):  # 1 hour TTL
        self.ttl_seconds = ttl_seconds
        self.seen_events: dict[str, datetime] = {}  # event_id -> timestamp
        self.content_hashes: dict[str, datetime] = {}  # content_hash -> timestamp

    def is_duplicate(self, event: BaseEvent) -> tuple[bool, str | None]:
        """
        Check if event is a duplicate.
        Returns (is_duplicate, reason)
        """
        now = datetime.utcnow()

        # Check by event ID
        if event.event_id in self.seen_events:
            return True, "duplicate_event_id"

        # Generate content hash for semantic deduplication
        content_hash = self._generate_content_hash(event)
        if content_hash in self.content_hashes:
            # Check if it's within a short time window (might be retry)
            if (now - self.content_hashes[content_hash]).total_seconds() < 60:
                return True, "duplicate_content"

        # Mark as seen
        self.seen_events[event.event_id] = now
        self.content_hashes[content_hash] = now

        return False, None

    def _generate_content_hash(self, event: BaseEvent) -> str:
        """Generate hash of event content for deduplication."""
        # Create hash from key fields
        key_fields = [
            str(event.user_id),
            event.event_type.value,
            event.timestamp.isoformat(),
        ]

        # Add type-specific fields
        if hasattr(event, 'transaction_id'):
            key_fields.append(f"tx_{event.transaction_id}")
        if hasattr(event, 'amount'):
            key_fields.append(f"amt_{event.amount}")
        if hasattr(event, 'account_id'):
            key_fields.append(f"acc_{event.account_id}")

        content = "|".join(key_fields)
        return hashlib.sha256(content.encode()).hexdigest()

    def cleanup_old_entries(self):
        """Remove old entries beyond TTL."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.ttl_seconds)

        self.seen_events = {
            k: v for k, v in self.seen_events.items()
            if v >= cutoff
        }
        self.content_hashes = {
            k: v for k, v in self.content_hashes.items()
            if v >= cutoff
        }


class EventStore:
    """In-memory event store with retention policies."""

    def __init__(self):
        self.detailed_events: list[dict[str, Any]] = []  # Last 90 days
        self.daily_aggregates: dict[str, dict[str, Any]] = {}  # Last 1 year
        self.monthly_aggregates: dict[str, dict[str, Any]] = {}  # Indefinite
        self.last_cleanup = datetime.utcnow()

    def store_event(self, event: BaseEvent):
        """Store event with timestamp."""
        event_dict = event.model_dump()
        event_dict['stored_at'] = datetime.utcnow()
        self.detailed_events.append(event_dict)

    def get_events(
        self,
        user_id: int | None = None,
        event_types: list[EventType] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 1000
    ) -> list[dict[str, Any]]:
        """Query events with filters."""
        events = self.detailed_events

        # Apply filters
        if user_id is not None:
            events = [e for e in events if e['user_id'] == user_id]

        if event_types:
            event_type_values = [et.value for et in event_types]
            events = [e for e in events if e['event_type'] in event_type_values]

        if start_date:
            events = [e for e in events if e['timestamp'] >= start_date]

        if end_date:
            events = [e for e in events if e['timestamp'] <= end_date]

        # Sort by timestamp desc
        events = sorted(events, key=lambda e: e['timestamp'], reverse=True)

        return events[:limit]

    def apply_retention_policy(self):
        """Apply retention policies: 90 days detailed, 1 year daily, indefinite monthly."""
        now = datetime.utcnow()

        # Only run cleanup every hour
        if (now - self.last_cleanup).total_seconds() < 3600:
            return

        # Remove detailed events older than 90 days
        cutoff_detailed = now - timedelta(days=90)
        old_events = [e for e in self.detailed_events if e['timestamp'] < cutoff_detailed]

        # Aggregate old events into daily summaries before deletion
        for event in old_events:
            date_key = event['timestamp'].date().isoformat()
            if date_key not in self.daily_aggregates:
                self.daily_aggregates[date_key] = {
                    'date': date_key,
                    'user_events': defaultdict(lambda: defaultdict(int)),
                    'event_counts': defaultdict(int),
                    'total_events': 0
                }

            agg = self.daily_aggregates[date_key]
            user_id = event['user_id']
            event_type = event['event_type']

            agg['user_events'][user_id][event_type] += 1
            agg['event_counts'][event_type] += 1
            agg['total_events'] += 1

        # Remove old detailed events
        self.detailed_events = [
            e for e in self.detailed_events
            if e['timestamp'] >= cutoff_detailed
        ]

        # Remove daily aggregates older than 1 year, move to monthly
        cutoff_daily = now - timedelta(days=365)
        old_daily = {
            k: v for k, v in self.daily_aggregates.items()
            if datetime.fromisoformat(k) < cutoff_daily.date()
        }

        # Aggregate into monthly
        for date_key, daily_data in old_daily.items():
            month_key = date_key[:7]  # YYYY-MM
            if month_key not in self.monthly_aggregates:
                self.monthly_aggregates[month_key] = {
                    'month': month_key,
                    'user_events': defaultdict(lambda: defaultdict(int)),
                    'event_counts': defaultdict(int),
                    'total_events': 0
                }

            monthly_agg = self.monthly_aggregates[month_key]
            for user_id, events in daily_data['user_events'].items():
                for event_type, count in events.items():
                    monthly_agg['user_events'][user_id][event_type] += count

            for event_type, count in daily_data['event_counts'].items():
                monthly_agg['event_counts'][event_type] += count

            monthly_agg['total_events'] += daily_data['total_events']

        # Remove old daily aggregates
        self.daily_aggregates = {
            k: v for k, v in self.daily_aggregates.items()
            if datetime.fromisoformat(k) >= cutoff_daily.date()
        }

        self.last_cleanup = now
        logger.info(
            f"Retention policy applied: {len(self.detailed_events)} detailed events, "
            f"{len(self.daily_aggregates)} daily aggregates, "
            f"{len(self.monthly_aggregates)} monthly aggregates"
        )


class EventStreamingService:
    """Main event streaming service coordinating all components."""

    def __init__(self):
        self.buffer = EventBuffer(window_seconds=300)
        self.deduplicator = EventDeduplicator(ttl_seconds=3600)
        self.event_store = EventStore()
        self.sequence_counters: dict[int, int] = defaultdict(int)  # user_id -> counter
        self.subscribers: list[asyncio.Queue] = []  # WebSocket subscribers
        self._cleanup_task: asyncio.Task | None = None

    def generate_event_id(self) -> str:
        """Generate unique event ID."""
        return str(uuid4())

    def capture_event(
        self,
        event_type: EventType,
        user_id: int,
        event_data: dict[str, Any],
        session_id: str | None = None,
        device_id: str | None = None,
        ip_address: str | None = None,
        correlation_id: str | None = None
    ) -> tuple[bool, str | None]:
        """
        Capture and process an event.
        Returns (success, error_message)
        """
        try:
            # Get appropriate event schema
            event_class = EVENT_SCHEMA_MAP.get(event_type, BaseEvent)

            # Generate event ID and sequence number
            event_id = self.generate_event_id()
            self.sequence_counters[user_id] += 1
            sequence_number = self.sequence_counters[user_id]

            # Create event
            event = event_class(
                event_id=event_id,
                event_type=event_type,
                user_id=user_id,
                sequence_number=sequence_number,
                session_id=session_id,
                device_id=device_id,
                ip_address=ip_address,
                correlation_id=correlation_id,
                **event_data
            )

            # Check for duplicates
            is_duplicate, dup_reason = self.deduplicator.is_duplicate(event)
            if is_duplicate:
                logger.debug(f"Duplicate event detected: {dup_reason}")
                return False, f"duplicate: {dup_reason}"

            # Add to buffer
            should_process, skip_reason = self.buffer.add_event(event)
            if not should_process:
                logger.warning(f"Event skipped: {skip_reason}")
                return False, f"skipped: {skip_reason}"

            # Store event
            self.event_store.store_event(event)

            # Notify subscribers (for real-time updates)
            self._notify_subscribers(event)

            return True, None

        except Exception as e:
            logger.error(f"Error capturing event: {e}", exc_info=True)
            return False, str(e)

    def get_events(
        self,
        user_id: int,
        event_types: list[EventType] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 1000
    ) -> list[dict[str, Any]]:
        """Query events for a user."""
        return self.event_store.get_events(
            user_id=user_id,
            event_types=event_types,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

    def _notify_subscribers(self, event: BaseEvent):
        """Notify WebSocket subscribers of new event."""
        # Remove closed queues
        self.subscribers = [
            q for q in self.subscribers
            if not (hasattr(q, '_closed') and q._closed)
        ]

        # Send to all subscribers
        event_dict = event.model_dump()
        for queue in self.subscribers:
            try:
                queue.put_nowait(event_dict)
            except asyncio.QueueFull:
                logger.warning("Subscriber queue full, dropping event")
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to event stream (for WebSocket)."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from event stream."""
        if queue in self.subscribers:
            self.subscribers.remove(queue)

    async def start_background_tasks(self):
        """Start background cleanup tasks."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def _periodic_cleanup(self):
        """Periodic cleanup of old data."""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                self.buffer.cleanup_old_events()
                self.deduplicator.cleanup_old_entries()
                self.event_store.apply_retention_policy()
                logger.info("Periodic cleanup completed")
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}", exc_info=True)


# Global event streaming service instance
event_streaming_service = EventStreamingService()
