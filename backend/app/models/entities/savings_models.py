from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Import shared enums from data_classes
from ..dto import ChallengeStatus, ChallengeType, RoundUpStatus, SavingsRuleFrequency, SavingsRuleType


# Request/Response Models
class RoundUpConfigRequest(BaseModel):
    source_account_id: int
    destination_account_id: int
    multiplier: float = Field(default=1.0, ge=1.0, le=10.0)
    max_round_up_amount: float | None = Field(default=10.0, gt=0)
    enabled_categories: list[int] | None = None


class RoundUpConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    source_account_id: int
    destination_account_id: int
    status: RoundUpStatus
    multiplier: float
    max_round_up_amount: float | None
    enabled_categories: list[int] | None
    total_saved: float
    transaction_count: int
    created_at: datetime
    last_round_up_at: datetime | None


class RoundUpTransaction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: int
    original_amount: float
    round_up_amount: float
    multiplied_amount: float
    transaction_date: datetime
    merchant_name: str
    category_name: str


class SavingsRuleRequest(BaseModel):
    name: str
    rule_type: SavingsRuleType
    source_account_id: int
    destination_account_id: int
    amount: float | None = None
    percentage: float | None = Field(default=None, ge=0, le=100)
    frequency: SavingsRuleFrequency
    trigger_conditions: dict[str, Any] | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class SavingsRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    rule_type: SavingsRuleType
    source_account_id: int
    destination_account_id: int
    amount: float | None
    percentage: float | None
    frequency: SavingsRuleFrequency
    trigger_conditions: dict[str, Any] | None
    is_active: bool
    total_saved: float
    execution_count: int
    last_executed_at: datetime | None
    next_execution_at: datetime | None
    created_at: datetime


class SavingsChallengeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    challenge_type: ChallengeType
    status: ChallengeStatus
    target_amount: float
    current_amount: float
    progress_percentage: float
    participant_count: int
    start_date: datetime
    end_date: datetime
    reward_description: str | None
    rules: list[str]
    leaderboard_position: int | None


class ChallengeJoinRequest(BaseModel):
    commitment_amount: float | None = None
    account_id: int


# Savings Goal Models
class SavingsGoalCreate(BaseModel):
    goal_name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    target_amount: float = Field(..., gt=0)
    current_amount: float = 0.0
    target_date: str | None = None
    category: str | None = None
    account_id: int | None = None
    auto_transfer_enabled: bool | None = False
    auto_transfer_amount: float | None = None
    auto_transfer_frequency: str | None = None

    @property
    def name(self):
        return self.goal_name


class RoundUpTransactionResponse(BaseModel):
    """Response model for round-up transactions."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    config_id: int
    transaction_id: int
    original_amount: float
    round_up_amount: float
    rounded_amount: float
    created_at: datetime
