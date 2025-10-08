"""
Mock database adapter to provide SQLAlchemy-like interface for mock data.
"""
import uuid
from datetime import datetime
from typing import Any, TypeVar

T = TypeVar('T')

class MockQuery:
    """Mock query object that mimics SQLAlchemy Query interface."""

    def __init__(self, model_class: type[T], data_store: list[dict[str, Any]]):
        self.model_class = model_class
        self.data_store = data_store
        self.filters = []
        self.order_by_field = None
        self.order_desc = False
        self._limit = None
        self._offset = None

    def filter_by(self, **kwargs):
        """Add filter conditions."""
        for key, value in kwargs.items():
            self.filters.append((key, '==', value))
        return self

    def filter(self, *conditions):
        """Add filter conditions using SQLAlchemy-style conditions."""
        # For now, just support simple equality
        return self

    def order_by(self, field):
        """Set ordering."""
        if hasattr(field, 'desc'):
            self.order_by_field = str(field).replace('.desc()', '')
            self.order_desc = True
        else:
            self.order_by_field = str(field)
            self.order_desc = False
        return self

    def limit(self, limit: int):
        """Set result limit."""
        self._limit = limit
        return self

    def offset(self, offset: int):
        """Set result offset."""
        self._offset = offset
        return self

    def first(self) -> T | None:
        """Get first result."""
        results = self._execute_query()
        return results[0] if results else None

    def all(self) -> list[T]:
        """Get all results."""
        return self._execute_query()

    def count(self) -> int:
        """Count results."""
        return len(self._execute_query())

    def _execute_query(self) -> list[T]:
        """Execute the query and return results."""
        results = self.data_store.copy()

        # Apply filters
        for field, op, value in self.filters:
            results = [r for r in results if self._match_filter(r, field, op, value)]

        # Apply ordering
        if self.order_by_field:
            results.sort(key=lambda x: x.get(self.order_by_field, ''), reverse=self.order_desc)

        # Apply offset and limit
        if self._offset:
            results = results[self._offset:]
        if self._limit:
            results = results[:self._limit]

        # Convert to model objects
        return [self._dict_to_model(r) for r in results]

    def _match_filter(self, record: dict[str, Any], field: str, op: str, value: Any) -> bool:
        """Check if record matches filter condition."""
        record_value = record.get(field)
        if op == '==':
            return record_value == value
        if op == '!=':
            return record_value != value
        if op == '<':
            return record_value < value if record_value is not None else False
        if op == '>':
            return record_value > value if record_value is not None else False
        return True

    def _dict_to_model(self, data: dict[str, Any]) -> T:
        """Convert dictionary to model object."""
        # Create a simple object with attributes
        obj = type('MockModel', (), {})()
        for key, value in data.items():
            setattr(obj, key, value)
        return obj


class MockSession:
    """Mock session object that mimics SQLAlchemy Session interface."""

    def __init__(self):
        from app.repositories.data_manager import data_manager
        self.data_manager = data_manager
        self._pending_commits = []

    def query(self, model_class: type[T]) -> MockQuery:
        """Create a query for the given model."""
        # Map model class to data store
        model_name = model_class.__name__.lower()

        # Get appropriate data store from data_manager
        if model_name == 'user':
            data_store = self.data_manager.users
        elif model_name == 'account':
            data_store = self.data_manager.accounts
        elif model_name == 'transaction':
            data_store = self.data_manager.transactions
        elif model_name == 'category':
            data_store = self.data_manager.categories
        elif model_name == 'card' or model_name == 'virtualcard':
            data_store = self.data_manager.cards
        elif model_name == 'budget':
            data_store = self.data_manager.budgets
        elif model_name == 'goal':
            data_store = self.data_manager.goals
        elif model_name == 'notification':
            data_store = self.data_manager.notifications
        elif model_name == 'message':
            data_store = self.data_manager.messages
        elif model_name == 'bill':
            data_store = self.data_manager.bills
        elif model_name == 'subscription':
            data_store = self.data_manager.subscriptions
        elif model_name == 'creditscore':
            data_store = self.data_manager.credit_scores
        elif model_name == 'socialconnection':
            data_store = self.data_manager.social_connections
        elif model_name == 'p2ptransaction':
            data_store = self.data_manager.p2p_transactions
        elif model_name == 'merchant':
            data_store = self.data_manager.merchants
        else:
            data_store = []

        return MockQuery(model_class, data_store)

    def add(self, obj: Any):
        """Add object to session (for commit)."""
        # Convert model object to dict
        obj_dict = {}
        for key in dir(obj):
            if not key.startswith('_') and not callable(getattr(obj, key)):
                obj_dict[key] = getattr(obj, key)

        # Add default fields if not present
        if 'id' not in obj_dict:
            obj_dict['id'] = str(uuid.uuid4())
        if 'created_at' not in obj_dict:
            obj_dict['created_at'] = datetime.utcnow().isoformat()

        self._pending_commits.append((type(obj).__name__, obj_dict))

    def commit(self):
        """Commit pending changes."""
        for model_name, obj_dict in self._pending_commits:
            # Add to appropriate data store
            model_name_lower = model_name.lower()

            if model_name_lower == 'user':
                self.data_manager.users.append(obj_dict)
            elif model_name_lower == 'account':
                self.data_manager.accounts.append(obj_dict)
            elif model_name_lower == 'transaction':
                self.data_manager.transactions.append(obj_dict)
            elif model_name_lower == 'category':
                self.data_manager.categories.append(obj_dict)
            elif model_name_lower == 'card' or model_name_lower == 'virtualcard':
                self.data_manager.cards.append(obj_dict)
            elif model_name_lower == 'budget':
                self.data_manager.budgets.append(obj_dict)
            elif model_name_lower == 'goal':
                self.data_manager.goals.append(obj_dict)
            elif model_name_lower == 'notification':
                self.data_manager.notifications.append(obj_dict)
            elif model_name_lower == 'message':
                self.data_manager.messages.append(obj_dict)
            elif model_name_lower == 'bill':
                self.data_manager.bills.append(obj_dict)
            elif model_name_lower == 'subscription':
                self.data_manager.subscriptions.append(obj_dict)

        self._pending_commits.clear()

    def rollback(self):
        """Rollback pending changes."""
        self._pending_commits.clear()

    def close(self):
        """Close the session."""
        self._pending_commits.clear()

    def refresh(self, obj: Any):
        """Refresh object from database."""
        # In mock system, this is a no-op


# Global mock session instance
mock_session = MockSession()
