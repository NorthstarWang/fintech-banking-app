# Production Code Quality Roadmap

Complete plan to bring all microservices to enterprise production standards.

**Timeline**: 3-4 weeks
**Current Status**: 0% → **Target**: 100% production-ready

---

## Phase 1: Week 1 - Critical Security Fixes

### 1.1 Password Security (ALL SERVICES)

**❌ Current Implementation**:
```python
password_hash = hash(user_data.password)  # INSECURE!
```

**✅ Production Implementation**:
```python
import bcrypt

password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
verified = bcrypt.checkpw(password.encode('utf-8'), password_hash)
```

**Files to Update**:
- [ ] `services/auth_service/app.py` → Use `app_production.py` as template
- [ ] `services/token_manager.py` → Add bcrypt integration
- [ ] All password-handling code

**Testing**:
- [ ] Write 15+ tests for password hashing
- [ ] Test bcrypt salt generation
- [ ] Test password verification
- [ ] Performance test (should take ~250ms per hash)

---

### 1.2 Input Validation (ALL SERVICES)

**❌ Current Implementation**:
```python
@app.put("/me")
async def update_profile(user_update: dict):  # ❌ No schema!
    setattr(user, field, user_update[field])  # ❌ Direct access
```

**✅ Production Implementation**:
```python
from pydantic import BaseModel, EmailStr, validator

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    @validator('first_name')
    def validate_first_name(cls, v):
        if v is not None and (len(v) < 1 or len(v) > 100):
            raise ValueError('First name must be 1-100 characters')
        return v

@app.put("/me")
async def update_profile(update: UserUpdate):  # ✅ Schema validated
    if update.first_name:
        user.first_name = update.first_name
```

**Files to Update**:
- [ ] `services/auth_service/models.py` → Add validators
- [ ] `services/notification_service/models.py` → Add validators
- [ ] `services/account_service/models.py` → Add validators
- [ ] All input-receiving endpoints

**Testing**:
- [ ] Test each validator with valid data
- [ ] Test with boundary values
- [ ] Test with malicious input
- [ ] Test error messages

---

### 1.3 Rate Limiting (Auth Service)

**✅ Implementation Required**:
```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.util import get_remote_address

@app.post("/login")
@limiter.limit("5/15minutes")
async def login(request: Request, credentials: UserLoginRequest):
    # Track failed attempts
    if not verify_credentials(credentials):
        increment_failed_attempts(credentials.username)
        raise HTTPException(status_code=401)
```

**Files to Create/Update**:
- [ ] `services/auth_service/rate_limiter.py` → Rate limiting logic
- [ ] `services/auth_service/app.py` → Integrate rate limiting
- [ ] Add `fastapi-limiter` to requirements.txt

**Testing**:
- [ ] Test allowing valid attempts (< 5)
- [ ] Test blocking on 5th attempt
- [ ] Test time-window expiration
- [ ] Test per-IP vs per-username tracking

---

### 1.4 Environment Variable Validation (ALL SERVICES)

**❌ Current Implementation**:
```python
port = int(os.getenv("SERVICE_PORT", "8001"))  # Could crash if invalid
api_key = os.getenv("AUTH_SERVICE_API_KEY", "auth-key-dev")  # ❌ Defaults to dev key!
```

**✅ Production Implementation**:
```python
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    service_port: int
    service_host: str
    auth_service_api_key: str  # ❌ No default!
    jwt_secret_key: str

    @validator('service_port')
    def validate_port(cls, v):
        if v <= 0 or v >= 65536:
            raise ValueError('Invalid port number')
        return v

    @validator('auth_service_api_key', 'jwt_secret_key')
    def validate_secrets(cls, v):
        if not v or v.startswith('dev-'):
            raise ValueError('Production API key required')
        return v

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()  # Raises on startup if invalid
```

**Files to Create/Update**:
- [ ] `services/core/config.py` → Centralized configuration
- [ ] `services/auth_service/app.py` → Use settings
- [ ] All services → Use centralized config

**Testing**:
- [ ] Test with missing required env vars
- [ ] Test with invalid port numbers
- [ ] Test with dev API keys (should fail)
- [ ] Test loading from .env file

---

## Phase 2: Week 2 - Error Handling & Logging

### 2.1 Comprehensive Error Handling

**❌ Current Implementation**:
```python
user = db_session.query(User).filter(...)  # ❌ What if DB is down?
response.set_cookie(...)  # ❌ What if fails?
```

**✅ Production Implementation**:
```python
from contextlib import asynccontextmanager

class DatabaseError(Exception):
    """Database operation failed."""
    pass

async def get_user_safely(user_id: int) -> Optional[User]:
    """
    Get user with comprehensive error handling.

    Args:
        user_id: User ID to fetch

    Returns:
        User object or None if not found

    Raises:
        DatabaseError: If database operation fails
        Exception: For unexpected errors
    """
    try:
        user = await db.users.find_by_id(user_id)
        return user

    except TimeoutError as e:
        logger.error("Database timeout", user_id=user_id)
        raise DatabaseError("Database operation timed out") from e

    except ConnectionError as e:
        logger.error("Database connection failed", user_id=user_id)
        raise DatabaseError("Database connection failed") from e

    except Exception as e:
        logger.error("Unexpected database error", error=str(e), user_id=user_id)
        raise
```

