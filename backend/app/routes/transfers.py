from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional, Any
from datetime import datetime
from decimal import Decimal

from ..storage.memory_adapter import db, or_, and_
from ..models import Account, Transaction, TransactionType, TransactionStatus, User, Notification, NotificationType, Contact, ContactStatus, DirectMessage
from ..models import (
    TransferRequest, TransferResponse, DepositRequest, WithdrawalRequest, 
    TransactionResponse, BillPaymentRequest
)
from ..utils.auth import get_current_user
from ..utils.validators import Validators, ValidationError
from ..utils.session_manager import session_manager
from pydantic import BaseModel, Field

router = APIRouter()

# Pydantic model for send money request
class SendMoneyRequest(BaseModel):
    recipient_identifier: str  # username or email
    source_account_id: int
    amount: float = Field(gt=0)
    description: Optional[str] = None
    transfer_fee: Optional[float] = 0.0  # Fee to be deducted from amount

@router.post("/transfer", response_model=TransactionResponse)
async def transfer_money(
    request: Request,
    transfer_data: TransferRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Transfer money between accounts"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    # Validate accounts exist and belong to user
    source_account = Validators.validate_account_ownership(
        db_session, transfer_data.source_account_id, current_user['user_id']
    )
    
    # For transfers to external accounts, validate destination differently
    if transfer_data.is_external:
        # External transfer logic - could integrate with banking API
        destination_account = None
        destination_user_id = None
    else:
        destination_account = db_session.query(Account).filter_by(
            id=transfer_data.destination_account_id
        ).first()
        
        if not destination_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Destination account not found"
            )
        
        destination_user_id = destination_account.user_id
    
    # Check sufficient balance
    if source_account.balance < transfer_data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    # Create debit transaction
    debit_transaction = Transaction(
        user_id=current_user['user_id'],
        account_id=source_account.id,
        amount=transfer_data.amount,  # Positive amount, type determines debit/credit
        transaction_type=TransactionType.DEBIT,  # Use DEBIT type for outgoing transfer
        status=TransactionStatus.COMPLETED,
        description=transfer_data.description or f"Transfer to {transfer_data.destination_account_id}",
        reference_number=f"TRF{datetime.now().strftime('%Y%m%d%H%M%S')}",
        transaction_date=datetime.utcnow(),
        category_id=15,  # Transfer category
        metadata={
            "transfer_type": "debit",
            "destination_account_id": transfer_data.destination_account_id,
            "is_external": transfer_data.is_external
        }
    )
    
    # Update source account balance
    source_account.balance -= transfer_data.amount
    
    db_session.add(debit_transaction)
    
    # Create credit transaction if internal transfer
    if not transfer_data.is_external and destination_account:
        credit_transaction = Transaction(
            user_id=destination_user_id,
            account_id=destination_account.id,
            amount=transfer_data.amount,  # Positive amount for credit
            transaction_type=TransactionType.CREDIT,  # Use CREDIT type for incoming transfer
            status=TransactionStatus.COMPLETED,
            description=f"Transfer from {source_account.name}",
            reference_number=f"TRF{datetime.now().strftime('%Y%m%d%H%M%S')}",
            transaction_date=datetime.utcnow(),
            category_id=15,  # Transfer category
            metadata={
                "transfer_type": "credit",
                "source_account_id": source_account.id,
                "is_external": False
            }
        )
        
        # Update destination account balance
        destination_account.balance += transfer_data.amount
        
        db_session.add(credit_transaction)
    
    # Create notification for sender
    sender_notification = Notification(
        user_id=current_user['user_id'],
        type=NotificationType.TRANSACTION_ALERT,
        title="Transfer Complete",
        message=f"You transferred ${transfer_data.amount:.2f}" + (f" to account {transfer_data.destination_account_id}" if not transfer_data.is_external else " (External Transfer)"),
        action_url=f"/transactions/{debit_transaction.id}",
        is_read=False,
        metadata={
            "transaction_id": debit_transaction.id,
            "amount": transfer_data.amount,
            "transfer_type": "external" if transfer_data.is_external else "internal"
        }
    )
    db_session.add(sender_notification)
    
    # Create notification for recipient if internal transfer
    if not transfer_data.is_external and destination_account and destination_user_id:
        # Get recipient user details
        recipient_user = db_session.query(User).filter_by(id=destination_user_id).first()
        sender_name = db_session.query(User).filter_by(id=current_user['user_id']).first()
        
        recipient_notification = Notification(
            user_id=destination_user_id,
            type=NotificationType.TRANSACTION_ALERT,
            title="Transfer Received",
            message=f"You received ${transfer_data.amount:.2f} from {sender_name.username if sender_name else 'a user'}",
            action_url=f"/transactions/{credit_transaction.id}",
            is_read=False,
            metadata={
                "transaction_id": credit_transaction.id,
                "amount": transfer_data.amount,
                "sender": sender_name.username if sender_name else 'Unknown'
            }
        )
        db_session.add(recipient_notification)
    
    db_session.commit()
    
    # Create transaction message if users are contacts
    if not transfer_data.is_external and destination_account:
        contact = db_session.query(Contact).filter(
            or_(
                and_(
                    Contact.user_id == current_user['user_id'],
                    Contact.contact_id == destination_account.user_id,
                    Contact.status == ContactStatus.ACCEPTED
                ),
                and_(
                    Contact.user_id == destination_account.user_id,
                    Contact.contact_id == current_user['user_id'],
                    Contact.status == ContactStatus.ACCEPTED
                )
            )
        ).first()
        
        if contact:
            # Get conversation (create if needed)
            from ..routes.conversations import get_or_create_conversation
            conversation = get_or_create_conversation(
                db_session, 
                current_user['user_id'], 
                destination_account.user_id
            )
            
            # Create transaction message
            transaction_message = DirectMessage(
                sender_id=current_user['user_id'],
                recipient_id=destination_account.user_id,
                subject=f"Money Transfer - ${transfer_data.amount}",
                message=f"Sent you ${transfer_data.amount}" + (f": {transfer_data.note}" if transfer_data.note else ""),
                priority="normal",
                message_type="transaction",
                metadata={
                    "transaction_id": debit_transaction.id,
                    "amount": float(transfer_data.amount),
                    "direction": "sent",
                    "note": transfer_data.note,
                    "transaction_date": debit_transaction.transaction_date.isoformat()
                },
                is_draft=False,
                is_read=False,
                sent_at=datetime.utcnow()
            )
            db_session.add(transaction_message)
            
            # Update conversation last message time
            conversation.last_message_at = datetime.utcnow()
            
            db_session.commit()
    
    # Log transfer
        session_id,
        debit_transaction.id,
        current_user['user_id'],
        source_account.id,
        transfer_data.destination_account_id,
        float(transfer_data.amount),
        transfer_data.is_external
    )
    
    # Instead of refreshing, create a response directly from the transaction object
    # This ensures we return the correct transaction without database lookup issues
    from ..models import TransactionResponse
    return TransactionResponse(
        id=debit_transaction.id,
        created_at=debit_transaction.created_at,
        updated_at=debit_transaction.updated_at,
        account_id=debit_transaction.account_id,
        category_id=debit_transaction.category_id,
        merchant_id=debit_transaction.merchant_id,
        merchant=None,
        amount=debit_transaction.amount,
        transaction_type=debit_transaction.transaction_type,
        status=debit_transaction.status,
        description=debit_transaction.description,
        notes=debit_transaction.notes,
        tags=debit_transaction.tags if hasattr(debit_transaction, 'tags') else [],
        attachments=debit_transaction.attachments if hasattr(debit_transaction, 'attachments') else [],
        transaction_date=debit_transaction.transaction_date,
        from_account_id=debit_transaction.from_account_id if hasattr(debit_transaction, 'from_account_id') else None,
        to_account_id=debit_transaction.to_account_id if hasattr(debit_transaction, 'to_account_id') else None,
        reference_number=debit_transaction.reference_number,
        recurring_rule_id=debit_transaction.recurring_rule_id if hasattr(debit_transaction, 'recurring_rule_id') else None
    )


