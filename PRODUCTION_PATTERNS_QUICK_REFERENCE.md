# Production-Ready Patterns - Quick Reference Guide

Use this quick reference guide to apply the same production-ready patterns to other microservices.

---

## Pattern 1: Secure Password Hashing

### Import
```python
try:
    import bcrypt
except ImportError:
    raise ImportError("bcrypt required: pip install bcrypt")
```

### Class Definition
```python
class PasswordManager:
    """Manages password hashing and verification."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password

        Raises:
            ValueError: If hashing fails
        """
        try:
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error("Password hashing failed", error=str(e))
            raise ValueError("Password hashing failed") from e

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Verify password against hash.

        Args:
            password: Plain text password
            hashed: Hashed password

        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error("Password verification failed", error=str(e))
            return False
```

### Usage
```python
# Hashing
password_hash = password_manager.hash_password(user_password)

# Verification
if not password_manager.verify_password(user_password, password_hash):
    logger.warning("Password verification failed", user_id=user_id)
    raise InvalidCredentialsError("Invalid password")
```

---

## Pattern 2: Input Validation with Pydantic

### Import
```python
from pydantic import BaseModel, EmailStr, validator, ValidationError as PydanticValidationError
```

### Schema Definition
```python
class UserUpdateRequest(BaseModel):
    """User update request with validation."""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @validator('phone')
    def validate_phone(cls, v):
        if v is not None and (len(v) < 10 or len(v) > 15):
            raise ValueError('Phone must be 10-15 characters')
        return v

    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError('Name must be 100 characters or less')
        return v
```

### Exception Handler
```python
@app.exception_handler(PydanticValidationError)
async def validation_exception_handler(request: Request, exc: PydanticValidationError):
    """Handle Pydantic validation errors."""
    logger.warning("Validation error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request data", "errors": exc.errors()}
    )
```

### Endpoint Usage
```python
@app.put("/me", response_model=UserProfileResponse)
async def update_profile(
    request: Request,
    user_update: UserUpdateRequest  # Pydantic validates automatically
) -> UserProfileResponse:
    """Update user profile with validated input."""
    # Pydantic ensures user_update is valid before this code runs
    # All validation exceptions are caught by the handler above
```

---

## Pattern 3: Rate Limiting

### Class Definition
```python
import time

class RateLimiter:
    """Rate limiting with time-window based tracking."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 900):
        self.attempts: Dict[str, list[float]] = {}
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds

    def check_limit(self, key: str) -> bool:
        """Check if rate limit exceeded."""
        now = time.time()
        if key in self.attempts:
            self.attempts[key] = [
                t for t in self.attempts[key]
                if now - t < self.window_seconds
            ]
        if key not in self.attempts:
            return False
        return len(self.attempts[key]) >= self.max_attempts

    def record_attempt(self, key: str) -> None:
        """Record an attempt."""
        now = time.time()
        if key not in self.attempts:
            self.attempts[key] = []
        self.attempts[key].append(now)

    def clear_attempts(self, key: str) -> None:
        """Clear tracking on success."""
        if key in self.attempts:
            del self.attempts[key]
```

### Usage
```python
rate_limiter = RateLimiter(max_attempts=5, window_seconds=900)  # 5/15min

@app.post("/expensive-operation")
async def expensive_operation(request: Request, data: ExpensiveRequest):
    user_id = extract_user_id(request)

    if rate_limiter.check_limit(f"user:{user_id}"):
        logger.warning("Rate limit exceeded", user_id=user_id)
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    try:
        # Perform expensive operation
        result = await perform_operation(data)
        rate_limiter.clear_attempts(f"user:{user_id}")
        return result
    except Exception:
        rate_limiter.record_attempt(f"user:{user_id}")
        raise
```

---

## Pattern 4: Comprehensive Error Handling

### Custom Exception Hierarchy
```python
class ServiceError(Exception):
    """Base exception for service."""
    pass

class ValidationError(ServiceError):
    """Validation failed."""
    pass

class AuthenticationError(ServiceError):
    """Authentication failed."""
    pass

class NotFoundError(ServiceError):
    """Resource not found."""
    pass

class ExternalServiceError(ServiceError):
    """External service error."""
    pass
```

