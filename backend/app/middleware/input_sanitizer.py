"""
Input validation and sanitization middleware for banking security.
Prevents XSS, injection attacks, and validates financial data formats.
"""
import re
import json
from typing import Any, Dict, List, Union
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class InputSanitizer:
    """Comprehensive input sanitization for banking application security."""

    def __init__(self):
        # Dangerous patterns to block
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<embed[^>]*>',
            r'<object[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>.*?</style>',
            r'vbscript:',
            r'data:text/html',
            r'expression\(',
            r'@import',
            r'<!\[CDATA\[',
        ]

        # SQL injection patterns (even though we use ORM)
        self.sql_patterns = [
            r'(union\s+select)',
            r'(drop\s+table)',
            r'(insert\s+into)',
            r'(delete\s+from)',
            r'(update\s+\w+\s+set)',
            r'(exec\s*\()',
            r'(script\s*\()',
            r'(\bor\b\s*\d+\s*=\s*\d+)',
            r'(\band\b\s*\d+\s*=\s*\d+)',
            r'(--\s*$)',
            r'(/\*.*?\*/)',
        ]

        # Financial data validation patterns
        self.financial_patterns = {
            'amount': r'^-?\d{1,10}(\.\d{1,2})?$',  # Max 10 digits, 2 decimal places
            'account_number': r'^[A-Z0-9-]{8,20}$',  # Alphanumeric with hyphens
            'routing_number': r'^\d{9}$',  # Exactly 9 digits
            'cvv': r'^\d{3,4}$',  # 3 or 4 digits
            'card_number': r'^\d{13,19}$',  # 13-19 digits
            'phone': r'^\+?[\d\s\-\(\)]{10,20}$',  # International phone format
            'zip_code': r'^[\d\-\s]{5,10}$',  # ZIP codes
        }

        # Safe HTML tags (very limited for banking)
        self.safe_tags = {'b', 'i', 'em', 'strong', 'u'}

        # Maximum lengths for different field types
        self.max_lengths = {
            'username': 50,
            'email': 254,
            'password': 200,
            'name': 100,
            'description': 500,
            'notes': 1000,
            'address': 200,
            'city': 100,
            'institution_name': 100,
            'merchant_name': 100,
        }

    def _is_suspicious_pattern(self, text: str) -> bool:
        """Check if text contains suspicious patterns."""
        if not isinstance(text, str):
            return False

        text_lower = text.lower()

        # Check XSS patterns
        for pattern in self.xss_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                return True

        # Check SQL injection patterns
        for pattern in self.sql_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False

    def _sanitize_string(self, text: str, field_name: str = "") -> str:
        """Sanitize string input by removing dangerous characters."""
        if not isinstance(text, str):
            return str(text)

        # Check for suspicious patterns first
        if self._is_suspicious_pattern(text):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid input detected in field '{field_name}'. Potentially dangerous content blocked."
            )

        # Remove control characters except newline, tab, carriage return
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Check maximum length
        max_len = self.max_lengths.get(field_name, 1000)
        if len(text) > max_len:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field '{field_name}' exceeds maximum length of {max_len} characters."
            )

        return text

    def _validate_financial_field(self, value: str, field_type: str) -> bool:
        """Validate financial field formats."""
        if field_type not in self.financial_patterns:
            return True

        pattern = self.financial_patterns[field_type]
        return bool(re.match(pattern, value))

    def _validate_amount(self, amount: Union[str, int, float]) -> float:
        """Validate and normalize financial amounts."""
        try:
            # Convert to Decimal for precise financial calculations
            decimal_amount = Decimal(str(amount))

            # Check for reasonable ranges
            if decimal_amount < -1000000 or decimal_amount > 1000000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Amount must be between -$1,000,000 and $1,000,000"
                )

            # Round to 2 decimal places for currency
            return float(decimal_amount.quantize(Decimal('0.01')))

        except (InvalidOperation, ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid amount format. Must be a valid number."
            )

    def _sanitize_dict(self, data: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
        """Recursively sanitize dictionary data."""
        sanitized = {}

        for key, value in data.items():
            full_key = f"{parent_key}.{key}" if parent_key else key

            if isinstance(value, str):
                sanitized[key] = self._sanitize_string(value, full_key)

                # Validate specific financial fields
                if key in ['account_number', 'routing_number', 'cvv', 'card_number']:
                    if not self._validate_financial_field(value, key):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid format for field '{key}'"
                        )

            elif isinstance(value, (int, float)) and key in ['amount', 'balance', 'credit_limit', 'target_amount']:
                sanitized[key] = self._validate_amount(value)

            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value, full_key)

            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_dict(item, f"{full_key}[{i}]") if isinstance(item, dict)
                    else self._sanitize_string(str(item), f"{full_key}[{i}]") if isinstance(item, str)
                    else item
                    for i, item in enumerate(value)
                ]

            else:
                sanitized[key] = value

        return sanitized

    async def sanitize_request(self, request: Request) -> None:
        """Sanitize incoming request data."""
        try:
            # Skip sanitization for certain content types
            content_type = request.headers.get("content-type", "")
            if "multipart/form-data" in content_type or "application/octet-stream" in content_type:
                return

            # Only process JSON requests
            if not content_type.startswith("application/json"):
                return

            # Get request body
            body = await request.body()
            if not body:
                return

            # Parse JSON
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON format"
                )

            # Sanitize data
            if isinstance(data, dict):
                sanitized_data = self._sanitize_dict(data)

                # Replace request body with sanitized data
                sanitized_body = json.dumps(sanitized_data).encode()
                request._body = sanitized_body

        except HTTPException:
            raise
        except Exception as e:
            # Log the error but don't break the request
            print(f"Input sanitization error: {e}")

    def validate_email(self, email: str) -> bool:
        """Validate email format with enhanced security checks."""
        if not isinstance(email, str):
            return False

        # Basic length check
        if len(email) > 254:
            return False

        # Enhanced email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False

        # Check for suspicious patterns in email
        if self._is_suspicious_pattern(email):
            return False

        # Additional security checks
        if '..' in email or email.startswith('.') or email.endswith('.'):
            return False

        return True


# Global sanitizer instance
input_sanitizer = InputSanitizer()


async def input_sanitization_middleware(request: Request, call_next):
    """Middleware to sanitize all incoming requests."""
    try:
        # Skip sanitization for certain paths
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/health", "/uploads/"]
        if any(skip_path in str(request.url.path) for skip_path in skip_paths):
            return await call_next(request)

        # Sanitize request
        await input_sanitizer.sanitize_request(request)

        response = await call_next(request)
        return response

    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": "Input validation failed",
                "detail": e.detail,
                "security_alert": "Potentially malicious input blocked"
            }
        )
    except Exception as e:
        print(f"Input sanitization middleware error: {e}")
        return await call_next(request)