**Files to Update**:
- [ ] All service `app.py` files
- [ ] All database operations
- [ ] All external API calls
- [ ] All file operations

**Testing**:
- [ ] Test normal success path
- [ ] Test timeout scenarios
- [ ] Test connection failures
- [ ] Test invalid input
- [ ] Test partial failures

---

### 2.2 Structured Logging (ALL SERVICES)

**❌ Current Implementation**:
```python
logger.info(f"User registered")  # No context!
```

**✅ Production Implementation**:
```python
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# Log with context
logger.info(
    "User registered",
    extra={
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "ip_address": security_context.ip_address,
        "user_agent": security_context.user_agent,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "auth-service"
    }
)

# For failed login (security event)
logger.warning(
    "Failed login attempt",
    extra={
        "username": credentials.username,
        "ip_address": security_context.ip_address,
        "reason": "invalid_password",
        "attempt_number": failed_attempt_count,
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

**Files to Create/Update**:
- [ ] `services/core/logging_config.py` → Centralized logging
- [ ] All service `app.py` files → Add logging throughout
- [ ] Update requirements.txt → Add python-json-logger

**Testing**:
- [ ] Verify JSON format output
- [ ] Test context inclusion
- [ ] Test log levels
- [ ] Test correlation ID propagation

---

## Phase 3: Week 3 - Comprehensive Testing

### 3.1 Create Test Infrastructure

**Files to Create**:
- [ ] `services/tests/conftest.py` → Pytest fixtures
- [ ] `services/tests/fixtures/` → Test data
- [ ] `services/tests/mocks/` → Mock objects
- [ ] `services/tests/factories/` → Test object factories

**Test Structure**:
```
services/tests/
├── conftest.py                    # Shared fixtures
├── fixtures/
│   ├── users.json               # Sample user data
│   ├── transactions.json         # Sample transactions
│   └── tokens.json              # Sample JWT tokens
├── mocks/
│   ├── mock_database.py        # Database mock
│   ├── mock_external_api.py   # API mock
│   └── mock_cache.py           # Cache mock
├── unit/
│   ├── test_auth_service.py    # 100+ tests
│   ├── test_circuit_breaker.py # Circuit breaker tests
│   ├── test_saga.py            # Saga pattern tests
│   └── ...
├── integration/
│   ├── test_auth_flow.py       # End-to-end auth
│   ├── test_service_discovery.py
│   └── ...
├── security/
│   ├── test_password_security.py
│   ├── test_input_validation.py
│   └── test_injection_attacks.py
└── performance/
    ├── test_load.py
    ├── test_stress.py
    └── test_concurrent_access.py
```

### 3.2 Unit Test Coverage (100% branch coverage)

**Each service needs**:
- [ ] 50-100+ unit tests
- [ ] Cover all branches and error paths
- [ ] Test with valid data
- [ ] Test with invalid data
- [ ] Test edge cases
- [ ] Test error conditions

**Example Target for Auth Service**:
```
functions:           15/15 (100%)
branches:            42/42 (100%)
lines:              285/285 (100%)
```

**Files to Create**:
- [ ] `services/tests/unit/test_auth_service.py` → 80+ tests
- [ ] `services/tests/unit/test_circuit_breaker.py` → 30+ tests
- [ ] `services/tests/unit/test_saga.py` → 40+ tests
- [ ] Similar for each service

### 3.3 Integration Tests

**Test Scenarios**:
- [ ] Service-to-service communication
- [ ] Request routing through gateway
- [ ] Saga pattern execution
- [ ] Failure recovery
- [ ] Database transactions
- [ ] Cache invalidation

### 3.4 Security Tests

**Test Cases**:
- [ ] SQL injection attempts
- [ ] XSS payload injection
- [ ] CSRF attacks
- [ ] Brute force attempts
- [ ] Malformed requests
- [ ] Buffer overflows
- [ ] Timing attacks

### 3.5 Performance Tests

**Benchmarks**:
- [ ] Password hashing: < 250ms
- [ ] Rate limit check: < 1ms
- [ ] Token generation: < 5ms
- [ ] Service discovery: < 10ms
- [ ] API call with retry: < 500ms

---

## Phase 4: Week 4 - Documentation & Type Hints

### 4.1 Add Type Hints Throughout

**❌ Current**:
```python
async def register(request, user_data):
    user = db_session.query(User).filter(...)
    return user
```

**✅ Production**:
```python
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

async def register(
    request: Request,
    user_data: UserRegistrationRequest,
    db_session: Session = Depends(get_db)
) -> UserProfileResponse:
    """Register a new user."""
    user: User = db_session.query(User).filter(...).first()
    return UserProfileResponse.from_orm(user)
