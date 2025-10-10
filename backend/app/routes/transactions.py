import uuid
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..models import (
    Account,
    Category,
    Merchant,
    Transaction,
    TransactionCreate,
    TransactionResponse,
    TransactionStatus,
    TransactionType,
    TransactionUpdate,
    TransferCreate,
)
from ..services.goal_update_service import GoalUpdateService
from ..storage.memory_adapter import db, or_
from ..utils.auth import get_current_user
from ..utils.validators import ValidationError, Validators

router = APIRouter()

@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    request: Request,
    transaction_data: TransactionCreate,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a new transaction"""


    # Validate account ownership
    account = Validators.validate_account_ownership(
        db_session,
        transaction_data.account_id,
        current_user['user_id']
    )

    # Validate amount
    Validators.validate_transaction_amount(transaction_data.amount)

    # Validate category if provided
    if transaction_data.category_id:
        Validators.validate_category_access(
            db_session,
            transaction_data.category_id,
            current_user['user_id']
        )

    # Check/create merchant if provided
    merchant = None
    if transaction_data.merchant_name:
        merchant = db_session.query(Merchant).filter(
            Merchant.name == transaction_data.merchant_name
        ).first()

        if not merchant:
            # Create new merchant
            merchant = Merchant(
                name=transaction_data.merchant_name,
                category_id=transaction_data.category_id
            )
            db_session.add(merchant)
            db_session.flush()

    # Calculate new balance
    if transaction_data.transaction_type == TransactionType.DEBIT:
        Validators.validate_sufficient_funds(account, transaction_data.amount)
        new_balance = account.balance - transaction_data.amount
    else:  # CREDIT
        new_balance = account.balance + transaction_data.amount

    # Validate credit limit for credit cards
    Validators.validate_credit_limit(account, new_balance)

    # Create transaction
    new_transaction = Transaction(
        account_id=account.id,
        category_id=transaction_data.category_id,
        merchant_id=merchant.id if merchant else None,
        amount=transaction_data.amount,
        transaction_type=transaction_data.transaction_type,
        status=TransactionStatus.COMPLETED,
        description=transaction_data.description.strip() if transaction_data.description else '',
        notes=transaction_data.notes,
        transaction_date=transaction_data.transaction_date,
        reference_number=str(uuid.uuid4())[:8].upper()
    )

    # Update account balance
    account.balance = new_balance
    account.updated_at = datetime.utcnow()

    db_session.add(new_transaction)
    db_session.commit()
    db_session.refresh(new_transaction)

    # Add merchant name if available
    if merchant:
        new_transaction.merchant = merchant.name



    # Process transaction for automatic goal contributions
    if transaction_data.transaction_type == TransactionType.CREDIT:
        GoalUpdateService.process_transaction_for_goals(
            db_session,
            new_transaction
        )

    return TransactionResponse.from_orm(new_transaction)

@router.post("/transfer", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    request: Request,
    transfer_data: TransferCreate,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Transfer money between accounts"""

    # Validate accounts
    from_account, to_account = Validators.validate_transfer_accounts(
        db_session,
        transfer_data.from_account_id,
        transfer_data.to_account_id,
        current_user['user_id']
    )

    # Validate amount
    Validators.validate_transaction_amount(transfer_data.amount)

    # Validate sufficient funds
    Validators.validate_sufficient_funds(from_account, transfer_data.amount)

    # Create reference number for both transactions
    ref_number = str(uuid.uuid4())[:8].upper()

    # Create debit transaction for source account
    transfer_out = Transaction(
        account_id=from_account.id,
        from_account_id=from_account.id,
        to_account_id=to_account.id,
        amount=transfer_data.amount,
        transaction_type=TransactionType.DEBIT,
        status=TransactionStatus.COMPLETED,
        description=transfer_data.description or f"Transfer to {to_account.name}",
        notes=transfer_data.notes,
        transaction_date=transfer_data.transaction_date,
        reference_number=ref_number
    )

    # Create credit transaction for destination account
    transfer_in = Transaction(
        account_id=to_account.id,
        from_account_id=from_account.id,
        to_account_id=to_account.id,
        amount=transfer_data.amount,
        transaction_type=TransactionType.CREDIT,
        status=TransactionStatus.COMPLETED,
        description=transfer_data.description or f"Transfer from {from_account.name}",
        notes=transfer_data.notes,
        transaction_date=transfer_data.transaction_date,
        reference_number=ref_number
    )

    # Update balances

    from_account.balance -= transfer_data.amount
    to_account.balance += transfer_data.amount

    from_account.updated_at = datetime.utcnow()
    to_account.updated_at = datetime.utcnow()

    db_session.add(transfer_out)
    db_session.add(transfer_in)
    db_session.commit()
    # Don't refresh to avoid picking up wrong transaction

    # Process the credit transaction for automatic goal contributions
    # Note: We don't process transfer_out as it's a debit
    GoalUpdateService.process_transaction_for_goals(
        db_session,
        transfer_in
    )

    # Create response directly without refresh to ensure correct transaction is returned
    return TransactionResponse(
        id=transfer_out.id,
        created_at=transfer_out.created_at,
        updated_at=transfer_out.updated_at,
        account_id=transfer_out.account_id,
        category_id=transfer_out.category_id,
        merchant_id=transfer_out.merchant_id,
        merchant=None,
        amount=transfer_out.amount,
        transaction_type=transfer_out.transaction_type,
        status=transfer_out.status,
        description=transfer_out.description,
        notes=transfer_out.notes,
        tags=transfer_out.tags if hasattr(transfer_out, 'tags') else [],
        attachments=transfer_out.attachments if hasattr(transfer_out, 'attachments') else [],
        transaction_date=transfer_out.transaction_date,
        from_account_id=transfer_out.from_account_id,
        to_account_id=transfer_out.to_account_id,
        reference_number=transfer_out.reference_number,
        recurring_rule_id=transfer_out.recurring_rule_id if hasattr(transfer_out, 'recurring_rule_id') else None
    )

