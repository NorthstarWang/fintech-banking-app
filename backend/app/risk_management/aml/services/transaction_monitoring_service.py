"""
Transaction Monitoring Service

Real-time and batch transaction monitoring for AML detection.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import asyncio

from ..models.alert_models import AlertType, AlertSeverity, AlertCreateRequest, AlertTrigger
from ..models.transaction_pattern_models import (
    PatternType, PatternSeverity, DetectedPattern, PatternRule,
    PatternAnalysisRequest, PatternAnalysisResult, StructuringPattern,
    VelocityPattern, TransactionProfileDeviation
)


class TransactionMonitoringService:
    """Service for real-time and batch transaction monitoring"""

    def __init__(self):
        self._rules: Dict[UUID, PatternRule] = {}
        self._detection_results: Dict[UUID, PatternAnalysisResult] = {}
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """Initialize default monitoring rules"""
        default_rules = [
            PatternRule(
                rule_code="STRUCT_001",
                rule_name="Cash Structuring Detection",
                pattern_type=PatternType.STRUCTURING,
                description="Detect transactions just below reporting threshold",
                logic_expression="amount >= threshold * 0.8 AND amount < threshold",
                parameters={"threshold": 10000, "time_window_days": 1},
                thresholds={"count_threshold": 3, "total_threshold": 25000},
                base_severity=PatternSeverity.HIGH,
                is_active=True,
                effective_from=datetime.utcnow(),
                created_by="system"
            ),
            PatternRule(
                rule_code="VEL_001",
                rule_name="Transaction Velocity Spike",
                pattern_type=PatternType.VELOCITY_SPIKE,
                description="Detect unusual increase in transaction frequency",
                logic_expression="current_velocity > baseline_velocity * threshold_multiplier",
                parameters={"baseline_period_days": 90, "current_period_days": 7},
                thresholds={"threshold_multiplier": 3.0, "min_transactions": 5},
                base_severity=PatternSeverity.MEDIUM,
                is_active=True,
                effective_from=datetime.utcnow(),
                created_by="system"
            ),
            PatternRule(
                rule_code="RAP_001",
                rule_name="Rapid Movement of Funds",
                pattern_type=PatternType.RAPID_MOVEMENT,
                description="Detect rapid in-and-out movement of funds",
                logic_expression="time_diff < threshold_hours AND amount_ratio > ratio_threshold",
                parameters={"threshold_hours": 24},
                thresholds={"ratio_threshold": 0.9, "min_amount": 5000},
                base_severity=PatternSeverity.HIGH,
                is_active=True,
                effective_from=datetime.utcnow(),
                created_by="system"
            ),
            PatternRule(
                rule_code="GEO_001",
                rule_name="High Risk Geography",
                pattern_type=PatternType.GEOGRAPHIC_ANOMALY,
                description="Detect transactions involving high risk jurisdictions",
                logic_expression="country IN high_risk_countries",
                parameters={"high_risk_countries": ["AF", "IR", "KP", "SY", "YE"]},
                thresholds={"alert_threshold": 1},
                base_severity=PatternSeverity.HIGH,
                is_active=True,
                effective_from=datetime.utcnow(),
                created_by="system"
            ),
            PatternRule(
                rule_code="DOR_001",
                rule_name="Dormant Account Activation",
                pattern_type=PatternType.DORMANT_ACTIVATION,
                description="Detect activity on previously dormant accounts",
                logic_expression="days_since_last_activity > dormancy_threshold",
                parameters={"dormancy_threshold_days": 180},
                thresholds={"min_amount": 1000},
                base_severity=PatternSeverity.MEDIUM,
                is_active=True,
                effective_from=datetime.utcnow(),
                created_by="system"
            ),
            PatternRule(
                rule_code="AMT_001",
                rule_name="Large Cash Transaction",
                pattern_type=PatternType.AMOUNT_ANOMALY,
                description="Detect large cash transactions",
                logic_expression="amount >= threshold AND transaction_type = 'cash'",
                parameters={},
                thresholds={"threshold": 10000},
                base_severity=PatternSeverity.LOW,
                is_active=True,
                effective_from=datetime.utcnow(),
                created_by="system"
            ),
        ]

        for rule in default_rules:
            self._rules[rule.rule_id] = rule

    async def monitor_transaction(
        self, transaction: Dict[str, Any], customer_profile: Dict[str, Any]
    ) -> List[DetectedPattern]:
        """Monitor a single transaction in real-time"""
        detected_patterns = []

        for rule in self._rules.values():
            if not rule.is_active:
                continue

            pattern = await self._evaluate_rule(rule, transaction, customer_profile)
            if pattern:
                detected_patterns.append(pattern)

        return detected_patterns

    async def _evaluate_rule(
        self, rule: PatternRule, transaction: Dict[str, Any], customer_profile: Dict[str, Any]
    ) -> Optional[DetectedPattern]:
        """Evaluate a single rule against a transaction"""

        if rule.pattern_type == PatternType.STRUCTURING:
            return await self._check_structuring(rule, transaction, customer_profile)
        elif rule.pattern_type == PatternType.VELOCITY_SPIKE:
            return await self._check_velocity(rule, transaction, customer_profile)
        elif rule.pattern_type == PatternType.RAPID_MOVEMENT:
            return await self._check_rapid_movement(rule, transaction, customer_profile)
        elif rule.pattern_type == PatternType.GEOGRAPHIC_ANOMALY:
            return await self._check_geographic(rule, transaction, customer_profile)
        elif rule.pattern_type == PatternType.DORMANT_ACTIVATION:
            return await self._check_dormant_activation(rule, transaction, customer_profile)
        elif rule.pattern_type == PatternType.AMOUNT_ANOMALY:
            return await self._check_amount_anomaly(rule, transaction, customer_profile)

        return None

    async def _check_structuring(
        self, rule: PatternRule, transaction: Dict[str, Any], customer_profile: Dict[str, Any]
    ) -> Optional[DetectedPattern]:
        """Check for structuring patterns"""
        threshold = rule.parameters.get("threshold", 10000)
        amount = transaction.get("amount", 0)

        if amount >= threshold * 0.8 and amount < threshold:
            # Check recent transaction history for similar patterns
            recent_similar = customer_profile.get("recent_below_threshold_count", 0)

            if recent_similar >= rule.thresholds.get("count_threshold", 3) - 1:
                return DetectedPattern(
                    pattern_type=PatternType.STRUCTURING,
                    severity=PatternSeverity.HIGH,
                    primary_entity_id=transaction.get("customer_id", ""),
                    primary_entity_type="customer",
                    primary_entity_name=transaction.get("customer_name", "Unknown"),
                    transaction_ids=[transaction.get("transaction_id", "")],
                    transaction_count=1,
                    total_amount=amount,
                    detection_rule_id=str(rule.rule_id),
                    detection_rule_name=rule.rule_name,
                    confidence_score=0.85,
                    pattern_details={
                        "amount": amount,
                        "threshold": threshold,
                        "below_threshold_ratio": amount / threshold,
                        "recent_similar_count": recent_similar + 1
                    }
                )
        return None

    async def _check_velocity(
        self, rule: PatternRule, transaction: Dict[str, Any], customer_profile: Dict[str, Any]
    ) -> Optional[DetectedPattern]:
        """Check for velocity anomalies"""
        current_velocity = customer_profile.get("current_transaction_velocity", 0)
        baseline_velocity = customer_profile.get("baseline_transaction_velocity", 1)
        multiplier = rule.thresholds.get("threshold_multiplier", 3.0)

        if baseline_velocity > 0 and current_velocity > baseline_velocity * multiplier:
            return DetectedPattern(
                pattern_type=PatternType.VELOCITY_SPIKE,
                severity=PatternSeverity.MEDIUM,
                primary_entity_id=transaction.get("customer_id", ""),
                primary_entity_type="customer",
                primary_entity_name=transaction.get("customer_name", "Unknown"),
                transaction_ids=[transaction.get("transaction_id", "")],
                transaction_count=1,
                total_amount=transaction.get("amount", 0),
                detection_rule_id=str(rule.rule_id),
                detection_rule_name=rule.rule_name,
                confidence_score=0.75,
                pattern_details={
                    "current_velocity": current_velocity,
                    "baseline_velocity": baseline_velocity,
                    "velocity_ratio": current_velocity / baseline_velocity
                }
            )
        return None

    async def _check_rapid_movement(
        self, rule: PatternRule, transaction: Dict[str, Any], customer_profile: Dict[str, Any]
    ) -> Optional[DetectedPattern]:
        """Check for rapid movement of funds"""
        last_large_credit = customer_profile.get("last_large_credit")
        min_amount = rule.thresholds.get("min_amount", 5000)
        threshold_hours = rule.parameters.get("threshold_hours", 24)

        if (
            last_large_credit and
            transaction.get("type") == "debit" and
            transaction.get("amount", 0) >= min_amount
        ):
            time_diff = (datetime.utcnow() - last_large_credit.get("timestamp", datetime.utcnow())).total_seconds() / 3600

            if time_diff < threshold_hours:
                ratio = transaction.get("amount", 0) / last_large_credit.get("amount", 1)
                if ratio > rule.thresholds.get("ratio_threshold", 0.9):
                    return DetectedPattern(
                        pattern_type=PatternType.RAPID_MOVEMENT,
                        severity=PatternSeverity.HIGH,
                        primary_entity_id=transaction.get("customer_id", ""),
                        primary_entity_type="customer",
                        primary_entity_name=transaction.get("customer_name", "Unknown"),
                        transaction_ids=[transaction.get("transaction_id", "")],
                        transaction_count=1,
                        total_amount=transaction.get("amount", 0),
                        detection_rule_id=str(rule.rule_id),
                        detection_rule_name=rule.rule_name,
                        confidence_score=0.80,
                        pattern_details={
                            "time_diff_hours": time_diff,
                            "amount_ratio": ratio,
                            "credit_amount": last_large_credit.get("amount"),
                            "debit_amount": transaction.get("amount")
                        }
                    )
        return None

    async def _check_geographic(
        self, rule: PatternRule, transaction: Dict[str, Any], customer_profile: Dict[str, Any]
    ) -> Optional[DetectedPattern]:
        """Check for high-risk geographic involvement"""
        high_risk_countries = rule.parameters.get("high_risk_countries", [])
        country = transaction.get("counterparty_country", "")

        if country in high_risk_countries:
            return DetectedPattern(
                pattern_type=PatternType.GEOGRAPHIC_ANOMALY,
                severity=PatternSeverity.HIGH,
                primary_entity_id=transaction.get("customer_id", ""),
                primary_entity_type="customer",
                primary_entity_name=transaction.get("customer_name", "Unknown"),
                transaction_ids=[transaction.get("transaction_id", "")],
                transaction_count=1,
                total_amount=transaction.get("amount", 0),
                detection_rule_id=str(rule.rule_id),
                detection_rule_name=rule.rule_name,
                confidence_score=0.90,
                pattern_details={
                    "country": country,
                    "high_risk_countries": high_risk_countries
                }
            )
        return None

    async def _check_dormant_activation(
        self, rule: PatternRule, transaction: Dict[str, Any], customer_profile: Dict[str, Any]
    ) -> Optional[DetectedPattern]:
        """Check for dormant account activation"""
        days_since_activity = customer_profile.get("days_since_last_activity", 0)
        threshold_days = rule.parameters.get("dormancy_threshold_days", 180)
        min_amount = rule.thresholds.get("min_amount", 1000)

        if days_since_activity > threshold_days and transaction.get("amount", 0) >= min_amount:
            return DetectedPattern(
                pattern_type=PatternType.DORMANT_ACTIVATION,
                severity=PatternSeverity.MEDIUM,
                primary_entity_id=transaction.get("customer_id", ""),
                primary_entity_type="customer",
                primary_entity_name=transaction.get("customer_name", "Unknown"),
                transaction_ids=[transaction.get("transaction_id", "")],
                transaction_count=1,
                total_amount=transaction.get("amount", 0),
                detection_rule_id=str(rule.rule_id),
                detection_rule_name=rule.rule_name,
                confidence_score=0.70,
                pattern_details={
                    "days_dormant": days_since_activity,
                    "dormancy_threshold": threshold_days
                }
            )
        return None

    async def _check_amount_anomaly(
        self, rule: PatternRule, transaction: Dict[str, Any], customer_profile: Dict[str, Any]
    ) -> Optional[DetectedPattern]:
        """Check for large transaction amounts"""
        threshold = rule.thresholds.get("threshold", 10000)
        amount = transaction.get("amount", 0)

        if amount >= threshold:
            return DetectedPattern(
                pattern_type=PatternType.AMOUNT_ANOMALY,
                severity=PatternSeverity.LOW,
                primary_entity_id=transaction.get("customer_id", ""),
                primary_entity_type="customer",
                primary_entity_name=transaction.get("customer_name", "Unknown"),
                transaction_ids=[transaction.get("transaction_id", "")],
                transaction_count=1,
                total_amount=amount,
                detection_rule_id=str(rule.rule_id),
                detection_rule_name=rule.rule_name,
                confidence_score=1.0,
                pattern_details={
                    "amount": amount,
                    "threshold": threshold
                }
            )
        return None

    async def run_batch_analysis(
        self, request: PatternAnalysisRequest
    ) -> PatternAnalysisResult:
        """Run batch pattern analysis"""
        result = PatternAnalysisResult(
            request_id=request.request_id,
            analysis_date=datetime.utcnow()
        )

        # Simulate batch processing
        result.customers_analyzed = len(request.customer_ids or [])
        result.transactions_analyzed = len(request.transaction_ids or [])
        result.rules_executed = len(self._rules)

        self._detection_results[result.result_id] = result
        return result

    async def get_rules(self) -> List[PatternRule]:
        """Get all monitoring rules"""
        return list(self._rules.values())

    async def get_rule(self, rule_id: UUID) -> Optional[PatternRule]:
        """Get a specific rule"""
        return self._rules.get(rule_id)

    async def create_rule(self, rule: PatternRule) -> PatternRule:
        """Create a new monitoring rule"""
        self._rules[rule.rule_id] = rule
        return rule

    async def update_rule(self, rule_id: UUID, updates: Dict[str, Any]) -> Optional[PatternRule]:
        """Update an existing rule"""
        rule = self._rules.get(rule_id)
        if not rule:
            return None

        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)

        rule.last_modified_at = datetime.utcnow()
        rule.version += 1
        return rule

    async def toggle_rule(self, rule_id: UUID, is_active: bool) -> Optional[PatternRule]:
        """Enable or disable a rule"""
        rule = self._rules.get(rule_id)
        if not rule:
            return None

        rule.is_active = is_active
        rule.last_modified_at = datetime.utcnow()
        return rule


# Global service instance
transaction_monitoring_service = TransactionMonitoringService()