@router.post("/deposit", response_model=TransactionResponse)
async def deposit_money(
    request: Request,
    deposit_data: DepositRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Deposit money to an account"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    # Validate account exists and belongs to user
    account = Validators.validate_account_ownership(
        db_session, deposit_data.account_id, current_user['user_id']
    )
    
    # Create deposit transaction
    transaction = Transaction(
        account_id=account.id,
        amount=deposit_data.amount,
        transaction_type=TransactionType.CREDIT,  # Deposits are credits
        status=TransactionStatus.COMPLETED,
        description=deposit_data.description or "Deposit",
        reference_number=f"DEP{datetime.now().strftime('%Y%m%d%H%M%S')}",
        transaction_date=datetime.utcnow()
    )
    
    # Update account balance
    account.balance += deposit_data.amount
    
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    
    # Log deposit
        session_id,
        transaction.id,
        current_user['user_id'],
        account.id,
        float(deposit_data.amount),
        deposit_data.deposit_method
    )
    
    return transaction


@router.post("/withdraw", response_model=TransactionResponse)
async def withdraw_money(
    request: Request,
    withdrawal_data: WithdrawalRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Withdraw money from an account"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    # Validate account exists and belongs to user
    account = Validators.validate_account_ownership(
        db_session, withdrawal_data.account_id, current_user['user_id']
    )
    
    # Check sufficient balance
    if account.balance < withdrawal_data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    # Create withdrawal transaction
    transaction = Transaction(
        user_id=current_user['user_id'],
        account_id=account.id,
        amount=withdrawal_data.amount,  # Positive amount for DEBIT transactions
        transaction_type=TransactionType.DEBIT,  # Withdrawals are debits
        status=TransactionStatus.COMPLETED,
        description=withdrawal_data.description or "Withdrawal",
        reference_number=f"WDR{datetime.now().strftime('%Y%m%d%H%M%S')}",
        metadata={
            "withdrawal_method": withdrawal_data.withdrawal_method
        }
    )
    
    # Update account balance
    account.balance -= withdrawal_data.amount
    
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    
    # Log withdrawal
        session_id,
        transaction.id,
        current_user['user_id'],
        account.id,
        float(withdrawal_data.amount),
        withdrawal_data.withdrawal_method
    )
    
    return transaction


