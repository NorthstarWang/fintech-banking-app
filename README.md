# BankFlow — Retail Digital Banking Platform

BankFlow is the retail digital-banking platform powering day-to-day money management for consumer and small-business customers. It provides multi-account banking, payments and transfers, card management, lending, budgeting and goals, investments, and customer analytics behind a single API surface and a unified web experience.

This repository contains the full platform: the FastAPI service layer, the Next.js customer web application, the service-decomposition workstream under `services/`, and the Kubernetes deployment manifests under `k8s/`.

## Contents

- [Architecture](#architecture)
- [Domain Modules](#domain-modules)
- [Technology Stack](#technology-stack)
- [Local Development](#local-development)
- [Quality Gates](#quality-gates)
- [Testing Strategy](#testing-strategy)
- [Deployment and Runtime](#deployment-and-runtime)
- [Platform Documentation](#platform-documentation)

## Architecture

The platform follows a modular-monolith design on the backend, with an active workstream extracting high-traffic capabilities into standalone services behind an API gateway.

```
fintech-banking-app/
├── backend/                  # Core FastAPI application
│   ├── app/
│   │   ├── routes/           # HTTP API — one router per domain module
│   │   ├── services/         # Domain services, event sourcing, saga orchestration
│   │   ├── repositories/     # Data access layer and domain managers
│   │   ├── models/           # Core models, entities, DTOs, enums
│   │   ├── storage/          # Storage adapters (in-memory development data layer)
│   │   ├── middleware/       # CSRF, rate limiting, input sanitization, security headers
│   │   ├── security/         # Field encryption, audit logging, anomaly detection
│   │   ├── risk_management/  # AML, fraud, credit, market, operational, regulatory risk
│   │   └── core/             # Configuration (Pydantic settings) and structured logging
│   └── tests/                # Pytest suites
├── frontend/                 # Next.js 15 customer web application
│   └── src/
│       ├── app/              # App Router pages (public and authenticated route groups)
│       ├── components/       # Domain-organized component library
│       ├── contexts/ hooks/ lib/ services/ utils/
│       └── __tests__/        # Jest integration tests
├── services/                 # Extracted services: api_gateway, auth, accounts,
│                             # transactions, payments, investments, notifications,
│                             # analytics, risk
├── k8s/                      # Kubernetes manifests (base, services, monitoring)
├── docs/                     # Architecture, operations, and API documentation
├── docker-compose.yaml       # Two-tier local stack (backend + frontend)
└── docker-compose.services.yml  # Gateway + extracted services stack
```

**Request flow.** The frontend calls the backend over a versioned REST surface mounted under `/api/*` (see `backend/app/main_banking.py` for the full router registry). Authentication is JWT-based with refresh tokens; cross-cutting concerns — request IDs, rate limiting, CSRF protection, input sanitization, security headers, and centralized error handling — are applied as ASGI middleware. Analytics supports WebSocket streaming for live dashboard updates.

**Data layer.** Storage is abstracted behind repository classes and storage adapters (`backend/app/storage/`). Local development and CI run against the in-memory data layer (`USE_MOCK_DB=true`, the default), which boots with deterministic seeded customers, accounts, transactions, budgets, and goals so every environment starts from a known state. A SQLAlchemy/SQLite-backed configuration is available via `DATABASE_URL`.

**Platform services.** Beyond CRUD, the backend includes an event-sourcing subsystem (event store, schemas, streaming), saga-pattern orchestration for multi-step money movement, a transaction coordinator and monitoring service, and a structured audit logger (`backend/app/services/`).

## Domain Modules

Each module corresponds to a router in `backend/app/routes/` and, where customer-facing, a route group in `frontend/src/app/(authenticated)/`.

| Module | Backend | What it does |
|---|---|---|
| Accounts | `accounts.py` | Multi-account management across checking, savings, credit, investment, and loan products; balances and account lifecycle |
| Transactions | `transactions.py`, `recurring.py` | Transaction history, categorization, search and filtering, recurring transaction detection and management |
| Transfers & Payments | `transfers.py`, `payment_methods.py` | Internal and external transfers, payment-method management |
| P2P Payments | `p2p.py` | Person-to-person transfers, payment requests, and splitting |
| Budgets & Goals | `budgets.py`, `goals.py` | Category budgets with threshold alerts; savings goals with contribution tracking |
| Smart Savings | `savings.py` | Round-up rules and automated savings transfers |
| Cards | `cards.py`, `credit_cards.py` | Physical and virtual card issuance, freeze/unfreeze, spending controls, credit-card servicing |
| Credit | `credit.py` | Credit score monitoring, simulation, and utilization tracking |
| Lending | `loans.py` | Loan products, schedules, and servicing |
| Insurance | `insurance.py` | Insurance policy management |
| Investments | `investments.py` | Portfolio and position management |
| Digital Assets | `crypto.py` | Digital-asset account support |
| Currency | `currency_converter.py` | Multi-currency conversion |
| Business Banking | `business.py` | Invoicing, expense tracking, and business account servicing |
| Subscriptions | `subscriptions.py` | Recurring-merchant detection and subscription cost analysis |
| Messaging & Contacts | `messages.py`, `conversations.py`, `contacts.py` | Payment-context messaging, conversations, and contact management |
| Notifications | `notifications.py` | Customer notification delivery and preferences |
| Analytics | `analytics.py`, `analytics_export.py`, `analytics_intelligence.py`, `analytics_websocket.py` | Spending insights, cash-flow analysis, report exports, and live streaming updates |
| Search & Exports | `search.py`, `exports.py`, `uploads.py` | Cross-entity search, data import/export, file uploads |
| Identity & Access | `auth.py`, `users.py`, `security.py`, `security_dashboard.py` | Registration, login, JWT/refresh tokens, session and device security, security dashboard |
| Unified Financial System | `unified.py`, `banking.py` | Aggregated cross-product views and banking integration surface |
| Health | `health.py` | Liveness/readiness endpoints for orchestration probes |

### Risk Management

`backend/app/risk_management/` is organized as a self-contained domain with its own models, repositories, routes, and services per discipline:

- **AML** — anti-money-laundering screening workflows
- **Fraud** — fraud detection rules and case handling
- **Credit / Market / Operational** — exposure and risk assessment
- **Regulatory & Audit** — regulatory reporting structures and audit trails
- **Data Quality** — data-integrity checks feeding the risk pipeline

### Security Controls

Application-level controls live in `backend/app/security/` and `backend/app/middleware/`: field-level encryption, request signing, device fingerprinting, anomaly detection, audit logging, CSRF protection, rate limiting, input sanitization, and security response headers. Swagger UI is disabled in production unless explicitly enabled (`ENABLE_SWAGGER_UI`).

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, python-jose (JWT), bcrypt, cryptography |
| Frontend | Next.js 15 (App Router), React 19, TypeScript 5, Tailwind CSS 4, Framer Motion |
| Backend QA | Ruff, Mypy, Pytest |
| Frontend QA | ESLint 9, TypeScript strict mode, Jest 29, Testing Library, MSW |
| Tooling | Husky + lint-staged pre-commit hooks |
| Runtime | Docker multi-stage images, Docker Compose, Kubernetes |

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker and Docker Compose (for the containerized stack)

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # adjust as needed
uvicorn app.main:app --reload # serves on http://localhost:8000
```

Key environment variables (see `backend/app/core/config.py` for the full validated set):

```bash
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
USE_MOCK_DB=true        # in-memory development data layer (default)
SECRET_KEY=...          # required for non-development environments
JWT_SECRET=...          # required for non-development environments
```

### Frontend

```bash
cd frontend
npm install
npm run dev               # serves on http://localhost:3000
```

Create `frontend/.env` with:

```bash
NODE_ENV=development
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Containerized stack

```bash
docker-compose up --build
# Frontend:  http://localhost:3000
# API:       http://localhost:8000
# API docs:  http://localhost:8000/docs (non-production)
```

### Seeded development accounts

The in-memory development data layer boots with fixture customers carrying 90 days of transaction history, budgets, goals, and contact relationships:

- Standard users: `john_doe`, `jane_smith`, `mike_wilson`, `sarah_jones`, `david_brown` (password `password123`)
- Administrative user: `admin` (password `admin123`)

These credentials exist only in the local development data layer and are never used in deployed environments.

## Quality Gates

All changes must pass the following checks before merge. Pre-commit hooks (Husky + lint-staged) enforce the frontend gates locally; CI runs the full set.

**Backend** (run from `backend/`):

```bash
python -m ruff check .
python -m mypy . --ignore-missing-imports
python -m pytest
```

**Frontend** (run from `frontend/`):

```bash
npm run lint
npx tsc --noEmit
npm test            # or: npm run test:ci
npm run build
```

## Testing Strategy

**Backend** — Pytest suites in `backend/tests/` cover each domain module (accounts, auth, budgets, business, cards, credit cards, investments, messages, notifications, savings, subscriptions, transactions, users), the analytics system, and the security stack (anomaly detection, audit logging, device fingerprinting, field encryption, request signing, security responses). Cross-cutting suites include endpoint smoke tests, transaction concurrency tests, and production-feature verification. Suites run against the in-memory data layer for deterministic, isolated execution.

**Frontend** — Jest with Testing Library and jsdom, with MSW for API interception. Integration tests live in `frontend/src/__tests__/integration/`; coverage reporting is available via `npm run test:coverage`.

## Deployment and Runtime

### Container images

Both tiers ship multi-stage Dockerfiles: the backend runs uvicorn workers as a non-root user with health-check configuration and graceful shutdown handling; the frontend uses Next.js standalone output with `dumb-init` and a non-root `nextjs` user.

### Compose topologies

- `docker-compose.yaml` — the standard two-service stack (backend + frontend) with health checks.
- `docker-compose.services.yml` — the decomposed topology: an API gateway fronting the extracted auth, notification, and analytics services on a dedicated network, configured via gateway API keys.

### Kubernetes

Manifests live under `k8s/`:

- `k8s/base/` — namespace, ConfigMap, Secrets, ServiceAccount, and NetworkPolicy
- `k8s/services/` — Deployments for the API gateway and auth service
- `k8s/monitoring/` — Prometheus scrape configuration

The backend exposes health endpoints (`backend/app/routes/health.py`) for liveness and readiness probes, and supports optional Prometheus metrics and Sentry error reporting via configuration.

## Platform Documentation

| Document | Purpose |
|---|---|
| [Backend API Specification](docs/backend-api-specification.md) | Endpoint-level API reference |
| [Frontend Architecture Guide](docs/frontend-architecture-guide.md) | Component and page structure |
| [Feature Overview](docs/project-feature-overview.md) | Capability inventory and status |
| [User Flow Documentation](docs/user-flow-documentation.md) | End-to-end customer journeys |
| [Security Architecture](docs/SECURITY_ARCHITECTURE.md) | Security controls and design |
| [Operational Runbooks](docs/OPERATIONAL_RUNBOOKS.md) | Day-2 operations procedures |
| [Incident Response](docs/INCIDENT_RESPONSE.md) | Incident handling process |
| [SLO/SLI Guide](docs/SLO_SLI_GUIDE.md) | Service-level objectives and indicators |

## License

Released under the MIT License. See [LICENSE](LICENSE) for details.
