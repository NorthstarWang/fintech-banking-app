"""Control Repository - Data access layer for control management"""

from typing import Any
from uuid import UUID

from ..models.control_models import (
    Control,
    ControlException,
    ControlFramework,
    ControlGap,
    ControlMapping,
    ControlMetrics,
    ControlTest,
)


class ControlRepository:
    def __init__(self):
        self._controls: dict[UUID, Control] = {}
        self._tests: dict[UUID, ControlTest] = {}
        self._exceptions: dict[UUID, ControlException] = {}
        self._gaps: dict[UUID, ControlGap] = {}
        self._frameworks: dict[UUID, ControlFramework] = {}
        self._mappings: dict[UUID, ControlMapping] = {}
        self._metrics: dict[UUID, ControlMetrics] = {}

    async def save_control(self, control: Control) -> Control:
        self._controls[control.control_id] = control
        return control

    async def find_control_by_id(self, control_id: UUID) -> Control | None:
        return self._controls.get(control_id)

    async def find_control_by_code(self, control_code: str) -> Control | None:
        for control in self._controls.values():
            if control.control_code == control_code:
                return control
        return None

    async def find_all_controls(self) -> list[Control]:
        return list(self._controls.values())

    async def update_control(self, control: Control) -> Control:
        self._controls[control.control_id] = control
        return control

    async def save_test(self, test: ControlTest) -> ControlTest:
        self._tests[test.test_id] = test
        return test

    async def find_tests_by_control(self, control_id: UUID) -> list[ControlTest]:
        return sorted(
            [t for t in self._tests.values() if t.control_id == control_id],
            key=lambda x: x.test_date,
            reverse=True
        )

    async def find_all_tests(self) -> list[ControlTest]:
        return list(self._tests.values())

    async def save_exception(self, exception: ControlException) -> ControlException:
        self._exceptions[exception.exception_id] = exception
        return exception

    async def find_exception_by_id(self, exception_id: UUID) -> ControlException | None:
        return self._exceptions.get(exception_id)

    async def find_exceptions_by_control(self, control_id: UUID) -> list[ControlException]:
        return [e for e in self._exceptions.values() if e.control_id == control_id]

    async def find_all_exceptions(self) -> list[ControlException]:
        return list(self._exceptions.values())

    async def save_gap(self, gap: ControlGap) -> ControlGap:
        self._gaps[gap.gap_id] = gap
        return gap

    async def find_gap_by_id(self, gap_id: UUID) -> ControlGap | None:
        return self._gaps.get(gap_id)

    async def find_all_gaps(self) -> list[ControlGap]:
        return list(self._gaps.values())

    async def save_framework(self, framework: ControlFramework) -> ControlFramework:
        self._frameworks[framework.framework_id] = framework
        return framework

    async def find_framework_by_id(self, framework_id: UUID) -> ControlFramework | None:
        return self._frameworks.get(framework_id)

    async def find_all_frameworks(self) -> list[ControlFramework]:
        return list(self._frameworks.values())

    async def save_mapping(self, mapping: ControlMapping) -> ControlMapping:
        self._mappings[mapping.mapping_id] = mapping
        return mapping

    async def find_mappings_by_control(self, control_id: UUID) -> list[ControlMapping]:
        return [m for m in self._mappings.values() if m.control_id == control_id]

    async def find_mappings_by_framework(self, framework_id: UUID) -> list[ControlMapping]:
        return [m for m in self._mappings.values() if m.framework_id == framework_id]

    async def save_metrics(self, metrics: ControlMetrics) -> ControlMetrics:
        self._metrics[metrics.metrics_id] = metrics
        return metrics

    async def get_statistics(self) -> dict[str, Any]:
        return {
            "total_controls": len(self._controls),
            "total_tests": len(self._tests),
            "total_exceptions": len(self._exceptions),
            "total_gaps": len(self._gaps)
        }


control_repository = ControlRepository()
