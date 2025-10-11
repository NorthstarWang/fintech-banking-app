"""Account service models."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AccountType(str, Enum):
    """Types of accounts."""
    CHECKING = "checking"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    CREDIT = "credit"


class CreateAccountRequest(BaseModel):
    """Request to create account."""
    user_id: int
    account_type: AccountType
    currency: str = "USD"
    description: str = ""


class AccountResponse(BaseModel):
    """Account information."""
    account_id: int
    user_id: int
    account_type: AccountType
    balance: float
    currency: str
    description: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
