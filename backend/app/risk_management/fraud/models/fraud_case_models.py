"""
Fraud Case Models

Defines data structures for fraud investigation cases.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class FraudCaseStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    CONFIRMED_FRAUD = "confirmed_fraud"
    NOT_FRAUD = "not_fraud"
    ESCALATED = "escalated"
    CLOSED = "closed"


class FraudCasePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class RecoveryStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PARTIAL_RECOVERY = "partial_recovery"
    FULL_RECOVERY = "full_recovery"
    UNABLE_TO_RECOVER = "unable_to_recover"


class CaseAction(BaseModel):
    action_id: UUID = Field(default_factory=uuid4)
    action_type: str
    description: str
    performed_by: str
    performed_at: datetime = Field(default_factory=datetime.utcnow)
    result: Optional[str] = None
    notes: Optional[str] = None


class CaseFinding(BaseModel):
    finding_id: UUID = Field(default_factory=uuid4)
    finding_type: str
    description: str
    evidence: List[str] = Field(default_factory=list)
    severity: str
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FraudCase(BaseModel):
    case_id: UUID = Field(default_factory=uuid4)
    case_number: str
    title: str
    description: str

    status: FraudCaseStatus = FraudCaseStatus.OPEN
    priority: FraudCasePriority = FraudCasePriority.MEDIUM

    customer_id: str
    customer_name: str
    account_ids: List[str] = Field(default_factory=list)

    alert_ids: List[UUID] = Field(default_factory=list)
    transaction_ids: List[str] = Field(default_factory=list)

    total_fraud_amount: float = 0.0
    recovered_amount: float = 0.0
    recovery_status: RecoveryStatus = RecoveryStatus.NOT_STARTED

    fraud_type: str
    fraud_confirmed: bool = False
    fraud_vector: Optional[str] = None

    assigned_to: Optional[str] = None
    investigator_notes: Optional[str] = None

    actions: List[CaseAction] = Field(default_factory=list)
    findings: List[CaseFinding] = Field(default_factory=list)

    law_enforcement_reported: bool = False
    law_enforcement_reference: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None

    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FraudCaseSummary(BaseModel):
    case_id: UUID
    case_number: str
    title: str
    status: FraudCaseStatus
    priority: FraudCasePriority
    customer_name: str
    fraud_type: str
    total_fraud_amount: float
    assigned_to: Optional[str] = None
    created_at: datetime


class FraudCaseStatistics(BaseModel):
    total_cases: int = 0
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_priority: Dict[str, int] = Field(default_factory=dict)
    confirmed_fraud_cases: int = 0
    total_fraud_amount: float = 0.0
    total_recovered: float = 0.0
    recovery_rate: float = 0.0
    open_cases: int = 0
    overdue_cases: int = 0
