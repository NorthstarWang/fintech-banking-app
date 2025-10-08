import random
import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from ..models import (
    Account,
    AccountType,
    BankLink,
    BankLinkRequest,
    BankLinkResponse,
    BankLinkStatus,
    CurrencyConversion,
    CurrencyInfo,
    LinkedAccount,
    LinkedAccountResponse,
    Transaction,
    TransactionStatus,
    TransactionType,
)
from ..storage.memory_adapter import db
from ..utils.auth import get_current_user
from ..utils.validators import ValidationError

router = APIRouter()

# Mock bank institutions
MOCK_INSTITUTIONS = {
    "chase": {
        "name": "Chase Bank",
        "supported_accounts": ["checking", "savings", "credit_card"],
        "logo": "https://example.com/chase-logo.png"
    },
    "bofa": {
        "name": "Bank of America",
        "supported_accounts": ["checking", "savings", "credit_card"],
        "logo": "https://example.com/bofa-logo.png"
    },
    "wells": {
        "name": "Wells Fargo",
        "supported_accounts": ["checking", "savings", "credit_card", "loan"],
        "logo": "https://example.com/wells-logo.png"
    },
    "amex": {
        "name": "American Express",
        "supported_accounts": ["credit_card"],
        "logo": "https://example.com/amex-logo.png"
    }
}

# Mock currency exchange rates (to USD)
CURRENCY_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "CAD": 1.36,
    "AUD": 1.53,
    "JPY": 149.50,
    "CNY": 7.24,
    "INR": 83.12,
    "MXN": 17.05,
    "BRL": 4.97
}

CURRENCY_NAMES = {
    "USD": "US Dollar",
    "EUR": "Euro",
    "GBP": "British Pound",
    "CAD": "Canadian Dollar",
    "AUD": "Australian Dollar",
    "JPY": "Japanese Yen",
    "CNY": "Chinese Yuan",
    "INR": "Indian Rupee",
    "MXN": "Mexican Peso",
    "BRL": "Brazilian Real"
}

CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "CAD": "C$",
    "AUD": "A$",
    "JPY": "¥",
    "CNY": "¥",
    "INR": "₹",
    "MXN": "$",
    "BRL": "R$"
}

async def mock_bank_sync(
    bank_link_id: int,
    db_session: Any
):
    """Mock background task to sync bank accounts"""
    # Get bank link
    bank_link = db_session.query(BankLink).filter(BankLink.id == bank_link_id).first()
    if not bank_link:
        return

    try:
        # Simulate processing delay
        import asyncio
        await asyncio.sleep(2)

        # Mock discovering accounts
        institution = MOCK_INSTITUTIONS.get(bank_link.institution_id, {})
        account_types = institution.get("supported_accounts", ["checking", "savings"])

        # Create 2-3 mock linked accounts
        num_accounts = random.randint(2, 3)
        for i in range(num_accounts):
            account_type = random.choice(account_types)

            # Generate mock account details
            account_num = f"****{random.randint(1000, 9999)}"
            balance = round(random.uniform(100, 50000), 2)

            linked_account = LinkedAccount(
                bank_link_id=bank_link_id,
                external_id=f"{bank_link.institution_id}_{uuid.uuid4().hex[:8]}",
                account_name=f"{institution.get('name', 'Bank')} {account_type.title()}",
                account_type=AccountType(account_type),
                account_number_masked=account_num,
                current_balance=balance,
                available_balance=balance * 0.95,  # 95% available
                is_active=True,
                last_sync=datetime.utcnow()
            )

            db_session.add(linked_account)

        # Update bank link status
        bank_link.status = BankLinkStatus.ACTIVE
        bank_link.last_sync = datetime.utcnow()
        bank_link.expires_at = datetime.utcnow() + timedelta(days=90)  # 90 day expiry

        db_session.commit()

    except Exception as e:
        # Mark as error
        bank_link.status = BankLinkStatus.ERROR
        bank_link.error_message = str(e)
        db_session.commit()

@router.get("/institutions")
async def get_supported_institutions():
    """Get list of supported bank institutions"""
    return [
        {
            "id": inst_id,
            "name": inst_data["name"],
            "logo": inst_data["logo"],
            "supported_account_types": inst_data["supported_accounts"]
        }
        for inst_id, inst_data in MOCK_INSTITUTIONS.items()
    ]

