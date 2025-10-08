"""
Transaction Adapter for Backward Compatibility

This module provides adapter functions that integrate the new transaction
management system with existing API endpoints, ensuring backward compatibility
while adding new features like transaction state tracking and proper locking.

This allows gradual migration of existing code to use the new system.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Tuple, Dict, Any

from app.services.transaction_coordinator import (
    TransactionContext,
    TransactionState,
    get_transaction_coordinator,
    reset_transaction_coordinator
)
from app.services.transaction_handler import get_transaction_handler
from app.services.event_store import get_event_store


class TransactionResult:
    """Result of a transaction operation"""

    def __init__(self,
                 transaction_id: str,
                 state: str,
                 success: bool,
                 message: str = ""):
        """Initialize transaction result"""
        self.transaction_id = transaction_id
        self.state = state
        self.success = success
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'transaction_id': self.transaction_id,
            'state': self.state,
            'success': self.success,
            'message': self.message
        }


def safe_transfer(from_account_id: int,
                  to_account_id: int,
                  amount: float,
                  user_id: int,
                  description: str = "") -> TransactionResult:
    """
    Perform a safe transfer with transaction coordination.

    This is a drop-in replacement for existing transfer code that adds:
    - Proper locking
    - Atomic operations
    - Event recording
    - Transaction state tracking

    Usage:
        result = safe_transfer(from_acc, to_acc, 100.0, user_id)
        if result.success:
            print("Transfer completed")
        else:
            print(f"Transfer failed: {result.message}")

    Args:
        from_account_id: Source account ID
        to_account_id: Destination account ID
        amount: Amount to transfer
        user_id: User performing transfer
        description: Optional description

    Returns:
        TransactionResult with status and details
    """
    transaction_id = str(uuid.uuid4())

    try:
        # Create transaction context
        context = TransactionContext(
            transaction_id=transaction_id,
            user_id=user_id,
            transaction_type='transfer',
            amount=Decimal(str(amount)),
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            description=description
        )

        # Get handler and coordinator
        handler = get_transaction_handler()
        coordinator = get_transaction_coordinator()

        # Submit and process synchronously
        coordinator.submit_transaction(context)
        handler.handle_transfer(context)

        return TransactionResult(
            transaction_id=transaction_id,
            state=context.state,
            success=True,
            message="Transfer completed successfully"
        )

    except Exception as e:
        return TransactionResult(
            transaction_id=transaction_id,
            state=TransactionState.FAILED,
            success=False,
            message=str(e)
        )


def safe_payment(from_account_id: int,
                 amount: float,
                 user_id: int,
                 description: str = "") -> TransactionResult:
    """
    Perform a safe payment with transaction coordination.

    This is a drop-in replacement for existing payment code.

    Args:
        from_account_id: Source account ID
        amount: Payment amount
        user_id: User performing payment
        description: Optional description

    Returns:
        TransactionResult with status and details
    """
    transaction_id = str(uuid.uuid4())

    try:
        context = TransactionContext(
            transaction_id=transaction_id,
            user_id=user_id,
            transaction_type='payment',
            amount=Decimal(str(amount)),
            from_account_id=from_account_id,
            description=description
        )

        handler = get_transaction_handler()
        coordinator = get_transaction_coordinator()

        coordinator.submit_transaction(context)
        handler.handle_payment(context)

        return TransactionResult(
            transaction_id=transaction_id,
            state=context.state,
            success=True,
            message="Payment processed successfully"
        )

    except Exception as e:
        return TransactionResult(
            transaction_id=transaction_id,
            state=TransactionState.FAILED,
            success=False,
            message=str(e)
        )


def safe_investment_buy(account_id: int,
                       amount: float,
                       user_id: int,
                       description: str = "") -> TransactionResult:
    """
    Perform a safe investment buy order.

    Args:
        account_id: Account ID
        amount: Order amount
        user_id: User placing order
        description: Order description

    Returns:
        TransactionResult with status and details
    """
    transaction_id = str(uuid.uuid4())

    try:
        context = TransactionContext(
            transaction_id=transaction_id,
            user_id=user_id,
            transaction_type='investment_buy',
            amount=Decimal(str(amount)),
            from_account_id=account_id,
            description=description
        )

        handler = get_transaction_handler()
        coordinator = get_transaction_coordinator()

        coordinator.submit_transaction(context)
        handler.handle_investment_buy(context)

        return TransactionResult(
            transaction_id=transaction_id,
            state=context.state,
            success=True,
            message="Buy order placed successfully"
        )

    except Exception as e:
        return TransactionResult(
            transaction_id=transaction_id,
            state=TransactionState.FAILED,
            success=False,
            message=str(e)
        )


def get_transaction_status(transaction_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of a transaction.

    Can be used in API endpoints to check transaction progress.

    Args:
        transaction_id: The transaction ID

    Returns:
        Dictionary with transaction status or None if not found
    """
    coordinator = get_transaction_coordinator()
    context = coordinator.get_transaction_status(transaction_id)

    if context:
        duration_ms = None
        if context.duration():
            duration_ms = context.duration().total_seconds() * 1000

        return {
            'transaction_id': context.transaction_id,
            'state': context.state.value,
            'amount': str(context.amount),
            'created_at': context.created_at.isoformat(),
            'started_at': context.started_at.isoformat() if context.started_at else None,
            'completed_at': (
                context.completed_at.isoformat()
                if context.completed_at else None
            ),
            'duration_ms': duration_ms,
            'error_message': context.error_message
        }

    return None


