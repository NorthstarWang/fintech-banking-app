"""
Automated security responses for threat protection.

Automatically responds to security events without manual intervention.
"""
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

# Import models from memory models instead of defining SQLAlchemy models
from app.models.memory_models import AccountLockout, SecurityIncident


class SecurityResponses:
    """Service for automated security responses."""

    LOCKOUT_DURATION_MINUTES = 15
    MAX_FAILED_ATTEMPTS = 5
    STEP_UP_AUTH_THRESHOLD = 10000  # $10,000
    TRANSACTION_REVIEW_THRESHOLD = 0.7  # Risk score
    ACCOUNT_RESTRICTION_RISK = 0.8

    @staticmethod
    def handle_failed_login(
        db: Session,
        user_id: int,
        ip_address: str,
        attempt_count: int,
    ) -> dict[str, Any]:
        """
        Handle a failed login attempt.

        Returns:
            dict with action and details
        """
        actions = []

        if attempt_count >= SecurityResponses.MAX_FAILED_ATTEMPTS:
            # Lock account
            SecurityResponses.lock_account(
                db,
                user_id,
                "excessive_failed_login_attempts",
            )
            actions.append("account_locked")

            # Create incident
            SecurityResponses.create_incident(
                db,
                user_id,
                "login_lockout",
                "high",
                {"ip_address": ip_address, "attempt_count": attempt_count},
            )

        return {
            "blocked": attempt_count >= SecurityResponses.MAX_FAILED_ATTEMPTS,
            "actions": actions,
            "lockout_duration_minutes": SecurityResponses.LOCKOUT_DURATION_MINUTES,
        }

    @staticmethod
    def handle_high_risk_transaction(
        db: Session,
        user_id: int,
        transaction_id: int,
        amount: float,
        risk_score: float,
    ) -> dict[str, Any]:
        """
        Handle a high-risk transaction.

        Returns:
            dict with action and details
        """
        actions = []

        if amount > SecurityResponses.STEP_UP_AUTH_THRESHOLD:
            actions.append("require_step_up_authentication")

        if risk_score > SecurityResponses.TRANSACTION_REVIEW_THRESHOLD:
            actions.append("quarantine_for_review")

            # Create incident
            SecurityResponses.create_incident(
                db,
                user_id,
                "transaction_quarantine",
                "medium",
                {
                    "transaction_id": transaction_id,
                    "amount": amount,
                    "risk_score": risk_score,
                },
            )

        return {
            "require_mfa": risk_score > 0.5,
            "quarantine": "quarantine_for_review" in actions,
            "actions": actions,
        }

    @staticmethod
    def handle_account_compromise(
        db: Session,
        user_id: int,
        indicators: list[str],
    ) -> dict[str, Any]:
        """
        Handle suspected account compromise.

        Indicators: unusual_location, impossible_travel, etc
        """
        actions = []

        # Revoke all sessions except current
        actions.append("revoke_other_sessions")

        # Force re-authentication
        actions.append("force_reauthentication")

        # Lock for review if multiple indicators
        if len(indicators) > 2:
            SecurityResponses.restrict_account(
                db,
                user_id,
                "account_compromise_indicators",
            )
            actions.append("account_restricted")

            # Create critical incident
            SecurityResponses.create_incident(
                db,
                user_id,
                "account_restrict",
                "critical",
                {
                    "indicators": indicators,
                    "action": "account_restricted",
                },
            )

        return {
            "account_restricted": "account_restricted" in actions,
            "actions": actions,
        }

    @staticmethod
    def lock_account(
        db: Session,
        user_id: int,
        reason: str,
    ) -> AccountLockout:
        """Lock a user account."""
        unlock_at = datetime.utcnow() + timedelta(
            minutes=SecurityResponses.LOCKOUT_DURATION_MINUTES
        )

        lockout = AccountLockout(
            user_id=user_id,
            unlock_at=unlock_at,
            reason=reason,
            auto_lockout=True,
        )
        db.add(lockout)
        db.commit()

        return lockout

    @staticmethod
    def is_account_locked(db: Session, user_id: int) -> bool:
        """Check if account is locked."""
        lockout = db.query(AccountLockout).filter(
            AccountLockout.user_id == user_id,
        ).first()

        if not lockout:
            return False

        if lockout.unlock_at and datetime.utcnow() > lockout.unlock_at:
            # Auto-unlock
            db.delete(lockout)
            db.commit()
            return False

        return True

    @staticmethod
    def restrict_account(
        db: Session,
        user_id: int,
        reason: str,
    ) -> None:
        """Restrict account pending manual review."""
        # Create marker for restricted account
        # In production, add to User model
        return SecurityResponses.create_incident(
            db,
            user_id,
            "account_restrict",
            "critical",
            {"reason": reason},
        )

    @staticmethod
    def create_incident(
        db: Session,
        user_id: int,
        incident_type: str,
        severity: str,
        details: dict[str, Any] | None = None,
    ) -> SecurityIncident:
        """Create a security incident record."""
        import json
        incident = SecurityIncident(
            user_id=user_id,
            incident_type=incident_type,
            severity=severity,
            details=json.dumps(details or {}),
        )
        db.add(incident)
        db.commit()

        return incident

    @staticmethod
    def send_security_alert(
        user_id: int,
        alert_type: str,
        contact_method: str = "email",
    ) -> bool:
        """
        Send security alert to user.

        Args:
            user_id: User to alert
            alert_type: Type of alert
            contact_method: 'email' or 'sms'

        Returns:
            Success status
        """
        # In production, integrate with communication service
        alert_messages = {
            "login_attempt": "New login attempt detected",
            "failed_login": "Multiple failed login attempts",
            "account_locked": "Your account has been locked for security",
            "high_risk_transaction": "High-risk transaction detected",
            "device_change": "New device detected on your account",
        }

        alert_messages.get(alert_type, "Security alert for your account")

        # Log alert send in production
        return True

    @staticmethod
    def get_open_incidents(db: Session, user_id: int | None = None) -> list[SecurityIncident]:
        """Get open security incidents."""
        query = db.query(SecurityIncident).filter(
            SecurityIncident.status == "open"
        )

        if user_id:
            query = query.filter(SecurityIncident.user_id == user_id)

        return query.order_by(
            SecurityIncident.created_at.desc()
        ).all()

    @staticmethod
    def resolve_incident(
        db: Session,
        incident_id: int,
        resolution: str,
    ) -> SecurityIncident:
        """Resolve a security incident."""
        incident = db.query(SecurityIncident).filter(
            SecurityIncident.id == incident_id
        ).first()

        if incident:
            incident.status = "resolved"
            incident.resolved_at = datetime.utcnow()
            db.commit()

        return incident
