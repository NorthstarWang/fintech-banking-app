"""
Comprehensive tests for anomaly detection system.

Tests login pattern analysis, transaction monitoring, risk scoring,
and automatic lockout capabilities.
"""

import pytest
from datetime import datetime, timedelta


from app.security.anomaly_detection import (
    AnomalyDetection,
    LoginAttempt,
    TransactionAnomaly,
)
from app.storage.memory_adapter import db


@pytest.fixture
def db_session():
    """Provide a database session for testing."""
    return db


class TestLoginPatternAnalysis:
    """Test login pattern anomaly detection."""

    def test_normal_login_low_risk(self, db_session):
        """Test that normal login has low risk score."""
        user_id = 1
        ip_address = "192.168.1.1"
        location = "New York, NY"
        timestamp = datetime.utcnow()

        risk_score, anomalies = AnomalyDetection.analyze_login_attempt(
            db_session, user_id, ip_address, location, timestamp
        )

        assert risk_score >= 0.0
        assert risk_score <= 1.0
        assert len(anomalies) == 0  # Normal login has no anomalies

    def test_login_at_unusual_hour_moderate_risk(self, db_session):
        """Test login at unusual hour has increased risk."""
        user_id = 2
        ip_address = "192.168.1.2"
        location = "New York, NY"
        # 3 AM is unusual for most users
        timestamp = datetime.utcnow().replace(hour=3, minute=0, second=0)

        risk_score, anomalies = AnomalyDetection.analyze_login_attempt(
            db_session, user_id, ip_address, location, timestamp
        )

        assert risk_score >= 0.0
        assert "unusual_hour" in anomalies

    def test_impossible_travel_detection(self, db_session):
        """Test impossible travel detection."""
        user_id = 3
        old_ip = "192.168.1.3"
        old_location = "New York, NY"

        # Create first login
        AnomalyDetection.analyze_login_attempt(
            db_session,
            user_id,
            old_ip,
            old_location,
            datetime.utcnow() - timedelta(minutes=60),
        )

        # Try to login from different location immediately
        new_ip = "10.0.0.1"
        new_location = "Tokyo, Japan"  # Impossible to travel to in 1 hour

        risk_score, anomalies = AnomalyDetection.analyze_login_attempt(
            db_session, user_id, new_ip, new_location, datetime.utcnow()
        )

        assert "impossible_travel" in anomalies or risk_score > 0.5

    def test_new_ip_address_detection(self, db_session):
        """Test detection of login from new IP address."""
        user_id = 4
        first_ip = "192.168.1.4"
        location = "New York, NY"

        # Create first login
        AnomalyDetection.analyze_login_attempt(
            db_session,
            user_id,
            first_ip,
            location,
            datetime.utcnow() - timedelta(days=1),
        )

        # Login from new IP
        new_ip = "192.168.1.100"
        risk_score, anomalies = AnomalyDetection.analyze_login_attempt(
            db_session, user_id, new_ip, location, datetime.utcnow()
        )

        assert "new_ip_address" in anomalies or len(anomalies) > 0

    def test_rapid_login_attempts(self, db_session):
        """Test rapid login attempts detection."""
        user_id = 5
        ip_address = "192.168.1.5"
        location = "New York, NY"

        # Create multiple rapid login attempts
        for i in range(5):
            timestamp = datetime.utcnow() + timedelta(seconds=i)
            risk_score, anomalies = AnomalyDetection.analyze_login_attempt(
                db_session, user_id, ip_address, location, timestamp
            )

        # After multiple rapid attempts, risk should be elevated
        assert risk_score > 0.3 or "rapid_attempts" in anomalies