def get_account_transaction_history(account_id: int,
                                   max_count: int = 100) -> list:
    """
    Get transaction history for an account.

    Can be used to display account statements.

    Args:
        account_id: The account ID
        max_count: Maximum number of transactions to return

    Returns:
        List of transactions
    """
    event_store = get_event_store()
    events = event_store.get_account_events(account_id)

    # Convert to transaction format
    transactions = []
    for event in events[-max_count:]:  # Get last N events
        transactions.append({
            'event_id': event.event_id,
            'transaction_id': event.transaction_id,
            'type': event.event_type.value,
            'amount': str(event.amount),
            'timestamp': event.timestamp.isoformat(),
            'status': event.status.value,
            'description': event.description
        })

    return transactions


def get_user_transaction_stats(user_id: int) -> Dict[str, Any]:
    """
    Get transaction statistics for a user.

    Args:
        user_id: The user ID

    Returns:
        Dictionary with transaction statistics
    """
    event_store = get_event_store()
    coordinator = get_transaction_coordinator()

    # Get all user events
    events = event_store.get_user_events(user_id)

    # Calculate statistics
    completed_transactions = sum(
        1 for e in events if 'completed' in e.event_type.value
    )
    failed_transactions = sum(
        1 for e in events if 'failed' in e.event_type.value
    )
    total_transferred = sum(
        e.amount for e in events
        if 'transfer' in e.event_type.value and 'completed' in e.event_type.value
    )

    return {
        'user_id': user_id,
        'total_events': len(events),
        'completed_transactions': completed_transactions,
        'failed_transactions': failed_transactions,
        'total_transferred': str(total_transferred),
        'coordinator_stats': coordinator.get_statistics(),
        'queue_size': coordinator.get_queue_size()
    }


def export_transaction_audit(user_id: int) -> str:
    """
    Export complete transaction audit trail for a user (JSON format).

    This can be used for compliance reporting.

    Args:
        user_id: The user ID

    Returns:
        JSON string of audit trail
    """
    event_store = get_event_store()
    return event_store.export_for_audit(user_id)


# ============================================================================
# Initialization and Setup Functions
# ============================================================================

def initialize_transaction_system() -> None:
    """
    Initialize the transaction management system.

    This should be called once at application startup.
    """
    coordinator = get_transaction_coordinator()
    coordinator.start_processing()


def shutdown_transaction_system() -> None:
    """
    Shutdown the transaction management system.

    This should be called at application shutdown.
    """
    coordinator = get_transaction_coordinator()
    coordinator.stop_processing()


def reset_transaction_system_for_testing() -> None:
    """
    Reset the entire transaction system (for testing only).

    WARNING: This clears all transaction data and event logs.
    """
    from app.services.event_store import reset_event_store
    from app.services.transaction_handler import reset_transaction_handler

    reset_event_store()
    reset_transaction_coordinator()
    reset_transaction_handler()


# ============================================================================
# Migration Guide
# ============================================================================

"""
MIGRATION GUIDE: How to update existing transaction code

Before (existing code):
    account.balance -= amount
    db.commit()

After (new code - option 1: Drop-in replacement):
    result = safe_transfer(from_account, to_account, amount, user_id)
    if result.success:
        # Transaction completed
    else:
        # Handle error
        raise Exception(result.message)

After (new code - option 2: With state tracking):
    result = safe_transfer(from_account, to_account, amount, user_id)

    # Check status asynchronously
    status = get_transaction_status(result.transaction_id)

    # In API endpoint:
    # GET /transactions/{id} returns current state
    # Possible states: pending, processing, completed, failed

Features gained:
✅ Atomic transactions (no partial updates)
✅ Optimistic locking (prevents concurrent modification)
✅ Complete event history (audit trail)
✅ Transaction state tracking (pending→processing→completed)
✅ Double-spending prevention
✅ Overdraft protection
✅ Concurrent transaction safety

Example: Payment Processing
    def make_payment(account_id, amount, user_id):
        result = safe_payment(account_id, amount, user_id)

        if result.success:
            # Emit payment completed event
            emit_event('payment_completed', {
                'transaction_id': result.transaction_id,
                'amount': amount
            })
        else:
            # Emit payment failed event
            emit_event('payment_failed', {
                'transaction_id': result.transaction_id,
                'error': result.message
            })
"""
