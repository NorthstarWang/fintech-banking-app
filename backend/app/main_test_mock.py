"""
Simplified FastAPI app for testing with mock data.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.repositories.data_manager import data_manager
from app.routes import accounts_mock as accounts
from app.routes import auth_mock_flexible as auth
from app.routes import budgets_mock as budgets
from app.routes import business_mock as business
from app.routes import cards_mock as cards
from app.routes import categories_mock as categories
from app.routes import messages_mock as messages
from app.routes import notifications_mock as notifications
from app.routes import savings_mock as savings
from app.routes import subscriptions_mock as subscriptions
from app.routes import transactions_mock as transactions
from app.routes import users_mock as users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    data_manager.reset(seed=42)
    yield
    # Shutdown

app = FastAPI(
    title="Test Banking API (Mock)",
    version="1.0.0",
    description="Simplified banking app for testing",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers for testing
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["Accounts"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["Budgets"])
app.include_router(cards.router, prefix="/api/cards", tags=["Cards"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(savings.router, prefix="/api/savings", tags=["Savings"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["Subscriptions"])
app.include_router(business.router, prefix="/api/business", tags=["Business"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Test Banking API (Mock System)",
        "version": "1.0.0",
        "mock_system": True
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mock_system": True,
        "users": len(data_manager.users)
    }
