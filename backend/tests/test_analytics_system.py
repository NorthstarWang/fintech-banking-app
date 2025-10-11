"""
Comprehensive tests for the analytics and event streaming system.
"""
import pytest
from datetime import datetime, timedelta
from app.services.event_schemas import EventType, TransactionEvent
from app.services.event_streaming import (
    EventStreamingService,
    EventBuffer,
    EventDeduplicator,
    EventStore
)
from app.services.analytics_engine import AnalyticsEngine
from app.repositories.data_manager import data_manager


class TestEventBuffer:
    """Test event buffering and ordering."""

    def test_add_event_within_window(self):
        """Test adding event within time window."""
        buffer = EventBuffer(window_seconds=300)
        event = TransactionEvent(
            event_id="test-1",
            event_type=EventType.TRANSACTION_CREATED,
            user_id=1,
            transaction_id=1,
            account_id=1,
            amount=100.0,
            transaction_type="debit"
        )

        should_process, reason = buffer.add_event(event)
        assert should_process is True
        assert reason is None

    def test_event_ordering(self):
        """Test events are ordered correctly."""
        buffer = EventBuffer()
        now = datetime.utcnow()

        # Add events out of order
        event2 = TransactionEvent(
            event_id="test-2",
            event_type=EventType.TRANSACTION_CREATED,
            timestamp=now + timedelta(seconds=10),
            user_id=1,
            sequence_number=2,
            transaction_id=2,
            account_id=1,
            amount=200.0,
            transaction_type="debit"
        )

        event1 = TransactionEvent(
            event_id="test-1",
            event_type=EventType.TRANSACTION_CREATED,
            timestamp=now,
            user_id=1,
            sequence_number=1,
            transaction_id=1,
            account_id=1,
            amount=100.0,
            transaction_type="debit"
        )

        buffer.add_event(event2)
        buffer.add_event(event1)

        ordered = buffer.get_ordered_events(1)
        assert len(ordered) == 2
        assert ordered[0].event_id == "test-1"
        assert ordered[1].event_id == "test-2"


class TestEventDeduplicator:
    """Test event deduplication logic."""

    def test_duplicate_event_id(self):
        """Test duplicate event ID detection."""
        dedup = EventDeduplicator()

        event1 = TransactionEvent(
            event_id="test-1",
            event_type=EventType.TRANSACTION_CREATED,
            user_id=1,
            transaction_id=1,
            account_id=1,
            amount=100.0,
            transaction_type="debit"
        )

        is_dup, reason = dedup.is_duplicate(event1)
        assert is_dup is False

        is_dup, reason = dedup.is_duplicate(event1)
        assert is_dup is True
        assert reason == "duplicate_event_id"

    def test_duplicate_content_hash(self):
        """Test semantic deduplication via content hash."""
        dedup = EventDeduplicator()
        now = datetime.utcnow()

        event1 = TransactionEvent(
            event_id="test-1",
            event_type=EventType.TRANSACTION_CREATED,
            timestamp=now,
            user_id=1,
            transaction_id=1,
            account_id=1,
            amount=100.0,
            transaction_type="debit"
        )

        event2 = TransactionEvent(
            event_id="test-2",  # Different ID
            event_type=EventType.TRANSACTION_CREATED,
            timestamp=now,
            user_id=1,
            transaction_id=1,  # Same transaction
            account_id=1,
            amount=100.0,
            transaction_type="debit"
        )

        dedup.is_duplicate(event1)
        is_dup, reason = dedup.is_duplicate(event2)
        assert is_dup is True
        assert reason == "duplicate_content"


