"""
Anomaly detection for login patterns and transaction activity.

Monitors and scores suspicious behavior for risk-based authentication.
"""
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import Session, declarative_base

# Create SQLAlchemy base for security models
Base = declarative_base()


class LoginAttempt(Base):
    """Model for tracking login attempts."""

    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    ip_address = Column(String(45), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    success = Column(Integer, default=0)
    location = Column(String(255))
    device_fingerprint = Column(String(256))
    risk_score = Column(Float, default=0.0)


class TransactionAnomaly(Base):
    """Model for tracking transaction anomalies."""

    __tablename__ = "transaction_anomalies"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    transaction_id = Column(Integer, index=True)
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    anomaly_type = Column(String(100))  # amount, velocity, category, location
    risk_score = Column(Float)
    flagged = Column(Integer, default=0)


class AnomalyDetector:
    """Service for detecting anomalous login and transaction patterns."""

    # Configuration thresholds
    FAILED_LOGIN_THRESHOLD = 5
    LOCKOUT_DURATION_MINUTES = 15
    UNUSUAL_HOUR_RISK = 0.2  # 2 AM - 5 AM
    LOCATION_CHANGE_RISK = 0.3
    IMPOSSIBLE_TRAVEL_RISK = 0.8
    HIGH_FREQUENCY_RISK = 0.4
    UNUSUAL_AMOUNT_MULTIPLIER = 2.0  # 2x average = risky
    VELOCITY_WINDOW_MINUTES = 60

    @staticmethod
    def analyze_login_attempt(
        db: Session,
        user_id: int,
        ip_address: str,
        location: str | None,
        device_fingerprint: str,
    ) -> dict[str, Any]:
        """
        Analyze a login attempt for anomalies.

        Returns:
            dict with risk_score and flags
        """
        risk_score = 0.0
        flags = []

        # Check recent failed attempts
        failed_attempts = db.query(LoginAttempt).filter(
            LoginAttempt.user_id == user_id,
            LoginAttempt.success == 0,
            LoginAttempt.timestamp > datetime.utcnow() - timedelta(minutes=30),
        ).count()

        if failed_attempts >= AnomalyDetector.FAILED_LOGIN_THRESHOLD:
            risk_score += 0.5
            flags.append("excessive_failed_attempts")

        # Check for unusual time of day
        hour = datetime.utcnow().hour
        if hour < 5 or hour > 23:
            risk_score += AnomalyDetector.UNUSUAL_HOUR_RISK
            flags.append("unusual_login_time")

        # Check for location changes
        last_login = db.query(LoginAttempt).filter(
            LoginAttempt.user_id == user_id,
            LoginAttempt.success == 1,
        ).order_by(LoginAttempt.timestamp.desc()).first()

        if last_login and location and last_login.location != location:
            risk_score += AnomalyDetector.LOCATION_CHANGE_RISK
            flags.append("location_change")

        # Check for impossible travel
        if (last_login and last_login.location and location and
                AnomalyDetector._is_impossible_travel(
                    last_login.timestamp,
                    last_login.location,
                    location,
                )):
            risk_score += AnomalyDetector.IMPOSSIBLE_TRAVEL_RISK
            flags.append("impossible_travel")

        # Record the attempt
        attempt = LoginAttempt(
            user_id=user_id,
            ip_address=ip_address,
            location=location,
            device_fingerprint=device_fingerprint,
            risk_score=min(risk_score, 1.0),
        )
        db.add(attempt)
        db.commit()

        return {
            "risk_score": min(risk_score, 1.0),
            "flags": flags,
            "requires_mfa": risk_score > 0.5,
            "requires_verification": risk_score > 0.7,
        }

    @staticmethod
    def analyze_transaction(
        db: Session,
        user_id: int,
        transaction_id: int,
        amount: float,
        category: str,
    ) -> dict[str, Any]:
        """
        Analyze a transaction for anomalies.

        Returns:
            dict with risk_score and flags
        """
        risk_score = 0.0
        flags = []
        anomaly_types = []

        # Get user's average transaction amount
        avg_amount = AnomalyDetector._get_average_transaction_amount(
            db,
            user_id,
            category,
        )

        # Check for unusual amounts
        if avg_amount and amount > avg_amount * AnomalyDetector.UNUSUAL_AMOUNT_MULTIPLIER:
            risk_score += 0.3
            flags.append("unusual_amount")
            anomaly_types.append("amount")

        # Check for high transaction velocity
        velocity = AnomalyDetector._get_transaction_velocity(
            db,
            user_id,
            minutes=AnomalyDetector.VELOCITY_WINDOW_MINUTES,
        )

        if velocity > 5:  # More than 5 transactions in last hour
            risk_score += AnomalyDetector.HIGH_FREQUENCY_RISK
            flags.append("high_velocity")
            anomaly_types.append("velocity")

        # Check for unusual category pattern
        if AnomalyDetector._is_unusual_category(db, user_id, category):
            risk_score += 0.2
            flags.append("unusual_category")
            anomaly_types.append("category")

        # Record anomaly if detected
        if risk_score > 0.2:
            anomaly = TransactionAnomaly(
                user_id=user_id,
                transaction_id=transaction_id,
                amount=amount,
                anomaly_type=",".join(anomaly_types),
                risk_score=min(risk_score, 1.0),
                flagged=1 if risk_score > 0.6 else 0,
            )
            db.add(anomaly)
            db.commit()

        return {
            "risk_score": min(risk_score, 1.0),
            "flags": flags,
            "requires_review": risk_score > 0.5,
            "should_quarantine": risk_score > 0.7,
        }

    @staticmethod
    def _is_impossible_travel(
        last_login_time: datetime,
        from_location: str,
        to_location: str,
    ) -> bool:
        """Check if travel between locations is geographically impossible."""
        # Simplified check - in production, use actual geolocation
        time_diff = (datetime.utcnow() - last_login_time).total_seconds() / 3600
        # Assume ~500 km/hour max travel speed
        # If different countries in < 1 hour = impossible
        return bool(from_location != to_location and time_diff < 1)

    @staticmethod
    def _get_average_transaction_amount(
        db: Session,
        user_id: int,
        category: str,
        days: int = 30,
    ) -> float | None:
        """Get average transaction amount for user in category."""
        # Query transaction history (mock)
        # In production, query actual transaction table
        return None

    @staticmethod
    def _get_transaction_velocity(
        db: Session,
        user_id: int,
        minutes: int = 60,
    ) -> int:
        """Get number of transactions in last N minutes."""
        return db.query(TransactionAnomaly).filter(
            TransactionAnomaly.user_id == user_id,
            TransactionAnomaly.timestamp > datetime.utcnow() - timedelta(minutes=minutes),
        ).count()

    @staticmethod
    def _is_unusual_category(
        db: Session,
        user_id: int,
        category: str,
    ) -> bool:
        """Check if category is unusual for this user."""
        # In production, analyze transaction history
        return False

    @staticmethod
    def get_failed_login_count(
        db: Session,
        user_id: int,
        minutes: int = 30,
    ) -> int:
        """Get number of failed login attempts in last N minutes."""
        return db.query(LoginAttempt).filter(
            LoginAttempt.user_id == user_id,
            LoginAttempt.success == 0,
            LoginAttempt.timestamp > datetime.utcnow() - timedelta(minutes=minutes),
        ).count()

    @staticmethod
    def is_account_locked(
        db: Session,
        user_id: int,
    ) -> bool:
        """Check if account is locked due to failed attempts."""
        failed_count = AnomalyDetector.get_failed_login_count(
            db,
            user_id,
            minutes=AnomalyDetector.LOCKOUT_DURATION_MINUTES,
        )
        return failed_count >= AnomalyDetector.FAILED_LOGIN_THRESHOLD