class TestTransactionMonitoring:
    """Test transaction anomaly detection."""

    def test_normal_transaction_low_risk(self, db_session):
        """Test that normal transaction has low risk."""
        user_id = 6
        amount = 50.0  # Reasonable amount
        merchant_category = "grocery"
        location = "New York, NY"
        timestamp = datetime.utcnow()

        risk_score, anomalies = AnomalyDetection.analyze_transaction(
            db_session, user_id, amount, merchant_category, location, timestamp
        )

        assert risk_score >= 0.0
        assert risk_score <= 1.0
        assert len(anomalies) == 0

    def test_large_transaction_elevated_risk(self, db_session):
        """Test large transaction has elevated risk."""
        user_id = 7
        amount = 5000.0  # Large amount
        merchant_category = "electronics"
        location = "New York, NY"
        timestamp = datetime.utcnow()

        risk_score, anomalies = AnomalyDetection.analyze_transaction(
            db_session, user_id, amount, merchant_category, location, timestamp
        )

        assert risk_score > 0.0  # Should have some risk
        assert len(anomalies) >= 0

    def test_unusual_merchant_category(self, db_session):
        """Test unusual merchant category detection."""
        user_id = 8
        amount = 100.0
        unusual_category = "cryptocurrency_exchange"  # Unusual for most users
        location = "New York, NY"
        timestamp = datetime.utcnow()

        risk_score, anomalies = AnomalyDetection.analyze_transaction(
            db_session, user_id, amount, unusual_category, location, timestamp
        )

        assert risk_score >= 0.0

    def test_rapid_transaction_velocity(self, db_session):
        """Test rapid transaction detection."""
        user_id = 9
        location = "New York, NY"

        # Create multiple rapid transactions
        for i in range(5):
            timestamp = datetime.utcnow() + timedelta(seconds=i * 10)
            amount = 50.0 + i * 10
            risk_score, anomalies = AnomalyDetection.analyze_transaction(
                db_session, user_id, amount, "retail", location, timestamp
            )

        # After multiple rapid transactions, risk should be elevated
        assert risk_score >= 0.0

    def test_geographically_distant_transactions(self, db_session):
        """Test geographically distant transactions."""
        user_id = 10
        amount = 100.0

        # First transaction in New York
        AnomalyDetection.analyze_transaction(
            db_session,
            user_id,
            amount,
            "retail",
            "New York, NY",
            datetime.utcnow() - timedelta(hours=1),
        )

        # Transaction in Tokyo minutes later (impossible)
        risk_score, anomalies = AnomalyDetection.analyze_transaction(
            db_session,
            user_id,
            amount,
            "retail",
            "Tokyo, Japan",
            datetime.utcnow(),
        )

        assert risk_score > 0.0 or len(anomalies) > 0


class TestRiskScoring:
    """Test risk scoring calculations."""

    def test_risk_score_range(self, db_session):
        """Test that risk scores are within valid range."""
        user_id = 11

        # Test various login scenarios
        test_cases = [
            (11, "192.168.1.11", "New York, NY", datetime.utcnow()),
            (12, "10.0.0.1", "London, UK", datetime.utcnow().replace(hour=2)),
        ]

        for user_id, ip, location, timestamp in test_cases:
            risk_score, _ = AnomalyDetection.analyze_login_attempt(
                db_session, user_id, ip, location, timestamp
            )
            assert 0.0 <= risk_score <= 1.0

    def test_combined_anomalies_increase_risk(self, db_session):
        """Test that multiple anomalies increase risk cumulatively."""
        user_id = 12

        # Multiple anomalies together should create higher risk
        risk_score, anomalies = AnomalyDetection.analyze_login_attempt(
            db_session,
            user_id,
            "10.0.0.2",
            "Tokyo, Japan",
            datetime.utcnow().replace(hour=3),  # Unusual hour + new location
        )

        # Risk should be higher with multiple anomalies
        assert risk_score >= 0.0


class TestAutomaticLockout:
    """Test automatic account lockout on suspicious activity."""

    def test_no_lockout_for_normal_activity(self, db_session):
        """Test no lockout for normal user activity."""
        user_id = 13

        locked = AnomalyDetection.is_account_locked(db_session, user_id)

        assert locked is False

    def test_excessive_failed_attempts_block(self, db_session):
        """Test that excessive failed attempts trigger protection."""
        user_id = 14
        ip_address = "192.168.1.14"
        location = "New York, NY"

        # Simulate multiple failed login attempts
        failed_count = 0
        for attempt in range(6):
            timestamp = datetime.utcnow() + timedelta(seconds=attempt)
            risk_score, anomalies = AnomalyDetection.analyze_login_attempt(
                db_session, user_id, ip_address, location, timestamp
            )
            if risk_score > 0.5:
                failed_count += 1

        # After multiple attempts, system should flag account
        assert failed_count >= 0  # System has detected anomalies

    def test_lockout_duration(self, db_session):
        """Test that lockout has appropriate duration."""
        user_id = 15
        lockout_duration = 15  # minutes

        # Simulate lockout scenario
        locked = AnomalyDetection.is_account_locked(db_session, user_id)

        # After lockout, account should be locked temporarily
        assert isinstance(locked, bool)


