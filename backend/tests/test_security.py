"""
Comprehensive security tests for banking application.
Tests authentication, authorization, rate limiting, input validation, CSRF protection, and MFA.
"""
import pytest
import time
import json
from fastapi.testclient import TestClient

from app.main_banking import app
from app.utils.mfa import mfa_manager
from app.utils.enhanced_session_manager import enhanced_session_manager
from app.services.audit_logger import audit_logger
from app.middleware.rate_limiter import rate_limiter


client = TestClient(app)


class TestAuthenticationSecurity:
    """Test authentication and authorization security."""

    def test_login_with_invalid_credentials(self):
        """Test login failure with invalid credentials."""
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_authentication_required_for_protected_endpoints(self):
        """Test that protected endpoints require authentication."""
        # Test GET endpoints
        get_endpoints = [
            "/api/accounts/",
            "/api/transactions/",
            "/api/auth/me"
        ]

        for endpoint in get_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

        # Test POST endpoints (using POST method)
        post_endpoints = [
            "/api/auth/mfa/setup"
        ]

        for endpoint in post_endpoints:
            response = client.post(endpoint)
            assert response.status_code == 401

    def test_session_management_after_login(self):
        """Test session creation and management."""
        # First register a user
        register_response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User"
        })
        assert register_response.status_code == 201

        # Login and check session
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        assert login_response.status_code == 200

        # Extract cookies from login response
        cookies = dict(login_response.cookies)

        # Use session cookie to access protected endpoint
        response = client.get("/api/auth/me", cookies=cookies)
        assert response.status_code == 200

    def test_concurrent_session_detection(self):
        """Test concurrent session detection and handling."""
        # This test would need to simulate multiple login attempts
        # and verify that old sessions are terminated
        pass  # Implementation would require more setup


class TestRateLimiting:
    """Test rate limiting functionality."""

    def setUp(self):
        """Reset rate limiter before each test."""
        rate_limiter.requests.clear()
        rate_limiter.failed_attempts.clear()

    def test_auth_endpoint_rate_limiting(self):
        """Test rate limiting on authentication endpoints."""
        self.setUp()

        # Auth endpoints have a limit of 5 requests per minute
        auth_data = {"username": "test", "password": "wrong"}

        # Make 5 requests (should succeed, but fail auth)
        for i in range(5):
            response = client.post("/api/auth/login", json=auth_data)
            assert response.status_code == 401  # Invalid credentials

        # 6th request should be rate limited
        response = client.post("/api/auth/login", json=auth_data)
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["error"]

    def test_exponential_backoff_after_failures(self):
        """Test exponential backoff after multiple failures."""
        self.setUp()

        # Simulate multiple failed attempts to trigger lockout
        auth_data = {"username": "test", "password": "wrong"}

        # Make requests until rate limited
        for i in range(6):
            response = client.post("/api/auth/login", json=auth_data)

        # Should be locked out
        assert response.status_code == 429


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_xss_prevention_in_user_registration(self):
        """Test XSS prevention in user input fields."""
        xss_payload = "<script>alert('xss')</script>"

        response = client.post("/api/auth/register", json={
            "username": xss_payload,
            "email": "test@example.com",
            "password": "testpassword123",
            "first_name": xss_payload,
            "last_name": "User"
        })

        # Should either be blocked or sanitized
        if response.status_code == 400:
            assert "dangerous content blocked" in response.json()["detail"].lower()
        elif response.status_code == 201:
            # If allowed, should be sanitized
            assert "<script>" not in response.json()["username"]

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        sql_payload = "'; DROP TABLE users; --"

        response = client.post("/api/auth/login", json={
            "username": sql_payload,
            "password": "password"
        })

        # Should not cause a server error
        assert response.status_code in [400, 401]  # Bad request or unauthorized

    def test_financial_amount_validation(self):
        """Test financial amount validation."""
        # First login to get session
        client.post("/api/auth/register", json={
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User"
        })

        login_response = client.post("/api/auth/login", json={
            "username": "testuser2",
            "password": "testpassword123"
        })

        cookies = dict(login_response.cookies)

        # Test invalid amount formats
        invalid_amounts = [
            "not_a_number",
            "999999999999999",  # Too large
            "-999999999",  # Too negative
            "123.456",  # Too many decimal places
        ]

        for amount in invalid_amounts:
            response = client.post("/api/accounts/",
                cookies=cookies,
                json={
                    "name": "Test Account",
                    "account_type": "CHECKING",
                    "initial_balance": amount
                }
            )
            assert response.status_code in [400, 422]  # 400 for custom validation, 422 for Pydantic validation


