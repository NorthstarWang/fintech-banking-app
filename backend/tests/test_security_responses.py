"""
Comprehensive tests for automated security responses system.

Tests account lockout, transaction quarantine, account restriction,
and incident tracking capabilities.
"""

import pytest
from datetime import datetime, timedelta


from app.security.security_responses import SecurityResponses, SecurityIncident, AccountLockout
from app.storage.memory_adapter import db


@pytest.fixture
def db_session():
    """Provide a database session for testing."""
    # Return the db object which has session-like methods
    # For memory adapter, db itself acts as a session
    return db._get_session()


class TestFailedLoginHandling:
    """Test handling of failed login attempts."""

    def test_handle_single_failed_attempt(self, db_session):
        """Test handling single failed login attempt."""
        user_id = 1
        ip_address = "192.168.1.1"
        attempt_count = 1

        response = SecurityResponses.handle_failed_login(
            db_session, user_id, ip_address, attempt_count
        )

        assert isinstance(response, dict)
        assert "blocked" in response
        assert response["blocked"] is False  # Single attempt shouldn't block

    def test_handle_threshold_failed_attempts(self, db_session):
        """Test handling when failed attempts exceed threshold."""
        user_id = 2
        ip_address = "192.168.1.2"
        attempt_count = SecurityResponses.MAX_FAILED_ATTEMPTS

        response = SecurityResponses.handle_failed_login(
            db_session, user_id, ip_address, attempt_count
        )

        assert response["blocked"] is True
        assert "account_locked" in response["actions"]
        assert response["lockout_duration_minutes"] == SecurityResponses.LOCKOUT_DURATION_MINUTES

    def test_lockout_duration_setting(self, db_session):
        """Test lockout duration is properly set."""
        user_id = 3
        ip_address = "192.168.1.3"

        response = SecurityResponses.handle_failed_login(
            db_session, user_id, ip_address, SecurityResponses.MAX_FAILED_ATTEMPTS
        )

        assert response["lockout_duration_minutes"] > 0
        assert response["lockout_duration_minutes"] == SecurityResponses.LOCKOUT_DURATION_MINUTES

    def test_incident_created_on_lockout(self, db_session):
        """Test incident is created on account lockout."""
        user_id = 4

        SecurityResponses.handle_failed_login(
            db_session, user_id, "192.168.1.4", SecurityResponses.MAX_FAILED_ATTEMPTS
        )

        incident = (
            db_session.query(SecurityIncident)
            .filter(SecurityIncident.user_id == user_id)
            .first()
        )

        assert incident is not None
        assert incident.incident_type == "login_lockout"
        assert incident.severity == "high"


class TestHighRiskTransactionHandling:
    """Test handling of high-risk transactions."""

    def test_handle_normal_transaction(self, db_session):
        """Test normal transaction has no special handling."""
        user_id = 5
        transaction_id = 1
        amount = 50.0
        risk_score = 0.2

        response = SecurityResponses.handle_high_risk_transaction(
            db_session, user_id, transaction_id, amount, risk_score
        )

        assert "require_mfa" in response
        assert response["require_mfa"] is False
        assert response["quarantine"] is False

    def test_handle_large_amount_transaction(self, db_session):
        """Test large amount transaction requires step-up auth."""
        user_id = 6
        transaction_id = 2
        amount = SecurityResponses.STEP_UP_AUTH_THRESHOLD + 1000
        risk_score = 0.3

        response = SecurityResponses.handle_high_risk_transaction(
            db_session, user_id, transaction_id, amount, risk_score
        )

        assert "require_step_up_authentication" in response["actions"]

    def test_handle_high_risk_score_transaction(self, db_session):
        """Test high risk score transaction is quarantined."""
        user_id = 7
        transaction_id = 3
        amount = 500.0
        risk_score = SecurityResponses.TRANSACTION_REVIEW_THRESHOLD + 0.1

        response = SecurityResponses.handle_high_risk_transaction(
            db_session, user_id, transaction_id, amount, risk_score
        )

        assert response["quarantine"] is True
        assert "quarantine_for_review" in response["actions"]

    def test_high_risk_transaction_incident(self, db_session):
        """Test incident created for high-risk transaction."""
        user_id = 8
        transaction_id = 4
        amount = 1000.0
        risk_score = 0.75

        SecurityResponses.handle_high_risk_transaction(
            db_session, user_id, transaction_id, amount, risk_score
        )

        incident = (
            db_session.query(SecurityIncident)
            .filter(SecurityIncident.user_id == user_id)
            .first()
        )

        assert incident is not None
        assert incident.incident_type == "transaction_quarantine"


