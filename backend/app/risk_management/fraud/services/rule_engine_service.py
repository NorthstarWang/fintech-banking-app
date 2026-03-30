"""Rule Engine Service - Rule-based fraud detection"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from ..models.fraud_rule_models import (
    FraudRule,
    RuleAction,
    RuleCondition,
    RuleEvaluationResult,
    RuleSet,
    RuleStatus,
    RuleType,
)


class RuleEngineService:
    def __init__(self):
        self._rules: dict[UUID, FraudRule] = {}
        self._rulesets: dict[UUID, RuleSet] = {}
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        default_rules = [
            FraudRule(
                rule_code="AMT_HIGH_001",
                rule_name="High Amount Transaction",
                rule_type=RuleType.THRESHOLD,
                description="Alert on transactions above threshold",
                conditions=[RuleCondition(field="amount", operator=">=", value=10000, data_type="number")],
                logic_expression="amount >= 10000",
                action=RuleAction.ALERT,
                alert_severity="medium",
                created_by="system"
            ),
            FraudRule(
                rule_code="VEL_001",
                rule_name="High Velocity",
                rule_type=RuleType.VELOCITY,
                description="Alert on high transaction velocity",
                conditions=[RuleCondition(field="transaction_count_1h", operator=">=", value=5, data_type="number")],
                logic_expression="transaction_count_1h >= 5",
                action=RuleAction.ALERT,
                alert_severity="high",
                created_by="system"
            ),
            FraudRule(
                rule_code="NEW_DEV_001",
                rule_name="New Device Alert",
                rule_type=RuleType.DEVICE,
                description="Alert on first-time device",
                conditions=[RuleCondition(field="is_new_device", operator="==", value=True, data_type="boolean")],
                logic_expression="is_new_device == true",
                action=RuleAction.CHALLENGE,
                alert_severity="low",
                created_by="system"
            ),
        ]
        for rule in default_rules:
            self._rules[rule.rule_id] = rule

    async def create_rule(self, rule: FraudRule) -> FraudRule:
        self._rules[rule.rule_id] = rule
        return rule

    async def get_rule(self, rule_id: UUID) -> FraudRule | None:
        return self._rules.get(rule_id)

    async def update_rule(self, rule_id: UUID, updates: dict[str, Any]) -> FraudRule | None:
        rule = self._rules.get(rule_id)
        if rule:
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            rule.updated_at = datetime.now(UTC)
            rule.version += 1
        return rule

    async def toggle_rule(self, rule_id: UUID, is_active: bool) -> FraudRule | None:
        rule = self._rules.get(rule_id)
        if rule:
            rule.status = RuleStatus.ACTIVE if is_active else RuleStatus.INACTIVE
            rule.updated_at = datetime.now(UTC)
        return rule

    async def evaluate_transaction(self, transaction: dict[str, Any]) -> list[RuleEvaluationResult]:
        results = []
        for rule in self._rules.values():
            if rule.status != RuleStatus.ACTIVE:
                continue
            start_time = datetime.now(UTC)
            matched, conditions_matched = self._evaluate_rule(rule, transaction)
            result = RuleEvaluationResult(
                rule_id=rule.rule_id,
                rule_name=rule.rule_name,
                matched=matched,
                score=rule.score_weight if matched else 0.0,
                action=rule.action if matched else RuleAction.LOG,
                conditions_matched=conditions_matched,
                evaluation_time_ms=(datetime.now(UTC) - start_time).total_seconds() * 1000
            )
            results.append(result)
            if matched:
                rule.hit_count += 1
                rule.last_hit_at = datetime.now(UTC)
        return results

    def _evaluate_rule(self, rule: FraudRule, transaction: dict[str, Any]) -> tuple:
        conditions_matched = []
        for condition in rule.conditions:
            value = transaction.get(condition.field)
            if value is None:
                continue
            matched = self._evaluate_condition(condition, value)
            if matched:
                conditions_matched.append(condition.field)
        all_matched = len(conditions_matched) == len(rule.conditions)
        return all_matched, conditions_matched

    def _evaluate_condition(self, condition: RuleCondition, value: Any) -> bool:
        operators = {
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            "in": lambda a, b: a in b,
        }
        op_func = operators.get(condition.operator)
        if op_func:
            return op_func(value, condition.value)
        return False

    async def get_all_rules(self) -> list[FraudRule]:
        return list(self._rules.values())

    async def get_active_rules(self) -> list[FraudRule]:
        return [r for r in self._rules.values() if r.status == RuleStatus.ACTIVE]


rule_engine_service = RuleEngineService()
