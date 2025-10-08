# Export all Pydantic models from core_models
from .core_models import *

# Import memory models (replacing SQLAlchemy)
from .memory_models import *

# Additional models for compatibility
Bill = type('Bill', (BaseMemoryModel,), {'__tablename__': 'bills'})
CreditScore = type('CreditScore', (BaseMemoryModel,), {'__tablename__': 'credit_scores'})
SocialConnection = type('SocialConnection', (BaseMemoryModel,), {'__tablename__': 'social_connections'})
P2PTransaction = type('P2PTransaction', (BaseMemoryModel,), {'__tablename__': 'p2p_transactions'})
InvestmentAccount = type('InvestmentAccount', (BaseMemoryModel,), {'__tablename__': 'investment_accounts'})
Holding = type('Holding', (BaseMemoryModel,), {'__tablename__': 'holdings'})
Alert = type('Alert', (BaseMemoryModel,), {'__tablename__': 'alerts'})
AnalyticsEvent = type('AnalyticsEvent', (BaseMemoryModel,), {'__tablename__': 'analytics_events'})
BankLink = type('BankLink', (BaseMemoryModel,), {'__tablename__': 'bank_links'})
PlaidAccount = type('PlaidAccount', (BaseMemoryModel,), {'__tablename__': 'plaid_accounts'})
TransactionsSyncStatus = type('TransactionsSyncStatus', (BaseMemoryModel,), {'__tablename__': 'transactions_sync_status'})
LinkedAccount = type('LinkedAccount', (BaseMemoryModel,), {'__tablename__': 'linked_accounts'})
CreditSimulation = type('CreditSimulation', (BaseMemoryModel,), {'__tablename__': 'credit_simulations'})
TwoFactorAuth = type('TwoFactorAuth', (BaseMemoryModel,), {'__tablename__': 'two_factor_auth'})
UserDevice = type('UserDevice', (BaseMemoryModel,), {'__tablename__': 'user_devices'})
SecurityAuditLog = type('SecurityAuditLog', (BaseMemoryModel,), {'__tablename__': 'security_audit_logs'})

# Additional models that don't have full implementations
SpendingLimit = type('SpendingLimit', (BaseMemoryModel,), {'__tablename__': 'spending_limits'})
RoundUpConfig = type('RoundUpConfig', (BaseMemoryModel,), {'__tablename__': 'round_up_configs'})
RoundUpTransaction = type('RoundUpTransaction', (BaseMemoryModel,), {'__tablename__': 'round_up_transactions'})
SavingsRule = type('SavingsRule', (BaseMemoryModel,), {'__tablename__': 'savings_rules'})
SavingsChallenge = type('SavingsChallenge', (BaseMemoryModel,), {'__tablename__': 'savings_challenges'})
ChallengeParticipant = type('ChallengeParticipant', (BaseMemoryModel,), {'__tablename__': 'challenge_participants'})
Invoice = type('Invoice', (BaseMemoryModel,), {'__tablename__': 'invoices'})
ExpenseReport = type('ExpenseReport', (BaseMemoryModel,), {'__tablename__': 'expense_reports'})
Receipt = type('Receipt', (BaseMemoryModel,), {'__tablename__': 'receipts'})
CancellationReminder = type('CancellationReminder', (BaseMemoryModel,), {'__tablename__': 'cancellation_reminders'})
DirectMessage = type('DirectMessage', (BaseMemoryModel,), {'__tablename__': 'direct_messages'})
MessageAttachment = type('MessageAttachment', (BaseMemoryModel,), {'__tablename__': 'message_attachments'})
MessageFolder = type('MessageFolder', (BaseMemoryModel,), {'__tablename__': 'message_folders'})
BlockedUser = type('BlockedUser', (BaseMemoryModel,), {'__tablename__': 'blocked_users'})
MessageSettings = type('MessageSettings', (BaseMemoryModel,), {'__tablename__': 'message_settings'})

# Create aliases for backward compatibility
VirtualCard = Card  # Routes expect VirtualCard
CardLimit = SpendingLimit  # Routes expect CardLimit
InvoiceLineItem = None  # Line items are stored as JSON in Invoice model

# Export enums from data_classes for convenience
# Additional enum for compatibility
import enum

