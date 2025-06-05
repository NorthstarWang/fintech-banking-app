"""
Main FastAPI application using memory-based mock data system.
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from app.repositories.data_manager import data_manager

# Import routers
import sys
sys.path.append('..')  # Add parent directory to path
from tests.mock_routes import auth_mock as auth

# For now, use regular routes with mock adapters
from app.routes import accounts
from app.routes import transactions
from app.routes import cards  
from app.routes import budgets
from app.routes import goals
from app.routes import subscriptions
from app.routes import messages
from app.routes import notifications
from app.routes import analytics
from app.routes import analytics_export
from app.routes import users
from app.routes import search
from app.routes import banking
from app.routes import business
from app.routes import categories
from app.routes import contacts
from app.routes import credit
from app.routes import exports
from app.routes import notes
from app.routes import payment_methods
from app.routes import recurring
from app.routes import savings
from app.routes import security

# Create placeholder routers for missing ones
from fastapi import APIRouter
social = type('Module', (), {'router': APIRouter()})()
investments = type('Module', (), {'router': APIRouter()})()
support = type('Module', (), {'router': APIRouter()})()
settings = type('Module', (), {'router': APIRouter()})()
bills = type('Module', (), {'router': APIRouter()})()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    print("Starting Banking Application with Mock Data System...")
    
    # Reset data manager and generate mock data
    data_manager.reset(seed=42)
    
    print("Mock data generated successfully!")
    
    yield
    
    # Shutdown
    print("Shutting down Banking Application...")

app = FastAPI(
    title="Banking & Finance Application API (Mock System)",
    version="2.0.0",
    description="Comprehensive banking application using in-memory mock data for easy testing",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get current user from session
async def get_current_user(authorization: Optional[str] = None) -> Dict[str, Any]:
    """
    Get current user from authorization header.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        Current user data
        
    Raises:
        HTTPException: If not authenticated
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    token = authorization.replace("Bearer ", "")
    user = data_manager.auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
        
    return user

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["Accounts"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(cards.router, prefix="/api/cards", tags=["Cards"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["Budgets"])
app.include_router(goals.router, prefix="/api/goals", tags=["Goals"])
app.include_router(bills.router, prefix="/api/bills", tags=["Bills"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["Subscriptions"])
app.include_router(social.router, prefix="/api/social", tags=["Social"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(investments.router, prefix="/api/investments", tags=["Investments"])
app.include_router(support.router, prefix="/api/support", tags=["Support"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(analytics_export.router, prefix="/api/analytics", tags=["Analytics Export"])
app.include_router(security.router, prefix="/api/security", tags=["Security"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])
app.include_router(payment_methods.router, prefix="/api/payment-methods", tags=["Payment Methods"])
app.include_router(recurring.router, prefix="/api/recurring", tags=["Recurring"])
app.include_router(exports.router, prefix="/api/exports", tags=["Exports"])
app.include_router(credit.router, prefix="/api/credit", tags=["Credit"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["Contacts"])
app.include_router(notes.router, prefix="/api/notes", tags=["Notes"])
app.include_router(savings.router, prefix="/api/savings", tags=["Savings"])
app.include_router(banking.router, prefix="/api/banking", tags=["Banking"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Banking & Finance API (Mock System)",
        "version": "2.0.0",
        "docs": "/docs",
        "mock_system": True
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "mock_system": True,
        "data_stats": {
            "users": len(data_manager.users),
            "accounts": len(data_manager.accounts),
            "transactions": len(data_manager.transactions),
            "cards": len(data_manager.cards)
        }
    }