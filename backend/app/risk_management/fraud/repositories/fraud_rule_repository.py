"""Fraud Rule Repository - Data access layer for fraud detection rules"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from ..models.fraud_rule_models import (
    FraudRule, RuleSet, RuleType, RuleStatus, RuleAction
)


class FraudRuleRepository:
    def __init__(self):
        self._rules: Dict[UUID, FraudRule] = {}
        self._rulesets: Dict[UUID, RuleSet] = {}
        self._rule_code_index: Dict[str, UUID] = {}
        self._rule_type_index: Dict[RuleType, List[UUID]] = {}

    async def save_rule(self, rule: FraudRule) -> FraudRule:
        self._rules[rule.rule_id] = rule
        self._rule_code_index[rule.rule_code] = rule.rule_id
        if rule.rule_type not in self._rule_type_index:
            self._rule_type_index[rule.rule_type] = []
        if rule.rule_id not in self._rule_type_index[rule.rule_type]:
            self._rule_type_index[rule.rule_type].append(rule.rule_id)
        return rule

    async def find_rule_by_id(self, rule_id: UUID) -> Optional[FraudRule]:
        return self._rules.get(rule_id)

    async def find_rule_by_code(self, rule_code: str) -> Optional[FraudRule]:
        rule_id = self._rule_code_index.get(rule_code)
        if rule_id:
            return self._rules.get(rule_id)
        return None

    async def find_rules_by_type(self, rule_type: RuleType) -> List[FraudRule]:
        rule_ids = self._rule_type_index.get(rule_type, [])
        return [self._rules[rid] for rid in rule_ids if rid in self._rules]

    async def find_active_rules(self) -> List[FraudRule]:
        return [r for r in self._rules.values() if r.status == RuleStatus.ACTIVE]

    async def find_rules_by_action(self, action: RuleAction) -> List[FraudRule]:
        return [r for r in self._rules.values() if r.action == action]

    async def find_rules_by_severity(self, severity: str) -> List[FraudRule]:
        return [r for r in self._rules.values() if r.alert_severity == severity]

    async def update_rule(self, rule: FraudRule) -> FraudRule:
        rule.updated_at = datetime.utcnow()
        rule.version += 1
        self._rules[rule.rule_id] = rule
        return rule

    async def delete_rule(self, rule_id: UUID) -> bool:
        if rule_id in self._rules:
            rule = self._rules[rule_id]
            del self._rules[rule_id]
            if rule.rule_code in self._rule_code_index:
                del self._rule_code_index[rule.rule_code]
            return True
        return False

    async def save_ruleset(self, ruleset: RuleSet) -> RuleSet:
        self._rulesets[ruleset.ruleset_id] = ruleset
        return ruleset

    async def find_ruleset_by_id(self, ruleset_id: UUID) -> Optional[RuleSet]:
        return self._rulesets.get(ruleset_id)

    async def find_active_rulesets(self) -> List[RuleSet]:
        return [rs for rs in self._rulesets.values() if rs.is_active]

    async def find_rulesets_by_channel(self, channel: str) -> List[RuleSet]:
        return [
            rs for rs in self._rulesets.values()
            if channel in rs.applicable_channels
        ]

    async def get_all_rules(self, limit: int = 500, offset: int = 0) -> List[FraudRule]:
        rules = sorted(self._rules.values(), key=lambda x: x.created_at, reverse=True)
        return rules[offset:offset + limit]

    async def get_all_rulesets(self, limit: int = 100, offset: int = 0) -> List[RuleSet]:
        rulesets = sorted(self._rulesets.values(), key=lambda x: x.created_at, reverse=True)
        return rulesets[offset:offset + limit]

    async def count_rules(self) -> int:
        return len(self._rules)

    async def count_rulesets(self) -> int:
        return len(self._rulesets)

    async def get_rule_statistics(self) -> Dict[str, Any]:
        active_count = len([r for r in self._rules.values() if r.status == RuleStatus.ACTIVE])
        by_type = {}
        for rule in self._rules.values():
            type_key = rule.rule_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
        return {
            "total_rules": len(self._rules),
            "active_rules": active_count,
            "inactive_rules": len(self._rules) - active_count,
            "by_type": by_type
        }

    async def increment_hit_count(self, rule_id: UUID) -> Optional[FraudRule]:
        rule = self._rules.get(rule_id)
        if rule:
            rule.hit_count += 1
            rule.last_hit_at = datetime.utcnow()
        return rule


fraud_rule_repository = FraudRuleRepository()
