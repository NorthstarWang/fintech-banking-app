"""
Fraud Investigation Models

Defines data structures for fraud investigation workflow.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class InvestigationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PENDING_INFO = "pending_info"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InvestigationType(str, Enum):
    STANDARD = "standard"
    EXPEDITED = "expedited"
    COMPLEX = "complex"
    EXTERNAL = "external"


class InvestigationOutcome(str, Enum):
    FRAUD_CONFIRMED = "fraud_confirmed"
    NO_FRAUD = "no_fraud"
    INCONCLUSIVE = "inconclusive"
    CUSTOMER_ERROR = "customer_error"


class InvestigationStep(BaseModel):
    step_id: UUID = Field(default_factory=uuid4)
    step_name: str
    step_type: str
    order: int

    status: str = "pending"
    is_required: bool = True

    assigned_to: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    result: Optional[str] = None
    notes: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)


class CustomerContact(BaseModel):
    contact_id: UUID = Field(default_factory=uuid4)
    contact_type: str
    contact_method: str

    contacted_at: datetime = Field(default_factory=datetime.utcnow)
    contacted_by: str

    outcome: str
    notes: str

    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None


class FraudInvestigation(BaseModel):
    investigation_id: UUID = Field(default_factory=uuid4)
    investigation_number: str

    case_id: UUID
    alert_ids: List[UUID] = Field(default_factory=list)

    investigation_type: InvestigationType = InvestigationType.STANDARD
    status: InvestigationStatus = InvestigationStatus.PENDING

    customer_id: str
    customer_name: str

    disputed_amount: float = 0.0
    disputed_transactions: List[str] = Field(default_factory=list)

    steps: List[InvestigationStep] = Field(default_factory=list)
    current_step: int = 0

    customer_contacts: List[CustomerContact] = Field(default_factory=list)

    assigned_investigator: Optional[str] = None
    supervisor: Optional[str] = None

    priority: str = "medium"
    sla_deadline: datetime

    outcome: Optional[InvestigationOutcome] = None
    outcome_reason: Optional[str] = None

    liability_decision: Optional[str] = None
    refund_amount: float = 0.0
    refund_processed: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    regulatory_reported: bool = False
    law_enforcement_involved: bool = False

    documents: List[Dict[str, Any]] = Field(default_factory=list)
    notes: List[Dict[str, Any]] = Field(default_factory=list)

    metadata: Dict[str, Any] = Field(default_factory=dict)


class DisputeRecord(BaseModel):
    dispute_id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID

    customer_id: str
    account_id: str

    transaction_id: str
    transaction_date: datetime
    transaction_amount: float
    merchant_name: Optional[str] = None

    dispute_reason: str
    customer_statement: str

    provisional_credit_given: bool = False
    provisional_credit_amount: float = 0.0
    provisional_credit_date: Optional[datetime] = None

    final_decision: Optional[str] = None
    final_decision_date: Optional[datetime] = None

    chargeback_filed: bool = False
    chargeback_date: Optional[datetime] = None
    chargeback_status: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


class InvestigationTemplate(BaseModel):
    template_id: UUID = Field(default_factory=uuid4)
    template_name: str
    investigation_type: InvestigationType

    description: str

    required_steps: List[Dict[str, Any]] = Field(default_factory=list)
    optional_steps: List[Dict[str, Any]] = Field(default_factory=list)

    default_sla_hours: int = 48

    is_active: bool = True

    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InvestigationStatistics(BaseModel):
    total_investigations: int = 0
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_outcome: Dict[str, int] = Field(default_factory=dict)
    total_disputed_amount: float = 0.0
    total_refunded: float = 0.0
    average_resolution_days: float = 0.0
    sla_compliance_rate: float = 0.0
    open_investigations: int = 0
    overdue_investigations: int = 0
