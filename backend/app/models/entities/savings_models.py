from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# Import shared enums from data_classes
from ..dto import (
    RoundUpStatus, SavingsRuleType, SavingsRuleFrequency,
    ChallengeStatus, ChallengeType
)


# Request/Response Models
class RoundUpConfigRequest(BaseModel):
    source_account_id: int
    destination_account_id: int
    multiplier: float = Field(default=1.0, ge=1.0, le=10.0)
    max_round_up_amount: Optional[float] = Field(default=10.0, gt=0)
    enabled_categories: Optional[List[int]] = None


class RoundUpConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    source_account_id: int
    destination_account_id: int
    status: RoundUpStatus
    multiplier: float
    max_round_up_amount: Optional[float]
    enabled_categories: Optional[List[int]]
    total_saved: float
    transaction_count: int
    created_at: datetime
    last_round_up_at: Optional[datetime]


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
    amount: Optional[float] = None
    percentage: Optional[float] = Field(default=None, ge=0, le=100)
    frequency: SavingsRuleFrequency
    trigger_conditions: Optional[Dict[str, Any]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SavingsRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    name: str
    rule_type: SavingsRuleType
    source_account_id: int
    destination_account_id: int
    amount: Optional[float]
    percentage: Optional[float]
    frequency: SavingsRuleFrequency
    trigger_conditions: Optional[Dict[str, Any]]
    is_active: bool
    total_saved: float
    execution_count: int
    last_executed_at: Optional[datetime]
    next_execution_at: Optional[datetime]
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
    reward_description: Optional[str]
    rules: List[str]
    leaderboard_position: Optional[int]


class ChallengeJoinRequest(BaseModel):
    commitment_amount: Optional[float] = None
    account_id: int


# Savings Goal Models
class SavingsGoalCreate(BaseModel):
    goal_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    target_amount: float = Field(..., gt=0)
    current_amount: float = 0.0
    target_date: Optional[str] = None
    category: Optional[str] = None
    account_id: Optional[int] = None
    auto_transfer_enabled: Optional[bool] = False
    auto_transfer_amount: Optional[float] = None
    auto_transfer_frequency: Optional[str] = None
    
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