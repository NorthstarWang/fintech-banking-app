"""GDPR Service - Business logic for GDPR compliance"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID
from ..models.gdpr_models import (
    ProcessingActivity, ConsentRecord, DataSubjectRequest, DataBreach,
    DataProtectionImpactAssessment, ThirdPartyDataTransfer, GDPRComplianceReport,
    LawfulBasis, DataSubjectRight, IncidentSeverity
)
from ..repositories.gdpr_repository import gdpr_repository


class GDPRService:
    def __init__(self):
        self.repository = gdpr_repository
        self._request_counter = 0

    async def register_processing_activity(
        self, activity_name: str, description: str, purpose: str, lawful_basis: LawfulBasis,
        data_categories: List[str], data_subjects: List[str], recipients: List[str],
        retention_period: str, technical_measures: List[str], organizational_measures: List[str],
        controller: str, **kwargs
    ) -> ProcessingActivity:
        activity = ProcessingActivity(
            activity_name=activity_name, description=description, purpose=purpose,
            lawful_basis=lawful_basis, data_categories=data_categories, data_subjects=data_subjects,
            recipients=recipients, retention_period=retention_period, technical_measures=technical_measures,
            organizational_measures=organizational_measures, controller=controller, **kwargs
        )
        await self.repository.save_activity(activity)
        return activity

    async def record_consent(
        self, data_subject_id: str, purpose: str, processing_activity_id: UUID,
        consent_method: str, consent_text: str, proof_location: str
    ) -> ConsentRecord:
        consent = ConsentRecord(
            data_subject_id=data_subject_id, purpose=purpose, processing_activity_id=processing_activity_id,
            consent_given=True, consent_date=datetime.utcnow(), consent_method=consent_method,
            consent_text=consent_text, proof_location=proof_location
        )
        await self.repository.save_consent(consent)
        return consent

    async def withdraw_consent(self, consent_id: UUID, withdrawal_method: str) -> Optional[ConsentRecord]:
        consent = await self.repository.find_consent_by_id(consent_id)
        if consent:
            consent.consent_given = False
            consent.withdrawal_date = datetime.utcnow()
            consent.withdrawal_method = withdrawal_method
            consent.is_active = False
        return consent

    async def create_dsar(
        self, data_subject_id: str, data_subject_email: str, right_type: DataSubjectRight,
        request_details: str
    ) -> DataSubjectRequest:
        self._request_counter += 1
        dsar = DataSubjectRequest(
            request_reference=f"DSAR-{date.today().strftime('%Y%m')}-{self._request_counter:05d}",
            data_subject_id=data_subject_id, data_subject_email=data_subject_email,
            right_type=right_type, request_details=request_details, received_date=datetime.utcnow(),
            due_date=date.today() + timedelta(days=30)
        )
        await self.repository.save_dsar(dsar)
        return dsar

    async def complete_dsar(
        self, request_id: UUID, response_details: str, closed_by: str
    ) -> Optional[DataSubjectRequest]:
        dsar = await self.repository.find_dsar_by_id(request_id)
        if dsar:
            dsar.response_details = response_details
            dsar.response_date = datetime.utcnow()
            dsar.completed_date = datetime.utcnow()
            dsar.closed_by = closed_by
            dsar.status = "completed"
        return dsar

    async def report_breach(
        self, breach_type: str, severity: IncidentSeverity, description: str,
        data_categories_affected: List[str], number_of_records: int, number_of_subjects: int,
        systems_affected: List[str], containment_measures: List[str]
    ) -> DataBreach:
        self._request_counter += 1
        now = datetime.utcnow()
        breach = DataBreach(
            breach_reference=f"BREACH-{date.today().strftime('%Y%m')}-{self._request_counter:05d}",
            discovery_date=now, occurrence_date=now, breach_type=breach_type, severity=severity,
            description=description, data_categories_affected=data_categories_affected,
            special_categories_affected=[], number_of_records=number_of_records,
            number_of_subjects=number_of_subjects, systems_affected=systems_affected,
            containment_measures=containment_measures, risk_to_subjects="under_assessment"
        )
        if severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]:
            breach.notification_required = True
        await self.repository.save_breach(breach)
        return breach

    async def create_dpia(
        self, project_name: str, description: str, necessity_assessment: str,
        proportionality_assessment: str, risks_identified: List[Dict[str, Any]],
        mitigation_measures: List[Dict[str, Any]]
    ) -> DataProtectionImpactAssessment:
        self._request_counter += 1
        dpia = DataProtectionImpactAssessment(
            dpia_reference=f"DPIA-{date.today().strftime('%Y%m')}-{self._request_counter:05d}",
            project_name=project_name, description=description,
            necessity_assessment=necessity_assessment, proportionality_assessment=proportionality_assessment,
            risks_identified=risks_identified, mitigation_measures=mitigation_measures, residual_risks=[]
        )
        await self.repository.save_dpia(dpia)
        return dpia

    async def register_transfer(
        self, data_exporter: str, data_importer: str, recipient_country: str,
        transfer_mechanism: str, data_categories: List[str], purposes: List[str],
        safeguards: List[str], valid_from: date
    ) -> ThirdPartyDataTransfer:
        transfer = ThirdPartyDataTransfer(
            data_exporter=data_exporter, data_importer=data_importer, recipient_country=recipient_country,
            is_adequate_country=False, transfer_mechanism=transfer_mechanism, data_categories=data_categories,
            purposes=purposes, safeguards=safeguards, supplementary_measures=[], valid_from=valid_from
        )
        await self.repository.save_transfer(transfer)
        return transfer

    async def generate_compliance_report(
        self, reporting_period: str, generated_by: str
    ) -> GDPRComplianceReport:
        activities = await self.repository.find_all_activities()
        consents = await self.repository.find_all_consents()
        dsars = await self.repository.find_all_dsars()
        breaches = await self.repository.find_all_breaches()

        report = GDPRComplianceReport(
            report_date=date.today(), reporting_period=reporting_period,
            total_processing_activities=len(activities),
            activities_with_lawful_basis=len([a for a in activities if a.lawful_basis]),
            total_consent_records=len(consents), active_consents=len([c for c in consents if c.is_active]),
            withdrawn_consents=len([c for c in consents if not c.is_active]),
            dsar_received=len(dsars), dsar_completed=len([d for d in dsars if d.status == "completed"]),
            dsar_avg_response_days=0, breaches_reported=len(breaches),
            breaches_notified_dpa=len([b for b in breaches if b.dpa_notified]),
            dpias_completed=0, third_country_transfers=0, training_completed=0,
            audit_findings=0, open_remediation_items=0, compliance_score=85.0, generated_by=generated_by
        )
        await self.repository.save_report(report)
        return report

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


gdpr_service = GDPRService()
