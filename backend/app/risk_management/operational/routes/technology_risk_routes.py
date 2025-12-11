"""Technology Risk Routes - API endpoints for IT risk management"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import date
from pydantic import BaseModel
from decimal import Decimal
from ..models.technology_risk_models import (
    ITAsset, Vulnerability, PatchManagement, TechRiskAssessment,
    SecurityIncident, AccessReview, ChangeRisk, TechRiskMetrics,
    AssetType, AssetCriticality, VulnerabilitySeverity, IncidentType
)
from ..services.technology_risk_service import technology_risk_service

router = APIRouter(prefix="/tech-risk", tags=["Technology Risk"])


class RegisterAssetRequest(BaseModel):
    asset_name: str
    asset_type: AssetType
    description: str
    criticality: AssetCriticality
    owner: str
    custodian: str
    business_unit: str
    location: str
    environment: str
    data_classification: str
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    operating_system: Optional[str] = None
    version: Optional[str] = None
    vendor: Optional[str] = None
    support_end_date: Optional[date] = None
    pii_stored: bool = False
    pci_scope: bool = False
    sox_scope: bool = False


class RecordVulnerabilityRequest(BaseModel):
    title: str
    description: str
    severity: VulnerabilitySeverity
    affected_assets: List[UUID]
    affected_systems: List[str]
    discovery_source: str
    remediation_steps: List[str]
    cve_id: Optional[str] = None
    cvss_score: Optional[Decimal] = None
    cvss_vector: Optional[str] = None
    exploit_available: bool = False
    actively_exploited: bool = False
    patch_available: bool = False
    patch_id: Optional[str] = None
    workaround: Optional[str] = None


class CreatePatchRequest(BaseModel):
    patch_code: str
    patch_name: str
    vendor: str
    release_date: date
    severity: str
    affected_products: List[str]
    affected_assets: List[UUID]
    cve_addressed: List[str]


class PerformAssessmentRequest(BaseModel):
    assessment_type: str
    assessor: str
    confidentiality_risk: str
    integrity_risk: str
    availability_risk: str
    threats_identified: List[str]
    vulnerabilities_found: List[str]
    controls_in_place: List[str]
    control_gaps: List[str]
    recommendations: List[str]


class ReportIncidentRequest(BaseModel):
    incident_type: IncidentType
    severity: str
    title: str
    description: str
    affected_assets: List[UUID]
    attack_vector: Optional[str] = None
    data_compromised: bool = False
    data_type_compromised: Optional[List[str]] = None
    records_affected: Optional[int] = None


class InitiateAccessReviewRequest(BaseModel):
    system_id: UUID
    system_name: str
    review_type: str
    reviewer: str
    total_users: int


class CompleteAccessReviewRequest(BaseModel):
    users_reviewed: int
    access_confirmed: int
    access_revoked: int
    access_modified: int
    privileged_accounts: int
    service_accounts: int
    orphan_accounts: int
    dormant_accounts: int
    segregation_conflicts: int
    findings: List[str]


class AssessChangeRiskRequest(BaseModel):
    change_ticket: str
    change_title: str
    change_type: str
    change_date: date
    affected_systems: List[UUID]
    impact_assessment: str
    rollback_plan: bool
    test_plan: bool
    created_by: str


@router.post("/assets", response_model=ITAsset)
async def register_asset(request: RegisterAssetRequest):
    """Register IT asset"""
    return await technology_risk_service.register_asset(
        asset_name=request.asset_name,
        asset_type=request.asset_type,
        description=request.description,
        criticality=request.criticality,
        owner=request.owner,
        custodian=request.custodian,
        business_unit=request.business_unit,
        location=request.location,
        environment=request.environment,
        data_classification=request.data_classification,
        ip_address=request.ip_address,
        hostname=request.hostname,
        operating_system=request.operating_system,
        version=request.version,
        vendor=request.vendor,
        support_end_date=request.support_end_date,
        pii_stored=request.pii_stored,
        pci_scope=request.pci_scope,
        sox_scope=request.sox_scope
    )


@router.get("/assets/{asset_id}", response_model=ITAsset)
async def get_asset(asset_id: UUID):
    """Get IT asset"""
    asset = await technology_risk_service.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.get("/assets", response_model=List[ITAsset])
async def list_assets(
    asset_type: Optional[AssetType] = Query(None),
    criticality: Optional[AssetCriticality] = Query(None),
    business_unit: Optional[str] = Query(None),
    environment: Optional[str] = Query(None)
):
    """List IT assets"""
    return await technology_risk_service.list_assets(
        asset_type, criticality, business_unit, environment
    )


@router.post("/vulnerabilities", response_model=Vulnerability)
async def record_vulnerability(request: RecordVulnerabilityRequest):
    """Record vulnerability"""
    return await technology_risk_service.record_vulnerability(
        title=request.title,
        description=request.description,
        severity=request.severity,
        affected_assets=request.affected_assets,
        affected_systems=request.affected_systems,
        discovery_source=request.discovery_source,
        remediation_steps=request.remediation_steps,
        cve_id=request.cve_id,
        cvss_score=request.cvss_score,
        cvss_vector=request.cvss_vector,
        exploit_available=request.exploit_available,
        actively_exploited=request.actively_exploited,
        patch_available=request.patch_available,
        patch_id=request.patch_id,
        workaround=request.workaround
    )


@router.get("/vulnerabilities/{vuln_id}", response_model=Vulnerability)
async def get_vulnerability(vuln_id: UUID):
    """Get vulnerability"""
    vuln = await technology_risk_service.get_vulnerability(vuln_id)
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return vuln


@router.get("/vulnerabilities", response_model=List[Vulnerability])
async def list_vulnerabilities(
    severity: Optional[VulnerabilitySeverity] = Query(None),
    status: str = Query("open"),
    asset_id: Optional[UUID] = Query(None)
):
    """List vulnerabilities"""
    return await technology_risk_service.list_vulnerabilities(severity, status, asset_id)


@router.put("/vulnerabilities/{vuln_id}/remediate")
async def remediate_vulnerability(vuln_id: UUID, assigned_to: str, due_date: date):
    """Assign vulnerability for remediation"""
    vuln = await technology_risk_service.remediate_vulnerability(vuln_id, assigned_to, due_date)
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return vuln


@router.put("/vulnerabilities/{vuln_id}/close")
async def close_vulnerability(vuln_id: UUID):
    """Close vulnerability"""
    vuln = await technology_risk_service.close_vulnerability(vuln_id)
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return vuln


@router.put("/vulnerabilities/{vuln_id}/accept-risk")
async def accept_risk(vuln_id: UUID, reason: str, expiry: date):
    """Accept vulnerability risk"""
    vuln = await technology_risk_service.accept_risk(vuln_id, reason, expiry)
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return vuln


@router.post("/patches", response_model=PatchManagement)
async def create_patch(request: CreatePatchRequest):
    """Create patch record"""
    return await technology_risk_service.create_patch(
        patch_code=request.patch_code,
        patch_name=request.patch_name,
        vendor=request.vendor,
        release_date=request.release_date,
        severity=request.severity,
        affected_products=request.affected_products,
        affected_assets=request.affected_assets,
        cve_addressed=request.cve_addressed
    )


@router.get("/patches/pending", response_model=List[PatchManagement])
async def get_pending_patches():
    """Get pending patches"""
    return await technology_risk_service.get_pending_patches()


@router.post("/assets/{asset_id}/assessments", response_model=TechRiskAssessment)
async def perform_assessment(asset_id: UUID, request: PerformAssessmentRequest):
    """Perform risk assessment"""
    return await technology_risk_service.perform_risk_assessment(
        asset_id=asset_id,
        assessment_type=request.assessment_type,
        assessor=request.assessor,
        confidentiality_risk=request.confidentiality_risk,
        integrity_risk=request.integrity_risk,
        availability_risk=request.availability_risk,
        threats_identified=request.threats_identified,
        vulnerabilities_found=request.vulnerabilities_found,
        controls_in_place=request.controls_in_place,
        control_gaps=request.control_gaps,
        recommendations=request.recommendations
    )


@router.get("/assets/{asset_id}/assessments", response_model=List[TechRiskAssessment])
async def get_assessments(asset_id: UUID):
    """Get asset assessments"""
    return await technology_risk_service.get_asset_assessments(asset_id)


@router.post("/security-incidents", response_model=SecurityIncident)
async def report_incident(request: ReportIncidentRequest):
    """Report security incident"""
    return await technology_risk_service.report_security_incident(
        incident_type=request.incident_type,
        severity=request.severity,
        title=request.title,
        description=request.description,
        affected_assets=request.affected_assets,
        attack_vector=request.attack_vector,
        data_compromised=request.data_compromised,
        data_type_compromised=request.data_type_compromised,
        records_affected=request.records_affected
    )


@router.put("/security-incidents/{incident_id}/contain")
async def contain_incident(incident_id: UUID):
    """Contain security incident"""
    incident = await technology_risk_service.contain_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.put("/security-incidents/{incident_id}/eradicate")
async def eradicate_incident(incident_id: UUID):
    """Eradicate security incident"""
    incident = await technology_risk_service.eradicate_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.put("/security-incidents/{incident_id}/recover")
async def recover_incident(incident_id: UUID):
    """Recover from security incident"""
    incident = await technology_risk_service.recover_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.put("/security-incidents/{incident_id}/close")
async def close_incident(
    incident_id: UUID,
    root_cause: str,
    lessons_learned: List[str],
    financial_impact: Optional[Decimal] = None
):
    """Close security incident"""
    incident = await technology_risk_service.close_security_incident(
        incident_id, root_cause, lessons_learned, financial_impact
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/security-incidents/open", response_model=List[SecurityIncident])
async def get_open_incidents():
    """Get open security incidents"""
    return await technology_risk_service.get_open_incidents()


@router.post("/access-reviews", response_model=AccessReview)
async def initiate_access_review(request: InitiateAccessReviewRequest):
    """Initiate access review"""
    return await technology_risk_service.initiate_access_review(
        system_id=request.system_id,
        system_name=request.system_name,
        review_type=request.review_type,
        reviewer=request.reviewer,
        total_users=request.total_users
    )


@router.put("/access-reviews/{review_id}/complete", response_model=AccessReview)
async def complete_access_review(review_id: UUID, request: CompleteAccessReviewRequest):
    """Complete access review"""
    review = await technology_risk_service.complete_access_review(
        review_id=review_id,
        users_reviewed=request.users_reviewed,
        access_confirmed=request.access_confirmed,
        access_revoked=request.access_revoked,
        access_modified=request.access_modified,
        privileged_accounts=request.privileged_accounts,
        service_accounts=request.service_accounts,
        orphan_accounts=request.orphan_accounts,
        dormant_accounts=request.dormant_accounts,
        segregation_conflicts=request.segregation_conflicts,
        findings=request.findings
    )
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.post("/change-risk", response_model=ChangeRisk)
async def assess_change_risk(request: AssessChangeRiskRequest):
    """Assess change risk"""
    return await technology_risk_service.assess_change_risk(
        change_ticket=request.change_ticket,
        change_title=request.change_title,
        change_type=request.change_type,
        change_date=request.change_date,
        affected_systems=request.affected_systems,
        impact_assessment=request.impact_assessment,
        rollback_plan=request.rollback_plan,
        test_plan=request.test_plan,
        created_by=request.created_by
    )


@router.get("/metrics", response_model=TechRiskMetrics)
async def get_metrics():
    """Get technology risk metrics"""
    return await technology_risk_service.generate_metrics()


@router.get("/statistics")
async def get_statistics():
    """Get technology risk statistics"""
    return await technology_risk_service.get_statistics()
