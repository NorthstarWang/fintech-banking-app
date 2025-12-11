"""Board Committee Models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


class CommitteeType(str, Enum):
    AUDIT = "audit"
    RISK = "risk"
    COMPENSATION = "compensation"
    NOMINATION = "nomination"
    GOVERNANCE = "governance"
    EXECUTIVE = "executive"
    TECHNOLOGY = "technology"
    COMPLIANCE = "compliance"


class Committee(BaseModel):
    committee_id: UUID = Field(default_factory=uuid4)
    committee_name: str
    committee_type: CommitteeType
    charter: str
    mandate: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    authority: List[str] = Field(default_factory=list)
    composition_requirements: Dict[str, Any] = Field(default_factory=dict)
    minimum_members: int = 3
    chairman: str = ""
    secretary: str = ""
    members: List[str] = Field(default_factory=list)
    meeting_frequency: str = "quarterly"
    quorum_requirement: int = 2
    established_date: date
    charter_last_reviewed: date
    status: str = "active"


class CommitteeMeeting(BaseModel):
    meeting_id: UUID = Field(default_factory=uuid4)
    committee_id: UUID
    meeting_reference: str
    meeting_date: date
    meeting_time: str
    meeting_type: str  # regular, special
    location: str
    attendees: List[str] = Field(default_factory=list)
    invited_guests: List[str] = Field(default_factory=list)
    agenda: List[Dict[str, Any]] = Field(default_factory=list)
    presentations: List[Dict[str, Any]] = Field(default_factory=list)
    discussions: List[Dict[str, Any]] = Field(default_factory=list)
    decisions: List[Dict[str, Any]] = Field(default_factory=list)
    action_items: List[Dict[str, Any]] = Field(default_factory=list)
    minutes_status: str = "pending"
    minutes_approved_date: Optional[date] = None


class CommitteeResolution(BaseModel):
    resolution_id: UUID = Field(default_factory=uuid4)
    committee_id: UUID
    meeting_id: UUID
    resolution_reference: str
    resolution_date: date
    subject: str
    resolution_text: str
    proposed_by: str
    seconded_by: str
    votes_for: int = 0
    votes_against: int = 0
    votes_abstained: int = 0
    passed: bool = False
    effective_date: date
    implementation_required: bool = False
    implementation_deadline: Optional[date] = None
    implementation_owner: str = ""
    status: str = "approved"


class CommitteeReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    committee_id: UUID
    report_period: str
    report_date: date
    prepared_by: str
    key_activities: List[str] = Field(default_factory=list)
    meetings_held: int = 0
    attendance_summary: Dict[str, Decimal] = Field(default_factory=dict)
    key_decisions: List[str] = Field(default_factory=list)
    oversight_activities: List[str] = Field(default_factory=list)
    issues_escalated: List[str] = Field(default_factory=list)
    recommendations_to_board: List[str] = Field(default_factory=list)
    self_assessment_results: Dict[str, Any] = Field(default_factory=dict)
    priorities_next_period: List[str] = Field(default_factory=list)
    status: str = "draft"


class CommitteeMember(BaseModel):
    membership_id: UUID = Field(default_factory=uuid4)
    committee_id: UUID
    member_id: UUID
    member_name: str
    role: str  # chairman, member, secretary
    appointment_date: date
    term_end_date: Optional[date] = None
    is_independent: bool = True
    expertise_relevant: List[str] = Field(default_factory=list)
    attendance_record: List[Dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True
