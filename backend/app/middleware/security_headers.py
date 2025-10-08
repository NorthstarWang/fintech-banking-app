"""
Security headers middleware for banking application.
Implements comprehensive security headers following OWASP recommendations.
"""
from fastapi import Request, Response


class SecurityHeaders:
    """Security headers middleware for enhanced protection."""

    def __init__(self):
        # Security headers configuration
        self.security_headers = {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",

            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",

            # Prevent clickjacking
            "X-Frame-Options": "DENY",

            # Don't send referrer to other domains
            "Referrer-Policy": "strict-origin-when-cross-origin",

            # Prevent caching of sensitive data
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0",

            # Prevent browser from inferring resource types
            "X-Content-Type-Options": "nosniff",

            # Remove server information
            "Server": "BankFlow/1.0",

            # Strict Transport Security (HTTPS only)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",

            # Permissions Policy (restrict browser features)
            "Permissions-Policy": (
                "camera=(), "
                "microphone=(), "
                "geolocation=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            ),

            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "upgrade-insecure-requests"
            )
        }

        # Headers that should only be set for HTML responses
        self.html_only_headers = {
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-XSS-Protection"
        }

        # Headers that should only be set for HTTPS
        self.https_only_headers = {
            "Strict-Transport-Security"
        }

    def apply_security_headers(self, request: Request, response: Response):
        """Apply security headers to response."""
        content_type = response.headers.get("content-type", "")
        is_html = "text/html" in content_type
        is_https = request.url.scheme == "https"

        for header_name, header_value in self.security_headers.items():
            # Skip HTML-only headers for non-HTML responses
            if header_name in self.html_only_headers and not is_html:
                continue

            # Skip HTTPS-only headers for HTTP requests
            if header_name in self.https_only_headers and not is_https:
                continue

            response.headers[header_name] = header_value

        # Add additional security headers based on response type
        if is_html:
            # Additional CSP for HTML responses
            response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
            response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

        # For API responses, add CORS security headers
        if "application/json" in content_type:
            response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # Banking-specific headers
        response.headers["X-Banking-Security"] = "enabled"
        response.headers["X-Financial-Data-Protection"] = "active"

        return response


# Global security headers instance
security_headers = SecurityHeaders()


async def security_headers_middleware(request: Request, call_next):
    """Middleware to apply security headers to all responses."""
    response = await call_next(request)

    # Apply security headers
    security_headers.apply_security_headers(request, response)

    return response