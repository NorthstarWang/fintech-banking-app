"""
Request ID middleware for request tracking and correlation.
"""
import logging
import time
import uuid

from fastapi import Request

logger = logging.getLogger(__name__)


async def request_id_middleware(request: Request, call_next):
    """
    Add a unique request ID to each request for tracking.
    Also logs request/response timing.
    """
    # Generate or get request ID
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    # Store request ID in request state
    request.state.request_id = request_id

    # Start timing
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Add headers to response
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)

    # Log request details
    logger.info(
        "Request processed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": process_time,
            "client_host": request.client.host if request.client else None
        }
    )

    return response