from .dto import (
    AccountType,
    BillingCycle,
    BudgetPeriod,
    CardStatus,
    CardType,
    ChallengeStatus,
    ChallengeType,
    ContactStatus,
    CreditFactorType,
    CreditScoreProvider,
    CreditScoreRange,
    ExpenseReportStatus,
    ExportFormat,
    GoalStatus,
    InvoiceStatus,
    MessageStatus,
    NotificationType,
    OptimizationSuggestionType,
    PaymentMethodStatus,
    PaymentMethodType,
    PaymentTerms,
    RoundUpStatus,
    SavingsRuleFrequency,
    SavingsRuleType,
    SecurityEventType,
    SpendingLimitPeriod,
    SubscriptionCategory,
    SubscriptionStatus,
    TaxCategory,
    TransactionStatus,
    TransactionType,
    TwoFactorMethod,
    UserRole,
)


class BankLinkStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

# Import card models
# Also make sub-modules available if needed
from .entities import business_models, card_models, credit_models, savings_models, subscription_models

# Import business models
from .entities.business_models import (
    APIKeyRequest,
    APIKeyResponse,
    AuthorizedUserRequest,
    AuthorizedUserResponse,
    BusinessAccountCreateRequest,
    BusinessAccountResponse,
    BusinessExpenseRequest,
    BusinessExpenseResponse,
    BusinessLoanApplicationRequest,
    BusinessLoanResponse,
    CashFlowAnalysisResponse,
    CreditLineApplicationRequest,
    CreditLineResponse,
    ExpenseReportRequest,
    ExpenseReportResponse,
    InvoiceCreateRequest,
    InvoiceResponse,
    PayrollEmployee,
    PayrollRequest,
    PayrollResponse,
    ReceiptResponse,
    ReceiptUploadRequest,
    RecurringPaymentRequest,
    RecurringPaymentResponse,
    TaxEstimateResponse,
    TaxReportResponse,
    TransactionCategorizationRequest,
    TransactionCategorizationResponse,
    VendorCreateRequest,
    VendorResponse,
)
from .entities.card_models import (
    CardAnalyticsResponse,
    CardFreezeRequest,
    CardLimitRequest,
    CardLimitResponse,
    VirtualCardCreate,
    VirtualCardResponse,
)

# Import credit models
from .entities.credit_models import (
    CreditHistoryResponse,
    CreditReportResponse,
    CreditScoreResponse,
    CreditSimulatorRequest,
    CreditSimulatorResponse,
    CreditTip,
    CreditTipsResponse,
)

# Import crypto models
from .entities.crypto_models import (
    BlockchainNetwork,
    CryptoAssetResponse,
    CryptoAssetType,
    CryptoPortfolioSummary,
    CryptoSwapQuote,
    CryptoSwapRequest,
    CryptoTransactionCreate,
    CryptoTransactionResponse,
    CryptoWalletCreate,
    CryptoWalletResponse,
    DeFiPositionResponse,
    DeFiProtocolType,
    NFTAssetResponse,
    TransactionDirection,
)

# Import savings models
from .entities.savings_models import (
    ChallengeJoinRequest,
    RoundUpConfigRequest,
    RoundUpConfigResponse,
    RoundUpTransactionResponse,
    SavingsChallengeResponse,
    SavingsGoalCreate,
    SavingsRuleRequest,
    SavingsRuleResponse,
)

# Import subscription models
from .entities.subscription_models import (
    BulkImportRequest,
    BulkImportResponse,
    CancellationReminderRequest,
    CancellationReminderResponse,
    OptimizationResponse,
    OptimizationSuggestion,
    PaymentHistoryResponse,
    SubscriptionAnalysisResponse,
    SubscriptionCancelRequest,
    SubscriptionCancelResponse,
    SubscriptionCreateRequest,
    SubscriptionDetailResponse,
    SubscriptionPauseRequest,
    SubscriptionPauseResponse,
    SubscriptionRecommendationsResponse,
    SubscriptionReminderRequest,
    SubscriptionReminderResponse,
    SubscriptionResponse,
    SubscriptionShareRequest,
    SubscriptionShareResponse,
    SubscriptionSummaryResponse,
    SubscriptionUpdateRequest,
    SubscriptionUsageRequest,
    SubscriptionUsageResponse,
)

# Import unified models
from .entities.unified_models import (
    AssetBridgeRequest,
    AssetBridgeResponse,
    AssetClass,
    CollateralPositionResponse,
    ConversionType,
    CrossAssetOpportunity,
    PortfolioOptimizationRequest,
    PortfolioOptimizationResponse,
    TransferStatus,
    UnifiedBalanceResponse,
    UnifiedSearchRequest,
    UnifiedSearchResponse,
    UnifiedTransferRequest,
    UnifiedTransferResponse,
)
