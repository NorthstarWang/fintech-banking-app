"""Loss Event Service - Business logic for operational loss tracking"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from ..models.loss_event_models import (
    LossEvent, LossRecovery, LossProvision, LossEventCausality,
    LossDistribution, OperationalLossCapital, LossEventReport,
    LossEventType, LossEventStatus, RecoveryType
)
from ..repositories.loss_event_repository import loss_event_repository


class LossEventService:
    def __init__(self):
        self.repository = loss_event_repository
        self._event_counter = 0

    def _generate_event_reference(self) -> str:
        self._event_counter += 1
        return f"LOSS-{date.today().strftime('%Y%m')}-{self._event_counter:05d}"

    async def create_loss_event(
        self,
        event_type: LossEventType,
        event_description: str,
        discovery_date: date,
        occurrence_date: date,
        accounting_date: date,
        business_line: str,
        business_unit: str,
        legal_entity: str,
        country: str,
        gross_loss: Decimal,
        reported_by: str,
        near_miss: bool = False,
        near_miss_amount: Optional[Decimal] = None,
        related_incident_id: Optional[UUID] = None
    ) -> LossEvent:
        event = LossEvent(
            event_reference=self._generate_event_reference(),
            event_type=event_type,
            event_description=event_description,
            discovery_date=discovery_date,
            occurrence_date=occurrence_date,
            accounting_date=accounting_date,
            business_line=business_line,
            business_unit=business_unit,
            legal_entity=legal_entity,
            country=country,
            gross_loss=gross_loss,
            net_loss=gross_loss,
            reported_by=reported_by,
            near_miss=near_miss,
            near_miss_amount=near_miss_amount,
            related_incident_id=related_incident_id
        )

        await self.repository.save_event(event)
        return event

    async def get_event(self, event_id: UUID) -> Optional[LossEvent]:
        return await self.repository.find_event_by_id(event_id)

    async def get_event_by_reference(self, reference: str) -> Optional[LossEvent]:
        return await self.repository.find_event_by_reference(reference)

    async def list_events(
        self,
        event_type: Optional[LossEventType] = None,
        status: Optional[LossEventStatus] = None,
        business_line: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_loss: Optional[Decimal] = None
    ) -> List[LossEvent]:
        events = await self.repository.find_all_events()

        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if status:
            events = [e for e in events if e.status == status]
        if business_line:
            events = [e for e in events if e.business_line == business_line]
        if start_date:
            events = [e for e in events if e.occurrence_date >= start_date]
        if end_date:
            events = [e for e in events if e.occurrence_date <= end_date]
        if min_loss:
            events = [e for e in events if e.gross_loss >= min_loss]

        return events

    async def update_event_status(
        self,
        event_id: UUID,
        new_status: LossEventStatus,
        updated_by: str
    ) -> Optional[LossEvent]:
        event = await self.repository.find_event_by_id(event_id)
        if not event:
            return None

        event.status = new_status

        if new_status == LossEventStatus.VALIDATED:
            event.validated_by = updated_by
            event.validation_date = datetime.utcnow()
        elif new_status == LossEventStatus.APPROVED:
            event.approved_by = updated_by
            event.approval_date = datetime.utcnow()

        await self.repository.update_event(event)
        return event

    async def add_recovery(
        self,
        event_id: UUID,
        recovery_type: RecoveryType,
        recovery_amount: Decimal,
        recovery_date: date,
        source: str,
        reference_number: Optional[str] = None
    ) -> LossRecovery:
        recovery = LossRecovery(
            event_id=event_id,
            recovery_type=recovery_type,
            recovery_amount=recovery_amount,
            recovery_date=recovery_date,
            source=source,
            reference_number=reference_number,
            status="received",
            received_date=recovery_date
        )

        await self.repository.save_recovery(recovery)

        event = await self.repository.find_event_by_id(event_id)
        if event:
            event.recoveries += recovery_amount
            event.net_loss = event.gross_loss - event.recoveries
            await self.repository.update_event(event)

        return recovery

    async def get_event_recoveries(self, event_id: UUID) -> List[LossRecovery]:
        return await self.repository.find_recoveries_by_event(event_id)

    async def add_provision(
        self,
        event_id: UUID,
        provision_type: str,
        provision_amount: Decimal,
        provision_date: date,
        approved_by: str
    ) -> LossProvision:
        provision = LossProvision(
            event_id=event_id,
            provision_type=provision_type,
            provision_amount=provision_amount,
            provision_date=provision_date,
            approved_by=approved_by
        )

        await self.repository.save_provision(provision)
        return provision

    async def release_provision(
        self,
        provision_id: UUID,
        release_amount: Decimal
    ) -> Optional[LossProvision]:
        provision = await self.repository.find_provision_by_id(provision_id)
        if not provision:
            return None

        provision.release_date = date.today()
        provision.release_amount = release_amount
        provision.status = "released"

        return provision

    async def add_causality(
        self,
        event_id: UUID,
        cause_category: str,
        cause_subcategory: str,
        cause_description: str,
        contributing_factor: bool = False,
        control_failure: bool = False,
        failed_control_id: Optional[UUID] = None
    ) -> LossEventCausality:
        causality = LossEventCausality(
            event_id=event_id,
            cause_category=cause_category,
            cause_subcategory=cause_subcategory,
            cause_description=cause_description,
            contributing_factor=contributing_factor,
            control_failure=control_failure,
            failed_control_id=failed_control_id
        )

        await self.repository.save_causality(causality)
        return causality

    async def calculate_loss_distribution(
        self,
        event_type: LossEventType,
        period_start: date,
        period_end: date
    ) -> LossDistribution:
        events = await self.list_events(
            event_type=event_type,
            start_date=period_start,
            end_date=period_end
        )

        if not events:
            return LossDistribution(
                analysis_date=date.today(),
                event_type=event_type,
                frequency=0,
                mean_loss=Decimal("0"),
                median_loss=Decimal("0"),
                percentile_95=Decimal("0"),
                percentile_99=Decimal("0"),
                max_loss=Decimal("0"),
                standard_deviation=Decimal("0"),
                total_loss=Decimal("0"),
                period_start=period_start,
                period_end=period_end
            )

        losses = sorted([e.net_loss for e in events])
        n = len(losses)
        total = sum(losses)
        mean = total / n
        median = losses[n // 2]

        variance = sum((l - mean) ** 2 for l in losses) / n
        std_dev = Decimal(str(variance ** Decimal("0.5")))

        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)

        distribution = LossDistribution(
            analysis_date=date.today(),
            event_type=event_type,
            frequency=n,
            mean_loss=mean,
            median_loss=median,
            percentile_95=losses[min(p95_idx, n - 1)],
            percentile_99=losses[min(p99_idx, n - 1)],
            max_loss=max(losses),
            standard_deviation=std_dev,
            total_loss=total,
            period_start=period_start,
            period_end=period_end
        )

        await self.repository.save_distribution(distribution)
        return distribution

    async def calculate_operational_capital(
        self,
        calculation_date: date,
        methodology: str,
        business_indicator: Decimal,
        confidence_level: Decimal = Decimal("0.999"),
        time_horizon: int = 1
    ) -> OperationalLossCapital:
        events = await self.repository.find_all_events()

        losses = [e.net_loss for e in events if e.status == LossEventStatus.APPROVED]
        loss_component = sum(losses) if losses else Decimal("0")

        ilm = Decimal("1.0")
        if losses:
            avg_loss = loss_component / len(losses)
            if avg_loss > business_indicator * Decimal("0.01"):
                ilm = Decimal("1.5")

        if methodology == "BIA":
            regulatory_capital = business_indicator * Decimal("0.15")
        elif methodology == "TSA":
            regulatory_capital = business_indicator * Decimal("0.12")
        else:
            regulatory_capital = business_indicator * Decimal("0.12") * ilm

        economic_capital = regulatory_capital * Decimal("1.2")

        capital = OperationalLossCapital(
            calculation_date=calculation_date,
            methodology=methodology,
            business_indicator=business_indicator,
            loss_component=loss_component,
            internal_loss_multiplier=ilm,
            regulatory_capital=regulatory_capital,
            economic_capital=economic_capital,
            confidence_level=confidence_level,
            time_horizon=time_horizon
        )

        await self.repository.save_capital(capital)
        return capital

    async def generate_report(
        self,
        report_period: str,
        period_start: date,
        period_end: date,
        generated_by: str
    ) -> LossEventReport:
        events = await self.list_events(start_date=period_start, end_date=period_end)

        by_type = {}
        by_status = {}
        total_gross = Decimal("0")
        total_recoveries = Decimal("0")
        total_net = Decimal("0")
        near_miss_count = 0
        near_miss_total = Decimal("0")
        business_breakdown = {}
        largest_event = None
        largest_loss = Decimal("0")

        for event in events:
            by_type[event.event_type.value] = by_type.get(event.event_type.value, 0) + 1
            by_status[event.status.value] = by_status.get(event.status.value, 0) + 1
            total_gross += event.gross_loss
            total_recoveries += event.recoveries
            total_net += event.net_loss

            if event.near_miss:
                near_miss_count += 1
                if event.near_miss_amount:
                    near_miss_total += event.near_miss_amount

            business_breakdown[event.business_line] = (
                business_breakdown.get(event.business_line, Decimal("0")) + event.net_loss
            )

            if event.net_loss > largest_loss:
                largest_loss = event.net_loss
                largest_event = {
                    "reference": event.event_reference,
                    "type": event.event_type.value,
                    "loss": str(event.net_loss)
                }

        avg_loss = total_net / len(events) if events else Decimal("0")

        report = LossEventReport(
            report_date=date.today(),
            report_period=report_period,
            period_start=period_start,
            period_end=period_end,
            total_events=len(events),
            events_by_type=by_type,
            events_by_status=by_status,
            total_gross_loss=total_gross,
            total_recoveries=total_recoveries,
            total_net_loss=total_net,
            total_near_misses=near_miss_count,
            near_miss_amount=near_miss_total,
            average_loss=avg_loss,
            largest_loss_event=largest_event or {},
            business_line_breakdown={k: str(v) for k, v in business_breakdown.items()},
            generated_by=generated_by
        )

        await self.repository.save_report(report)
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


loss_event_service = LossEventService()