@router.post("/bill-payment", response_model=TransactionResponse)
async def pay_bill(
    request: Request,
    payment_data: BillPaymentRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Pay a bill"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    # Validate account exists and belongs to user
    account = Validators.validate_account_ownership(
        db_session, payment_data.account_id, current_user['user_id']
    )
    
    # Check sufficient balance
    if account.balance < payment_data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    # Create bill payment transaction
    transaction = Transaction(
        user_id=current_user['user_id'],
        account_id=account.id,
        amount=payment_data.amount,  # Positive amount for DEBIT transactions
        transaction_type=TransactionType.DEBIT,  # Bill payments are debits
        status=TransactionStatus.COMPLETED,
        description=f"Bill payment to {payment_data.payee_name}",
        merchant_name=payment_data.payee_name,
        category_id=payment_data.category_id,
        reference_number=f"BILL{datetime.now().strftime('%Y%m%d%H%M%S')}",
        metadata={
            "bill_type": payment_data.bill_type,
            "account_number": payment_data.payee_account_number,
            "due_date": payment_data.due_date.isoformat() if payment_data.due_date else None
        }
    )
    
    # Update account balance
    account.balance -= payment_data.amount
    
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    
    # Log bill payment
        session_id,
        transaction.id,
        current_user['user_id'],
        account.id,
        float(payment_data.amount),
        payment_data.payee_name,
        payment_data.bill_type
    )
    
    return transaction


