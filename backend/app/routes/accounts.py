from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional, Any
from datetime import datetime

from ..storage.memory_adapter import db, desc
from ..models import Account, AccountType, Transaction, User
from ..models import AccountCreate, JointAccountCreate, AccountUpdate, AccountResponse, AccountSummary
from ..utils.auth import get_current_user
from ..utils.validators import Validators, ValidationError
from ..utils.session_manager import session_manager

router = APIRouter()

@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    request: Request,
    account_data: AccountCreate,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a new account"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    # Create new account
    # Convert string to enum value
    account_type_value = AccountType[account_data.account_type.upper()]
    
    new_account = Account(
        user_id=current_user['user_id'],
        name=account_data.name,
        account_type=account_type_value,
        account_number=account_data.account_number,
        institution_name=account_data.institution_name,
        balance=account_data.initial_balance,
        credit_limit=account_data.credit_limit,
        interest_rate=account_data.interest_rate,
        is_active=True
    )
    
    db_session.add(new_account)
    db_session.commit()
    db_session.refresh(new_account)
    
    # Log account creation
        session_id, 
        new_account.id, 
        current_user['user_id'],
        account_data.account_type.value,
        account_data.name
    )
    
    return AccountResponse.from_orm(new_account)

@router.post("/joint", status_code=status.HTTP_201_CREATED)
async def create_joint_account(
    request: Request,
    account_data: JointAccountCreate,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a new joint account"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    
    # Validate required fields
    if not account_data.joint_owner_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Joint owner username is required"
        )
    
    # Find the joint owner by username
    joint_owner = db_session.query(User).filter(User.username == account_data.joint_owner_username).first()
    if not joint_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username '{account_data.joint_owner_username}' not found"
        )
    
    # Check if joint owner is different from current user
    if joint_owner.id == current_user['user_id']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create joint account with yourself"
        )
    
    # Create new account
    account_type_value = AccountType[account_data.account_type.upper()]
    
    new_account = Account(
        user_id=current_user['user_id'],  # Primary owner
        name=account_data.name,
        account_type=account_type_value,
        account_number=account_data.account_number,
        institution_name=account_data.institution_name,
        balance=account_data.initial_balance,
        credit_limit=account_data.credit_limit,
        interest_rate=account_data.interest_rate,
        is_active=True
    )
    
    db_session.add(new_account)
    db_session.flush()  # Get the account ID
    
    # For memory-based system, store joint owner info in metadata
    new_account.joint_owner_id = joint_owner.id
    new_account.is_joint = True
    
    db_session.commit()
    db_session.refresh(new_account)
    
    # Log account creation
        session_id, 
        new_account.id, 
        current_user['user_id'],
        account_data.account_type.value,
        f"Joint account '{account_data.name}' with {joint_owner.username}"
    )
    
    # Get current user details for notifications
    current_user_obj = db_session.query(User).get(current_user['user_id'])
    
    # Create notifications for both users
    from ..models import Notification, NotificationType
    
    # Notification for the creator
    creator_notification = Notification(
        user_id=current_user['user_id'],
        type=NotificationType.ACCOUNT_UPDATE,
        title="Joint Account Created",
        message=f"You've successfully created a joint {account_data.account_type.value} account '{account_data.name}' with {joint_owner.full_name}",
        is_read=False,
        metadata={
            "account_id": new_account.id,
            "joint_owner_id": joint_owner.id,
            "joint_owner_name": joint_owner.full_name
        }
    )
    db_session.add(creator_notification)
    
    # Notification for the joint owner
    joint_owner_notification = Notification(
        user_id=joint_owner.id,
        type=NotificationType.ACCOUNT_UPDATE,
        title="Added to Joint Account",
        message=f"{current_user_obj.full_name} has added you as a joint owner of the {account_data.account_type.value} account '{account_data.name}'",
        is_read=False,
        metadata={
            "account_id": new_account.id,
            "creator_id": current_user['user_id'],
            "creator_name": current_user_obj.full_name
        }
    )
    db_session.add(joint_owner_notification)
    
    db_session.commit()
    
    # Create custom response with owners field
    response = AccountResponse.from_orm(new_account).dict()
    # For memory-based system, manually create owners list
    response["owners"] = [
        {"id": current_user_obj.id, "username": current_user_obj.username, "email": current_user_obj.email},
        {"id": joint_owner.id, "username": joint_owner.username, "email": joint_owner.email}
    ]
    
    return response

