"""Transaction service data models."""
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional


class TransactionType(str, Enum):
    """Types of transactions."""
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"
    PAYMENT = "payment"


class TransactionStatus(str, Enum):
    """Transaction status."""
    INITIATED = "initiated"
    AUTHORIZED = "authorized"
    CLEARED = "cleared"
    SETTLED = "settled"
    FAILED = "failed"
    REVERSED = "reversed"


class InitiateTransactionRequest(BaseModel):
    """Request to initiate transaction."""
    user_id: int
    account_id: int
    transaction_type: TransactionType
    amount: float
    description: str
    metadata: Optional[dict] = None


class TransactionResponse(BaseModel):
    """Transaction response."""
    transaction_id: str
    user_id: int
    account_id: int
    transaction_type: TransactionType
    amount: float
    status: TransactionStatus
    description: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[dict] = None