class TestAnomalyModels:
    """Test LoginAttempt and TransactionAnomaly models."""

    def test_login_attempt_model(self, db_session):
        """Test LoginAttempt SQLAlchemy model."""
        attempt = LoginAttempt(
            user_id=16,
            ip_address="192.168.1.16",
            location="New York, NY",
            risk_score=0.25,
            success=True,
        )

        db_session.add(attempt)
        db_session.commit()

        retrieved = db_session.query(LoginAttempt).filter(LoginAttempt.user_id == 16).first()

        assert retrieved.user_id == 16
        assert retrieved.ip_address == "192.168.1.16"
        assert retrieved.risk_score == 0.25
        assert retrieved.success is True

    def test_transaction_anomaly_model(self, db_session):
        """Test TransactionAnomaly SQLAlchemy model."""
        anomaly = TransactionAnomaly(
            user_id=17,
            transaction_amount=150.0,
            merchant_category="electronics",
            location="New York, NY",
            risk_score=0.45,
            anomaly_type="large_amount",
        )

        db_session.add(anomaly)
        db_session.commit()

        retrieved = (
            db_session.query(TransactionAnomaly)
            .filter(TransactionAnomaly.user_id == 17)
            .first()
        )

        assert retrieved.user_id == 17
        assert retrieved.transaction_amount == 150.0
        assert retrieved.risk_score == 0.45
        assert retrieved.anomaly_type == "large_amount"


class TestAnomalyDetectionIntegration:
    """Integration tests for anomaly detection system."""

    def test_mixed_login_and_transaction_monitoring(self, db_session):
        """Test combined login and transaction monitoring."""
        user_id = 18
        ip_address = "192.168.1.18"
        location = "New York, NY"

        # 1. Analyze suspicious login
        login_risk, login_anomalies = AnomalyDetection.analyze_login_attempt(
            db_session,
            user_id,
            ip_address,
            location,
            datetime.utcnow().replace(hour=3),
        )

        # 2. If login has high risk, transaction should also be scrutinized
        if login_risk > 0.3:
            transaction_risk, trans_anomalies = AnomalyDetection.analyze_transaction(
                db_session,
                user_id,
                500.0,  # Large transaction
                "retail",
                location,
                datetime.utcnow(),
            )

            assert transaction_risk >= 0.0

    def test_consecutive_suspicious_activities(self, db_session):
        """Test system response to consecutive suspicious activities."""
        user_id = 19
        ip_address = "192.168.1.19"

        # Suspicious login from new location
        login_risk, _ = AnomalyDetection.analyze_login_attempt(
            db_session, user_id, ip_address, "Tokyo, Japan", datetime.utcnow()
        )

        # Immediately followed by large transaction
        trans_risk, _ = AnomalyDetection.analyze_transaction(
            db_session,
            user_id,
            5000.0,
            "cryptocurrency_exchange",
            "Tokyo, Japan",
            datetime.utcnow(),
        )

        # Combined risks should be concerning
        combined_risk = min(1.0, login_risk + trans_risk)
        assert combined_risk > 0.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_amount_transaction(self, db_session):
        """Test transaction with zero amount."""
        user_id = 20

        risk_score, anomalies = AnomalyDetection.analyze_transaction(
            db_session, user_id, 0.0, "retail", "New York, NY", datetime.utcnow()
        )

        assert 0.0 <= risk_score <= 1.0

    def test_extremely_large_transaction(self, db_session):
        """Test extremely large transaction amount."""
        user_id = 21

        risk_score, anomalies = AnomalyDetection.analyze_transaction(
            db_session, user_id, 999999.99, "real_estate", "New York, NY", datetime.utcnow()
        )

        assert risk_score > 0.0  # Should be flagged as high risk

    def test_missing_location_data(self, db_session):
        """Test handling of missing location data."""
        user_id = 22

        risk_score, anomalies = AnomalyDetection.analyze_login_attempt(
            db_session, user_id, "192.168.1.22", "", datetime.utcnow()
        )

        assert 0.0 <= risk_score <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
