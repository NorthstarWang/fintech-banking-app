"""Data Quality Service"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from ..models.data_quality_models import (
    DataQualityRule, DataQualityCheck, DataQualityScore, DataQualityIssue,
    DataQualityReport, DataQualityThreshold, QualityDimension, RuleSeverity
)
from ..repositories.data_quality_repository import data_quality_repository


class DataQualityService:
    def __init__(self):
        self.repository = data_quality_repository
        self._rule_counter = 0
        self._issue_counter = 0

    async def create_rule(
        self, rule_name: str, rule_description: str, dimension: QualityDimension,
        severity: RuleSeverity, data_domain: str, table_name: str,
        rule_expression: str, owner: str, column_name: Optional[str] = None,
        threshold_percentage: Decimal = Decimal("100")
    ) -> DataQualityRule:
        self._rule_counter += 1
        rule = DataQualityRule(
            rule_code=f"DQR-{self._rule_counter:05d}", rule_name=rule_name,
            rule_description=rule_description, dimension=dimension, severity=severity,
            data_domain=data_domain, table_name=table_name, column_name=column_name,
            rule_expression=rule_expression, threshold_percentage=threshold_percentage,
            owner=owner
        )
        await self.repository.save_rule(rule)
        return rule

    async def execute_check(
        self, rule_id: UUID, total_records: int, passed_records: int,
        execution_time_ms: int = 0, error_samples: List[Dict[str, Any]] = None
    ) -> DataQualityCheck:
        failed_records = total_records - passed_records
        pass_percentage = Decimal(str(passed_records / total_records * 100)) if total_records > 0 else Decimal("0")

        check = DataQualityCheck(
            rule_id=rule_id, total_records=total_records, passed_records=passed_records,
            failed_records=failed_records, pass_percentage=pass_percentage,
            execution_time_ms=execution_time_ms, error_samples=error_samples or []
        )
        await self.repository.save_check(check)

        rule = await self.repository.find_rule_by_id(rule_id)
        if rule and pass_percentage < rule.threshold_percentage:
            await self._create_issue(rule_id, check.check_id, failed_records, pass_percentage)

        return check

    async def _create_issue(
        self, rule_id: UUID, check_id: UUID, affected_records: int, pass_percentage: Decimal
    ) -> DataQualityIssue:
        self._issue_counter += 1
        issue = DataQualityIssue(
            rule_id=rule_id, check_id=check_id,
            issue_reference=f"DQI-{date.today().strftime('%Y%m')}-{self._issue_counter:05d}",
            issue_type="threshold_breach",
            description=f"Data quality check failed with {pass_percentage}% pass rate",
            affected_records=affected_records, impact_assessment="Under review"
        )
        await self.repository.save_issue(issue)
        return issue

    async def calculate_score(
        self, data_domain: str, table_name: str, calculated_by: str = "system"
    ) -> DataQualityScore:
        checks = await self.repository.find_checks_by_table(table_name)
        rules = await self.repository.find_rules_by_table(table_name)

        dimension_scores = {}
        for dim in QualityDimension:
            dim_checks = [c for c in checks for r in rules if r.dimension == dim and c.rule_id == r.rule_id]
            if dim_checks:
                avg_score = sum(c.pass_percentage for c in dim_checks) / len(dim_checks)
                dimension_scores[dim.value] = avg_score

        overall = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else Decimal("0")

        score = DataQualityScore(
            score_date=date.today(), data_domain=data_domain, table_name=table_name,
            overall_score=overall, dimension_scores=dimension_scores,
            rules_evaluated=len(rules), calculated_by=calculated_by
        )
        await self.repository.save_score(score)
        return score

    async def resolve_issue(self, issue_id: UUID, resolution: str, resolved_by: str) -> Optional[DataQualityIssue]:
        issue = await self.repository.find_issue_by_id(issue_id)
        if issue:
            issue.status = "resolved"
            issue.remediation_plan = resolution
            issue.assigned_to = resolved_by
        return issue

    async def generate_report(
        self, report_period: str, generated_by: str, domains_covered: List[str]
    ) -> DataQualityReport:
        checks = await self.repository.find_all_checks()
        issues = await self.repository.find_all_issues()

        passed = len([c for c in checks if c.pass_percentage >= Decimal("95")])

        report = DataQualityReport(
            report_date=date.today(), report_period=report_period, generated_by=generated_by,
            domains_covered=domains_covered, rules_executed=len(checks),
            checks_passed=passed, checks_failed=len(checks) - passed,
            issues_identified=len([i for i in issues if i.status == "open"]),
            issues_resolved=len([i for i in issues if i.status == "resolved"])
        )
        await self.repository.save_report(report)
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


data_quality_service = DataQualityService()
