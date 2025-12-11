"""Technology Risk Service - Business logic for IT risk management"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from ..models.technology_risk_models import (
    ITAsset, Vulnerability, PatchManagement, TechRiskAssessment,
    SecurityIncident, AccessReview, ChangeRisk, TechRiskMetrics,
    AssetType, AssetCriticality, VulnerabilitySeverity, PatchStatus, IncidentType
)
from ..repositories.technology_risk_repository import technology_risk_repository


class TechnologyRiskService:
    def __init__(self):
        self.repository = technology_risk_repository
        self._asset_counter = 0
        self._incident_counter = 0

    def _generate_asset_code(self, asset_type: AssetType) -> str:
        self._asset_counter += 1
        prefix = asset_type.value[:3].upper()
        return f"ASSET-{prefix}-{self._asset_counter:05d}"

    def _generate_incident_number(self) -> str:
        self._incident_counter += 1
        return f"SEC-{date.today().strftime('%Y%m')}-{self._incident_counter:05d}"

    async def register_asset(
        self,
        asset_name: str,
        asset_type: AssetType,
        description: str,
        criticality: AssetCriticality,
        owner: str,
        custodian: str,
        business_unit: str,
        location: str,
        environment: str,
        data_classification: str,
        ip_address: Optional[str] = None,
        hostname: Optional[str] = None,
        operating_system: Optional[str] = None,
        version: Optional[str] = None,
        vendor: Optional[str] = None,
        support_end_date: Optional[date] = None,
        pii_stored: bool = False,
        pci_scope: bool = False,
        sox_scope: bool = False
    ) -> ITAsset:
        asset = ITAsset(
            asset_code=self._generate_asset_code(asset_type),
            asset_name=asset_name,
            asset_type=asset_type,
            description=description,
            criticality=criticality,
            owner=owner,
            custodian=custodian,
            business_unit=business_unit,
            location=location,
            environment=environment,
            data_classification=data_classification,
            ip_address=ip_address,
            hostname=hostname,
            operating_system=operating_system,
            version=version,
            vendor=vendor,
            support_end_date=support_end_date,
            pii_stored=pii_stored,
            pci_scope=pci_scope,
            sox_scope=sox_scope
        )

        await self.repository.save_asset(asset)
        return asset

    async def get_asset(self, asset_id: UUID) -> Optional[ITAsset]:
        return await self.repository.find_asset_by_id(asset_id)

    async def get_asset_by_code(self, asset_code: str) -> Optional[ITAsset]:
        return await self.repository.find_asset_by_code(asset_code)

    async def list_assets(
        self,
        asset_type: Optional[AssetType] = None,
        criticality: Optional[AssetCriticality] = None,
        business_unit: Optional[str] = None,
        environment: Optional[str] = None
    ) -> List[ITAsset]:
        assets = await self.repository.find_all_assets()

        if asset_type:
            assets = [a for a in assets if a.asset_type == asset_type]
        if criticality:
            assets = [a for a in assets if a.criticality == criticality]
        if business_unit:
            assets = [a for a in assets if a.business_unit == business_unit]
        if environment:
            assets = [a for a in assets if a.environment == environment]

        return assets

    async def record_vulnerability(
        self,
        title: str,
        description: str,
        severity: VulnerabilitySeverity,
        affected_assets: List[UUID],
        affected_systems: List[str],
        discovery_source: str,
        remediation_steps: List[str],
        cve_id: Optional[str] = None,
        cvss_score: Optional[Decimal] = None,
        cvss_vector: Optional[str] = None,
        exploit_available: bool = False,
        actively_exploited: bool = False,
        patch_available: bool = False,
        patch_id: Optional[str] = None,
        workaround: Optional[str] = None
    ) -> Vulnerability:
        vuln = Vulnerability(
            cve_id=cve_id,
            title=title,
            description=description,
            severity=severity,
            cvss_score=cvss_score,
            cvss_vector=cvss_vector,
            affected_assets=affected_assets,
            affected_systems=affected_systems,
            discovery_date=date.today(),
            discovery_source=discovery_source,
            exploit_available=exploit_available,
            actively_exploited=actively_exploited,
            patch_available=patch_available,
            patch_id=patch_id,
            remediation_steps=remediation_steps,
            workaround=workaround
        )

        await self.repository.save_vulnerability(vuln)

        for asset_id in affected_assets:
            asset = await self.repository.find_asset_by_id(asset_id)
            if asset:
                asset.vulnerability_count += 1
                await self.repository.update_asset(asset)

        return vuln

    async def get_vulnerability(self, vuln_id: UUID) -> Optional[Vulnerability]:
        return await self.repository.find_vulnerability_by_id(vuln_id)

    async def list_vulnerabilities(
        self,
        severity: Optional[VulnerabilitySeverity] = None,
        status: str = "open",
        asset_id: Optional[UUID] = None
    ) -> List[Vulnerability]:
        vulns = await self.repository.find_all_vulnerabilities()

        if severity:
            vulns = [v for v in vulns if v.severity == severity]
        if status:
            vulns = [v for v in vulns if v.status == status]
        if asset_id:
            vulns = [v for v in vulns if asset_id in v.affected_assets]

        return vulns

    async def remediate_vulnerability(
        self,
        vuln_id: UUID,
        assigned_to: str,
        due_date: date
    ) -> Optional[Vulnerability]:
        vuln = await self.repository.find_vulnerability_by_id(vuln_id)
        if not vuln:
            return None

        vuln.assigned_to = assigned_to
        vuln.due_date = due_date
        vuln.status = "in_progress"

        return vuln

    async def close_vulnerability(
        self,
        vuln_id: UUID
    ) -> Optional[Vulnerability]:
        vuln = await self.repository.find_vulnerability_by_id(vuln_id)
        if not vuln:
            return None

        vuln.status = "closed"
        vuln.remediation_date = date.today()

        for asset_id in vuln.affected_assets:
            asset = await self.repository.find_asset_by_id(asset_id)
            if asset and asset.vulnerability_count > 0:
                asset.vulnerability_count -= 1
                await self.repository.update_asset(asset)

        return vuln

    async def accept_risk(
        self,
        vuln_id: UUID,
        reason: str,
        expiry: date
    ) -> Optional[Vulnerability]:
        vuln = await self.repository.find_vulnerability_by_id(vuln_id)
        if not vuln:
            return None

        vuln.risk_accepted = True
        vuln.acceptance_reason = reason
        vuln.acceptance_expiry = expiry
        vuln.status = "risk_accepted"

        return vuln

    async def create_patch(
        self,
        patch_code: str,
        patch_name: str,
        vendor: str,
        release_date: date,
        severity: str,
        affected_products: List[str],
        affected_assets: List[UUID],
        cve_addressed: List[str]
    ) -> PatchManagement:
        patch = PatchManagement(
            patch_code=patch_code,
            patch_name=patch_name,
            vendor=vendor,
            release_date=release_date,
            severity=severity,
            affected_products=affected_products,
            affected_assets=affected_assets,
            cve_addressed=cve_addressed
        )

        await self.repository.save_patch(patch)
        return patch

    async def schedule_patch(
        self,
        patch_id: UUID,
        scheduled_date: date,
        change_ticket: str
    ) -> Optional[PatchManagement]:
        patch = await self.repository.find_patch_by_id(patch_id)
        if not patch:
            return None

        patch.status = PatchStatus.SCHEDULED
        patch.scheduled_date = scheduled_date
        patch.change_ticket = change_ticket

        return patch

    async def apply_patch(
        self,
        patch_id: UUID,
        applied_by: str
    ) -> Optional[PatchManagement]:
        patch = await self.repository.find_patch_by_id(patch_id)
        if not patch:
            return None

        patch.status = PatchStatus.APPLIED
        patch.applied_date = date.today()
        patch.applied_by = applied_by

        return patch

    async def get_pending_patches(self) -> List[PatchManagement]:
        patches = await self.repository.find_all_patches()
        return [p for p in patches if p.status in [PatchStatus.PENDING, PatchStatus.SCHEDULED]]

    async def perform_risk_assessment(
        self,
        asset_id: UUID,
        assessment_type: str,
        assessor: str,
        confidentiality_risk: str,
        integrity_risk: str,
        availability_risk: str,
        threats_identified: List[str],
        vulnerabilities_found: List[str],
        controls_in_place: List[str],
        control_gaps: List[str],
        recommendations: List[str]
    ) -> TechRiskAssessment:
        risk_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        avg_risk = (
            risk_levels.get(confidentiality_risk, 2) +
            risk_levels.get(integrity_risk, 2) +
            risk_levels.get(availability_risk, 2)
        ) / 3

        if avg_risk >= 3.5:
            overall = "critical"
        elif avg_risk >= 2.5:
            overall = "high"
        elif avg_risk >= 1.5:
            overall = "medium"
        else:
            overall = "low"

        assessment = TechRiskAssessment(
            asset_id=asset_id,
            assessment_type=assessment_type,
            assessment_date=date.today(),
            assessor=assessor,
            confidentiality_risk=confidentiality_risk,
            integrity_risk=integrity_risk,
            availability_risk=availability_risk,
            overall_risk_rating=overall,
            threats_identified=threats_identified,
            vulnerabilities_found=vulnerabilities_found,
            controls_in_place=controls_in_place,
            control_gaps=control_gaps,
            recommendations=recommendations,
            next_assessment_date=date(date.today().year + 1, date.today().month, date.today().day)
        )

        await self.repository.save_assessment(assessment)
        return assessment

    async def get_asset_assessments(self, asset_id: UUID) -> List[TechRiskAssessment]:
        return await self.repository.find_assessments_by_asset(asset_id)

    async def report_security_incident(
        self,
        incident_type: IncidentType,
        severity: str,
        title: str,
        description: str,
        affected_assets: List[UUID],
        attack_vector: Optional[str] = None,
        data_compromised: bool = False,
        data_type_compromised: Optional[List[str]] = None,
        records_affected: Optional[int] = None
    ) -> SecurityIncident:
        now = datetime.utcnow()

        incident = SecurityIncident(
            incident_number=self._generate_incident_number(),
            incident_type=incident_type,
            severity=severity,
            title=title,
            description=description,
            detected_time=now,
            reported_time=now,
            affected_assets=affected_assets,
            attack_vector=attack_vector,
            data_compromised=data_compromised,
            data_type_compromised=data_type_compromised,
            records_affected=records_affected
        )

        await self.repository.save_security_incident(incident)
        return incident

    async def contain_incident(self, incident_id: UUID) -> Optional[SecurityIncident]:
        incident = await self.repository.find_security_incident_by_id(incident_id)
        if not incident:
            return None

        incident.containment_time = datetime.utcnow()
        incident.status = "contained"

        return incident

    async def eradicate_incident(self, incident_id: UUID) -> Optional[SecurityIncident]:
        incident = await self.repository.find_security_incident_by_id(incident_id)
        if not incident:
            return None

        incident.eradication_time = datetime.utcnow()
        incident.status = "eradicated"

        return incident

    async def recover_incident(self, incident_id: UUID) -> Optional[SecurityIncident]:
        incident = await self.repository.find_security_incident_by_id(incident_id)
        if not incident:
            return None

        incident.recovery_time = datetime.utcnow()
        incident.status = "recovered"

        return incident

    async def close_security_incident(
        self,
        incident_id: UUID,
        root_cause: str,
        lessons_learned: List[str],
        financial_impact: Optional[Decimal] = None
    ) -> Optional[SecurityIncident]:
        incident = await self.repository.find_security_incident_by_id(incident_id)
        if not incident:
            return None

        incident.closure_time = datetime.utcnow()
        incident.status = "closed"
        incident.root_cause = root_cause
        incident.lessons_learned = lessons_learned
        incident.financial_impact = financial_impact

        return incident

    async def get_open_incidents(self) -> List[SecurityIncident]:
        incidents = await self.repository.find_all_security_incidents()
        return [i for i in incidents if i.status != "closed"]

    async def initiate_access_review(
        self,
        system_id: UUID,
        system_name: str,
        review_type: str,
        reviewer: str,
        total_users: int
    ) -> AccessReview:
        review = AccessReview(
            system_id=system_id,
            system_name=system_name,
            review_type=review_type,
            review_date=date.today(),
            reviewer=reviewer,
            total_users=total_users,
            users_reviewed=0,
            access_confirmed=0,
            access_revoked=0,
            access_modified=0,
            privileged_accounts=0,
            service_accounts=0,
            orphan_accounts=0,
            dormant_accounts=0,
            segregation_conflicts=0
        )

        await self.repository.save_access_review(review)
        return review

    async def complete_access_review(
        self,
        review_id: UUID,
        users_reviewed: int,
        access_confirmed: int,
        access_revoked: int,
        access_modified: int,
        privileged_accounts: int,
        service_accounts: int,
        orphan_accounts: int,
        dormant_accounts: int,
        segregation_conflicts: int,
        findings: List[str]
    ) -> Optional[AccessReview]:
        review = await self.repository.find_access_review_by_id(review_id)
        if not review:
            return None

        review.users_reviewed = users_reviewed
        review.access_confirmed = access_confirmed
        review.access_revoked = access_revoked
        review.access_modified = access_modified
        review.privileged_accounts = privileged_accounts
        review.service_accounts = service_accounts
        review.orphan_accounts = orphan_accounts
        review.dormant_accounts = dormant_accounts
        review.segregation_conflicts = segregation_conflicts
        review.findings = findings
        review.status = "completed"
        review.completion_date = date.today()
        review.next_review_date = date(date.today().year + 1, date.today().month, date.today().day)

        return review

    async def assess_change_risk(
        self,
        change_ticket: str,
        change_title: str,
        change_type: str,
        change_date: date,
        affected_systems: List[UUID],
        impact_assessment: str,
        rollback_plan: bool,
        test_plan: bool,
        created_by: str
    ) -> ChangeRisk:
        risk_score = 0

        critical_systems = 0
        for sys_id in affected_systems:
            asset = await self.repository.find_asset_by_id(sys_id)
            if asset and asset.criticality == AssetCriticality.CRITICAL:
                critical_systems += 1

        risk_score += critical_systems * 20
        risk_score += len(affected_systems) * 5

        if not rollback_plan:
            risk_score += 25
        if not test_plan:
            risk_score += 20

        if change_type == "emergency":
            risk_score += 30

        if risk_score >= 80:
            risk_category = "high"
        elif risk_score >= 50:
            risk_category = "medium"
        else:
            risk_category = "low"

        change = ChangeRisk(
            change_ticket=change_ticket,
            change_title=change_title,
            change_type=change_type,
            change_date=change_date,
            affected_systems=affected_systems,
            risk_category=risk_category,
            risk_score=risk_score,
            impact_assessment=impact_assessment,
            rollback_plan=rollback_plan,
            test_plan=test_plan,
            approval_status="pending",
            implementation_status="pending",
            created_by=created_by
        )

        await self.repository.save_change_risk(change)
        return change

    async def generate_metrics(self) -> TechRiskMetrics:
        assets = await self.repository.find_all_assets()
        vulns = await self.repository.find_all_vulnerabilities()
        patches = await self.repository.find_all_patches()
        incidents = await self.repository.find_all_security_incidents()
        reviews = await self.repository.find_all_access_reviews()

        total_assets = len(assets)
        critical_assets = len([a for a in assets if a.criticality == AssetCriticality.CRITICAL])
        scanned = len([a for a in assets if a.last_scan_date])
        scan_coverage = Decimal(str(scanned / total_assets * 100)) if total_assets > 0 else Decimal("0")

        open_vulns = [v for v in vulns if v.status == "open"]
        critical_vulns = len([v for v in open_vulns if v.severity == VulnerabilitySeverity.CRITICAL])
        high_vulns = len([v for v in open_vulns if v.severity == VulnerabilitySeverity.HIGH])
        medium_vulns = len([v for v in open_vulns if v.severity == VulnerabilitySeverity.MEDIUM])
        low_vulns = len([v for v in open_vulns if v.severity == VulnerabilitySeverity.LOW])

        current_month = date.today().month
        current_year = date.today().year
        remediated_mtd = len([
            v for v in vulns
            if v.remediation_date and v.remediation_date.month == current_month and v.remediation_date.year == current_year
        ])

        remediation_days = []
        for v in vulns:
            if v.remediation_date:
                days = (v.remediation_date - v.discovery_date).days
                remediation_days.append(days)
        avg_remediation = sum(remediation_days) / len(remediation_days) if remediation_days else 0

        patches_pending = len([p for p in patches if p.status == PatchStatus.PENDING])
        patches_overdue = len([
            p for p in patches
            if p.status == PatchStatus.PENDING and p.release_date < date.today()
        ])

        incidents_mtd = len([
            i for i in incidents
            if i.detected_time.month == current_month and i.detected_time.year == current_year
        ])

        resolution_times = []
        for i in incidents:
            if i.closure_time and i.detected_time:
                hours = (i.closure_time - i.detected_time).total_seconds() / 3600
                resolution_times.append(hours)
        mttr = sum(resolution_times) / len(resolution_times) if resolution_times else 0

        completed_reviews = len([r for r in reviews if r.status == "completed"])
        pending_reviews = len([r for r in reviews if r.status != "completed"])

        compliant = len([a for a in assets if a.compliance_status == "compliant"])
        compliance_score = Decimal(str(compliant / total_assets * 100)) if total_assets > 0 else Decimal("0")

        metrics = TechRiskMetrics(
            metrics_date=date.today(),
            total_assets=total_assets,
            critical_assets=critical_assets,
            assets_scanned=scanned,
            scan_coverage=scan_coverage,
            total_vulnerabilities=len(open_vulns),
            critical_vulnerabilities=critical_vulns,
            high_vulnerabilities=high_vulns,
            medium_vulnerabilities=medium_vulns,
            low_vulnerabilities=low_vulns,
            vulnerabilities_remediated_mtd=remediated_mtd,
            average_remediation_days=avg_remediation,
            patches_pending=patches_pending,
            patches_overdue=patches_overdue,
            security_incidents_mtd=incidents_mtd,
            mttr_hours=mttr,
            access_reviews_completed=completed_reviews,
            access_reviews_pending=pending_reviews,
            compliance_score=compliance_score
        )

        await self.repository.save_metrics(metrics)
        return metrics

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


technology_risk_service = TechnologyRiskService()