class TestAccountCompromiseHandling:
    """Test handling of suspected account compromise."""

    def test_handle_single_indicator(self, db_session):
        """Test handling single compromise indicator."""
        user_id = 9
        indicators = ["unusual_location"]

        response = SecurityResponses.handle_account_compromise(
            db_session, user_id, indicators
        )

        assert "revoke_other_sessions" in response["actions"]
        assert "force_reauthentication" in response["actions"]
        assert response["account_restricted"] is False  # Single indicator

    def test_handle_multiple_indicators(self, db_session):
        """Test handling multiple compromise indicators."""
        user_id = 10
        indicators = ["unusual_location", "impossible_travel", "new_device"]

        response = SecurityResponses.handle_account_compromise(
            db_session, user_id, indicators
        )

        assert response["account_restricted"] is True
        assert "account_restricted" in response["actions"]

    def test_compromise_incident_created(self, db_session):
        """Test critical incident created for compromise."""
        user_id = 11
        indicators = ["impossible_travel", "new_device", "unusual_time"]

        SecurityResponses.handle_account_compromise(db_session, user_id, indicators)

        incident = (
            db_session.query(SecurityIncident)
            .filter(SecurityIncident.user_id == user_id)
            .first()
        )

        assert incident is not None
        assert incident.severity == "critical"


class TestAccountLockout:
    """Test account lockout functionality."""

    def test_lock_account(self, db_session):
        """Test locking an account."""
        user_id = 12
        reason = "excessive_failed_attempts"

        lockout = SecurityResponses.lock_account(db_session, user_id, reason)

        assert lockout is not None
        assert lockout.user_id == user_id
        assert lockout.reason == reason
        assert lockout.auto_lockout is True

    def test_lockout_has_unlock_time(self, db_session):
        """Test lockout has unlock time set."""
        user_id = 13
        reason = "security_incident"

        lockout = SecurityResponses.lock_account(db_session, user_id, reason)

        assert lockout.unlock_at is not None
        # Unlock time should be in the future
        assert lockout.unlock_at > datetime.utcnow()

    def test_is_account_locked(self, db_session):
        """Test checking if account is locked."""
        user_id = 14

        # Account should not be locked initially
        is_locked = SecurityResponses.is_account_locked(db_session, user_id)
        assert is_locked is False

        # Lock account
        SecurityResponses.lock_account(db_session, user_id, "test_lock")

        # Account should now be locked
        is_locked = SecurityResponses.is_account_locked(db_session, user_id)
        assert is_locked is True

    def test_auto_unlock_on_expiration(self, db_session):
        """Test account auto-unlocks when lockout expires."""
        user_id = 15

        # Lock account
        lockout = SecurityResponses.lock_account(db_session, user_id, "test_lock")

        # Re-query the lockout to ensure it's tracked for updates
        lockout = db_session.query(AccountLockout).filter(
            AccountLockout.user_id == user_id
        ).first()

        # Set unlock time to past
        lockout.unlock_at = datetime.utcnow() - timedelta(minutes=1)
        db_session.commit()

        # Should be automatically unlocked
        is_locked = SecurityResponses.is_account_locked(db_session, user_id)
        assert is_locked is False


class TestAccountRestriction:
    """Test account restriction for pending review."""

    def test_restrict_account(self, db_session):
        """Test restricting an account."""
        user_id = 16
        reason = "suspicious_activity"

        SecurityResponses.restrict_account(db_session, user_id, reason)

        incident = (
            db_session.query(SecurityIncident)
            .filter(SecurityIncident.user_id == user_id)
            .first()
        )

        assert incident is not None
        assert incident.incident_type == "account_restrict"

    def test_restriction_has_critical_severity(self, db_session):
        """Test restricted account has critical severity."""
        user_id = 17
        reason = "compromise_detected"

        SecurityResponses.restrict_account(db_session, user_id, reason)

        incident = (
            db_session.query(SecurityIncident)
            .filter(SecurityIncident.user_id == user_id)
            .first()
        )

        assert incident.severity == "critical"


class TestIncidentCreation:
    """Test security incident creation and management."""

    def test_create_incident(self, db_session):
        """Test creating a security incident."""
        user_id = 18
        incident_type = "login_lockout"
        severity = "high"
        details = {"reason": "excessive_attempts"}

        incident = SecurityResponses.create_incident(
            db_session, user_id, incident_type, severity, details
        )

        assert incident is not None
        assert incident.user_id == user_id
        assert incident.incident_type == incident_type
        assert incident.severity == severity
        assert incident.status == "open"

    def test_incident_has_timestamp(self, db_session):
        """Test incident has creation timestamp."""
        user_id = 19

        incident = SecurityResponses.create_incident(
            db_session, user_id, "test", "medium", {}
        )

        assert incident.created_at is not None
        assert isinstance(incident.created_at, datetime)

    def test_get_open_incidents(self, db_session):
        """Test retrieving open incidents."""
        user_id = 20

        # Create multiple incidents
        for i in range(3):
            SecurityResponses.create_incident(
                db_session, user_id, "test", "low", {"index": i}
            )

        open_incidents = SecurityResponses.get_open_incidents(db_session, user_id)

        assert len(open_incidents) == 3

    def test_resolve_incident(self, db_session):
        """Test resolving an incident."""
        user_id = 21

        incident = SecurityResponses.create_incident(
            db_session, user_id, "test_incident", "medium", {}
        )

        # Resolve incident
        resolved = SecurityResponses.resolve_incident(
            db_session, incident.id, "manual_review_passed"
        )

        assert resolved.status == "resolved"
        assert resolved.resolved_at is not None


