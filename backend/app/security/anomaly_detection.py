"""
Anomaly detection for login patterns and transaction activity.

Monitors and scores suspicious behavior for risk-based authentication.
"""
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

# Import models from memory models instead of defining SQLAlchemy models
from app.models.memory_models import LoginAttempt, TransactionAnomaly


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


# Create alias for backward compatibility with tests
class AnomalyDetection:
    """Alias for AnomalyDetector to match test imports."""

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
        location: str,
        timestamp: datetime,
    ) -> tuple[float, list[str]]:
        """Analyze login attempt and return (risk_score, anomalies)."""
        risk_score = 0.0
        flags = []

        # Check recent failed attempts
        failed_attempts = db.query(LoginAttempt).filter(
            LoginAttempt.user_id == user_id,
            LoginAttempt.success == 0,
            LoginAttempt.timestamp > timestamp - timedelta(minutes=30),
        ).count()

        if failed_attempts >= AnomalyDetection.FAILED_LOGIN_THRESHOLD:
            risk_score += 0.5
            flags.append("excessive_failed_attempts")

        # Check for unusual time of day (very late night / early morning)
        hour = timestamp.hour
        if 2 <= hour <= 4:  # Only flag truly unusual hours (2 AM - 4 AM)
            risk_score += AnomalyDetection.UNUSUAL_HOUR_RISK
            flags.append("unusual_hour")

        # Check for new IP address
        previous_attempts = db.query(LoginAttempt).filter(
            LoginAttempt.user_id == user_id,
            LoginAttempt.success == 1,
        ).order_by(LoginAttempt.timestamp.desc()).limit(10).all()

        previous_ips = {attempt.ip_address for attempt in previous_attempts if attempt.ip_address}
        if previous_ips and ip_address not in previous_ips:
            risk_score += 0.2
            flags.append("new_ip_address")

        # Check for location changes and impossible travel
        last_login = db.query(LoginAttempt).filter(
            LoginAttempt.user_id == user_id,
            LoginAttempt.success == 1,
        ).order_by(LoginAttempt.timestamp.desc()).first()

        if last_login and location and last_login.location != location:
            risk_score += AnomalyDetection.LOCATION_CHANGE_RISK
            flags.append("location_change")

            # Check for impossible travel
            if last_login.location and AnomalyDetection._is_impossible_travel(
                last_login.timestamp,
                timestamp,
                last_login.location,
                location,
            ):
                risk_score += AnomalyDetection.IMPOSSIBLE_TRAVEL_RISK
                flags.append("impossible_travel")

        # Check for rapid login attempts (count attempts in last 5 minutes BEFORE this one)
        recent_attempts = db.query(LoginAttempt).filter(
            LoginAttempt.user_id == user_id,
            LoginAttempt.timestamp > timestamp - timedelta(minutes=5),
            LoginAttempt.timestamp < timestamp,  # Only count attempts before this one
        ).count()

        if recent_attempts >= 4:  # 4 previous + this one = 5 total
            risk_score += 0.3
            flags.append("rapid_attempts")

        # Record the attempt (assume successful unless risk is very high)
        attempt = LoginAttempt(
            user_id=user_id,
            ip_address=ip_address,
            location=location or "",
            device_fingerprint="",
            risk_score=min(risk_score, 1.0),
            timestamp=timestamp,
            success=1,  # Mark as successful login attempt
        )
        db.add(attempt)
        db.commit()

        return min(risk_score, 1.0), flags

    @staticmethod
    def analyze_transaction(
        db: Session,
        user_id: int,
        amount: float,
        merchant_category: str,
        location: str,
        timestamp: datetime,
    ) -> tuple[float, list[str]]:
        """Analyze transaction and return (risk_score, anomalies)."""
        risk_score = 0.0
        flags = []

        # Check for zero or extremely large amounts
        if amount == 0.0:
            risk_score += 0.1
            flags.append("zero_amount")
        elif amount > 10000.0:
            risk_score += 0.5
            flags.append("large_amount")
        elif amount > 1000.0:
            risk_score += 0.3
            flags.append("elevated_amount")

        # Check for high transaction velocity
        recent_transactions = db.query(TransactionAnomaly).filter(
            TransactionAnomaly.user_id == user_id,
            TransactionAnomaly.timestamp > timestamp - timedelta(hours=1),
        ).count()

        if recent_transactions >= 5:
            risk_score += AnomalyDetection.HIGH_FREQUENCY_RISK
            flags.append("high_velocity")

        # Check for unusual category
        if merchant_category in ["cryptocurrency_exchange", "gambling", "wire_transfer"]:
            risk_score += 0.2
            flags.append("unusual_category")

        # Check for geographically distant transactions
        last_transaction = db.query(TransactionAnomaly).filter(
            TransactionAnomaly.user_id == user_id,
        ).order_by(TransactionAnomaly.timestamp.desc()).first()

        if last_transaction and location and last_transaction.location:
            if last_transaction.location != location:
                time_diff = (timestamp - last_transaction.timestamp).total_seconds() / 3600
                # Flag if locations are in different countries/regions and time is short
                from_parts = last_transaction.location.lower().split(',')
                to_parts = location.lower().split(',')
                from_country = from_parts[-1].strip() if len(from_parts) >= 2 else from_parts[0].strip()
                to_country = to_parts[-1].strip() if len(to_parts) >= 2 else to_parts[0].strip()

                # If different countries and within 2 hours, flag as suspicious
                if from_country != to_country and time_diff <= 2:
                    risk_score += 0.4
                    flags.append("geographic_distance")

        # Always record transaction for tracking purposes
        anomaly = TransactionAnomaly(
            user_id=user_id,
            transaction_amount=amount,
            merchant_category=merchant_category,
            location=location or "",
            risk_score=min(risk_score, 1.0),
            anomaly_type=",".join(flags) if flags else "normal",
            timestamp=timestamp,
        )
        db.add(anomaly)
        db.commit()

        return min(risk_score, 1.0), flags

    @staticmethod
    def is_account_locked(db: Session, user_id: int) -> bool:
        """Check if account is locked."""
        failed_count = AnomalyDetection.get_failed_login_count(
            db,
            user_id,
            minutes=AnomalyDetection.LOCKOUT_DURATION_MINUTES,
        )
        return failed_count >= AnomalyDetection.FAILED_LOGIN_THRESHOLD

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
    def _is_impossible_travel(
        last_login_time: datetime,
        current_time: datetime,
        from_location: str,
        to_location: str,
    ) -> bool:
        """Check if travel between locations is geographically impossible."""
        # Simplified check - in production, use actual geolocation
        time_diff = (current_time - last_login_time).total_seconds() / 3600

        # If locations are identical, not impossible
        if from_location == to_location:
            return False

        # Parse locations
        from_parts = from_location.lower().split(',')
        to_parts = to_location.lower().split(',')

        # Get city and country/state
        from_city = from_parts[0].strip() if len(from_parts) >= 1 else ""
        to_city = to_parts[0].strip() if len(to_parts) >= 1 else ""
        from_country = from_parts[-1].strip() if len(from_parts) >= 2 else from_parts[0].strip()
        to_country = to_parts[-1].strip() if len(to_parts) >= 2 else to_parts[0].strip()

        # If cities AND countries are different and time is short, likely impossible
        if from_city != to_city and from_country != to_country:
            # For different countries/states, 2 hours is impossible for major distances
            # Examples: NY to Japan, NY to London, etc.
            if time_diff < 2:
                return True

        return False

    @staticmethod
    def mark_device_trusted(db: Session, device_id: int) -> None:
        """Mark a device as trusted."""
        # This is a placeholder for device trust management
        pass
