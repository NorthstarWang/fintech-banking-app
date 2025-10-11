"""
Notification Service FastAPI Application.

Provides email, SMS, and push notification capabilities.
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List

from ..core.correlation_id import CorrelationIDMiddleware, StructuredLogger
from ..core.health_check import ServiceHealthChecker
from ..core.service_registry import get_registry, init_registry
from .models import (
    SendNotificationRequest,
    NotificationResponse,
    NotificationStatus,
    BatchNotificationRequest,
    GetNotificationsRequest
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger_instance = logging.getLogger(__name__)
logger = StructuredLogger(logger_instance)

# Initialize service
app = FastAPI(
    title="Notification Service",
    description="Handles email, SMS, and push notifications",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware, service_name="notification-service")

# Initialize service components
registry = init_registry()
health_checker = ServiceHealthChecker("notification-service")

# Register health checks
health_checker.register_callable_check(
    "notification_service_ready",
    lambda: True,
    "Check if notification service is ready"
)

# In-memory storage for demo (replace with database in production)
notifications: Dict[str, dict] = {}
user_notifications: Dict[int, List[str]] = {}


async def send_email(recipient: str, subject: str, body: str) -> bool:
    """Send email notification."""
    # TODO: Integrate with email service (SendGrid, AWS SES, etc.)
    logger.info(f"Sending email", recipient=recipient, subject=subject)
    return True


async def send_sms(recipient: str, body: str) -> bool:
    """Send SMS notification."""
    # TODO: Integrate with SMS service (Twilio, AWS SNS, etc.)
    logger.info(f"Sending SMS", recipient=recipient, body=body)
    return True


async def send_push(device_token: str, subject: str, body: str) -> bool:
    """Send push notification."""
    # TODO: Integrate with push notification service (Firebase, etc.)
    logger.info(f"Sending push notification", device_token=device_token, subject=subject)
    return True


@app.on_event("startup")
async def startup():
    """Initialize service on startup."""
    logger.info("Notification Service starting up", service="notification-service")

    # Register this service instance with the registry
    registry.register(
        service_name="notification-service",
        instance_id=os.getenv("SERVICE_INSTANCE_ID", "notification-1"),
        host=os.getenv("SERVICE_HOST", "localhost"),
        port=int(os.getenv("SERVICE_PORT", "8002")),
        health_check_url="/health",
        api_key=os.getenv("NOTIFICATION_SERVICE_API_KEY", "notification-key-dev"),
        metadata={"version": "1.0.0"}
    )


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    logger.info("Notification Service shutting down", service="notification-service")
    registry.deregister(
        "notification-service",
        os.getenv("SERVICE_INSTANCE_ID", "notification-1")
    )


@app.post("/health")
async def health_check():
    """Health check endpoint."""
    health_status = await health_checker.run_all_checks()
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(health_status, status_code=status_code)


@app.post("/send", response_model=NotificationResponse)
async def send_notification(request: Request, notif: SendNotificationRequest):
    """Send a notification to a user."""
    notification_id = str(uuid.uuid4())
    now = datetime.utcnow()

    try:
        # Route to appropriate sender based on type
        if notif.notification_type.value == "email":
            success = await send_email(notif.recipient, notif.subject or "", notif.body)
        elif notif.notification_type.value == "sms":
            success = await send_sms(notif.recipient, notif.body)
        elif notif.notification_type.value == "push":
            success = await send_push(notif.recipient, notif.subject or "", notif.body)
        else:
            success = False

        # Store notification record
        notification = {
            "id": notification_id,
            "user_id": notif.user_id,
            "notification_type": notif.notification_type.value,
            "status": NotificationStatus.SENT.value if success else NotificationStatus.FAILED.value,
            "sent_at": now,
            "delivered_at": now if success else None,
            "error_message": None if success else "Failed to send"
        }

        notifications[notification_id] = notification

        # Track for user
        if notif.user_id not in user_notifications:
            user_notifications[notif.user_id] = []
        user_notifications[notif.user_id].append(notification_id)

        logger.info(
            f"Notification sent",
            notification_id=notification_id,
            user_id=notif.user_id,
            type=notif.notification_type.value
        )

        return NotificationResponse(**notification)

    except Exception as e:
        logger.error(
            f"Failed to send notification",
            notification_id=notification_id,
            user_id=notif.user_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )


@app.post("/send-batch")
async def send_batch_notifications(request: Request, batch: BatchNotificationRequest):
    """Send notifications to multiple users."""
    results = []

    for user_id in batch.user_ids:
        # In production, this would queue these for async processing
        # For now, we'll just send them sequentially
        notif = SendNotificationRequest(
            user_id=user_id,
            notification_type=batch.notification_type,
            recipient=f"user_{user_id}@example.com",  # Mock recipient
            subject=batch.subject,
            body=batch.body,
            metadata=batch.metadata
        )

        try:
            result = await send_notification(request, notif)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to send batch notification to user {user_id}: {str(e)}")
            continue

    logger.info(f"Batch notifications sent", count=len(results), total=len(batch.user_ids))

    return {
        "sent": len(results),
        "total": len(batch.user_ids),
        "notifications": results
    }


@app.get("/user/{user_id}")
async def get_user_notifications(
    user_id: int,
    limit: int = 20,
    offset: int = 0
):
    """Get notifications for a user."""
    notif_ids = user_notifications.get(user_id, [])

    # Paginate
    paginated_ids = notif_ids[offset:offset + limit]

    result = [
        notifications[notif_id]
        for notif_id in paginated_ids
        if notif_id in notifications
    ]

    logger.info(
        f"Retrieved user notifications",
        user_id=user_id,
        count=len(result),
        total=len(notif_ids)
    )

    return {
        "user_id": user_id,
        "count": len(result),
        "total": len(notif_ids),
        "notifications": result
    }


@app.get("/notification/{notification_id}")
async def get_notification(notification_id: str):
    """Get a specific notification."""
    notification = notifications.get(notification_id)

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    return notification


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("SERVICE_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVICE_PORT", "8002"))
    )
