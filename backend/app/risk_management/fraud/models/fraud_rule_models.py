"""
Fraud Rule Models

Defines data structures for fraud detection rules.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class RuleType(str, Enum):
    THRESHOLD = "threshold"
    VELOCITY = "velocity"
    PATTERN = "pattern"
    GEOGRAPHIC = "geographic"
    BEHAVIORAL = "behavioral"
    DEVICE = "device"
    TIME_BASED = "time_based"
    COMPOSITE = "composite"


class RuleStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    DEPRECATED = "deprecated"


class RuleAction(str, Enum):
    ALERT = "alert"
    BLOCK = "block"
    CHALLENGE = "challenge"
    REVIEW = "review"
    LOG = "log"


class RuleCondition(BaseModel):
    condition_id: UUID = Field(default_factory=uuid4)
    field: str
    operator: str
    value: Any
    data_type: str = "string"


class FraudRule(BaseModel):
    rule_id: UUID = Field(default_factory=uuid4)
    rule_code: str
    rule_name: str
    rule_type: RuleType
    description: str

    status: RuleStatus = RuleStatus.ACTIVE
    priority: int = 1

    conditions: List[RuleCondition] = Field(default_factory=list)
    logic_expression: str

    action: RuleAction = RuleAction.ALERT
    alert_severity: str = "medium"
    score_weight: float = 1.0

    applicable_channels: List[str] = Field(default_factory=list)
    applicable_products: List[str] = Field(default_factory=list)
    excluded_customers: List[str] = Field(default_factory=list)

    effective_from: datetime = Field(default_factory=datetime.utcnow)
    effective_to: Optional[datetime] = None

    hit_count: int = 0
    last_hit_at: Optional[datetime] = None
    false_positive_rate: float = 0.0

    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    version: int = 1
    parent_rule_id: Optional[UUID] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)


class RuleSet(BaseModel):
    ruleset_id: UUID = Field(default_factory=uuid4)
    ruleset_name: str
    description: str

    rules: List[UUID] = Field(default_factory=list)
    evaluation_mode: str = "all"

    is_active: bool = True
    priority: int = 1

    applicable_channels: List[str] = Field(default_factory=list)

    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RuleEvaluationResult(BaseModel):
    rule_id: UUID
    rule_name: str
    matched: bool
    score: float
    action: RuleAction
    conditions_matched: List[str] = Field(default_factory=list)
    evaluation_time_ms: float = 0.0


class RulePerformanceMetrics(BaseModel):
    rule_id: UUID
    rule_name: str
    total_evaluations: int = 0
    total_hits: int = 0
    hit_rate: float = 0.0
    true_positives: int = 0
    false_positives: int = 0
    false_positive_rate: float = 0.0
    average_evaluation_time_ms: float = 0.0
    period_start: datetime
    period_end: datetime