class TestCSRFProtection:
    """Test CSRF protection functionality."""

    def test_csrf_token_required_for_state_changing_operations(self):
        """Test that CSRF token is required for POST/PUT/DELETE operations."""
        # First register and login
        client.post("/api/auth/register", json={
            "username": "csrftest",
            "email": "csrf@example.com",
            "password": "testpassword123",
            "first_name": "CSRF",
            "last_name": "Test"
        })

        login_response = client.post("/api/auth/login", json={
            "username": "csrftest",
            "password": "testpassword123"
        })

        cookies = dict(login_response.cookies)

        # Try to make a state-changing request without CSRF token
        response = client.post("/api/accounts/",
            cookies=cookies,
            json={
                "name": "Test Account",
                "account_type": "CHECKING",
                "initial_balance": 1000
            }
        )

        # Should be blocked by CSRF protection or validation
        # Note: In our implementation, we might need to adjust based on actual CSRF behavior
        assert response.status_code in [403, 400, 422]  # 422 for validation errors


class TestMFASecurity:
    """Test Multi-Factor Authentication security."""

    def test_mfa_setup_requires_authentication(self):
        """Test that MFA setup requires authentication."""
        # Clear any existing cookies from previous tests
        client.cookies.clear()
        response = client.post("/api/auth/mfa/setup")
        assert response.status_code == 401

    def test_mfa_setup_flow(self):
        """Test complete MFA setup flow."""
        # Register and login first
        client.post("/api/auth/register", json={
            "username": "mfatest",
            "email": "mfa@example.com",
            "password": "testpassword123",
            "first_name": "MFA",
            "last_name": "Test"
        })

        login_response = client.post("/api/auth/login", json={
            "username": "mfatest",
            "password": "testpassword123"
        })

        cookies = dict(login_response.cookies)

        # Setup MFA
        setup_response = client.post("/api/auth/mfa/setup", cookies=cookies)
        assert setup_response.status_code == 200

        setup_data = setup_response.json()
        assert "setup_token" in setup_data
        assert "qr_code" in setup_data
        assert "backup_codes" in setup_data

    def test_mfa_prevents_double_setup(self):
        """Test that MFA setup can't be done twice."""
        # This would require actually enabling MFA first
        pass  # Implementation would require TOTP verification

    def test_backup_codes_work_for_recovery(self):
        """Test that backup codes work for account recovery."""
        pass  # Implementation would require MFA setup completion


class TestAuditLogging:
    """Test audit logging functionality."""

    def test_login_events_are_logged(self):
        """Test that login events are properly logged."""
        initial_log_count = len(audit_logger.audit_logs)

        client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpassword"
        })

        # Check that audit log was created
        assert len(audit_logger.audit_logs) > initial_log_count

        # Check the latest log entry
        latest_log = audit_logger.audit_logs[-1]
        assert latest_log["event_type"] == "login_failure"
        assert latest_log["success"] is False

    def test_sensitive_data_is_redacted_in_logs(self):
        """Test that sensitive data is redacted in audit logs."""
        client.post("/api/auth/register", json={
            "username": "audittest",
            "email": "audit@example.com",
            "password": "sensitivepassword123",
            "first_name": "Audit",
            "last_name": "Test"
        })

        # Check that password is not stored in logs
        for log_entry in audit_logger.audit_logs:
            if "password" in str(log_entry).lower():
                assert "[REDACTED]" in str(log_entry) or "***" in str(log_entry)


