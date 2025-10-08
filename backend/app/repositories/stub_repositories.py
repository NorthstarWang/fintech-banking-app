"""
Stub repositories for mock system - simplified implementations.
"""
from typing import Any

from app.repositories.base_repository import BaseRepository


class CardRepository(BaseRepository[dict[str, Any]]):
    """Stub card repository."""
    def __init__(self, cards, credit_scores, credit_reports):
        super().__init__(cards)
        self.credit_scores = credit_scores
        self.credit_reports = credit_reports

class BudgetRepository(BaseRepository[dict[str, Any]]):
    """Stub budget repository."""
    def __init__(self, budgets, budget_categories=None):
        super().__init__(budgets)
        self.budget_categories = budget_categories or []

class GoalRepository(BaseRepository[dict[str, Any]]):
    """Stub goal repository."""
    def __init__(self, goals, goal_contributions):
        super().__init__(goals)
        self.goal_contributions = goal_contributions

class BillRepository(BaseRepository[dict[str, Any]]):
    """Stub bill repository."""
    def __init__(self, bills):
        super().__init__(bills)

class SubscriptionRepository(BaseRepository[dict[str, Any]]):
    """Stub subscription repository."""
    def __init__(self, subscriptions, cancellation_reminders):
        super().__init__(subscriptions)
        self.cancellation_reminders = cancellation_reminders

class SocialRepository(BaseRepository[dict[str, Any]]):
    """Stub social repository."""
    def __init__(self, social_connections, p2p_transactions):
        super().__init__(social_connections)
        self.p2p_transactions = p2p_transactions

class MessageRepository(BaseRepository[dict[str, Any]]):
    """Stub message repository."""
    def __init__(self, messages, conversations, participants, read_receipts,
                 direct_messages, attachments, folders, blocked_users, settings):
        super().__init__(messages)
        self.conversations = conversations
        self.participants = participants
        self.read_receipts = read_receipts
        self.direct_messages = direct_messages
        self.attachments = attachments
        self.folders = folders
        self.blocked_users = blocked_users
        self.settings = settings

class NotificationRepository(BaseRepository[dict[str, Any]]):
    """Stub notification repository."""
    def __init__(self, notifications):
        super().__init__(notifications)

class InvestmentRepository(BaseRepository[dict[str, Any]]):
    """Stub investment repository."""
    def __init__(self, investment_accounts, holdings):
        super().__init__(investment_accounts)
        self.holdings = holdings

class SupportRepository(BaseRepository[dict[str, Any]]):
    """Stub support repository."""
    def __init__(self, tickets, faq_items):
        super().__init__(tickets)
        self.faq_items = faq_items

class AnalyticsRepository(BaseRepository[dict[str, Any]]):
    """Stub analytics repository."""
    def __init__(self, analytics_events):
        super().__init__(analytics_events)
