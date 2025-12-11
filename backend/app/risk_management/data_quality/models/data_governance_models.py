"""Data Governance Models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field


class DataClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"
    PCI = "pci"


class DataDomain(BaseModel):
    domain_id: UUID = Field(default_factory=uuid4)
    domain_name: str
    domain_code: str
    description: str
    business_owner: str
    data_steward: str
    technical_owner: str
    parent_domain_id: Optional[UUID] = None
    sub_domains: List[str] = Field(default_factory=list)
    critical_data_elements: List[str] = Field(default_factory=list)
    policies: List[str] = Field(default_factory=list)
    created_date: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class DataOwnership(BaseModel):
    ownership_id: UUID = Field(default_factory=uuid4)
    asset_id: UUID
    asset_name: str
    business_owner: str
    data_steward: str
    technical_owner: str
    custodian: str = ""
    effective_date: date
    expiry_date: Optional[date] = None
    responsibilities: Dict[str, List[str]] = Field(default_factory=dict)
    escalation_path: List[str] = Field(default_factory=list)
    status: str = "active"


class DataPolicy(BaseModel):
    policy_id: UUID = Field(default_factory=uuid4)
    policy_code: str
    policy_name: str
    policy_type: str  # quality, security, retention, usage, sharing
    description: str
    scope: str
    requirements: List[str] = Field(default_factory=list)
    controls: List[str] = Field(default_factory=list)
    exceptions_process: str = ""
    owner: str
    approver: str
    effective_date: date
    review_date: date
    version: str = "1.0"
    status: str = "active"


class DataStandard(BaseModel):
    standard_id: UUID = Field(default_factory=uuid4)
    standard_code: str
    standard_name: str
    standard_type: str  # naming, format, encoding, modeling
    description: str
    domain_applicability: List[str] = Field(default_factory=list)
    rules: List[Dict[str, Any]] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    owner: str
    effective_date: date
    is_mandatory: bool = True
    status: str = "active"


class BusinessGlossary(BaseModel):
    term_id: UUID = Field(default_factory=uuid4)
    term_name: str
    term_definition: str
    domain_id: UUID
    synonyms: List[str] = Field(default_factory=list)
    related_terms: List[str] = Field(default_factory=list)
    business_rules: List[str] = Field(default_factory=list)
    owner: str
    steward: str
    status: str = "approved"
    created_date: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class DataAccessRequest(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    requestor: str
    requestor_department: str
    asset_id: UUID
    asset_name: str
    access_type: str  # read, write, full
    purpose: str
    duration: str
    justification: str
    approver: str = ""
    approval_date: Optional[datetime] = None
    status: str = "pending"
    expiry_date: Optional[date] = None
    created_date: datetime = Field(default_factory=datetime.utcnow)


class DataPrivacyAssessment(BaseModel):
    assessment_id: UUID = Field(default_factory=uuid4)
    asset_id: UUID
    asset_name: str
    assessment_date: date
    assessor: str
    contains_pii: bool = False
    pii_categories: List[str] = Field(default_factory=list)
    data_subjects: List[str] = Field(default_factory=list)
    processing_purposes: List[str] = Field(default_factory=list)
    retention_period: str = ""
    sharing_partners: List[str] = Field(default_factory=list)
    security_controls: List[str] = Field(default_factory=list)
    risk_level: str = "low"
    recommendations: List[str] = Field(default_factory=list)
    status: str = "completed"


class GovernanceMetric(BaseModel):
    metric_id: UUID = Field(default_factory=uuid4)
    metric_date: date
    domain_id: Optional[UUID] = None
    metric_name: str
    metric_type: str
    current_value: float
    target_value: float
    threshold_value: float
    trend: str = "stable"
    status: str = "green"
    calculated_by: str = "system"
