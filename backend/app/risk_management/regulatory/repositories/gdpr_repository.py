"""GDPR Repository - Data access for GDPR compliance"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.gdpr_models import (
    ProcessingActivity, DataSubjectConsent, DataSubjectAccessRequest,
    DataBreach, DataProtectionImpactAssessment, DataRetentionPolicy,
    CrossBorderTransfer, GDPRReport
)


class GDPRRepository:
    def __init__(self):
        self._activities: Dict[UUID, ProcessingActivity] = {}
        self._consents: Dict[UUID, DataSubjectConsent] = {}
        self._dsars: Dict[UUID, DataSubjectAccessRequest] = {}
        self._breaches: Dict[UUID, DataBreach] = {}
        self._dpias: Dict[UUID, DataProtectionImpactAssessment] = {}
        self._retention_policies: Dict[UUID, DataRetentionPolicy] = {}
        self._transfers: Dict[UUID, CrossBorderTransfer] = {}
        self._reports: Dict[UUID, GDPRReport] = {}

    async def save_activity(self, activity: ProcessingActivity) -> None:
        self._activities[activity.activity_id] = activity

    async def find_activity_by_id(self, activity_id: UUID) -> Optional[ProcessingActivity]:
        return self._activities.get(activity_id)

    async def find_all_activities(self) -> List[ProcessingActivity]:
        return list(self._activities.values())

    async def find_activities_by_purpose(self, purpose: str) -> List[ProcessingActivity]:
        return [a for a in self._activities.values() if purpose.lower() in a.processing_purpose.lower()]

    async def find_high_risk_activities(self) -> List[ProcessingActivity]:
        return [a for a in self._activities.values() if a.risk_level == "high"]

    async def save_consent(self, consent: DataSubjectConsent) -> None:
        self._consents[consent.consent_id] = consent

    async def find_consent_by_id(self, consent_id: UUID) -> Optional[DataSubjectConsent]:
        return self._consents.get(consent_id)

    async def find_all_consents(self) -> List[DataSubjectConsent]:
        return list(self._consents.values())

    async def find_consents_by_subject(self, subject_id: str) -> List[DataSubjectConsent]:
        return [c for c in self._consents.values() if c.data_subject_id == subject_id]

    async def find_active_consents(self) -> List[DataSubjectConsent]:
        return [c for c in self._consents.values() if c.is_active and not c.withdrawn]

    async def save_dsar(self, dsar: DataSubjectAccessRequest) -> None:
        self._dsars[dsar.dsar_id] = dsar

    async def find_dsar_by_id(self, dsar_id: UUID) -> Optional[DataSubjectAccessRequest]:
        return self._dsars.get(dsar_id)

    async def find_all_dsars(self) -> List[DataSubjectAccessRequest]:
        return list(self._dsars.values())

    async def find_dsars_by_status(self, status: str) -> List[DataSubjectAccessRequest]:
        return [d for d in self._dsars.values() if d.status.value == status]

    async def find_pending_dsars(self) -> List[DataSubjectAccessRequest]:
        return [d for d in self._dsars.values() if d.status.value in ["received", "in_progress"]]

    async def save_breach(self, breach: DataBreach) -> None:
        self._breaches[breach.breach_id] = breach

    async def find_breach_by_id(self, breach_id: UUID) -> Optional[DataBreach]:
        return self._breaches.get(breach_id)

    async def find_all_breaches(self) -> List[DataBreach]:
        return list(self._breaches.values())

    async def find_breaches_requiring_notification(self) -> List[DataBreach]:
        return [b for b in self._breaches.values() if b.authority_notification_required]

    async def find_open_breaches(self) -> List[DataBreach]:
        return [b for b in self._breaches.values() if b.status != "closed"]

    async def save_dpia(self, dpia: DataProtectionImpactAssessment) -> None:
        self._dpias[dpia.dpia_id] = dpia

    async def find_dpia_by_id(self, dpia_id: UUID) -> Optional[DataProtectionImpactAssessment]:
        return self._dpias.get(dpia_id)

    async def find_all_dpias(self) -> List[DataProtectionImpactAssessment]:
        return list(self._dpias.values())

    async def find_dpias_pending_review(self) -> List[DataProtectionImpactAssessment]:
        return [d for d in self._dpias.values() if d.status == "pending_review"]

    async def save_retention_policy(self, policy: DataRetentionPolicy) -> None:
        self._retention_policies[policy.policy_id] = policy

    async def find_retention_policy_by_id(self, policy_id: UUID) -> Optional[DataRetentionPolicy]:
        return self._retention_policies.get(policy_id)

    async def find_all_retention_policies(self) -> List[DataRetentionPolicy]:
        return list(self._retention_policies.values())

    async def save_transfer(self, transfer: CrossBorderTransfer) -> None:
        self._transfers[transfer.transfer_id] = transfer

    async def find_transfer_by_id(self, transfer_id: UUID) -> Optional[CrossBorderTransfer]:
        return self._transfers.get(transfer_id)

    async def find_all_transfers(self) -> List[CrossBorderTransfer]:
        return list(self._transfers.values())

    async def find_transfers_by_destination(self, country: str) -> List[CrossBorderTransfer]:
        return [t for t in self._transfers.values() if t.destination_country == country]

    async def save_report(self, report: GDPRReport) -> None:
        self._reports[report.report_id] = report

    async def find_report_by_id(self, report_id: UUID) -> Optional[GDPRReport]:
        return self._reports.get(report_id)

    async def find_all_reports(self) -> List[GDPRReport]:
        return list(self._reports.values())

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_activities": len(self._activities),
            "total_consents": len(self._consents),
            "active_consents": len([c for c in self._consents.values() if c.is_active]),
            "total_dsars": len(self._dsars),
            "pending_dsars": len([d for d in self._dsars.values() if d.status.value in ["received", "in_progress"]]),
            "total_breaches": len(self._breaches),
            "open_breaches": len([b for b in self._breaches.values() if b.status != "closed"]),
            "total_dpias": len(self._dpias),
            "total_transfers": len(self._transfers),
            "total_reports": len(self._reports),
        }


gdpr_repository = GDPRRepository()
