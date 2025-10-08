"""
Production-ready error handling middleware.
"""
import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """
    Global error handler middleware that catches all exceptions
    and returns appropriate error responses.
    """
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        return await handle_exception(request, exc)


async def handle_exception(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle different types of exceptions and return appropriate responses.
    """
    # FastAPI HTTPException
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.detail,
                    "type": "http_error",
                    "status_code": exc.status_code
                }
            }
        )

    # Pydantic validation error
    if isinstance(exc, (RequestValidationError, ValidationError)):
        errors = []
        if isinstance(exc, RequestValidationError):
            for error in exc.errors():
                errors.append({
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                })
        else:
            for error in exc.errors():
                errors.append({
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                })

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "message": "Validation error",
                    "type": "validation_error",
                    "details": errors
                }
            }
        )

    # Generic exception
    # Log the full exception with traceback
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {exc!s}",
        exc_info=True,
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "path": request.url.path,
            "method": request.method
        }
    )

    # In production, don't expose internal errors
    error_message = "An internal error occurred"
    if hasattr(request.app.state, "debug") and request.app.state.debug:
        error_message = str(exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": error_message,
                "type": "internal_error",
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


def register_exception_handlers(app):
    """
    Register exception handlers for the FastAPI application.
    """
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return await handle_exception(request, exc)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return await handle_exception(request, exc)

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return await handle_exception(request, exc)
