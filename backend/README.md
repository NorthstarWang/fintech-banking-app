# Backend API Documentation


## Getting Started

### Running with Docker
```bash
# From the root directory
docker-compose up backend
```

### Local Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main_banking:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
When running, visit `http://localhost:8000/docs` for interactive Swagger documentation.

## Architecture

- **Framework**: FastAPI with async support
- **Database**: SQLAlchemy ORM with SQLite
- **Authentication**: JWT tokens with Bearer authentication
- **Models**: Comprehensive financial domain models

## Main Components

### Directory Structure
```
backend/
├── app/
│   ├── main_banking.py      # Main application entry point
│   ├── models/              # SQLAlchemy models
│   ├── routes/              # API route handlers
│   ├── services/            # Business logic
│   ├── utils/               # Utilities and helpers
│   └── db/                  # Database configuration
├── tests/                   # Test files
└── requirements.txt         # Python dependencies
```

### Database Models

#### Core Models
- **User**: User accounts with authentication
- **Account**: Financial accounts (checking, savings, credit cards)
- **Transaction**: Financial transactions with categorization
- **Category**: Spending categories with icons
- **Budget**: Monthly/weekly/yearly budgets
- **Goal**: Financial goals with progress tracking

#### Social Models
- **Contact**: User connections for P2P payments
- **Conversation**: Chat conversations
- **Message**: Chat messages with read receipts

#### Business Models
- **Card**: Credit/debit card management
- **Subscription**: Subscription tracking
- **Merchant**: Transaction merchants

### API Routes

#### Authentication (`/auth`)
- User registration with password hashing
- JWT-based login/logout
- Session management

#### Financial Management
- **Accounts**: CRUD operations, balance management
- **Transactions**: Create, list, filter, categorize
- **Budgets**: Track spending against limits
- **Goals**: Progress tracking, contributions

#### Social Features
- **Contacts**: Friend requests, contact management
- **Messages**: Real-time messaging for payment context
- **P2P Transfers**: Send money between users

#### Analytics & Tracking
- **Custom Events**: Track UI interactions
- **Session Management**: Track user sessions

#### Investments & Live Market Data
- **Accounts / Portfolios / Positions**: ETF, stock, and crypto holdings
- **Trading**: Market/limit orders with fill pricing from the market-data layer
- **Live Market Data**: Real-time prices ingested from a public WebSocket feed
- **Live Portfolio Valuation**: Mark-to-market valuation of holdings

### Live Market Data Streaming (Real-Time)

BankFlow ships an enterprise live market-data layer that replaces static mock
prices for the investments domain with a real-time feed.

**Architecture**
- `app/services/market_data_stream.py` — a long-running async WebSocket *client*
  (`MarketDataStreamService`, exposed as the module-level singleton
  `market_data_stream_service`). It connects out to a public, no-auth feed and
  ingests `ticker` updates into an in-memory `MarketDataStore` (latest price plus
  a small rolling history per product).
- **Upstream source (default):** Coinbase Exchange —
  `wss://ws-feed.exchange.coinbase.com`, `ticker` channel, products
  `BTC-USD, ETH-USD, SOL-USD, ADA-USD, DOT-USD`.
- **Lifecycle:** started/stopped from the FastAPI `lifespan` in
  `app/main_banking.py` alongside the event-streaming service. `start()` is
  idempotent and stores the `asyncio.Task`; `stop()` cancels it and closes the
  socket for graceful shutdown.
- **Reconnect / resilience:** the ingest loop reconnects with exponential backoff
  plus jitter (capped) and never propagates feed errors into the app.
- **Graceful degradation:** when the feed is disabled, disconnected, or a quote is
  stale, the investments domain transparently falls back to the existing mock
  price generator, so the API (and the test suite) work fully offline.

**Investments integration**
- `InvestmentManager.get_market_data()` prefers a fresh live quote, then falls back
  to seeded mock pricing. This feeds trade fill pricing, buying-power checks, and
  the asset-detail endpoints.
- Portfolio read paths (`get_positions`, `get_portfolio`, `get_investment_summary`,
  `get_portfolio_summary`) re-mark positions to market
  (`current_value = shares * live_price`) for symbols covered by the feed, so
  valuation reflects live prices instead of frozen mark-at-fill values.

**Endpoints** (under `/api/investments`)
- `GET /market-data/live/{symbol}` — latest live quote for a symbol (falls back to
  a mock quote with `"is_live": false, "source": "mock_fallback"` when offline).
- `GET /market-data/stream/status` — operational status of the streaming service
  (enabled, connected, products, last update, per-product freshness).
- `GET /portfolio/{account_id}/live-valuation` — mark-to-market valuation of an
  account's holdings, with a per-holding `price_source` (`live` vs `mock`) flag.

**Configuration** (`app/core/config.py`, overridable via env / `.env`)
- `MARKET_DATA_ENABLED` (default `true`)
- `MARKET_DATA_SOURCE_URL` (default `wss://ws-feed.exchange.coinbase.com`)
- `MARKET_DATA_PRODUCTS` (comma-separated or JSON list)
- `MARKET_DATA_RECONNECT_MIN_SECONDS` / `MARKET_DATA_RECONNECT_MAX_SECONDS`
- `MARKET_DATA_HISTORY_SIZE`, `MARKET_DATA_STALENESS_SECONDS`

### Mock Data Generation

The backend automatically generates realistic mock data on startup:

- **Users**: 6 pre-configured users (5 regular + 1 admin)
- **Accounts**: Multiple accounts per user with realistic balances
- **Transactions**: 90 days of categorized transaction history
- **Merchants**: 21 common merchants (Amazon, Starbucks, etc.)
- **Categories**: 16 system categories for income/expenses
- **Budgets**: Pre-configured monthly budgets
- **Goals**: Active financial goals with progress

- Page views, clicks, form submissions
- API requests and responses
- User authentication events
- Transaction operations

#### Interactive Component Events
- Slide-to-confirm gestures
- Toggle animations
- Chart interactions
- Drag gestures
- Calendar interactions

#### Event Structure
```json
{
  "session_id": "uuid",
  "action_type": "CLICK",
  "payload": {
    "text": "Human-readable description",
    "element_identifier": "button-id",
    "page_url": "current-page",
    "coordinates": {"x": 100, "y": 200}
  }
}
```

### Security Features

- Password hashing with bcrypt
- JWT token authentication
- Role-based access control (USER/ADMIN)
- Session management
- CORS configuration for frontend integration

### Performance Optimizations

- Async request handling
- Database connection pooling
- Efficient query optimization
- In-memory SQLite for development
- Pagination support for large datasets

## Common Tasks

### Adding a New Endpoint
1. Create route handler in `app/routes/`
2. Define request/response models
3. Implement business logic in services
5. Update API documentation

### Modifying Mock Data
Edit `app/utils/mock_data_generator.py` to customize:
- Number of users
- Transaction patterns
- Account balances
- Category definitions

### Testing
Run tests with pytest:
```bash
pytest tests/
```

## Environment Variables

- `SEED`: Random seed for deterministic data (default: "0000000000000000")
- `DATABASE_URL`: SQLite connection string (default: in-memory)
- `SECRET_KEY`: JWT signing key (auto-generated if not set)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration (default: 30)