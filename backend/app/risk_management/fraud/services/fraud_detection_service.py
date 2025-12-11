"""Fraud Detection Service - Real-time fraud detection engine"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from ..models.fraud_alert_models import FraudType, FraudAlertSeverity, FraudIndicator


class FraudDetectionService:
    def __init__(self):
        self._thresholds = {
            "high_amount": 10000.0,
            "velocity_count": 5,
            "velocity_window_minutes": 60,
            "geo_distance_km": 500,
            "geo_time_minutes": 30,
        }

    async def analyze_transaction(self, transaction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        indicators = []
        fraud_score = 0.0

        # Amount analysis
        if transaction.get("amount", 0) > self._thresholds["high_amount"]:
            indicators.append(FraudIndicator(
                indicator_type="amount",
                indicator_name="High Transaction Amount",
                description=f"Transaction amount {transaction.get('amount')} exceeds threshold",
                weight=1.5,
                score=25.0
            ))
            fraud_score += 25.0

        # Velocity check
        recent_count = context.get("recent_transaction_count", 0)
        if recent_count > self._thresholds["velocity_count"]:
            indicators.append(FraudIndicator(
                indicator_type="velocity",
                indicator_name="High Transaction Velocity",
                description=f"{recent_count} transactions in short time window",
                weight=2.0,
                score=30.0
            ))
            fraud_score += 30.0

        # New device check
        if context.get("is_new_device", False):
            indicators.append(FraudIndicator(
                indicator_type="device",
                indicator_name="New Device",
                description="Transaction from unrecognized device",
                weight=1.0,
                score=15.0
            ))
            fraud_score += 15.0

        # Geographic anomaly
        if context.get("geo_anomaly", False):
            indicators.append(FraudIndicator(
                indicator_type="geographic",
                indicator_name="Geographic Anomaly",
                description="Impossible travel detected",
                weight=2.5,
                score=35.0
            ))
            fraud_score += 35.0

        # Time anomaly
        if context.get("unusual_time", False):
            indicators.append(FraudIndicator(
                indicator_type="time",
                indicator_name="Unusual Time",
                description="Transaction at unusual time for customer",
                weight=0.5,
                score=10.0
            ))
            fraud_score += 10.0

        fraud_score = min(fraud_score, 100.0)
        severity = self._score_to_severity(fraud_score)
        fraud_type = self._determine_fraud_type(indicators)

        return {
            "fraud_score": fraud_score,
            "severity": severity,
            "fraud_type": fraud_type,
            "indicators": indicators,
            "should_alert": fraud_score >= 50.0,
            "should_block": fraud_score >= 80.0
        }

    def _score_to_severity(self, score: float) -> FraudAlertSeverity:
        if score >= 80:
            return FraudAlertSeverity.CRITICAL
        elif score >= 60:
            return FraudAlertSeverity.HIGH
        elif score >= 40:
            return FraudAlertSeverity.MEDIUM
        return FraudAlertSeverity.LOW

    def _determine_fraud_type(self, indicators: List[FraudIndicator]) -> FraudType:
        indicator_types = {i.indicator_type for i in indicators}
        if "geographic" in indicator_types and "device" in indicator_types:
            return FraudType.ACCOUNT_TAKEOVER
        if "velocity" in indicator_types:
            return FraudType.CARD_NOT_PRESENT
        return FraudType.CARD_NOT_PRESENT

    async def check_velocity(self, customer_id: str, time_window_minutes: int = 60) -> Dict[str, Any]:
        # In production, would query actual transaction history
        return {"count": 0, "total_amount": 0.0, "is_anomaly": False}

    async def check_geo_anomaly(self, customer_id: str, current_location: Dict, current_time: datetime) -> Dict[str, Any]:
        return {"is_anomaly": False, "distance_km": 0, "time_diff_minutes": 0}


fraud_detection_service = FraudDetectionService()