### Exception Handlers
```python
@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    logger.warning("Validation error", error=str(exc))
    return JSONResponse(status_code=400, content={"detail": str(exc)})

@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    logger.warning("Authentication error", error=str(exc))
    return JSONResponse(status_code=401, content={"detail": str(exc)})

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    logger.warning("Resource not found", error=str(exc))
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(ExternalServiceError)
async def external_error_handler(request: Request, exc: ExternalServiceError):
    logger.error("External service error", error=str(exc))
    return JSONResponse(status_code=503, content={"detail": "Service unavailable"})

@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    logger.error("Unexpected error", error=str(exc), error_type=type(exc).__name__)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

### Endpoint with Error Handling
```python
@app.post("/operation")
async def operation(request: Request, data: OperationRequest):
    """Perform operation with comprehensive error handling."""
    try:
        # Input validation
        if not data.value:
            raise ValidationError("Value is required")

        # Business logic with error handling
        try:
            result = await external_service.call(data)
        except asyncio.TimeoutError:
            logger.error("External service timeout")
            raise ExternalServiceError("External service timeout")
        except Exception as e:
            logger.error("External service error", error=str(e))
            raise ExternalServiceError(f"External service error: {str(e)}")

        # Check result
        if not result:
            raise NotFoundError("Result not found")

        logger.info("Operation completed", result_id=result.id)
        return result

    except (ValidationError, AuthenticationError, NotFoundError, ExternalServiceError):
        # These are handled by exception handlers above
        raise
    except Exception as e:
        logger.error("Unexpected error in operation", error=str(e), error_type=type(e).__name__)
        raise
```

---

## Pattern 5: Security Context Tracking

### Class Definition
```python
class SecurityContext:
    """Tracks security context for request."""

    def __init__(self, request: Request):
        self.ip_address = self._extract_ip(request)
        self.user_agent = request.headers.get("user-agent", "unknown")
        self.correlation_id = get_correlation_id()
        self.timestamp = datetime.utcnow().isoformat()

    @staticmethod
    def _extract_ip(request: Request) -> str:
        """Extract IP handling reverse proxies."""
        if forwarded := request.headers.get("x-forwarded-for"):
            return forwarded.split(",")[0].strip()
        if real_ip := request.headers.get("x-real-ip"):
            return real_ip
        return str(request.client.host) if request.client else "unknown"
```

### Usage
```python
@app.post("/sensitive-operation")
async def sensitive_operation(request: Request, data: SensitiveRequest):
    security_context = SecurityContext(request)

    try:
        # Log with security context
        logger.info(
            "Sensitive operation started",
            ip=security_context.ip_address,
            user_agent=security_context.user_agent,
            correlation_id=security_context.correlation_id
        )

        # Perform operation
        result = await perform_operation(data)

        logger.info(
            "Sensitive operation completed",
            ip=security_context.ip_address,
            result_id=result.id
        )
        return result

    except Exception as e:
        logger.error(
            "Sensitive operation failed",
            error=str(e),
            ip=security_context.ip_address,
            correlation_id=security_context.correlation_id
        )
        raise
```

---

## Pattern 6: Structured Logging

### Configuration
```python
import logging
from ..core.correlation_id import StructuredLogger, get_correlation_id

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger_instance = logging.getLogger(__name__)
logger = StructuredLogger(logger_instance)
```

### Usage Examples
```python
# Info log with context
logger.info(
    "User operation",
    user_id=user.id,
    username=user.username,
    action="login",
    ip=security_context.ip_address
)

# Warning log (security relevant)
logger.warning(
    "Failed authentication attempt",
    username=credentials.username,
    ip=security_context.ip_address,
    reason="invalid_password",
    attempt_number=failed_count
)

# Error log with details
logger.error(
    "Database operation failed",
    operation="save_user",
    error=str(e),
    error_type=type(e).__name__,
    user_id=user_id
)

# Debug log
logger.debug(
    "Processing request",
    path=request.url.path,
    method=request.method
)
```

---

## Pattern 7: Type Hints

### Function with Full Type Hints
```python
from typing import Dict, Any, Optional, List