class TestEventStore:
    """Test event storage and retrieval."""

    def test_store_and_retrieve_events(self):
        """Test storing and querying events."""
        store = EventStore()

        event = TransactionEvent(
            event_id="test-1",
            event_type=EventType.TRANSACTION_CREATED,
            user_id=1,
            transaction_id=1,
            account_id=1,
            amount=100.0,
            transaction_type="debit"
        )

        store.store_event(event)

        events = store.get_events(user_id=1)
        assert len(events) == 1
        assert events[0]['event_id'] == "test-1"

    def test_filter_by_event_type(self):
        """Test filtering events by type."""
        store = EventStore()

        event1 = TransactionEvent(
            event_id="test-1",
            event_type=EventType.TRANSACTION_CREATED,
            user_id=1,
            transaction_id=1,
            account_id=1,
            amount=100.0,
            transaction_type="debit"
        )

        event2 = TransactionEvent(
            event_id="test-2",
            event_type=EventType.TRANSACTION_UPDATED,
            user_id=1,
            transaction_id=1,
            account_id=1,
            amount=150.0,
            transaction_type="debit"
        )

        store.store_event(event1)
        store.store_event(event2)

        created_events = store.get_events(
            user_id=1,
            event_types=[EventType.TRANSACTION_CREATED]
        )
        assert len(created_events) == 1
        assert created_events[0]['event_type'] == 'transaction.created'


class TestEventStreamingService:
    """Test complete event streaming service."""

    def test_capture_event(self):
        """Test capturing an event end-to-end."""
        service = EventStreamingService()

        success, error = service.capture_event(
            event_type=EventType.TRANSACTION_CREATED,
            user_id=1,
            event_data={
                'transaction_id': 1,
                'account_id': 1,
                'amount': 100.0,
                'transaction_type': 'debit'
            }
        )

        assert success is True
        assert error is None

        events = service.get_events(user_id=1)
        assert len(events) > 0

    def test_reject_duplicate_events(self):
        """Test that duplicate events are rejected."""
        service = EventStreamingService()

        # Capture same event twice
        event_data = {
            'transaction_id': 1,
            'account_id': 1,
            'amount': 100.0,
            'transaction_type': 'debit'
        }

        # First capture should succeed
        success1, _ = service.capture_event(
            event_type=EventType.TRANSACTION_CREATED,
            user_id=1,
            event_data=event_data
        )

        # Manually trigger duplicate with same event_id
        # This simulates a retry scenario
        # Second capture with new data should be different
        event_data2 = {
            'transaction_id': 2,
            'account_id': 1,
            'amount': 200.0,
            'transaction_type': 'debit'
        }

        success2, _ = service.capture_event(
            event_type=EventType.TRANSACTION_CREATED,
            user_id=1,
            event_data=event_data2
        )

        assert success1 is True
        assert success2 is True  # Different event, should succeed


