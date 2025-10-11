"""Data models for notification service."""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum
from typing import Optional


class NotificationType(str, Enum):
    """Types of notifications."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, Enum):
    """Status of a notification."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


class SendNotificationRequest(BaseModel):
    """Request to send a notification."""
    user_id: int
    notification_type: NotificationType
    recipient: str  # email, phone, or device token
    subject: Optional[str] = None
    body: str
    metadata: Optional[dict] = None


class NotificationResponse(BaseModel):
    """Response for a sent notification."""
    id: str
    user_id: int
    notification_type: NotificationType
    status: NotificationStatus
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None


class BatchNotificationRequest(BaseModel):
    """Request to send notifications to multiple users."""
    notification_type: NotificationType
    subject: Optional[str] = None
    body: str
    user_ids: list[int]
    metadata: Optional[dict] = None


class GetNotificationsRequest(BaseModel):
    """Request to get notifications for a user."""
    user_id: int
    limit: int = 20
    offset: int = 0