def process_data(
    data: Dict[str, Any],
    filter_key: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Process data with filtering.

    Args:
        data: Input data dictionary
        filter_key: Optional filter key
        limit: Result limit

    Returns:
        List of filtered data dictionaries

    Raises:
        ValueError: If data is invalid
    """
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")

    filtered = []
    for key, value in data.items():
        if filter_key and filter_key not in key:
            continue
        filtered.append({"key": key, "value": value})
        if len(filtered) >= limit:
            break

    return filtered
```

### Async Function Type Hints
```python
async def fetch_user(
    user_id: int,
    timeout_seconds: float = 5.0
) -> Optional[User]:
    """
    Fetch user with timeout.

    Args:
        user_id: User ID to fetch
        timeout_seconds: Operation timeout

    Returns:
        User object or None if not found

    Raises:
        asyncio.TimeoutError: If operation times out
    """
    try:
        return await asyncio.wait_for(
            db.users.get(user_id),
            timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        logger.error("User fetch timeout", user_id=user_id)
        raise
```

---

## Pattern 8: Comprehensive Docstrings

### Google-Style Docstring
```python
def calculate_total(
    items: List[float],
    tax_rate: float = 0.1,
    discount: float = 0.0
) -> float:
    """
    Calculate total price with tax and discount.

    Calculates the total by summing all items, applying discount,
    then adding tax. Tax is calculated on discounted amount.

    Args:
        items: List of item prices
        tax_rate: Tax rate as decimal (0.1 = 10%), defaults to 10%
        discount: Discount as decimal (0.1 = 10% off), defaults to 0%

    Returns:
        Total price as float

    Raises:
        ValueError: If items is empty or tax_rate/discount invalid
        TypeError: If items contains non-numeric values

    Example:
        >>> items = [10.0, 20.0, 30.0]
        >>> calculate_total(items, tax_rate=0.1, discount=0.1)
        56.7

    Note:
        - Discount is applied before tax
        - Negative prices are not allowed
        - Results are rounded to 2 decimal places for currency

    See Also:
        calculate_item_total: Calculate total for single item
    """
    if not items:
        raise ValueError("Items list cannot be empty")
    if not (0 <= tax_rate <= 1):
        raise ValueError("Tax rate must be between 0 and 1")
    if not (0 <= discount <= 1):
        raise ValueError("Discount must be between 0 and 1")

    subtotal = sum(float(item) for item in items)
    after_discount = subtotal * (1 - discount)
    total = after_discount * (1 + tax_rate)

    return round(total, 2)
```

---

## Pattern 9: Complete Endpoint Template

```python
@app.post("/resource", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    request: Request,
    resource_data: ResourceCreateRequest
) -> ResourceResponse:
    """
    Create a new resource.

    Args:
        request: HTTP request with security context
        resource_data: Resource creation data (Pydantic validated)

    Returns:
        ResourceResponse with created resource

    Raises:
        HTTPException: 400 if validation fails
        HTTPException: 409 if resource already exists
        HTTPException: 500 if database error occurs
    """
    security_context = SecurityContext(request)

    try:
        # Validate input (Pydantic already did basic validation)
        if not resource_data.name or len(resource_data.name) < 1:
            logger.warning("Invalid resource name", ip=security_context.ip_address)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resource name is required"
            )

        # Check for duplicates
        async with db_lock:
            if await db.resources.exists_by_name(resource_data.name):
                logger.warning(
                    "Resource already exists",
                    name=resource_data.name,
                    ip=security_context.ip_address
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Resource with this name already exists"
                )

            # Create resource
            resource = await db.resources.create(resource_data)

        logger.info(
            "Resource created",
            resource_id=resource.id,
            name=resource_data.name,
            ip=security_context.ip_address
        )

        return ResourceResponse(**resource.dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Resource creation failed",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resource creation failed"
        )
```

---

## Checklist for Production-Ready Service

- [ ] Bcrypt for password hashing (12 rounds)
- [ ] Pydantic schemas with validators on all inputs
- [ ] Rate limiting on sensitive operations
- [ ] Custom exception hierarchy
- [ ] Comprehensive exception handlers
- [ ] Security context tracking (IP, correlation ID)
- [ ] Structured logging throughout
- [ ] Full type hints on all functions
- [ ] Comprehensive docstrings (Google style)
- [ ] Try-catch on all external calls
- [ ] Async/await for I/O operations
- [ ] Thread-safe operations
- [ ] Graceful shutdown handling
- [ ] Health check endpoints
- [ ] Comprehensive test suite (100% coverage)
- [ ] Performance benchmarks

---

## Running Tests

```bash
# Install dependencies
pip install pytest pytest-asyncio bcrypt pydantic

# Run all tests
pytest services/tests/ -v

# Run with coverage
pytest services/tests/ --cov=services --cov-report=html

# Run specific test class
pytest services/tests/test_service.py::TestClassName -v

# Run with performance analysis
pytest services/tests/ -v --durations=10
```

---

**Apply these patterns to all services for consistent production-grade quality.**