@router.post("/link", response_model=BankLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_bank_account(
    request: Request,
    link_request: BankLinkRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Link a bank account"""

    # Validate institution
    if link_request.institution_id not in MOCK_INSTITUTIONS:
        raise ValidationError("Invalid institution ID")

    # Check if already linked
    existing = db_session.query(BankLink).filter(
        BankLink.user_id == current_user['user_id'],
        BankLink.institution_id == link_request.institution_id,
        BankLink.status.in_([BankLinkStatus.PENDING, BankLinkStatus.ACTIVE])
    ).first()

    if existing:
        raise ValidationError("This institution is already linked")

    # Mock credential validation
    required_creds = ["username", "password"]
    for cred in required_creds:
        if cred not in link_request.credentials:
            raise ValidationError(f"Missing credential: {cred}")

    # Create bank link
    link_id = str(uuid.uuid4())
    bank_link = BankLink(
        user_id=current_user['user_id'],
        link_id=link_id,
        institution_id=link_request.institution_id,
        institution_name=MOCK_INSTITUTIONS[link_request.institution_id]["name"],
        access_token=f"mock_token_{uuid.uuid4().hex}"  # In production, encrypt this
    )

    db_session.add(bank_link)
    db_session.commit()
    db_session.refresh(bank_link)

    # Start background sync
    background_tasks.add_task(
        mock_bank_sync,
        bank_link.id,
        db_session
    )

    # Log the linking

    return BankLinkResponse(
        link_id=link_id,
        institution_name=bank_link.institution_name,
        status="pending",
        accounts_found=0
    )

@router.get("/links", response_model=list[BankLinkResponse])
async def get_bank_links(
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get all bank links for current user"""
    query = db_session.query(BankLink).filter(
        BankLink.user_id == current_user['user_id']
    )

    if not include_inactive:
        query = query.filter(BankLink.status != BankLinkStatus.ERROR)

    links = query.all()

    results = []
    for link in links:
        # Count linked accounts
        account_count = db_session.query(LinkedAccount).filter(
            LinkedAccount.bank_link_id == link.id,
            LinkedAccount.is_active == True
        ).count()

        results.append(
            BankLinkResponse(
                link_id=link.link_id,
                institution_name=link.institution_name,
                status=link.status.value,
                accounts_found=account_count,
                last_sync=link.last_sync,
                error_message=link.error_message
            )
        )

    return results

@router.get("/links/{link_id}/accounts", response_model=list[LinkedAccountResponse])
async def get_linked_accounts(
    link_id: str,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get accounts for a bank link"""
    # Get bank link
    bank_link = db_session.query(BankLink).filter(
        BankLink.link_id == link_id,
        BankLink.user_id == current_user['user_id']
    ).first()

    if not bank_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank link not found"
        )

    # Get linked accounts
    accounts = db_session.query(LinkedAccount).filter(
        LinkedAccount.bank_link_id == bank_link.id,
        LinkedAccount.is_active == True
    ).all()

    return [
        LinkedAccountResponse(
            id=acc.id,
            external_id=acc.external_id,
            institution_name=bank_link.institution_name,
            account_name=acc.account_name,
            account_type=acc.account_type,
            account_number_masked=acc.account_number_masked,
            current_balance=acc.current_balance,
            available_balance=acc.available_balance,
            last_sync=acc.last_sync
        )
        for acc in accounts
    ]

@router.post("/links/{link_id}/sync")
async def sync_bank_link(
    request: Request,
    link_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Manually trigger bank account sync"""

    # Get bank link
    bank_link = db_session.query(BankLink).filter(
        BankLink.link_id == link_id,
        BankLink.user_id == current_user['user_id']
    ).first()

    if not bank_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank link not found"
        )

    if bank_link.status == BankLinkStatus.PENDING:
        raise ValidationError("Sync already in progress")

    # Reset status
    bank_link.status = BankLinkStatus.PENDING
    db_session.commit()

    # Start background sync
    background_tasks.add_task(
        mock_bank_sync,
        bank_link.id,
        db_session
    )

    # Log the sync

    return {"message": "Sync started successfully"}

@router.post("/accounts/{linked_account_id}/import")
async def import_to_internal_account(
    request: Request,
    linked_account_id: int,
    account_name: str | None = None,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Import linked account as internal account"""

    # Get linked account
    linked_account = db_session.query(LinkedAccount).join(
        BankLink
    ).filter(
        LinkedAccount.id == linked_account_id,
        BankLink.user_id == current_user['user_id']
    ).first()

    if not linked_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked account not found"
        )

    if linked_account.account_id:
        raise ValidationError("Account already imported")

    # Create internal account
    internal_account = Account(
        user_id=current_user['user_id'],
        name=account_name or linked_account.account_name,
        account_type=linked_account.account_type,
        balance=linked_account.current_balance,
        currency="USD",
        is_active=True
    )

    db_session.add(internal_account)
    db_session.flush()

    # Link to external account
    linked_account.account_id = internal_account.id

    # Import recent transactions (mock)
    # In production, would fetch from bank API
    num_transactions = random.randint(10, 30)
    for i in range(num_transactions):
        days_ago = random.randint(1, 30)
        tx_date = datetime.utcnow() - timedelta(days=days_ago)

        # Random transaction
        is_debit = random.random() > 0.3  # 70% debits
        amount = round(random.uniform(5, 500), 2)

        transaction = Transaction(
            account_id=internal_account.id,
            amount=amount,
            transaction_type=TransactionType.DEBIT if is_debit else TransactionType.CREDIT,
            status=TransactionStatus.COMPLETED,
            description=f"Imported transaction {i+1}",
            transaction_date=tx_date,
            reference_number=f"IMP{uuid.uuid4().hex[:8]}"
        )

        db_session.add(transaction)

    db_session.commit()

    # Log the import

    return {
        "message": "Account imported successfully",
        "account_id": internal_account.id,
        "transactions_imported": num_transactions
    }

@router.delete("/links/{link_id}")
async def unlink_bank_account(
    request: Request,
    link_id: str,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Unlink a bank account"""

    # Get bank link
    bank_link = db_session.query(BankLink).filter(
        BankLink.link_id == link_id,
        BankLink.user_id == current_user['user_id']
    ).first()

    if not bank_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank link not found"
        )

    # Check if any accounts are imported
    imported_accounts = db_session.query(LinkedAccount).filter(
        LinkedAccount.bank_link_id == bank_link.id,
        LinkedAccount.account_id.isnot(None)
    ).count()

    if imported_accounts > 0:
        raise ValidationError(
            f"Cannot unlink: {imported_accounts} accounts are imported. "
            "Remove imported accounts first."
        )

    institution_name = bank_link.institution_name

    # Delete bank link (cascades to linked accounts)
    db_session.delete(bank_link)
    db_session.commit()

    # Log the unlink

    return {"message": "Bank account unlinked successfully"}

# Currency endpoints
@router.get("/currencies", response_model=list[CurrencyInfo])
async def get_supported_currencies():
    """Get list of supported currencies"""
    return [
        CurrencyInfo(
            code=code,
            name=CURRENCY_NAMES[code],
            symbol=CURRENCY_SYMBOLS[code],
            exchange_rate=rate
        )
        for code, rate in CURRENCY_RATES.items()
    ]

@router.post("/currency/convert", response_model=CurrencyConversion)
async def convert_currency(
    from_currency: str,
    to_currency: str,
    amount: float,
    current_user: dict = Depends(get_current_user)
):
    """Convert between currencies"""
    # Validate currencies
    if from_currency not in CURRENCY_RATES:
        raise ValidationError(f"Unsupported currency: {from_currency}")

    if to_currency not in CURRENCY_RATES:
        raise ValidationError(f"Unsupported currency: {to_currency}")

    # Convert through USD
    usd_amount = amount / CURRENCY_RATES[from_currency]
    converted_amount = usd_amount * CURRENCY_RATES[to_currency]

    # Calculate direct rate
    exchange_rate = CURRENCY_RATES[to_currency] / CURRENCY_RATES[from_currency]

    return CurrencyConversion(
        from_currency=from_currency,
        to_currency=to_currency,
        amount=amount,
        converted_amount=round(converted_amount, 2),
        exchange_rate=round(exchange_rate, 6),
        conversion_date=datetime.utcnow()
    )

@router.get("/statements/generate")
async def generate_statement(
    request: Request,
    account_id: int,
    month: int,
    year: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Generate a monthly statement"""

    # Verify account ownership
    account = db_session.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user['user_id']
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Calculate date range
    from datetime import calendar
    start_date = datetime(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59)

    # Get transactions
    transactions = db_session.query(Transaction).filter(
        Transaction.account_id == account_id,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).order_by(Transaction.transaction_date).all()

    # Calculate summary
    total_credits = sum(t.amount for t in transactions if t.transaction_type == TransactionType.CREDIT)
    total_debits = sum(t.amount for t in transactions if t.transaction_type == TransactionType.DEBIT)

    # Mock opening balance (in production, calculate from previous transactions)
    opening_balance = account.balance - (total_credits - total_debits)
    closing_balance = account.balance

    # Generate statement data
    statement = {
        "account": {
            "name": account.name,
            "type": account.account_type.value,
            "account_number": f"****{account.id % 10000:04d}"
        },
        "period": {
            "month": month,
            "year": year,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "summary": {
            "opening_balance": round(opening_balance, 2),
            "total_credits": round(total_credits, 2),
            "total_debits": round(total_debits, 2),
            "closing_balance": round(closing_balance, 2),
            "transaction_count": len(transactions)
        },
        "transactions": [
            {
                "date": t.transaction_date.isoformat(),
                "description": t.description,
                "type": t.transaction_type.value,
                "amount": t.amount,
                "balance": 0  # Would calculate running balance
            }
            for t in transactions
        ],
        "generated_at": datetime.utcnow().isoformat()
    }

    # Log statement generation

    return statement
