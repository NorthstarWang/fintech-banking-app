"""Consumer Protection Repository - Data access for consumer protection compliance"""

from typing import Any
from uuid import UUID

from ..models.consumer_protection_models import (
    ComplaintStatus,
    ConsumerComplaint,
    ConsumerProtectionReport,
    FairLendingAnalysis,
    RESPADisclosure,
    ServicememberProtection,
    TILADisclosure,
    UDAPReview,
)


class ConsumerProtectionRepository:
    def __init__(self):
        self._complaints: dict[UUID, ConsumerComplaint] = {}
        self._fair_lending: dict[UUID, FairLendingAnalysis] = {}
        self._tila_disclosures: dict[UUID, TILADisclosure] = {}
        self._respa_disclosures: dict[UUID, RESPADisclosure] = {}
        self._udap_reviews: dict[UUID, UDAPReview] = {}
        self._servicemember: dict[UUID, ServicememberProtection] = {}
        self._reports: dict[UUID, ConsumerProtectionReport] = {}

    async def save_complaint(self, complaint: ConsumerComplaint) -> None:
        self._complaints[complaint.complaint_id] = complaint

    async def find_complaint_by_id(self, complaint_id: UUID) -> ConsumerComplaint | None:
        return self._complaints.get(complaint_id)

    async def find_all_complaints(self) -> list[ConsumerComplaint]:
        return list(self._complaints.values())

    async def find_complaints_by_status(self, status: ComplaintStatus) -> list[ConsumerComplaint]:
        return [c for c in self._complaints.values() if c.status == status]

    async def find_open_complaints(self) -> list[ConsumerComplaint]:
        return [c for c in self._complaints.values() if c.status in [ComplaintStatus.OPEN, ComplaintStatus.IN_PROGRESS, ComplaintStatus.ESCALATED]]

    async def find_regulatory_complaints(self) -> list[ConsumerComplaint]:
        return [c for c in self._complaints.values() if c.regulatory_complaint]

    async def find_complaints_by_customer(self, customer_id: str) -> list[ConsumerComplaint]:
        return [c for c in self._complaints.values() if c.customer_id == customer_id]

    async def save_fair_lending(self, analysis: FairLendingAnalysis) -> None:
        self._fair_lending[analysis.analysis_id] = analysis

    async def find_fair_lending_by_id(self, analysis_id: UUID) -> FairLendingAnalysis | None:
        return self._fair_lending.get(analysis_id)

    async def find_all_fair_lending(self) -> list[FairLendingAnalysis]:
        return list(self._fair_lending.values())

    async def find_fair_lending_with_findings(self) -> list[FairLendingAnalysis]:
        return [f for f in self._fair_lending.values() if f.statistical_significance]

    async def find_fair_lending_by_protected_class(self, protected_class: str) -> list[FairLendingAnalysis]:
        return [f for f in self._fair_lending.values() if f.protected_class.value == protected_class]

    async def save_tila(self, disclosure: TILADisclosure) -> None:
        self._tila_disclosures[disclosure.disclosure_id] = disclosure

    async def find_tila_by_id(self, disclosure_id: UUID) -> TILADisclosure | None:
        return self._tila_disclosures.get(disclosure_id)

    async def find_all_tila(self) -> list[TILADisclosure]:
        return list(self._tila_disclosures.values())

    async def find_tila_by_loan(self, loan_id: str) -> list[TILADisclosure]:
        return [t for t in self._tila_disclosures.values() if t.loan_id == loan_id]

    async def find_tila_by_customer(self, customer_id: str) -> list[TILADisclosure]:
        return [t for t in self._tila_disclosures.values() if t.customer_id == customer_id]

    async def save_respa(self, disclosure: RESPADisclosure) -> None:
        self._respa_disclosures[disclosure.disclosure_id] = disclosure

    async def find_respa_by_id(self, disclosure_id: UUID) -> RESPADisclosure | None:
        return self._respa_disclosures.get(disclosure_id)

    async def find_all_respa(self) -> list[RESPADisclosure]:
        return list(self._respa_disclosures.values())

    async def find_respa_by_loan(self, loan_id: str) -> list[RESPADisclosure]:
        return [r for r in self._respa_disclosures.values() if r.loan_id == loan_id]

    async def save_udap(self, review: UDAPReview) -> None:
        self._udap_reviews[review.review_id] = review

    async def find_udap_by_id(self, review_id: UUID) -> UDAPReview | None:
        return self._udap_reviews.get(review_id)

    async def find_all_udap(self) -> list[UDAPReview]:
        return list(self._udap_reviews.values())

    async def find_udap_requiring_remediation(self) -> list[UDAPReview]:
        return [u for u in self._udap_reviews.values() if u.remediation_required]

    async def find_high_risk_udap(self) -> list[UDAPReview]:
        return [u for u in self._udap_reviews.values() if u.risk_rating == "high"]

    async def save_servicemember(self, protection: ServicememberProtection) -> None:
        self._servicemember[protection.protection_id] = protection

    async def find_servicemember_by_id(self, protection_id: UUID) -> ServicememberProtection | None:
        return self._servicemember.get(protection_id)

    async def find_all_servicemember(self) -> list[ServicememberProtection]:
        return list(self._servicemember.values())

    async def find_servicemember_by_customer(self, customer_id: str) -> list[ServicememberProtection]:
        return [s for s in self._servicemember.values() if s.customer_id == customer_id]

    async def find_active_servicemember_protections(self) -> list[ServicememberProtection]:
        return [s for s in self._servicemember.values() if s.is_active]

    async def save_report(self, report: ConsumerProtectionReport) -> None:
        self._reports[report.report_id] = report

    async def find_report_by_id(self, report_id: UUID) -> ConsumerProtectionReport | None:
        return self._reports.get(report_id)

    async def find_all_reports(self) -> list[ConsumerProtectionReport]:
        return list(self._reports.values())

    async def get_statistics(self) -> dict[str, Any]:
        return {
            "total_complaints": len(self._complaints),
            "open_complaints": len([c for c in self._complaints.values() if c.status in [ComplaintStatus.OPEN, ComplaintStatus.IN_PROGRESS]]),
            "regulatory_complaints": len([c for c in self._complaints.values() if c.regulatory_complaint]),
            "total_fair_lending_analyses": len(self._fair_lending),
            "fair_lending_with_findings": len([f for f in self._fair_lending.values() if f.statistical_significance]),
            "total_tila_disclosures": len(self._tila_disclosures),
            "total_respa_disclosures": len(self._respa_disclosures),
            "total_udap_reviews": len(self._udap_reviews),
            "udap_requiring_remediation": len([u for u in self._udap_reviews.values() if u.remediation_required]),
            "servicemember_protections": len(self._servicemember),
            "total_reports": len(self._reports),
        }


consumer_protection_repository = ConsumerProtectionRepository()