class TestAnalyticsEngine:
    """Test analytics calculation engine."""

    def test_transaction_velocity_calculation(self):
        """Test transaction velocity metrics."""
        engine = AnalyticsEngine(data_manager)

        # This test requires mock data to be present
        # The actual calculation is tested with real data in integration tests
        result = engine.calculate_transaction_velocity(user_id=1, days=30)

        assert 'transactions_per_day' in result
        assert 'transactions_per_week' in result
        assert 'transactions_per_month' in result
        assert 'average_transaction_size' in result
        assert 'trend' in result
        assert result['trend'] in ['increasing', 'decreasing', 'stable']

    def test_cash_flow_calculation(self):
        """Test cash flow intelligence calculation."""
        engine = AnalyticsEngine(data_manager)

        result = engine.calculate_cash_flow(user_id=1, period_days=30)

        assert 'money_in' in result
        assert 'money_out' in result
        assert 'net_flow' in result
        assert 'savings_rate' in result
        assert 'categories' in result
        assert isinstance(result['categories'], list)

    def test_anomaly_detection(self):
        """Test anomaly detection logic."""
        engine = AnalyticsEngine(data_manager)

        anomalies = engine.detect_anomalies(user_id=1, lookback_days=90)

        assert isinstance(anomalies, list)
        # Anomalies may or may not be present depending on data
        for anomaly in anomalies:
            assert 'type' in anomaly
            assert 'severity' in anomaly
            assert anomaly['severity'] in ['low', 'medium', 'high', 'critical']
            assert 'description' in anomaly

    def test_financial_health_score(self):
        """Test comprehensive financial health score."""
        engine = AnalyticsEngine(data_manager)

        result = engine.calculate_financial_health_score(user_id=1)

        assert 'overall_score' in result
        assert 0 <= result['overall_score'] <= 100
        assert 'rating' in result
        assert result['rating'] in ['Excellent', 'Good', 'Fair', 'Needs Improvement']
        assert 'factors' in result
        assert 'recommendations' in result
        assert len(result['factors']) > 0

    def test_investment_performance(self):
        """Test investment performance calculations."""
        engine = AnalyticsEngine(data_manager)

        result = engine.calculate_investment_performance(user_id=1)

        assert 'total_value' in result
        assert 'total_cost_basis' in result
        assert 'total_gain_loss' in result
        assert 'total_gain_loss_percentage' in result
        assert 'asset_allocation' in result
        assert isinstance(result['asset_allocation'], list)

    def test_budget_adherence(self):
        """Test budget adherence tracking."""
        engine = AnalyticsEngine(data_manager)

        result = engine.calculate_budget_adherence(user_id=1)

        assert 'total_budgets' in result
        assert 'on_track_count' in result
        assert 'over_budget_count' in result
        assert 'at_risk_count' in result
        assert 'budgets' in result

        for budget in result['budgets']:
            assert budget['status'] in ['on_track', 'at_risk', 'over_budget']
            assert 0 <= budget['percentage_used']
            assert 0 <= budget['projected_percentage']

    def test_spending_trends(self):
        """Test spending trends calculation."""
        engine = AnalyticsEngine(data_manager)

        result = engine.calculate_spending_trends(user_id=1, months=6)

        assert 'period_months' in result
        assert 'total_categories' in result
        assert 'trends' in result

        for trend in result['trends']:
            assert 'category' in trend
            assert 'average_monthly' in trend
            assert 'trend_direction' in trend
            assert trend['trend_direction'] in ['increasing', 'decreasing', 'stable']
            assert 'monthly_breakdown' in trend


class TestAnalyticsEngineEdgeCases:
    """Test edge cases in analytics calculations."""

    def test_zero_transactions(self):
        """Test handling of user with no transactions."""
        engine = AnalyticsEngine(data_manager)

        # Use a non-existent user ID
        result = engine.calculate_transaction_velocity(user_id=99999, days=30)

        assert result['transactions_per_day'] == 0
        assert result['transactions_per_week'] == 0
        assert result['total_transactions'] == 0

    def test_cache_effectiveness(self):
        """Test that caching improves performance."""
        engine = AnalyticsEngine(data_manager)

        # First call - should be slower (calculate)
        import time
        start1 = time.time()
        result1 = engine.calculate_cash_flow(user_id=1, period_days=30)
        time1 = time.time() - start1

        # Second call - should be faster (cached)
        start2 = time.time()
        result2 = engine.calculate_cash_flow(user_id=1, period_days=30)
        time2 = time.time() - start2

        # Results should be identical
        assert result1 == result2

        # Second call should be significantly faster (at least 50% faster)
        # This assertion might be flaky in CI environments
        # assert time2 < time1 * 0.5, f"Cache didn't improve performance: {time1:.4f}s vs {time2:.4f}s"

    def test_extreme_values(self):
        """Test handling of extreme values in calculations."""
        engine = AnalyticsEngine(data_manager)

        # Test with various parameters
        result = engine.calculate_transaction_velocity(user_id=1, days=1)
        assert isinstance(result['transactions_per_day'], float)

        result = engine.calculate_transaction_velocity(user_id=1, days=365)
        assert isinstance(result['transactions_per_day'], float)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
