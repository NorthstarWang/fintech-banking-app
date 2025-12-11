"""
Fraud Alert Models

Defines data structures for fraud alerts.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class FraudAlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudAlertStatus(str, Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    INVESTIGATING = "investigating"
    CONFIRMED_FRAUD = "confirmed_fraud"
    FALSE_POSITIVE = "false_positive"
    CLOSED = "closed"


class FraudType(str, Enum):
    ACCOUNT_TAKEOVER = "account_takeover"
    NEW_ACCOUNT_FRAUD = "new_account_fraud"
    CARD_NOT_PRESENT = "card_not_present"
    CARD_PRESENT = "card_present"
    IDENTITY_THEFT = "identity_theft"
    SYNTHETIC_IDENTITY = "synthetic_identity"
    FIRST_PARTY_FRAUD = "first_party_fraud"
    FRIENDLY_FRAUD = "friendly_fraud"
    CHECK_FRAUD = "check_fraud"
    WIRE_FRAUD = "wire_fraud"
    ACH_FRAUD = "ach_fraud"
    PHISHING = "phishing"
    SOCIAL_ENGINEERING = "social_engineering"
    APPLICATION_FRAUD = "application_fraud"


class FraudIndicator(BaseModel):
    indicator_id: UUID = Field(default_factory=uuid4)
    indicator_type: str
    indicator_name: str
    description: str
    weight: float = 1.0
    score: float = 0.0
    evidence: Optional[str] = None


class FraudAlert(BaseModel):
    alert_id: UUID = Field(default_factory=uuid4)
    alert_number: str
    fraud_type: FraudType
    severity: FraudAlertSeverity
    status: FraudAlertStatus = FraudAlertStatus.NEW

    customer_id: str
    account_id: Optional[str] = None
    transaction_id: Optional[str] = None

    title: str
    description: str
    fraud_score: float = Field(ge=0, le=100)

    indicators: List[FraudIndicator] = Field(default_factory=list)
    detection_method: str
    detection_rule_id: Optional[str] = None
    ml_model_id: Optional[str] = None

    transaction_amount: Optional[float] = None
    potential_loss: float = 0.0

    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[Dict[str, Any]] = None

    assigned_to: Optional[str] = None
    case_id: Optional[UUID] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FraudAlertSummary(BaseModel):
    alert_id: UUID
    alert_number: str
    fraud_type: FraudType
    severity: FraudAlertSeverity
    status: FraudAlertStatus
    customer_id: str
    fraud_score: float
    potential_loss: float
    created_at: datetime
    assigned_to: Optional[str] = None


class FraudAlertStatistics(BaseModel):
    total_alerts: int = 0
    by_severity: Dict[str, int] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_fraud_type: Dict[str, int] = Field(default_factory=dict)
    confirmed_fraud_count: int = 0
    false_positive_count: int = 0
    total_potential_loss: float = 0.0
    total_confirmed_loss: float = 0.0
    average_fraud_score: float = 0.0


class FraudAlertCreateRequest(BaseModel):
    fraud_type: FraudType
    severity: FraudAlertSeverity
    customer_id: str
    account_id: Optional[str] = None
    transaction_id: Optional[str] = None
    title: str
    description: str
    fraud_score: float = Field(ge=0, le=100)
    detection_method: str
    transaction_amount: Optional[float] = None


class FraudAlertSearchCriteria(BaseModel):
    fraud_types: Optional[List[FraudType]] = None
    severities: Optional[List[FraudAlertSeverity]] = None
    statuses: Optional[List[FraudAlertStatus]] = None
    customer_ids: Optional[List[str]] = None
    min_fraud_score: Optional[float] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    page_size: int = 50
