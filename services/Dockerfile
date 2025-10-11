# Multi-stage build for microservices
# Usage: docker build -t service-name:latest -f services/Dockerfile --build-arg SERVICE_NAME=auth_service .

ARG SERVICE_NAME=auth_service
ARG PYTHON_VERSION=3.11

# Stage 1: Builder
FROM python:${PYTHON_VERSION}-slim as builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (assuming common requirements)
COPY requirements.txt .

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:${PYTHON_VERSION}-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SERVICE_NAME=${SERVICE_NAME}

# Copy application code
COPY services /app/services
COPY backend /app/backend

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${SERVICE_PORT:-8000}/health || exit 1

# Run the service based on SERVICE_NAME
CMD case ${SERVICE_NAME} in \
    auth_service) python -m services.auth_service.app ;; \
    notification_service) python -m services.notification_service.app ;; \
    analytics_service) python -m services.analytics_service.app ;; \
    api_gateway) python -m services.api_gateway.gateway ;; \
    *) echo "Unknown service: ${SERVICE_NAME}" && exit 1 ;; \
    esac
