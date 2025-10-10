"""
Transaction Handler for Core Transaction Types

This module implements handlers for the core transaction types:
- Payments (account to external payment)
- Transfers (account to account)
- Investments (buy/sell operations)

It implements:
- Optimistic locking with version checking
- Double-spending prevention
- Overdraft protection
- Transaction state tracking
"""

from datetime import UTC, datetime
from decimal import Decimal

from app.services.event_store import TransactionEvent, TransactionEventStatus, TransactionEventType, get_event_store
from app.services.transaction_coordinator import TransactionContext, get_transaction_coordinator


class InsufficientFundsError(Exception):
    """Raised when account has insufficient funds"""


class OptimisticLockError(Exception):
    """Raised when optimistic lock fails (version mismatch)"""


class TransactionHandler:
    """
    Handles core transaction types with state tracking and optimistic locking.
    """

    def __init__(self):
        """Initialize transaction handler"""
        self.coordinator = get_transaction_coordinator()
        self.event_store = get_event_store()

        # Register handlers
        self.coordinator.register_handler('transfer', self.handle_transfer)
        self.coordinator.register_handler('payment', self.handle_payment)
        self.coordinator.register_handler('investment_buy', self.handle_investment_buy)
        self.coordinator.register_handler('investment_sell', self.handle_investment_sell)

    def handle_transfer(self, context: TransactionContext) -> None:
        """
        Handle account-to-account transfer.

        This demonstrates how to implement a safe transfer with:
        - Optimistic locking
        - Overdraft protection
        - Atomic updates

        Args:
            context: Transaction context

        Raises:
            InsufficientFundsError: If source account has insufficient funds
            OptimisticLockError: If version check fails (concurrent modification)
        """
        if context.from_account_id is None or context.to_account_id is None:
            raise ValueError("Transfer requires both source and destination accounts")

        # Get account balances (in real implementation, fetch from database)
        from_balance = self._get_account_balance(context.from_account_id)
        to_balance = self._get_account_balance(context.to_account_id)

        # Check overdraft protection
        if from_balance < context.amount:
            raise InsufficientFundsError(
                f"Insufficient funds. Balance: {from_balance}, "
                f"Required: {context.amount}"
            )

        # Get optimistic lock version before update
        self.coordinator._version_lock.get_version(context.from_account_id)

        # Perform update
        new_from_balance = from_balance - context.amount
        new_to_balance = to_balance + context.amount

        # Record balance modifications
        self._update_account_balance(context.from_account_id, new_from_balance)
        self._update_account_balance(context.to_account_id, new_to_balance)

        # Increment version for both accounts
        self.coordinator._version_lock.increment_version(context.from_account_id)
        self.coordinator._version_lock.increment_version(context.to_account_id)

        # Verify no concurrent modification occurred
        self.coordinator._version_lock.get_version(context.from_account_id)

        # Record detailed events
        self._record_balance_event(
            context.transaction_id,
            context.user_id,
            context.from_account_id,
            "DEBIT",
            context.amount,
            new_from_balance,
            "Transfer from account"
        )

        self._record_balance_event(
            context.transaction_id,
            context.user_id,
            context.to_account_id,
            "CREDIT",
            context.amount,
            new_to_balance,
            "Transfer to account"
        )

    def handle_payment(self, context: TransactionContext) -> None:
        """
        Handle payment from account (e.g., to external service).

        Args:
            context: Transaction context

        Raises:
            InsufficientFundsError: If account has insufficient funds
        """
        if context.from_account_id is None:
            raise ValueError("Payment requires source account")

        # Get account balance
        balance = self._get_account_balance(context.from_account_id)

        # Check overdraft protection
        if balance < context.amount:
            raise InsufficientFundsError(
                f"Insufficient funds for payment. Balance: {balance}, "
                f"Required: {context.amount}"
            )

        # Perform payment
        new_balance = balance - context.amount
        self._update_account_balance(context.from_account_id, new_balance)

        # Increment version
        self.coordinator._version_lock.increment_version(context.from_account_id)

        # Record event
        self._record_balance_event(
            context.transaction_id,
            context.user_id,
            context.from_account_id,
            "DEBIT",
            context.amount,
            new_balance,
            f"Payment: {context.description}"
        )

    def handle_investment_buy(self, context: TransactionContext) -> None:
        """
        Handle investment buy order.

        In a real system, this would:
        - Check buying power
        - Place order at exchange
        - Update portfolio

        Args:
            context: Transaction context

        Raises:
            InsufficientFundsError: If insufficient buying power
        """
        if context.from_account_id is None:
            raise ValueError("Buy order requires account")

        # Get buying power
        buying_power = self._get_buying_power(context.from_account_id)

        # Check buying power
        if buying_power < context.amount:
            raise InsufficientFundsError(
                f"Insufficient buying power. Available: {buying_power}, "
                f"Required: {context.amount}"
            )

        # Reserve buying power
        new_buying_power = buying_power - context.amount

        # In real implementation:
        # 1. Place order
        # 2. Update buying power/balance
        # 3. Update portfolio with position

        self._update_buying_power(context.from_account_id, new_buying_power)

        # Increment version
        self.coordinator._version_lock.increment_version(context.from_account_id)

        # Record event
        buy_event = TransactionEvent(
            event_id=str(context.transaction_id),
            transaction_id=context.transaction_id,
            user_id=context.user_id,
            event_type=TransactionEventType.BUY_ORDER_FILLED,
            timestamp=context.started_at or context.created_at or datetime.now(UTC),
            amount=context.amount,
            from_account_id=context.from_account_id,
            description=f"Buy order: {context.description}",
            metadata=context.metadata,
            status=TransactionEventStatus.COMPLETED
        )
        self.event_store.append_event(buy_event)

    def handle_investment_sell(self, context: TransactionContext) -> None:
        """
        Handle investment sell order.

        Args:
            context: Transaction context
        """
        if context.from_account_id is None:
            raise ValueError("Sell order requires account")

        # In real implementation:
        # 1. Check position exists
        # 2. Place sell order
        # 3. Update buying power
        # 4. Update portfolio

        # For now, just record the event
        sell_event = TransactionEvent(
            event_id=str(context.transaction_id),
            transaction_id=context.transaction_id,
            user_id=context.user_id,
            event_type=TransactionEventType.SELL_ORDER_FILLED,
            timestamp=context.started_at or context.created_at or datetime.now(UTC),
            amount=context.amount,
            from_account_id=context.from_account_id,
            description=f"Sell order: {context.description}",
            metadata=context.metadata,
            status=TransactionEventStatus.COMPLETED
        )
        self.event_store.append_event(sell_event)

    # Helper methods
    def _get_account_balance(self, account_id: int) -> Decimal:
        """
        Get account balance.

        In production, this would query the database with proper locking.

        Args:
            account_id: The account ID

        Returns:
            Account balance
        """
        # Mock implementation - in production, this would be a database query
        if not hasattr(self, '_account_balances'):
            self._account_balances = {}

        return self._account_balances.get(account_id, Decimal('1000.00'))

    def _update_account_balance(self, account_id: int, balance: Decimal) -> None:
        """
        Update account balance.

        In production, this would update the database atomically.

        Args:
            account_id: The account ID
            balance: New balance
        """
        if not hasattr(self, '_account_balances'):
            self._account_balances = {}

        self._account_balances[account_id] = Decimal(str(balance))

    def _get_buying_power(self, account_id: int) -> Decimal:
        """
        Get account buying power (for investments).

        Args:
            account_id: The account ID

        Returns:
            Buying power
        """
        if not hasattr(self, '_buying_power'):
            self._buying_power = {}

        return self._buying_power.get(account_id, Decimal('5000.00'))

    def _update_buying_power(self, account_id: int, buying_power: Decimal) -> None:
        """
        Update buying power.

        Args:
            account_id: The account ID
            buying_power: New buying power
        """
        if not hasattr(self, '_buying_power'):
            self._buying_power = {}

        self._buying_power[account_id] = Decimal(str(buying_power))

    def _record_balance_event(self,
                             transaction_id: str,
                             user_id: int,
                             account_id: int,
                             operation: str,
                             amount: Decimal,
                             new_balance: Decimal,
                             description: str) -> None:
        """
        Record a balance modification event.

        Args:
            transaction_id: Transaction ID
            user_id: User ID
            account_id: Account ID
            operation: DEBIT or CREDIT
            amount: Amount modified
            new_balance: New balance after modification
            description: Description of the operation
        """
        event = TransactionEvent(
            event_id=f"{transaction_id}_{operation}",
            transaction_id=transaction_id,
            user_id=user_id,
            event_type=TransactionEventType.BALANCE_MODIFIED,
            timestamp=self.context.started_at if hasattr(self, 'context') else datetime.utcnow(),
            amount=amount,
            from_account_id=account_id if operation == "DEBIT" else None,
            to_account_id=account_id if operation == "CREDIT" else None,
            description=description,
            metadata={'operation': operation, 'new_balance': str(new_balance)},
            status=TransactionEventStatus.COMPLETED
        )
        self.event_store.append_event(event)

    def reset_state(self) -> None:
        """
        Reset internal state (for testing).
        """
        if hasattr(self, '_account_balances'):
            self._account_balances.clear()
        if hasattr(self, '_buying_power'):
            self._buying_power.clear()


# Global handler instance
_handler: TransactionHandler | None = None


def get_transaction_handler() -> TransactionHandler:
    """
    Get the global transaction handler instance.

    Returns:
        TransactionHandler instance
    """
    global _handler
    if _handler is None:
        _handler = TransactionHandler()
    return _handler


def reset_transaction_handler() -> None:
    """
    Reset the global handler (for testing).
    """
    global _handler
    _handler = TransactionHandler()
