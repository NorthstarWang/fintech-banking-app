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
from .dto import (
    UserRole, AccountType, TransactionType, TransactionStatus,
    BudgetPeriod, GoalStatus, NotificationType, ContactStatus,
    MessageStatus, CardStatus, CardType, SpendingLimitPeriod,
    CreditScoreProvider, CreditScoreRange, CreditFactorType,
    RoundUpStatus, SavingsRuleType, SavingsRuleFrequency,
    ChallengeStatus, ChallengeType, InvoiceStatus, PaymentTerms,
    TaxCategory, ExpenseReportStatus, SubscriptionStatus,
    BillingCycle, SubscriptionCategory, OptimizationSuggestionType,
    SecurityEventType, PaymentMethodType, PaymentMethodStatus,
    TwoFactorMethod, ExportFormat
)

# Additional enum for compatibility
import enum
class BankLinkStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

# Import card models
from .entities.card_models import (
    VirtualCardCreate, VirtualCardResponse, CardFreezeRequest,
    CardLimitRequest, CardLimitResponse, CardAnalyticsResponse
)

# Import savings models
from .entities.savings_models import (
    RoundUpConfigRequest, RoundUpConfigResponse, RoundUpTransactionResponse,
    SavingsRuleRequest, SavingsRuleResponse, SavingsChallengeResponse,
    ChallengeJoinRequest, SavingsGoalCreate
)

# Import credit models
from .entities.credit_models import (
    CreditScoreResponse, CreditHistoryResponse, CreditSimulatorRequest,
    CreditSimulatorResponse, CreditTip, CreditTipsResponse, CreditReportResponse
)

# Import subscription models
from .entities.subscription_models import (
    SubscriptionResponse, SubscriptionUpdateRequest, SubscriptionAnalysisResponse,
    CancellationReminderRequest, CancellationReminderResponse,
    OptimizationSuggestion, OptimizationResponse,
    SubscriptionCreateRequest, SubscriptionDetailResponse, SubscriptionCancelRequest,
    SubscriptionCancelResponse, SubscriptionPauseRequest, SubscriptionPauseResponse,
    SubscriptionSummaryResponse, PaymentHistoryResponse, SubscriptionReminderRequest,
    SubscriptionReminderResponse, SubscriptionUsageRequest, SubscriptionUsageResponse,
    SubscriptionRecommendationsResponse, SubscriptionShareRequest, SubscriptionShareResponse,
    BulkImportRequest, BulkImportResponse
)

# Import business models
from .entities.business_models import (
    InvoiceCreateRequest, InvoiceResponse,
    ExpenseReportRequest, ExpenseReportResponse, TransactionCategorizationRequest,
    TransactionCategorizationResponse, ReceiptUploadRequest, ReceiptResponse,
    TaxEstimateResponse,
    BusinessAccountCreateRequest, BusinessAccountResponse,
    CreditLineApplicationRequest, CreditLineResponse,
    PayrollRequest, PayrollResponse, PayrollEmployee,
    VendorCreateRequest, VendorResponse,
    BusinessExpenseRequest, BusinessExpenseResponse,
    TaxReportResponse, CashFlowAnalysisResponse,
    AuthorizedUserRequest, AuthorizedUserResponse,
    RecurringPaymentRequest, RecurringPaymentResponse,
    BusinessLoanApplicationRequest, BusinessLoanResponse,
    APIKeyRequest, APIKeyResponse
)

# Also make sub-modules available if needed
from .entities import business_models
from .entities import card_models
from .entities import credit_models
from .entities import savings_models
from .entities import subscription_models


# Import crypto models
from .entities.crypto_models import (
    CryptoAssetType, BlockchainNetwork, TransactionDirection, DeFiProtocolType,
    CryptoWalletCreate, CryptoWalletResponse, CryptoAssetResponse,
    NFTAssetResponse, CryptoTransactionCreate, CryptoTransactionResponse,
    DeFiPositionResponse, CryptoPortfolioSummary, CryptoSwapRequest,
    CryptoSwapQuote
)

# Import unified models
from .entities.unified_models import (
    AssetClass, ConversionType, TransferStatus,
    UnifiedBalanceResponse, AssetBridgeRequest, AssetBridgeResponse,
    UnifiedTransferRequest, UnifiedTransferResponse, CollateralPositionResponse,
    CrossAssetOpportunity, PortfolioOptimizationRequest, PortfolioOptimizationResponse,
    UnifiedSearchRequest, UnifiedSearchResponse
)