"""Corporate Governance Models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


class GovernanceFramework(BaseModel):
    framework_id: UUID = Field(default_factory=uuid4)
    framework_name: str
    framework_version: str
    effective_date: date
    description: str
    principles: List[str] = Field(default_factory=list)
    governance_structure: Dict[str, Any] = Field(default_factory=dict)
    roles_responsibilities: Dict[str, List[str]] = Field(default_factory=dict)
    reporting_lines: Dict[str, str] = Field(default_factory=dict)
    approved_by: str
    approval_date: date
    next_review_date: date
    status: str = "active"


class BoardMember(BaseModel):
    member_id: UUID = Field(default_factory=uuid4)
    member_name: str
    position: str
    member_type: str  # independent, executive, non-executive
    appointment_date: date
    term_end_date: Optional[date] = None
    committees: List[str] = Field(default_factory=list)
    qualifications: List[str] = Field(default_factory=list)
    expertise_areas: List[str] = Field(default_factory=list)
    other_directorships: List[str] = Field(default_factory=list)
    annual_fee: Decimal = Decimal("0")
    attendance_rate: Decimal = Decimal("100")
    is_active: bool = True
    conflict_of_interest: List[Dict[str, Any]] = Field(default_factory=list)


class BoardMeeting(BaseModel):
    meeting_id: UUID = Field(default_factory=uuid4)
    meeting_type: str  # regular, special, annual
    meeting_date: date
    meeting_time: str
    location: str
    agenda_items: List[Dict[str, Any]] = Field(default_factory=list)
    attendees: List[str] = Field(default_factory=list)
    absentees: List[str] = Field(default_factory=list)
    quorum_present: bool = True
    minutes_prepared_by: str = ""
    minutes_approved_date: Optional[date] = None
    resolutions: List[Dict[str, Any]] = Field(default_factory=list)
    action_items: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = "scheduled"


class GovernancePolicy(BaseModel):
    policy_id: UUID = Field(default_factory=uuid4)
    policy_code: str
    policy_name: str
    policy_category: str
    description: str
    scope: str
    owner: str
    approver: str
    effective_date: date
    review_date: date
    version: str
    status: str = "active"
    key_provisions: List[str] = Field(default_factory=list)
    related_policies: List[str] = Field(default_factory=list)
    compliance_requirements: List[str] = Field(default_factory=list)


class ConflictOfInterest(BaseModel):
    conflict_id: UUID = Field(default_factory=uuid4)
    declarant_name: str
    declarant_position: str
    declaration_date: date
    conflict_type: str
    description: str
    related_party: str
    nature_of_interest: str
    mitigation_measures: List[str] = Field(default_factory=list)
    review_committee: str
    review_date: Optional[date] = None
    decision: str = ""
    status: str = "pending"
    annual_declaration: bool = False


class GovernanceAssessment(BaseModel):
    assessment_id: UUID = Field(default_factory=uuid4)
    assessment_year: int
    assessment_type: str
    assessor: str
    assessment_date: date
    areas_assessed: List[str] = Field(default_factory=list)
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    overall_rating: str
    board_effectiveness_score: Decimal = Decimal("0")
    compliance_score: Decimal = Decimal("0")
    risk_management_score: Decimal = Decimal("0")
    status: str = "draft"