@router.get("/", response_model=List[AccountResponse])
async def get_accounts(
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get all user accounts (including joint accounts)"""
    
    # Get accounts where user is primary owner or joint owner
    user = db_session.query(User).get(current_user['user_id'])
    
    # Get primary accounts
    primary_query = db_session.query(Account).filter(Account.user_id == current_user['user_id'])
    
    if not include_inactive:
        primary_query = primary_query.filter(Account.is_active == True)
    
    primary_accounts = primary_query.all()
    
    # Get joint accounts - query for accounts where current user is joint owner
    joint_accounts = []
    all_accounts_query = db_session.query(Account).filter(
        Account.joint_owner_id == current_user['user_id']
    )
    if not include_inactive:
        all_accounts_query = all_accounts_query.filter(Account.is_active == True)
    joint_accounts = all_accounts_query.all()
    
    # Combine and deduplicate
    all_accounts = list({acc.id: acc for acc in primary_accounts + joint_accounts}.values())
    
    # Sort by created_at
    all_accounts.sort(key=lambda x: x.created_at, reverse=True)
    
    return [AccountResponse.from_orm(acc) for acc in all_accounts]

@router.get("/summary", response_model=AccountSummary)
async def get_account_summary(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get financial summary across all accounts (including joint accounts)"""
    # Get user for joint accounts
    user = db_session.query(User).get(current_user['user_id'])
    
    # Get primary accounts
    primary_accounts = db_session.query(Account).filter(
        Account.user_id == current_user['user_id'],
        Account.is_active == True
    ).all()
    
    # Get joint accounts - query for accounts where current user is joint owner
    joint_accounts = db_session.query(Account).filter(
        Account.joint_owner_id == current_user['user_id'],
        Account.is_active == True
    ).all()
    
    # Combine and deduplicate
    all_accounts = list({acc.id: acc for acc in primary_accounts + joint_accounts}.values())
    
    total_assets = 0.0
    total_liabilities = 0.0
    
    for account in all_accounts:
        if account.account_type in [AccountType.CHECKING, AccountType.SAVINGS, AccountType.INVESTMENT]:
            total_assets += account.balance
        elif account.account_type in [AccountType.CREDIT_CARD, AccountType.LOAN]:
            total_liabilities += abs(account.balance)
    
    net_worth = total_assets - total_liabilities
    
    return AccountSummary(
        total_assets=round(total_assets, 2),
        total_liabilities=round(total_liabilities, 2),
        net_worth=round(net_worth, 2),
        accounts=[AccountResponse.from_orm(acc) for acc in all_accounts]
    )

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get specific account details"""
    account = Validators.validate_account_ownership(
        db_session, 
        account_id, 
        current_user['user_id']
    )
    
    return AccountResponse.from_orm(account)

@router.get("/{account_id}/transactions")
async def get_account_transactions(
    account_id: int,
    skip: int = 0,
    limit: int = 20,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get transactions for a specific account"""
    # Validate account ownership
    account = Validators.validate_account_ownership(
        db_session, 
        account_id, 
        current_user['user_id']
    )
    
    # Build query
    query = db_session.query(Transaction).filter(Transaction.account_id == account_id)
    
    # Apply date filters if provided
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Transaction.transaction_date >= start_dt)
        except:
            pass
            
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Transaction.transaction_date <= end_dt)
        except:
            pass
    
    # Order by date descending and apply pagination
    transactions = query.order_by(desc(Transaction.transaction_date)).offset(skip).limit(limit).all()
    
    # Get categories for transactions - include merchant info too
    from ..models import Category, Merchant
    category_ids = [t.category_id for t in transactions if t.category_id]
    categories = {}
    if category_ids:
        cats = db_session.query(Category).filter(Category.id.in_(category_ids)).all()
        categories = {c.id: c for c in cats}
    
    # Get merchants for transactions
    merchant_ids = [t.merchant_id for t in transactions if hasattr(t, 'merchant_id') and t.merchant_id]
    merchants = {}
    if merchant_ids:
        merch = db_session.query(Merchant).filter(Merchant.id.in_(merchant_ids)).all()
        merchants = {m.id: m.name for m in merch}
    
    # Convert to response format
    return [
        {
            "id": t.id,
            "account_id": t.account_id,
            "category_id": t.category_id,
            "category": {
                "id": categories[t.category_id].id,
                "name": categories[t.category_id].name,
                "type": "income" if categories[t.category_id].is_income else "expense",
                "icon": categories[t.category_id].icon,
                "color": categories[t.category_id].color
            } if t.category_id and t.category_id in categories else None,
            "transaction_type": t.transaction_type.value if hasattr(t.transaction_type, 'value') else t.transaction_type,
            "amount": float(t.amount),
            "description": t.description,
            "merchant": merchants.get(t.merchant_id) if hasattr(t, 'merchant_id') and t.merchant_id else None,
            "merchant_id": t.merchant_id if hasattr(t, 'merchant_id') else None,
            "transaction_date": t.transaction_date.isoformat(),
            "posted_date": t.posted_date.isoformat() if t.posted_date else None,
            "location": t.location,
            "notes": t.notes,
            "tags": t.tags if hasattr(t, 'tags') else [],
            "attachments": t.attachments if hasattr(t, 'attachments') else [],
            "is_flagged": t.is_flagged if hasattr(t, 'is_flagged') else False,
            "created_at": t.created_at.isoformat(),
            "status": t.status.value if hasattr(t, 'status') and hasattr(t.status, 'value') else (t.status if hasattr(t, 'status') else "completed")
        }
        for t in transactions
    ]