@router.get("/transfer-limits")
async def get_transfer_limits(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get user's transfer limits"""
    # This would typically fetch from user settings or account type
    return {
        "daily_limit": 10000.00,
        "single_transaction_limit": 5000.00,
        "monthly_limit": 50000.00,
        "remaining_daily": 8500.00,
        "remaining_monthly": 42000.00
    }


@router.post("/send-money", response_model=TransactionResponse)
async def send_money(
    request: Request,
    send_data: SendMoneyRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Send money to another user by username or email"""
    session_id = request.cookies.get("session_id") or session_manager.get_session() or "no_session"
    
    # Validate source account exists and belongs to sender
    source_account = Validators.validate_account_ownership(
        db_session, send_data.source_account_id, current_user['user_id']
    )
    
    # Find recipient user by username or email
    recipient_user = db_session.query(User).filter(
        (User.username == send_data.recipient_identifier) | 
        (User.email == send_data.recipient_identifier)
    ).first()
    
    if not recipient_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    
    # Cannot send money to yourself
    if recipient_user.id == current_user['user_id']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send money to yourself"
        )
    
    # Get recipient's default account (checking account)
    recipient_account = db_session.query(Account).filter(
        Account.user_id == recipient_user.id,
        Account.account_type == "CHECKING",
        Account.is_active == True
    ).first()
    
    if not recipient_account:
        # Try to get any active account
        recipient_account = db_session.query(Account).filter(
            Account.user_id == recipient_user.id,
            Account.is_active == True
        ).first()
        
    if not recipient_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipient has no active accounts"
        )
    
    # Calculate total amount to deduct from sender (including fee)
    fee = send_data.transfer_fee or 0.0
    total_amount = send_data.amount + fee
    
    # Check sufficient balance (including fee)
    if source_account.balance < total_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    # Store old balances for logging
    old_source_balance = source_account.balance
    old_recipient_balance = recipient_account.balance
    
    # Create debit transaction for sender (including fee)
    debit_transaction = Transaction(
        user_id=current_user['user_id'],
        account_id=source_account.id,
        amount=total_amount,  # Include fee in debit
        transaction_type=TransactionType.DEBIT,
        status=TransactionStatus.COMPLETED,
        description=send_data.description or f"Sent to {recipient_user.username}",
        reference_number=f"SND{datetime.now().strftime('%Y%m%d%H%M%S')}",
        transaction_date=datetime.utcnow(),
        category_id=15,  # Transfer category
        metadata={
            "transfer_type": "send_money",
            "recipient_user_id": recipient_user.id,
            "recipient_account_id": recipient_account.id,
            "recipient_identifier": send_data.recipient_identifier,
            "fee": fee,
            "base_amount": send_data.amount
        }
    )
    
    # Create credit transaction for recipient (base amount only)
    credit_transaction = Transaction(
        user_id=recipient_user.id,
        account_id=recipient_account.id,
        amount=send_data.amount,  # Only base amount, no fee
        transaction_type=TransactionType.CREDIT,
        status=TransactionStatus.COMPLETED,
        description=f"Received from {current_user.get('username', 'User')}",
        reference_number=f"RCV{datetime.now().strftime('%Y%m%d%H%M%S')}",
        transaction_date=datetime.utcnow(),
        category_id=15,  # Transfer category
        metadata={
            "transfer_type": "receive_money",
            "sender_user_id": current_user['user_id'],
            "sender_account_id": source_account.id,
            "sender_username": current_user.get('username', 'User')
        }
    )
    
    # Update account balances
    source_account.balance -= total_amount  # Deduct full amount including fee
    recipient_account.balance += send_data.amount  # Credit only base amount
    
    # Add transactions to database
    db_session.add(debit_transaction)
    db_session.add(credit_transaction)
    
    # Create notifications for both users
    sender_notification = Notification(
        user_id=current_user['user_id'],
        type=NotificationType.TRANSACTION_ALERT,
        title="Money Sent",
        message=f"You sent ${send_data.amount:.2f} to {recipient_user.username}",
        action_url=f"/transactions/{debit_transaction.id}",
        is_read=False,
        metadata={
            "transaction_id": debit_transaction.id,
            "amount": send_data.amount,
            "recipient": recipient_user.username
        }
    )
    
    recipient_notification = Notification(
        user_id=recipient_user.id,
        type=NotificationType.TRANSACTION_ALERT,
        title="Money Received",
        message=f"You received ${send_data.amount:.2f} from {current_user.get('username', 'User')}",
        action_url=f"/transactions/{credit_transaction.id}",
        is_read=False,
        metadata={
            "transaction_id": credit_transaction.id,
            "amount": send_data.amount,
            "sender": current_user.get('username', 'User')
        }
    )
    
    db_session.add(sender_notification)
    db_session.add(recipient_notification)
    
    # Commit all changes
    db_session.commit()
    db_session.refresh(debit_transaction)
    db_session.refresh(credit_transaction)
    
        session_id,
        debit_transaction.id,
        current_user['user_id'],
        source_account.id,
        recipient_account.id,
        float(send_data.amount),
        False  # Not external
    )
    
    # Log balance updates
        session_id,
        source_account.id,
        float(old_source_balance),
        float(source_account.balance),
        "Send money"
    )
    
        session_id,
        recipient_account.id,
        float(old_recipient_balance),
        float(recipient_account.balance),
        "Receive money"
    )
    
    return debit_transaction