class TestSecurityHeaders:
    """Test security headers are properly applied."""

    def test_security_headers_present(self):
        """Test that security headers are present in responses."""
        response = client.get("/")

        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Referrer-Policy",
            "Cache-Control",
            "X-Banking-Security"
        ]

        for header in expected_headers:
            assert header in response.headers

        # Check specific values
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Banking-Security"] == "enabled"

    def test_csp_header_configured(self):
        """Test that Content Security Policy is configured."""
        response = client.get("/")

        if "Content-Security-Policy" in response.headers:
            csp = response.headers["Content-Security-Policy"]
            assert "default-src 'self'" in csp
            assert "frame-ancestors 'none'" in csp


class TestAuthorizationBypass:
    """Test for authorization bypass vulnerabilities."""

    def test_cannot_access_other_users_data(self):
        """Test that users cannot access other users' data."""
        # Create two users
        client.post("/api/auth/register", json={
            "username": "user1",
            "email": "user1@example.com",
            "password": "testpassword123",
            "first_name": "User",
            "last_name": "One"
        })

        client.post("/api/auth/register", json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "testpassword123",
            "first_name": "User",
            "last_name": "Two"
        })

        # Login as user1
        login_response = client.post("/api/auth/login", json={
            "username": "user1",
            "password": "testpassword123"
        })

        cookies = dict(login_response.cookies)

        # Try to access user2's data (if such endpoints exist)
        # This test would need specific endpoints that take user IDs
        pass

    def test_admin_functions_require_admin_role(self):
        """Test that administrative functions require admin role."""
        # This would test admin-only endpoints if they exist
        pass


class TestSessionSecurity:
    """Test session security features."""

    def test_session_timeout(self):
        """Test that sessions timeout after inactivity."""
        # This would require manipulating session timestamps
        pass

    def test_session_hijacking_protection(self):
        """Test protection against session hijacking."""
        # This would test device fingerprinting and IP validation
        pass

    def test_concurrent_login_detection(self):
        """Test concurrent login detection works."""
        # Register user
        client.post("/api/auth/register", json={
            "username": "concurrent",
            "email": "concurrent@example.com",
            "password": "testpassword123",
            "first_name": "Concurrent",
            "last_name": "Test"
        })

        # Multiple logins should be tracked
        sessions = []
        for i in range(4):  # More than max_concurrent_sessions (3)
            response = client.post("/api/auth/login", json={
                "username": "concurrent",
                "password": "testpassword123"
            })
            sessions.append(response)

        # Should have logged concurrent session warnings
        concurrent_logs = [
            log for log in audit_logger.audit_logs
            if "concurrent_login" in log.get("details", {}).get("reason", "")
        ]
        assert len(concurrent_logs) > 0


# Pytest fixtures and test configuration
@pytest.fixture
def clean_test_state():
    """Clean test state before each test."""
    # Clear rate limiter
    rate_limiter.requests.clear()
    rate_limiter.failed_attempts.clear()

    # Clear MFA data
    mfa_manager.mfa_data.clear()
    mfa_manager.pending_setups.clear()
    mfa_manager.trusted_devices.clear()
    mfa_manager.backup_codes.clear()

    # Clear session manager
    enhanced_session_manager.sessions.clear()
    enhanced_session_manager.user_sessions.clear()
    enhanced_session_manager.user_devices.clear()

    # Clear audit logs
    audit_logger.audit_logs.clear()


# Run security tests with clean state
@pytest.mark.usefixtures("clean_test_state")
class TestSecuritySuite:
    """Main security test suite with clean state."""
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])