@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    request: Request,
    account_id: int,
    account_update: AccountUpdate,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Update account details"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    account = Validators.validate_account_ownership(
        db_session, 
        account_id, 
        current_user['user_id']
    )
    
    # Update allowed fields
    update_data = account_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(account, field) and value is not None:
            setattr(account, field, value)
    
    account.updated_at = datetime.utcnow()
    db_session.commit()
    db_session.refresh(account)
    
    return AccountResponse.from_orm(account)

@router.delete("/{account_id}")
async def deactivate_account(
    request: Request,
    account_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Deactivate an account (soft delete)"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    account = Validators.validate_account_ownership(
        db_session, 
        account_id, 
        current_user['user_id']
    )
    
    # Check if account has non-zero balance
    if abs(account.balance) > 0.01:  # Small tolerance for floating point
        raise ValidationError(
            f"Cannot deactivate account with non-zero balance: ${account.balance:.2f}"
        )
    
    # Deactivate account
    account.is_active = False
    account.updated_at = datetime.utcnow()
    db_session.commit()
    
    # Log deactivation
        session_id,
        "accounts",
        account_id,
        f"Account '{account.name}' deactivated"
    )
    
    return {"message": "Account deactivated successfully"}

@router.get("/{account_id}/balance")
async def get_account_balance(
    account_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get current account balance with recent transactions"""
    account = Validators.validate_account_ownership(
        db_session, 
        account_id, 
        current_user['user_id']
    )
    
    # Get last 5 transactions
    recent_transactions = db_session.query(Transaction).filter(
        Transaction.account_id == account_id
    ).order_by(Transaction.transaction_date.desc()).limit(5).all()
    
    return {
        "account_id": account.id,
        "account_name": account.name,
        "balance": account.balance,
        "account_type": account.account_type.value,
        "credit_limit": account.credit_limit,
        "available_credit": account.credit_limit + account.balance if account.credit_limit else None,
        "recent_transactions": [
            {
                "id": tx.id,
                "amount": tx.amount,
                "type": tx.transaction_type.value,
                "description": tx.description,
                "date": tx.transaction_date.isoformat()
            }
            for tx in recent_transactions
        ]
    }