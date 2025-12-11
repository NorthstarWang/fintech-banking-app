"""KRI Service - Business logic for Key Risk Indicators"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from ..models.kri_models import (
    KeyRiskIndicator, KRIMeasurement, KRIThresholdBreach, KRITarget,
    KRITrendAnalysis, KRIDashboard, KRIReport,
    KRIType, KRICategory, ThresholdStatus, KRITrend
)
from ..repositories.kri_repository import kri_repository


class KRIService:
    def __init__(self):
        self.repository = kri_repository
        self._kri_counter = 0

    def _generate_kri_code(self, category: KRICategory) -> str:
        self._kri_counter += 1
        prefix = category.value[:3].upper()
        return f"KRI-{prefix}-{self._kri_counter:04d}"

    def _determine_threshold_status(
        self,
        value: Decimal,
        kri: KeyRiskIndicator
    ) -> ThresholdStatus:
        if kri.higher_is_worse:
            if kri.red_threshold_min and value >= kri.red_threshold_min:
                return ThresholdStatus.RED
            if kri.amber_threshold_min and value >= kri.amber_threshold_min:
                return ThresholdStatus.AMBER
            return ThresholdStatus.GREEN
        else:
            if kri.red_threshold_max and value <= kri.red_threshold_max:
                return ThresholdStatus.RED
            if kri.amber_threshold_max and value <= kri.amber_threshold_max:
                return ThresholdStatus.AMBER
            return ThresholdStatus.GREEN

    def _determine_trend(
        self,
        current_value: Decimal,
        previous_value: Optional[Decimal],
        higher_is_worse: bool
    ) -> KRITrend:
        if previous_value is None:
            return KRITrend.STABLE

        if current_value == previous_value:
            return KRITrend.STABLE

        if higher_is_worse:
            if current_value > previous_value:
                return KRITrend.DETERIORATING
            return KRITrend.IMPROVING
        else:
            if current_value < previous_value:
                return KRITrend.DETERIORATING
            return KRITrend.IMPROVING

    async def create_kri(
        self,
        kri_name: str,
        description: str,
        kri_type: KRIType,
        category: KRICategory,
        business_unit: str,
        owner: str,
        measurement_unit: str,
        measurement_frequency: str,
        data_source: str,
        calculation_method: str,
        green_threshold_max: Optional[Decimal] = None,
        amber_threshold_min: Optional[Decimal] = None,
        amber_threshold_max: Optional[Decimal] = None,
        red_threshold_min: Optional[Decimal] = None,
        higher_is_worse: bool = True
    ) -> KeyRiskIndicator:
        kri = KeyRiskIndicator(
            kri_code=self._generate_kri_code(category),
            kri_name=kri_name,
            description=description,
            kri_type=kri_type,
            category=category,
            business_unit=business_unit,
            owner=owner,
            measurement_unit=measurement_unit,
            measurement_frequency=measurement_frequency,
            data_source=data_source,
            calculation_method=calculation_method,
            green_threshold_max=green_threshold_max,
            amber_threshold_min=amber_threshold_min,
            amber_threshold_max=amber_threshold_max,
            red_threshold_min=red_threshold_min,
            higher_is_worse=higher_is_worse
        )

        await self.repository.save_kri(kri)
        return kri

    async def get_kri(self, kri_id: UUID) -> Optional[KeyRiskIndicator]:
        return await self.repository.find_kri_by_id(kri_id)

    async def get_kri_by_code(self, kri_code: str) -> Optional[KeyRiskIndicator]:
        return await self.repository.find_kri_by_code(kri_code)

    async def list_kris(
        self,
        category: Optional[KRICategory] = None,
        business_unit: Optional[str] = None,
        is_active: bool = True
    ) -> List[KeyRiskIndicator]:
        kris = await self.repository.find_all_kris()

        if is_active:
            kris = [k for k in kris if k.is_active]
        if category:
            kris = [k for k in kris if k.category == category]
        if business_unit:
            kris = [k for k in kris if k.business_unit == business_unit]

        return kris

    async def record_measurement(
        self,
        kri_id: UUID,
        measurement_date: date,
        measurement_period: str,
        value: Decimal,
        recorded_by: str,
        notes: Optional[str] = None
    ) -> KRIMeasurement:
        kri = await self.repository.find_kri_by_id(kri_id)
        if not kri:
            raise ValueError(f"KRI {kri_id} not found")

        previous_measurements = await self.repository.find_measurements_by_kri(kri_id)
        previous_value = previous_measurements[-1].value if previous_measurements else None

        threshold_status = self._determine_threshold_status(value, kri)
        trend = self._determine_trend(value, previous_value, kri.higher_is_worse)

        variance = None
        variance_pct = None
        if previous_value:
            variance = value - previous_value
            if previous_value != 0:
                variance_pct = (variance / previous_value) * 100

        breach = threshold_status in [ThresholdStatus.AMBER, ThresholdStatus.RED]

        measurement = KRIMeasurement(
            kri_id=kri_id,
            measurement_date=measurement_date,
            measurement_period=measurement_period,
            value=value,
            previous_value=previous_value,
            threshold_status=threshold_status,
            trend=trend,
            variance_from_target=variance,
            variance_percentage=variance_pct,
            breach_occurred=breach,
            breach_type=threshold_status.value if breach else None,
            notes=notes,
            recorded_by=recorded_by
        )

        await self.repository.save_measurement(measurement)

        if breach:
            await self._record_breach(kri_id, measurement)

        return measurement

    async def _record_breach(
        self,
        kri_id: UUID,
        measurement: KRIMeasurement
    ) -> KRIThresholdBreach:
        kri = await self.repository.find_kri_by_id(kri_id)

        threshold = kri.amber_threshold_min if measurement.breach_type == "amber" else kri.red_threshold_min

        breach = KRIThresholdBreach(
            kri_id=kri_id,
            measurement_id=measurement.measurement_id,
            breach_date=measurement.measurement_date,
            breach_type=measurement.breach_type,
            breach_value=measurement.value,
            threshold_breached=threshold or Decimal("0")
        )

        await self.repository.save_breach(breach)
        return breach

    async def get_kri_measurements(
        self,
        kri_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[KRIMeasurement]:
        measurements = await self.repository.find_measurements_by_kri(kri_id)

        if start_date:
            measurements = [m for m in measurements if m.measurement_date >= start_date]
        if end_date:
            measurements = [m for m in measurements if m.measurement_date <= end_date]

        return measurements

    async def get_kri_breaches(
        self,
        kri_id: Optional[UUID] = None,
        status: str = "open"
    ) -> List[KRIThresholdBreach]:
        if kri_id:
            breaches = await self.repository.find_breaches_by_kri(kri_id)
        else:
            breaches = await self.repository.find_all_breaches()

        if status:
            breaches = [b for b in breaches if b.status == status]

        return breaches

    async def resolve_breach(
        self,
        breach_id: UUID,
        action_taken: str,
        resolution_notes: str
    ) -> Optional[KRIThresholdBreach]:
        breach = await self.repository.find_breach_by_id(breach_id)
        if not breach:
            return None

        breach.action_taken = action_taken
        breach.resolution_date = date.today()
        breach.resolution_notes = resolution_notes
        breach.status = "resolved"

        return breach

    async def set_target(
        self,
        kri_id: UUID,
        target_period: str,
        target_value: Decimal,
        target_type: str,
        effective_from: date,
        approved_by: str,
        rationale: Optional[str] = None
    ) -> KRITarget:
        target = KRITarget(
            kri_id=kri_id,
            target_period=target_period,
            target_value=target_value,
            target_type=target_type,
            effective_from=effective_from,
            approved_by=approved_by,
            approval_date=date.today(),
            rationale=rationale
        )

        await self.repository.save_target(target)
        return target

    async def analyze_trend(
        self,
        kri_id: UUID,
        period_start: date,
        period_end: date
    ) -> KRITrendAnalysis:
        measurements = await self.get_kri_measurements(kri_id, period_start, period_end)

        if not measurements:
            raise ValueError("No measurements found for analysis")

        values = [m.value for m in measurements]
        n = len(values)

        avg = sum(values) / n
        min_val = min(values)
        max_val = max(values)

        variance = sum((v - avg) ** 2 for v in values) / n
        std_dev = Decimal(str(variance ** Decimal("0.5")))

        green_count = len([m for m in measurements if m.threshold_status == ThresholdStatus.GREEN])
        amber_count = len([m for m in measurements if m.threshold_status == ThresholdStatus.AMBER])
        red_count = len([m for m in measurements if m.threshold_status == ThresholdStatus.RED])

        breach_count = len([m for m in measurements if m.breach_occurred])

        if n > 1:
            x_mean = (n - 1) / 2
            y_mean = avg
            numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            trend_coef = Decimal(str(numerator / denominator)) if denominator != 0 else Decimal("0")
        else:
            trend_coef = Decimal("0")

        if trend_coef > Decimal("0.1"):
            trend_dir = KRITrend.DETERIORATING
        elif trend_coef < Decimal("-0.1"):
            trend_dir = KRITrend.IMPROVING
        else:
            trend_dir = KRITrend.STABLE

        kri = await self.repository.find_kri_by_id(kri_id)
        if kri and not kri.higher_is_worse:
            if trend_dir == KRITrend.DETERIORATING:
                trend_dir = KRITrend.IMPROVING
            elif trend_dir == KRITrend.IMPROVING:
                trend_dir = KRITrend.DETERIORATING

        analysis = KRITrendAnalysis(
            kri_id=kri_id,
            analysis_date=date.today(),
            analysis_period=f"{period_start} to {period_end}",
            period_start=period_start,
            period_end=period_end,
            data_points=n,
            average_value=avg,
            min_value=min_val,
            max_value=max_val,
            standard_deviation=std_dev,
            trend_direction=trend_dir,
            trend_coefficient=trend_coef,
            green_percentage=Decimal(str(green_count / n * 100)),
            amber_percentage=Decimal(str(amber_count / n * 100)),
            red_percentage=Decimal(str(red_count / n * 100)),
            breach_count=breach_count,
            volatility=std_dev / avg if avg != 0 else Decimal("0")
        )

        await self.repository.save_trend_analysis(analysis)
        return analysis

    async def generate_dashboard(
        self,
        business_unit: Optional[str] = None
    ) -> KRIDashboard:
        kris = await self.list_kris(business_unit=business_unit)

        kri_summary = []
        green = amber = red = 0
        improving = stable = deteriorating = 0
        breaches = 0
        data_quality = 0

        for kri in kris:
            measurements = await self.repository.find_measurements_by_kri(kri.kri_id)
            if measurements:
                latest = measurements[-1]

                if latest.threshold_status == ThresholdStatus.GREEN:
                    green += 1
                elif latest.threshold_status == ThresholdStatus.AMBER:
                    amber += 1
                else:
                    red += 1

                if latest.trend == KRITrend.IMPROVING:
                    improving += 1
                elif latest.trend == KRITrend.STABLE:
                    stable += 1
                else:
                    deteriorating += 1

                if latest.breach_occurred:
                    breaches += 1

                if latest.data_quality_flag:
                    data_quality += 1

                kri_summary.append({
                    "kri_code": kri.kri_code,
                    "kri_name": kri.kri_name,
                    "value": str(latest.value),
                    "status": latest.threshold_status.value,
                    "trend": latest.trend.value
                })

        top_concerns = [s for s in kri_summary if s["status"] == "red"][:5]

        dashboard = KRIDashboard(
            dashboard_date=date.today(),
            business_unit=business_unit,
            total_kris=len(kris),
            active_kris=len(kris),
            green_count=green,
            amber_count=amber,
            red_count=red,
            breaches_this_period=breaches,
            improving_count=improving,
            stable_count=stable,
            deteriorating_count=deteriorating,
            data_quality_issues=data_quality,
            kri_summary=kri_summary,
            top_concerns=top_concerns
        )

        await self.repository.save_dashboard(dashboard)
        return dashboard

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


kri_service = KRIService()