@router.get("/stats")
async def get_transaction_stats(
    start_date: str = Query(..., description="Start date in ISO format"),
    end_date: str = Query(..., description="End date in ISO format"),
    category_id: int | None = Query(None, description="Category ID to get stats for (optional)"),
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get transaction statistics for a date range"""
    from dateutil import parser

    # Parse dates from ISO format
    try:
        start_dt = parser.parse(start_date)
        end_dt = parser.parse(end_date)
    except Exception:
        return {"error": "Invalid date format"}

    # Get user's accounts
    user_accounts = db_session.query(Account.id).filter(
        Account.user_id == current_user['user_id']
    ).subquery()

    # Build query based on whether category_id is provided
    query = db_session.query(Transaction).filter(
        Transaction.account_id.in_(user_accounts),
        Transaction.transaction_date >= start_dt,
        Transaction.transaction_date <= end_dt
    )

    # Add category filter if provided
    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)

    transactions = query.order_by(Transaction.transaction_date).all()

    # Calculate income and expenses
    total_income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.CREDIT)
    total_expenses = sum(t.amount for t in transactions if t.transaction_type == TransactionType.DEBIT)


    # Calculate categories breakdown
    categories_breakdown = []

    if category_id is not None:
        # Single category stats
        category = db_session.query(Category).filter(Category.id == category_id).first()
        category_name = category.name if category else "Unknown"

        if transactions:
            categories_breakdown.append({
                "category_id": category_id,
                "category_name": category_name,
                "total_amount": total_expenses,
                "transaction_count": len(transactions)
            })
    else:
        # All categories breakdown
        from collections import defaultdict
        category_totals = defaultdict(lambda: {"amount": 0.0, "count": 0})

        for transaction in transactions:
            if transaction.category_id and transaction.transaction_type == TransactionType.DEBIT:
                category_totals[transaction.category_id]["amount"] += transaction.amount
                category_totals[transaction.category_id]["count"] += 1

        # Get category names
        if category_totals:
            category_ids = list(category_totals.keys())
            categories = db_session.query(Category).filter(Category.id.in_(category_ids)).all()
            category_map = {c.id: c.name for c in categories}

            for cat_id, totals in category_totals.items():
                categories_breakdown.append({
                    "category_id": cat_id,
                    "category_name": category_map.get(cat_id, "Unknown"),
                    "total_amount": round(totals["amount"], 2),
                    "transaction_count": totals["count"]
                })

            # Sort by total amount descending
            categories_breakdown.sort(key=lambda x: x["total_amount"], reverse=True)

    # Calculate average transaction
    avg_transaction = sum(t.amount for t in transactions) / len(transactions) if transactions else 0

    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_flow": round(total_income - total_expenses, 2),
        "transaction_count": len(transactions),
        "average_transaction": round(avg_transaction, 2),
        "categories_breakdown": categories_breakdown
    }

@router.get("/", response_model=list[TransactionResponse])
async def get_transactions(
    account_id: int | None = None,
    category_id: int | None = None,
    transaction_type: TransactionType | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get transactions with filtering and pagination"""
    # Validate date range
    Validators.validate_date_range(start_date, end_date)

    # Build base query - get all user's transactions
    user_accounts = db_session.query(Account.id).filter(
        Account.user_id == current_user['user_id']
    ).subquery()

    query = db_session.query(Transaction).filter(
        Transaction.account_id.in_(user_accounts)
    )

    # Apply filters
    if account_id:
        # Validate ownership
        Validators.validate_account_ownership(db_session, account_id, current_user['user_id'])
        query = query.filter(Transaction.account_id == account_id)

    if category_id:
        query = query.filter(Transaction.category_id == category_id)

    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)

    if start_date:
        query = query.filter(Transaction.transaction_date >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query = query.filter(Transaction.transaction_date <= datetime.combine(end_date, datetime.max.time()))

    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)

    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Transaction.description.ilike(search_term),
                Transaction.notes.ilike(search_term)
            )
        )

    # Order by date descending
    query = query.order_by(Transaction.transaction_date.desc())

    # Pagination
    offset = (page - 1) * page_size
    transactions = query.offset(offset).limit(page_size).all()

    # Get all unique merchant IDs
    merchant_ids = set()
    for tx in transactions:
        if hasattr(tx, 'merchant_id') and tx.merchant_id:
            merchant_ids.add(tx.merchant_id)

    # Fetch all merchants in one query
    merchants_map = {}
    if merchant_ids:
        merchants = db_session.query(Merchant).filter(
            Merchant.id.in_(merchant_ids)
        ).all()
        merchants_map = {m.id: m.name for m in merchants}

    # Add merchant names to transactions
    for tx in transactions:
        if hasattr(tx, 'merchant_id') and tx.merchant_id and tx.merchant_id in merchants_map:
            tx.merchant = merchants_map[tx.merchant_id]

    return [TransactionResponse.from_orm(tx) for tx in transactions]

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get specific transaction details"""
    # Get transaction and verify ownership
    transaction = db_session.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Verify user owns the account
    Validators.validate_account_ownership(
        db_session,
        transaction.account_id,
        current_user['user_id']
    )

    # Get merchant name if merchant_id exists
    if hasattr(transaction, 'merchant_id') and transaction.merchant_id:
        merchant = db_session.query(Merchant).filter(
            Merchant.id == transaction.merchant_id
        ).first()
        if merchant:
            transaction.merchant = merchant.name

    return TransactionResponse.from_orm(transaction)

@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    request: Request,
    transaction_id: int,
    update_data: TransactionUpdate,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Update transaction details (category, description, notes only)"""

    # Get transaction and verify ownership
    transaction = db_session.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Verify user owns the account
    Validators.validate_account_ownership(
        db_session,
        transaction.account_id,
        current_user['user_id']
    )

    # Only allow updating certain fields
    if update_data.category_id is not None:
        if update_data.category_id:
            Validators.validate_category_access(
                db_session,
                update_data.category_id,
                current_user['user_id']
            )
        transaction.category_id = update_data.category_id

    if update_data.description is not None:
        transaction.description = update_data.description.strip() if update_data.description else ''

    if update_data.merchant is not None:
        # Check if merchant exists or create new one
        if update_data.merchant:
            merchant = db_session.query(Merchant).filter(
                Merchant.name == update_data.merchant
            ).first()

            if not merchant:
                # Create new merchant
                merchant = Merchant(
                    name=update_data.merchant,
                    category_id=transaction.category_id
                )
                db_session.add(merchant)
                db_session.flush()

            transaction.merchant_id = merchant.id
        else:
            transaction.merchant_id = None

    if update_data.notes is not None:
        transaction.notes = update_data.notes

    if update_data.tags is not None:
        transaction.tags = update_data.tags

    if update_data.attachments is not None:
        transaction.attachments = update_data.attachments

    transaction.updated_at = datetime.utcnow()
    db_session.commit()
    db_session.refresh(transaction)

    # Get merchant name if merchant_id exists
    if hasattr(transaction, 'merchant_id') and transaction.merchant_id:
        merchant = db_session.query(Merchant).filter(
            Merchant.id == transaction.merchant_id
        ).first()
        if merchant:
            # Add merchant name to transaction for response
            transaction.merchant = merchant.name

    return TransactionResponse.from_orm(transaction)

@router.delete("/{transaction_id}")
async def delete_transaction(
    request: Request,
    transaction_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Delete a transaction (only if pending)"""

    # Get transaction and verify ownership
    transaction = db_session.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Verify user owns the account
    Validators.validate_account_ownership(
        db_session,
        transaction.account_id,
        current_user['user_id']
    )

    # Only allow deletion of pending transactions
    if transaction.status != TransactionStatus.PENDING:
        raise ValidationError("Only pending transactions can be deleted")

    # Delete transaction
    db_session.delete(transaction)
    db_session.commit()


    return {"message": "Transaction deleted successfully"}


# Transaction Notes
@router.put("/{transaction_id}/notes")
async def update_transaction_notes(
    request: Request,
    transaction_id: int,
    notes: str,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Update transaction notes"""

    # Get transaction
    transaction = db_session.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Verify ownership
    Validators.validate_account_ownership(
        db_session,
        transaction.account_id,
        current_user['user_id']
    )

    # Update notes
    transaction.notes = notes
    transaction.updated_at = datetime.utcnow()
    db_session.commit()

    return {"message": "Notes updated successfully", "notes": notes}
