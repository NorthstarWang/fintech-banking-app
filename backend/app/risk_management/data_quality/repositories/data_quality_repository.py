"""Data Quality Repository"""

from typing import Any
from uuid import UUID

from ..models.data_quality_models import (
    DataQualityCheck,
    DataQualityDimension,
    DataQualityIssue,
    DataQualityReport,
    DataQualityRule,
    DataQualityScore,
    DataQualitySLA,
    DataQualityThreshold,
)


class DataQualityRepository:
    def __init__(self):
        self._rules: dict[UUID, DataQualityRule] = {}
        self._checks: dict[UUID, DataQualityCheck] = {}
        self._scores: dict[UUID, DataQualityScore] = {}
        self._issues: dict[UUID, DataQualityIssue] = {}
        self._reports: dict[UUID, DataQualityReport] = {}
        self._thresholds: dict[UUID, DataQualityThreshold] = {}
        self._dimensions: dict[UUID, DataQualityDimension] = {}
        self._slas: dict[UUID, DataQualitySLA] = {}

    async def save_rule(self, rule: DataQualityRule) -> DataQualityRule:
        self._rules[rule.rule_id] = rule
        return rule

    async def find_rule_by_id(self, rule_id: UUID) -> DataQualityRule | None:
        return self._rules.get(rule_id)

    async def find_all_rules(self) -> list[DataQualityRule]:
        return list(self._rules.values())

    async def find_rules_by_dimension(self, dimension: str) -> list[DataQualityRule]:
        return [r for r in self._rules.values() if r.dimension == dimension]

    async def delete_rule(self, rule_id: UUID) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    async def save_check(self, check: DataQualityCheck) -> DataQualityCheck:
        self._checks[check.check_id] = check
        return check

    async def find_check_by_id(self, check_id: UUID) -> DataQualityCheck | None:
        return self._checks.get(check_id)

    async def find_all_checks(self) -> list[DataQualityCheck]:
        return list(self._checks.values())

    async def find_checks_by_rule(self, rule_id: UUID) -> list[DataQualityCheck]:
        return [c for c in self._checks.values() if c.rule_id == rule_id]

    async def find_checks_by_status(self, status: str) -> list[DataQualityCheck]:
        return [c for c in self._checks.values() if c.status == status]

    async def save_score(self, score: DataQualityScore) -> DataQualityScore:
        self._scores[score.score_id] = score
        return score

    async def find_score_by_id(self, score_id: UUID) -> DataQualityScore | None:
        return self._scores.get(score_id)

    async def find_all_scores(self) -> list[DataQualityScore]:
        return list(self._scores.values())

    async def find_scores_by_dataset(self, dataset: str) -> list[DataQualityScore]:
        return [s for s in self._scores.values() if s.dataset_name == dataset]

    async def save_issue(self, issue: DataQualityIssue) -> DataQualityIssue:
        self._issues[issue.issue_id] = issue
        return issue

    async def find_issue_by_id(self, issue_id: UUID) -> DataQualityIssue | None:
        return self._issues.get(issue_id)

    async def find_all_issues(self) -> list[DataQualityIssue]:
        return list(self._issues.values())

    async def find_issues_by_severity(self, severity: str) -> list[DataQualityIssue]:
        return [i for i in self._issues.values() if i.severity == severity]

    async def find_open_issues(self) -> list[DataQualityIssue]:
        return [i for i in self._issues.values() if i.status == "open"]

    async def save_report(self, report: DataQualityReport) -> DataQualityReport:
        self._reports[report.report_id] = report
        return report

    async def find_report_by_id(self, report_id: UUID) -> DataQualityReport | None:
        return self._reports.get(report_id)

    async def find_all_reports(self) -> list[DataQualityReport]:
        return list(self._reports.values())

    async def save_threshold(self, threshold: DataQualityThreshold) -> DataQualityThreshold:
        self._thresholds[threshold.threshold_id] = threshold
        return threshold

    async def find_threshold_by_id(self, threshold_id: UUID) -> DataQualityThreshold | None:
        return self._thresholds.get(threshold_id)

    async def find_all_thresholds(self) -> list[DataQualityThreshold]:
        return list(self._thresholds.values())

    async def save_dimension(self, dimension: DataQualityDimension) -> DataQualityDimension:
        self._dimensions[dimension.dimension_id] = dimension
        return dimension

    async def find_dimension_by_id(self, dimension_id: UUID) -> DataQualityDimension | None:
        return self._dimensions.get(dimension_id)

    async def find_all_dimensions(self) -> list[DataQualityDimension]:
        return list(self._dimensions.values())

    async def save_sla(self, sla: DataQualitySLA) -> DataQualitySLA:
        self._slas[sla.sla_id] = sla
        return sla

    async def find_sla_by_id(self, sla_id: UUID) -> DataQualitySLA | None:
        return self._slas.get(sla_id)

    async def find_all_slas(self) -> list[DataQualitySLA]:
        return list(self._slas.values())

    async def get_statistics(self) -> dict[str, Any]:
        passed_checks = len([c for c in self._checks.values() if c.status == "passed"])
        total_checks = len(self._checks)
        return {
            "total_rules": len(self._rules),
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": total_checks - passed_checks,
            "total_scores": len(self._scores),
            "open_issues": len([i for i in self._issues.values() if i.status == "open"]),
            "total_reports": len(self._reports),
            "total_thresholds": len(self._thresholds),
            "total_dimensions": len(self._dimensions),
            "total_slas": len(self._slas),
        }


data_quality_repository = DataQualityRepository()