```

**Coverage Target**: 95%+ of functions have type hints

### 4.2 Add Comprehensive Docstrings

**Format**: Google-style docstrings

```python
def hash_password(password: str) -> str:
    """
    Hash password using bcrypt with configurable rounds.

    Uses bcrypt with 12 rounds, which provides a good balance between
    security and performance. Should complete in approximately 250ms.

    Args:
        password: Plain text password to hash (1-255 characters)

    Returns:
        bcrypt hash string suitable for storage in database

    Raises:
        ValueError: If hashing fails (e.g., invalid input)
        RuntimeError: If bcrypt library unavailable

    Example:
        >>> hashed = hash_password("SecurePass123!")
        >>> verify_password("SecurePass123!", hashed)
        True

    Security Notes:
        - Never store plain text passwords
        - Always compare hashes using constant-time comparison
        - Use 12+ rounds for production
    """
    ...
```

**Coverage Target**: 95%+ of functions have docstrings

### 4.3 Create API Documentation

**Tools**: FastAPI auto-docs + custom guides

- [ ] OpenAPI/Swagger documentation
- [ ] Authentication flow diagrams
- [ ] Error response catalog
- [ ] Rate limit documentation
- [ ] Example requests/responses

---

## Quality Metrics Dashboard

### Before & After

```
Metric                    Before    Target    Deadline
─────────────────────────────────────────────────────
Test Coverage             0%        100%      Week 3
Type Hints                50%       95%       Week 4
Docstring Coverage        30%       95%       Week 4
Error Handling            20%       100%      Week 2
Input Validation          15%       100%      Week 1
Security Issues           8         0         Week 1
Code Smells               50+       0         Week 2
Performance Issues        5         0         Week 3
```

---

## Checklist for Each Service

### Authentication Service

- [ ] Replace `hash()` with bcrypt
- [ ] Add rate limiting
- [ ] Add comprehensive input validation
- [ ] Implement error handling
- [ ] Add structured logging
- [ ] Write 100+ unit tests
- [ ] Write 20+ integration tests
- [ ] Write 15+ security tests
- [ ] Add type hints to all functions
- [ ] Add docstrings to all functions
- [ ] Performance tests all major operations
- [ ] Security audit complete

### Circuit Breaker

- [ ] Test all state transitions
- [ ] Test concurrent access
- [ ] Handle edge cases
- [ ] Write 40+ unit tests
- [ ] Performance tests
- [ ] Thread safety verification

### Saga Pattern

- [ ] Test happy path
- [ ] Test failure scenarios
- [ ] Test compensation logic
- [ ] Test retry logic
- [ ] Write 50+ unit tests
- [ ] Test concurrent sagas

### Other Services

Apply same template to:
- [ ] Notification Service
- [ ] Analytics Service
- [ ] Transaction Service
- [ ] Account Service
- [ ] Payment Service
- [ ] Risk Service

---

## Running Tests

### Install dependencies
```bash
pip install pytest pytest-cov pytest-asyncio python-json-logger bcrypt fastapi-limiter pydantic
```

### Run all tests with coverage
```bash
pytest services/tests/ --cov=services --cov-report=html --cov-report=term
```

### Run specific test file
```bash
pytest services/tests/unit/test_auth_service.py -v
```

### Run with specific coverage threshold
```bash
pytest services/tests/ --cov=services --cov-fail-under=100
```

### Generate coverage HTML report
```bash
pytest services/tests/ --cov=services --cov-report=html
open htmlcov/index.html
```

---

## Definition of Done

Each service is production-ready when it meets:

- ✅ 100% branch coverage (tests)
- ✅ 0 security vulnerabilities (audit passed)
- ✅ 100% error handling (all paths covered)
- ✅ 95%+ type hints
- ✅ 95%+ docstring coverage
- ✅ Structured logging throughout
- ✅ All validation implemented
- ✅ Performance benchmarks met
- ✅ Security tests passing
- ✅ Load tested (1000+ req/sec)
- ✅ Code review passed
- ✅ Documentation complete

---

## Deployment Gates

✅ **Pre-production Gate 1** (After Week 1)
- No security vulnerabilities
- All input validated
- Rate limiting in place

✅ **Pre-production Gate 2** (After Week 2)
- 80%+ test coverage
- Comprehensive error handling
- Structured logging

✅ **Pre-production Gate 3** (After Week 3)
- 100% test coverage
- All performance targets met
- Load tests passing

✅ **Production Gate** (After Week 4)
- All above + documentation complete
- Type hints 95%+
- Docstrings 95%+
- Security audit passed
- Performance audit passed
- Team sign-off obtained

---

## Success Criteria

**Week 1**: ✅ All security issues resolved
**Week 2**: ✅ 80% test coverage, comprehensive logging
**Week 3**: ✅ 100% test coverage, all performance targets met
**Week 4**: ✅ Full documentation, ready for production