class TestSecurityAlerts:
    """Test security alert sending."""

    def test_send_security_alert(self):
        """Test sending security alert."""
        user_id = 22
        alert_type = "login_attempt"
        contact_method = "email"

        result = SecurityResponses.send_security_alert(user_id, alert_type, contact_method)

        assert isinstance(result, bool)
        assert result is True

    def test_alert_types(self):
        """Test various alert types."""
        user_id = 23
        alert_types = [
            "login_attempt",
            "failed_login",
            "account_locked",
            "high_risk_transaction",
            "device_change",
        ]

        for alert_type in alert_types:
            result = SecurityResponses.send_security_alert(user_id, alert_type, "email")
            assert isinstance(result, bool)


class TestIncidentModels:
    """Test SecurityIncident and AccountLockout models."""

    def test_security_incident_model(self, db_session):
        """Test SecurityIncident SQLAlchemy model."""
        incident = SecurityIncident(
            user_id=24,
            incident_type="test_incident",
            severity="high",
            status="open",
            details='{"test": "data"}',
        )

        db_session.add(incident)
        db_session.commit()

        retrieved = (
            db_session.query(SecurityIncident)
            .filter(SecurityIncident.user_id == 24)
            .first()
        )

        assert retrieved.user_id == 24
        assert retrieved.incident_type == "test_incident"
        assert retrieved.severity == "high"

    def test_account_lockout_model(self, db_session):
        """Test AccountLockout SQLAlchemy model."""
        lockout = AccountLockout(
            user_id=25,
            unlock_at=datetime.utcnow() + timedelta(minutes=15),
            reason="test_lockout",
            auto_lockout=True,
        )

        db_session.add(lockout)
        db_session.commit()

        retrieved = db_session.query(AccountLockout).filter(
            AccountLockout.user_id == 25
        ).first()

        assert retrieved.user_id == 25
        assert retrieved.reason == "test_lockout"
        assert retrieved.auto_lockout is True


class TestSecurityResponseThresholds:
    """Test security response thresholds and constants."""

    def test_lockout_threshold(self):
        """Test max failed attempts threshold."""
        assert SecurityResponses.MAX_FAILED_ATTEMPTS > 0
        assert SecurityResponses.MAX_FAILED_ATTEMPTS <= 10

    def test_step_up_auth_threshold(self):
        """Test step-up auth amount threshold."""
        assert SecurityResponses.STEP_UP_AUTH_THRESHOLD > 0
        assert SecurityResponses.STEP_UP_AUTH_THRESHOLD <= 100000

    def test_transaction_review_threshold(self):
        """Test transaction review risk score threshold."""
        assert 0.0 <= SecurityResponses.TRANSACTION_REVIEW_THRESHOLD <= 1.0

    def test_account_restriction_risk_threshold(self):
        """Test account restriction risk threshold."""
        assert 0.0 <= SecurityResponses.ACCOUNT_RESTRICTION_RISK <= 1.0


class TestSecurityResponseIntegration:
    """Integration tests for security response system."""

    def test_full_security_incident_workflow(self, db_session):
        """Test full workflow from detection to resolution."""
        user_id = 26

        # 1. Detect suspicious activity - multiple failed logins
        response1 = SecurityResponses.handle_failed_login(
            db_session, user_id, "192.168.1.26", SecurityResponses.MAX_FAILED_ATTEMPTS
        )

        assert response1["blocked"] is True

        # 2. Verify account is locked
        is_locked = SecurityResponses.is_account_locked(db_session, user_id)
        assert is_locked is True

        # 3. Get open incidents
        incidents = SecurityResponses.get_open_incidents(db_session, user_id)
        assert len(incidents) > 0

        # 4. Resolve incident
        incident = incidents[0]
        SecurityResponses.resolve_incident(db_session, incident.id, "admin_investigation_complete")

        # 5. Verify incident is resolved
        resolved_incident = db_session.query(SecurityIncident).filter(
            SecurityIncident.id == incident.id
        ).first()

        assert resolved_incident.status == "resolved"

    def test_cascading_security_responses(self, db_session):
        """Test cascading security responses."""
        user_id = 27

        # High-risk transaction triggers multiple responses
        response = SecurityResponses.handle_high_risk_transaction(
            db_session,
            user_id,
            100,
            SecurityResponses.STEP_UP_AUTH_THRESHOLD + 5000,  # Large amount
            0.9,  # High risk score
        )

        # Should require authentication and quarantine
        assert "require_step_up_authentication" in response["actions"]
        assert response["quarantine"] is True

        # Incident should be created
        incident = (
            db_session.query(SecurityIncident)
            .filter(SecurityIncident.user_id == user_id)
            .first()
        )

        assert incident is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
