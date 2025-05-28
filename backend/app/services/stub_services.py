"""
Stub services for mock system - simplified implementations.
"""

class BaseService:
    """Base service class."""
    def __init__(self, repository):
        self.repository = repository

class AccountService(BaseService):
    """Stub account service."""
    def __init__(self, account_repository, transaction_repository):
        self.account_repository = account_repository
        self.transaction_repository = transaction_repository

class TransactionService(BaseService):
    """Stub transaction service."""
    def __init__(self, transaction_repository, account_repository, notification_service):
        self.transaction_repository = transaction_repository
        self.account_repository = account_repository
        self.notification_service = notification_service

class CardService(BaseService):
    """Stub card service."""
    def __init__(self, card_repository, account_repository, transaction_repository):
        self.card_repository = card_repository
        self.account_repository = account_repository
        self.transaction_repository = transaction_repository

class BudgetService(BaseService):
    """Stub budget service."""
    def __init__(self, budget_repository, transaction_repository, notification_service):
        self.budget_repository = budget_repository
        self.transaction_repository = transaction_repository
        self.notification_service = notification_service

class GoalService(BaseService):
    """Stub goal service."""
    def __init__(self, goal_repository, account_repository, notification_service):
        self.goal_repository = goal_repository
        self.account_repository = account_repository
        self.notification_service = notification_service

class BillService(BaseService):
    """Stub bill service."""
    def __init__(self, bill_repository, account_repository, notification_service):
        self.bill_repository = bill_repository
        self.account_repository = account_repository
        self.notification_service = notification_service

class SubscriptionService(BaseService):
    """Stub subscription service."""
    def __init__(self, subscription_repository, transaction_repository, notification_service):
        self.subscription_repository = subscription_repository
        self.transaction_repository = transaction_repository
        self.notification_service = notification_service

class SocialService(BaseService):
    """Stub social service."""
    def __init__(self, social_repository, user_repository, notification_service):
        self.social_repository = social_repository
        self.user_repository = user_repository
        self.notification_service = notification_service

class MessageService(BaseService):
    """Stub message service."""
    def __init__(self, message_repository, user_repository, notification_service):
        self.message_repository = message_repository
        self.user_repository = user_repository
        self.notification_service = notification_service

class NotificationService(BaseService):
    """Stub notification service."""
    def __init__(self, notification_repository):
        self.notification_repository = notification_repository

class InvestmentService(BaseService):
    """Stub investment service."""
    def __init__(self, investment_repository, account_repository, transaction_repository):
        self.investment_repository = investment_repository
        self.account_repository = account_repository
        self.transaction_repository = transaction_repository

class SupportService(BaseService):
    """Stub support service."""
    def __init__(self, support_repository, user_repository):
        self.support_repository = support_repository
        self.user_repository = user_repository

class AnalyticsService(BaseService):
    """Stub analytics service."""
    def __init__(self, analytics_repository):
        self.analytics_repository = analytics_repository