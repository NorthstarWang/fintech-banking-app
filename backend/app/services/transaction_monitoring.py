"""
Comprehensive Transaction Monitoring System

Tracks transaction metrics, performance, failures, and system health.
Provides real-time dashboards and alerting capabilities.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import statistics


@dataclass
class TransactionMetrics:
    """Metrics for a single transaction"""
    transaction_id: str
    user_id: int
    transaction_type: str
    amount: Decimal
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "in_progress"
    error: Optional[str] = None

    @property
    def duration_ms(self) -> Optional[float]:
        """Duration in milliseconds"""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None


@dataclass
class SystemHealthMetrics:
    """System-wide health metrics"""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    queue_size: int = 0
    processing_rate: float = 0.0  # TPS
    failure_rate: float = 0.0  # percentage
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    deadletter_size: int = 0
    active_sagas: int = 0


class TransactionMonitor:
    """Monitor transaction performance and health"""

    def __init__(self, window_size: int = 3600):
        """
        Initialize monitor.

        Args:
            window_size: Time window in seconds for metrics (default 1 hour)
        """
        self.window_size = window_size
        self._metrics: Dict[str, TransactionMetrics] = {}
        self._transaction_timings: List[float] = []
        self._failure_log: List[Dict[str, Any]] = []
        self._queue_history: List[tuple] = []
        self._health_snapshots: List[SystemHealthMetrics] = []

    def record_transaction_start(
        self,
        transaction_id: str,
        user_id: int,
        transaction_type: str,
        amount: Decimal,
    ) -> None:
        """Record transaction start"""
        self._metrics[transaction_id] = TransactionMetrics(
            transaction_id=transaction_id,
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            started_at=datetime.now(timezone.utc),
        )

    def record_transaction_complete(
        self,
        transaction_id: str,
        status: str = "completed",
        error: Optional[str] = None,
    ) -> None:
        """Record transaction completion"""
        if transaction_id not in self._metrics:
            return

        metric = self._metrics[transaction_id]
        metric.completed_at = datetime.now(timezone.utc)
        metric.status = status
        metric.error = error

        if metric.duration_ms:
            self._transaction_timings.append(metric.duration_ms)

        if status == "failed":
            self._failure_log.append({
                'transaction_id': transaction_id,
                'timestamp': datetime.now(timezone.utc),
                'error': error,
                'type': metric.transaction_type,
            })

    def record_queue_size(self, size: int) -> None:
        """Record queue size for history"""
        self._queue_history.append(
            (datetime.now(timezone.utc), size)
        )

    def get_transaction_metrics(self, transaction_id: str) -> Optional[TransactionMetrics]:
        """Get metrics for a transaction"""
        return self._metrics.get(transaction_id)

    def get_health_snapshot(self) -> SystemHealthMetrics:
        """Get current system health"""
        # Clean old timing data
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.window_size)
        active_metrics = [
            m for m in self._metrics.values()
            if m.started_at > cutoff
        ]

        # Calculate metrics
        timings = [m.duration_ms for m in active_metrics if m.duration_ms]
        failed = sum(1 for m in active_metrics if m.status == 'failed')
        total = len(active_metrics)
        failure_rate = (failed / total * 100) if total > 0 else 0

        health = SystemHealthMetrics(
            queue_size=len(active_metrics),
            processing_rate=len(active_metrics) / self.window_size,
            failure_rate=failure_rate,
            avg_latency_ms=statistics.mean(timings) if timings else 0,
            p95_latency_ms=(
                sorted(timings)[int(len(timings) * 0.95)]
                if len(timings) >= 20 else 0
            ),
            p99_latency_ms=(
                sorted(timings)[int(len(timings) * 0.99)]
                if len(timings) >= 100 else 0
            ),
        )

        self._health_snapshots.append(health)
        return health

    def get_failure_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get failure report for specified time window"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_failures = [
            f for f in self._failure_log
            if f['timestamp'] > cutoff
        ]

        # Group by type
        by_type = defaultdict(list)
        for failure in recent_failures:
            by_type[failure['type']].append(failure)

        return {
            'total_failures': len(recent_failures),
            'by_type': dict(by_type),
            'failure_rate': (
                len(recent_failures) / len(self._metrics) * 100
                if self._metrics else 0
            ),
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance metrics report"""
        if not self._transaction_timings:
            return {
                'min_ms': 0,
                'max_ms': 0,
                'avg_ms': 0,
                'median_ms': 0,
                'p95_ms': 0,
                'p99_ms': 0,
            }

        sorted_timings = sorted(self._transaction_timings)
        return {
            'min_ms': min(self._transaction_timings),
            'max_ms': max(self._transaction_timings),
            'avg_ms': statistics.mean(self._transaction_timings),
            'median_ms': statistics.median(self._transaction_timings),
            'p95_ms': sorted_timings[int(len(sorted_timings) * 0.95)],
            'p99_ms': sorted_timings[int(len(sorted_timings) * 0.99)],
        }

    def get_throughput_report(self) -> Dict[str, Any]:
        """Get throughput metrics"""
        now = datetime.now(timezone.utc)

        # Count by hour
        hourly = defaultdict(int)
        for metric in self._metrics.values():
            hour = metric.started_at.replace(minute=0, second=0, microsecond=0)
            hourly[hour] += 1

        return {
            'total_processed': len(self._metrics),
            'hourly_breakdown': dict(hourly),
            'current_tps': len([
                m for m in self._metrics.values()
                if (now - m.started_at).total_seconds() < 60
            ]) / 60,
        }

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all dashboard data"""
        health = self.get_health_snapshot()

        return {
            'health': {
                'queue_size': health.queue_size,
                'processing_rate': health.processing_rate,
                'failure_rate': health.failure_rate,
                'avg_latency_ms': health.avg_latency_ms,
                'p95_latency_ms': health.p95_latency_ms,
                'p99_latency_ms': health.p99_latency_ms,
            },
            'performance': self.get_performance_report(),
            'throughput': self.get_throughput_report(),
            'failures': self.get_failure_report(hours=24),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }


# Global monitor instance
_monitor: Optional[TransactionMonitor] = None


def get_transaction_monitor() -> TransactionMonitor:
    """Get global transaction monitor"""
    global _monitor
    if _monitor is None:
        _monitor = TransactionMonitor()
    return _monitor


def reset_transaction_monitor() -> None:
    """Reset monitor (for testing)"""
    global _monitor
    _monitor = TransactionMonitor()
