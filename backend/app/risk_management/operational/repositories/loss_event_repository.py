"""Loss Event Repository - Data access layer for operational losses"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.loss_event_models import (
    LossEvent, LossRecovery, LossProvision, LossEventCausality,
    LossDistribution, OperationalLossCapital, LossEventReport
)


class LossEventRepository:
    def __init__(self):
        self._events: Dict[UUID, LossEvent] = {}
        self._recoveries: Dict[UUID, LossRecovery] = {}
        self._provisions: Dict[UUID, LossProvision] = {}
        self._causalities: Dict[UUID, LossEventCausality] = {}
        self._distributions: Dict[UUID, LossDistribution] = {}
        self._capitals: Dict[UUID, OperationalLossCapital] = {}
        self._reports: Dict[UUID, LossEventReport] = {}

    async def save_event(self, event: LossEvent) -> LossEvent:
        self._events[event.event_id] = event
        return event

    async def find_event_by_id(self, event_id: UUID) -> Optional[LossEvent]:
        return self._events.get(event_id)

    async def find_event_by_reference(self, reference: str) -> Optional[LossEvent]:
        for event in self._events.values():
            if event.event_reference == reference:
                return event
        return None

    async def find_all_events(self) -> List[LossEvent]:
        return list(self._events.values())

    async def update_event(self, event: LossEvent) -> LossEvent:
        self._events[event.event_id] = event
        return event

    async def save_recovery(self, recovery: LossRecovery) -> LossRecovery:
        self._recoveries[recovery.recovery_id] = recovery
        return recovery

    async def find_recoveries_by_event(self, event_id: UUID) -> List[LossRecovery]:
        return [r for r in self._recoveries.values() if r.event_id == event_id]

    async def save_provision(self, provision: LossProvision) -> LossProvision:
        self._provisions[provision.provision_id] = provision
        return provision

    async def find_provision_by_id(self, provision_id: UUID) -> Optional[LossProvision]:
        return self._provisions.get(provision_id)

    async def find_provisions_by_event(self, event_id: UUID) -> List[LossProvision]:
        return [p for p in self._provisions.values() if p.event_id == event_id]

    async def save_causality(self, causality: LossEventCausality) -> LossEventCausality:
        self._causalities[causality.causality_id] = causality
        return causality

    async def find_causalities_by_event(self, event_id: UUID) -> List[LossEventCausality]:
        return [c for c in self._causalities.values() if c.event_id == event_id]

    async def save_distribution(self, distribution: LossDistribution) -> LossDistribution:
        self._distributions[distribution.distribution_id] = distribution
        return distribution

    async def save_capital(self, capital: OperationalLossCapital) -> OperationalLossCapital:
        self._capitals[capital.capital_id] = capital
        return capital

    async def save_report(self, report: LossEventReport) -> LossEventReport:
        self._reports[report.report_id] = report
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        from decimal import Decimal
        total_gross = sum(e.gross_loss for e in self._events.values())
        total_net = sum(e.net_loss for e in self._events.values())
        return {
            "total_events": len(self._events),
            "total_gross_loss": str(total_gross),
            "total_net_loss": str(total_net)
        }


loss_event_repository = LossEventRepository()
