"""External Audit Models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


class ExternalAuditType(str, Enum):
    FINANCIAL_STATEMENT = "financial_statement"
    SOX = "sox"
    INTEGRATED = "integrated"
    REGULATORY = "regulatory"
    SOC1 = "soc1"
    SOC2 = "soc2"
    SPECIAL_PURPOSE = "special_purpose"


class AuditOpinion(str, Enum):
    UNQUALIFIED = "unqualified"
    QUALIFIED = "qualified"
    ADVERSE = "adverse"
    DISCLAIMER = "disclaimer"


class ExternalAuditEngagement(BaseModel):
    engagement_id: UUID = Field(default_factory=uuid4)
    engagement_reference: str
    audit_firm: str
    audit_type: ExternalAuditType
    fiscal_year: int
    engagement_partner: str
    engagement_manager: str
    engagement_letter_date: date
    scope: str
    materiality_threshold: Decimal
    planned_start_date: date
    planned_end_date: date
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    fee_estimate: Decimal = Decimal("0")
    actual_fee: Decimal = Decimal("0")
    status: str = "planned"
    internal_coordinator: str = ""
    created_date: datetime = Field(default_factory=datetime.utcnow)


class PBCRequest(BaseModel):
    """Prepared by Client Request"""
    pbc_id: UUID = Field(default_factory=uuid4)
    engagement_id: UUID
    pbc_reference: str
    item_description: str
    category: str
    requested_by: str
    requested_date: date
    due_date: date
    assigned_to: str
    status: str = "pending"
    submitted_date: Optional[date] = None
    submitted_by: Optional[str] = None
    file_references: List[str] = Field(default_factory=list)
    auditor_comments: str = ""
    priority: str = "normal"


class AuditAdjustment(BaseModel):
    adjustment_id: UUID = Field(default_factory=uuid4)
    engagement_id: UUID
    adjustment_reference: str
    adjustment_type: str
    account_affected: str
    debit_amount: Decimal = Decimal("0")
    credit_amount: Decimal = Decimal("0")
    description: str
    proposed_by: str
    proposed_date: date
    management_accepted: bool = False
    acceptance_date: Optional[date] = None
    posted: bool = False
    posting_date: Optional[date] = None
    materiality_impact: str = ""


class ExternalAuditFinding(BaseModel):
    finding_id: UUID = Field(default_factory=uuid4)
    engagement_id: UUID
    finding_reference: str
    finding_type: str
    description: str
    severity: str
    management_letter_item: bool = False
    significant_deficiency: bool = False
    material_weakness: bool = False
    management_response: str = ""
    remediation_plan: str = ""
    target_remediation_date: Optional[date] = None
    status: str = "open"


class AuditOpinionLetter(BaseModel):
    opinion_id: UUID = Field(default_factory=uuid4)
    engagement_id: UUID
    opinion_type: AuditOpinion
    opinion_date: date
    report_date: date
    basis_for_opinion: str
    key_audit_matters: List[Dict[str, str]] = Field(default_factory=list)
    emphasis_of_matter: List[str] = Field(default_factory=list)
    other_matter: List[str] = Field(default_factory=list)
    going_concern_doubt: bool = False
    going_concern_explanation: str = ""
    signed_by: str
    firm_name: str


class ManagementRepresentationLetter(BaseModel):
    letter_id: UUID = Field(default_factory=uuid4)
    engagement_id: UUID
    letter_date: date
    fiscal_year_end: date
    representations: List[Dict[str, Any]] = Field(default_factory=list)
    signed_by_ceo: str
    signed_by_cfo: str
    ceo_signature_date: Optional[date] = None
    cfo_signature_date: Optional[date] = None
    status: str = "draft"
