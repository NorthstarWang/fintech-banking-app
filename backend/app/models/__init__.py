# ruff: noqa: I001
# Export all Pydantic models from core_models
import enum

from .core_models import *
from .core_models import (
    CurrencyConversionRequest,
    CurrencyConversionResponse,
    CurrencyInfo,
    CurrencyInfoResponse,
    LinkedAccountResponse,
)
from .enums import *
from .mock_models import (
    Account as MockAccount,
    Alert,
    AnalyticsEvent,
    BankLink,
    Bill,
    Budget as MockBudget,
    Card as MockCard,
    Category as MockCategory,
    CreditScore as MockCreditScore,
    Goal as MockGoal,
    Holding,
    InvestmentAccount,
    Message as MockMessage,
    Notification as MockNotification,
    P2PTransaction,
    PlaidAccount,
    SocialConnection,
    Subscription as MockSubscription,
    Transaction as MockTransaction,
    TransactionsSyncStatus,
    User as MockUser,
)
from .memory_models import (
    Account,
    AccountType,
    AssetBridge,
    AssetClass,
    BlockchainNetwork,
    Budget,
    BudgetPeriod,
    Card,
    CardSpendingLimit,
    CardStatus,
    CardType,
    Category,
    CollateralPosition,
    Contact,
    ContactStatus,
    Conversation,
    ConversationParticipant,
    ConversionRate,
    ConversionType,
    CreditAlert,
    CreditAlertSeverity,
    CreditAlertType,
    CreditBuilderAccount,
    CreditBuilderType,
    CreditDispute,
    CreditDisputeStatus,
    CreditDisputeType,
    CreditScore,
    CreditSimulation,
    CryptoAsset,
    CryptoAssetType,
    CryptoTransaction,
    CryptoTransactionStatus,
    CryptoWallet,
    DeFiPosition,
    DeFiProtocolType,
    DirectMessage,
    ExpenseReport as ExpenseReportMemory,
    Goal,
    GoalContribution,
    GoalStatus,
    Invoice as InvoiceMemory,
    LinkedAccount,
    Log,
    Merchant,
    Message,
    MessageReadReceipt,
    MessageStatus,
    NFTAsset,
    Note,
    Notification,
    NotificationType,
    PaymentMethod,
    PaymentMethodStatus,
    PaymentMethodType,
    Receipt as ReceiptMemory,
    RecurringRule,
    SecurityAuditLog,
    SecurityEvent,
    SecurityEventType,
    Subscription,
    SubscriptionCategory,
    SubscriptionStatus,
    TwoFactorAuth,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
    Transaction,
    UnifiedBalance,
    UnifiedTransaction,
    UnifiedTransferStatus,
    User,
    UserDevice,
    UserRole,
)
from .dto import (
    AccountType as AccountType,
    BillingCycle as BillingCycle,
    BudgetPeriod as BudgetPeriod,
    CardStatus as CardStatus,
    CardType as CardType,
    ChallengeStatus as ChallengeStatus,
    ChallengeType as ChallengeType,
    ContactStatus as ContactStatus,
    CreditFactorType as CreditFactorType,
    CreditScoreProvider as CreditScoreProvider,
    CreditScoreRange as CreditScoreRange,
    ExpenseReportStatus as ExpenseReportStatus,
    ExportFormat as ExportFormat,
    GoalStatus as GoalStatus,
    InvoiceStatus as InvoiceStatus,
    MessageStatus as MessageStatus,
    NotificationType as NotificationType,
    OptimizationSuggestionType as OptimizationSuggestionType,
    PaymentMethodStatus as PaymentMethodStatus,
    PaymentMethodType as PaymentMethodType,
    PaymentTerms as PaymentTerms,
    RoundUpStatus as RoundUpStatus,
    SavingsRuleFrequency as SavingsRuleFrequency,
    SavingsRuleType as SavingsRuleType,
    SecurityEventType as SecurityEventType,
    SpendingLimitPeriod as SpendingLimitPeriod,
    SubscriptionCategory as SubscriptionCategory,
    SubscriptionStatus as SubscriptionStatus,
    TaxCategory as TaxCategory,
    TransactionStatus as TransactionStatus,
    TransactionType as TransactionType,
    TwoFactorMethod as TwoFactorMethod,
    UserRole as UserRole,
)
from .entities import (
    business_models as business_models,
    card_models as card_models,
    credit_models as credit_models,
    savings_models as savings_models,
    subscription_models as subscription_models,
)

# Business Models
from .entities.business_models import (
    APIKeyRequest as APIKeyRequest,
    APIKeyResponse as APIKeyResponse,
    AuthorizedUserRequest as AuthorizedUserRequest,
    AuthorizedUserResponse as AuthorizedUserResponse,
    BusinessAccountCreateRequest as BusinessAccountCreateRequest,
    BusinessAccountResponse as BusinessAccountResponse,
    BusinessExpenseRequest as BusinessExpenseRequest,
    BusinessExpenseResponse as BusinessExpenseResponse,
    BusinessLoanApplicationRequest as BusinessLoanApplicationRequest,
    BusinessLoanResponse as BusinessLoanResponse,
    CashFlowAnalysisResponse as CashFlowAnalysisResponse,
    CreditLineApplicationRequest as CreditLineApplicationRequest,
    CreditLineResponse as CreditLineResponse,
    ExpenseReportRequest as ExpenseReportRequest,
    ExpenseReportResponse as ExpenseReportResponse,
    InvoiceCreateRequest as InvoiceCreateRequest,
    InvoiceLineItem as InvoiceLineItem,
    InvoiceResponse as InvoiceResponse,
    PayrollEmployee as PayrollEmployee,
    PayrollRequest as PayrollRequest,
    PayrollResponse as PayrollResponse,
    ReceiptResponse as ReceiptResponse,
    ReceiptUploadRequest as ReceiptUploadRequest,
    RecurringPaymentRequest as RecurringPaymentRequest,
    RecurringPaymentResponse as RecurringPaymentResponse,
    TaxEstimateResponse as TaxEstimateResponse,
    TaxReportResponse as TaxReportResponse,
    TransactionCategorizationRequest as TransactionCategorizationRequest,
    TransactionCategorizationResponse as TransactionCategorizationResponse,
    VendorCreateRequest as VendorCreateRequest,
    VendorResponse as VendorResponse,
)

# Card Models
from .entities.card_models import (
    CardAnalyticsResponse as CardAnalyticsResponse,
    CardFreezeRequest as CardFreezeRequest,
    CardLimitRequest as CardLimitRequest,
    CardLimitResponse as CardLimitResponse,
    VirtualCardCreate as VirtualCardCreate,
    VirtualCardResponse as VirtualCardResponse,
)

# Credit Models
from .entities.credit_models import (
    CreditHistoryResponse as CreditHistoryResponse,
    CreditReportResponse as CreditReportResponse,
    CreditScoreResponse as CreditScoreResponse,
    CreditSimulatorRequest as CreditSimulatorRequest,
    CreditSimulatorResponse as CreditSimulatorResponse,
    CreditTip as CreditTip,
    CreditTipsResponse as CreditTipsResponse,
)

# Crypto Models
from .entities.crypto_models import (
    BlockchainNetwork as BlockchainNetwork,
    CryptoAssetResponse as CryptoAssetResponse,
    CryptoAssetType as CryptoAssetType,
    CryptoPortfolioSummary as CryptoPortfolioSummary,
    CryptoSwapQuote as CryptoSwapQuote,
    CryptoSwapRequest as CryptoSwapRequest,
    CryptoTransactionCreate as CryptoTransactionCreate,
    CryptoTransactionResponse as CryptoTransactionResponse,
    CryptoWalletCreate as CryptoWalletCreate,
    CryptoWalletResponse as CryptoWalletResponse,
    DeFiPositionResponse as DeFiPositionResponse,
    DeFiProtocolType as DeFiProtocolType,
    NFTAssetResponse as NFTAssetResponse,
    TransactionDirection as TransactionDirection,
)

# Currency Converter Models
from .entities.currency_converter_models import (
    ComplianceCheckResponse as ComplianceCheckResponse,
    ConversionHistoryResponse as ConversionHistoryResponse,
    ConversionOrderCreate as ConversionOrderCreate,
    ConversionOrderResponse as ConversionOrderResponse,
    ConversionQuoteRequest as ConversionQuoteRequest,
    ConversionQuoteResponse as ConversionQuoteResponse,
    CurrencyBalanceResponse as CurrencyBalanceResponse,
    CurrencyPair as CurrencyPair,
    CurrencySupportedResponse as CurrencySupportedResponse,
    CurrencyType as CurrencyType,
    ExchangeRateResponse as ExchangeRateResponse,
    FeeType as FeeType,
    P2PTradeRequest as P2PTradeRequest,
    P2PTradeResponse as P2PTradeResponse,
    PeerOfferCreate as PeerOfferCreate,
    PeerOfferResponse as PeerOfferResponse,
    PeerStatus as PeerStatus,
    TransferLimitResponse as TransferLimitResponse,
    TransferMethod as TransferMethod,
    TransferStatus as TransferStatus,
    VerificationLevel as VerificationLevel,
)

# Insurance Models
from .entities.insurance_models import (
    AutoInsuranceDetails as AutoInsuranceDetails,
    ClaimStatus as ClaimStatus,
    ClaimTimelineEvent as ClaimTimelineEvent,
    CoverageType as CoverageType,
    HealthInsuranceDetails as HealthInsuranceDetails,
    InsuranceClaimCreate as InsuranceClaimCreate,
    InsuranceClaimResponse as InsuranceClaimResponse,
    InsurancePolicyCreate as InsurancePolicyCreate,
    InsurancePolicyResponse as InsurancePolicyResponse,
    InsuranceProviderResponse as InsuranceProviderResponse,
    InsuranceQuoteRequest as InsuranceQuoteRequest,
    InsuranceQuoteResponse as InsuranceQuoteResponse,
    InsuranceSummaryResponse as InsuranceSummaryResponse,
    InsuranceType as InsuranceType,
    PolicyStatus as PolicyStatus,
    PremiumFrequency as PremiumFrequency,
)

# Investment Models
from .entities.investment_models import (
    AssetResponse as AssetResponse,
    AssetType as AssetType,
    ETFDetailResponse as ETFDetailResponse,
    InvestmentAccountCreate as InvestmentAccountCreate,
    InvestmentAccountResponse as InvestmentAccountResponse,
    InvestmentAccountType as InvestmentAccountType,
    InvestmentSummaryResponse as InvestmentSummaryResponse,
    MarketDataResponse as MarketDataResponse,
    OrderSide as OrderSide,
    OrderStatus as OrderStatus,
    OrderType as OrderType,
    PortfolioAnalysisResponse as PortfolioAnalysisResponse,
    PortfolioResponse as PortfolioResponse,
    PortfolioRiskLevel as PortfolioRiskLevel,
    PositionResponse as PositionResponse,
    ResearchReportResponse as ResearchReportResponse,
    StockDetailResponse as StockDetailResponse,
    TaxDocumentResponse as TaxDocumentResponse,
    TradeHistoryResponse as TradeHistoryResponse,
    TradeOrderCreate as TradeOrderCreate,
    TradeOrderResponse as TradeOrderResponse,
    TradingSession as TradingSession,
    WatchlistCreate as WatchlistCreate,
    WatchlistResponse as WatchlistResponse,
)

# Loan Models
from .entities.loan_models import (
    CryptoLoanCreate as CryptoLoanCreate,
    InterestType as InterestType,
    LoanAmortizationRequest as LoanAmortizationRequest,
    LoanApplicationCreate as LoanApplicationCreate,
    LoanApplicationResponse as LoanApplicationResponse,
    LoanOfferResponse as LoanOfferResponse,
    LoanPaymentCreate as LoanPaymentCreate,
    LoanPaymentResponse as LoanPaymentResponse,
    LoanPaymentScheduleResponse as LoanPaymentScheduleResponse,
    LoanRefinanceAnalysis as LoanRefinanceAnalysis,
    LoanResponse as LoanResponse,
    LoanStatus as LoanStatus,
    LoanSummaryStats as LoanSummaryStats,
    LoanType as LoanType,
    PaymentFrequency as PaymentFrequency,
)

# Savings Models
from .entities.savings_models import (
    ChallengeJoinRequest as ChallengeJoinRequest,
    RoundUpConfigRequest as RoundUpConfigRequest,
    RoundUpConfigResponse as RoundUpConfigResponse,
    RoundUpTransaction as RoundUpTransaction,
    RoundUpTransactionResponse as RoundUpTransactionResponse,
    SavingsChallengeResponse as SavingsChallengeResponse,
    SavingsGoalCreate as SavingsGoalCreate,
    SavingsRuleRequest as SavingsRuleRequest,
    SavingsRuleResponse as SavingsRuleResponse,
)

# Subscription Models
from .entities.subscription_models import (
    BulkImportRequest as BulkImportRequest,
    BulkImportResponse as BulkImportResponse,
    CancellationReminderRequest as CancellationReminderRequest,
    CancellationReminderResponse as CancellationReminderResponse,
    OptimizationResponse as OptimizationResponse,
    OptimizationSuggestion as OptimizationSuggestion,
    PaymentHistoryResponse as PaymentHistoryResponse,
    SubscriptionAnalysisResponse as SubscriptionAnalysisResponse,
    SubscriptionCancelRequest as SubscriptionCancelRequest,
    SubscriptionCancelResponse as SubscriptionCancelResponse,
    SubscriptionCreateRequest as SubscriptionCreateRequest,
    SubscriptionDetailResponse as SubscriptionDetailResponse,
    SubscriptionPauseRequest as SubscriptionPauseRequest,
    SubscriptionPauseResponse as SubscriptionPauseResponse,
    SubscriptionRecommendationsResponse as SubscriptionRecommendationsResponse,
    SubscriptionReminderRequest as SubscriptionReminderRequest,
    SubscriptionReminderResponse as SubscriptionReminderResponse,
    SubscriptionResponse as SubscriptionResponse,
    SubscriptionShareRequest as SubscriptionShareRequest,
    SubscriptionShareResponse as SubscriptionShareResponse,
    SubscriptionSummaryResponse as SubscriptionSummaryResponse,
    SubscriptionUpdateRequest as SubscriptionUpdateRequest,
    SubscriptionUsageRequest as SubscriptionUsageRequest,
    SubscriptionUsageResponse as SubscriptionUsageResponse,
)

# Unified Models
from .entities.unified_models import (
    AssetBridgeRequest as AssetBridgeRequest,
    AssetBridgeResponse as AssetBridgeResponse,
    AssetClass as AssetClass,
    CollateralPositionResponse as CollateralPositionResponse,
    ConversionType as ConversionType,
    CrossAssetOpportunity as CrossAssetOpportunity,
    PortfolioOptimizationRequest as PortfolioOptimizationRequest,
    PortfolioOptimizationResponse as PortfolioOptimizationResponse,
    TransferStatus as TransferStatus,
    UnifiedBalanceResponse as UnifiedBalanceResponse,
    UnifiedSearchRequest as UnifiedSearchRequest,
    UnifiedSearchResponse as UnifiedSearchResponse,
    UnifiedTransferRequest as UnifiedTransferRequest,
    UnifiedTransferResponse as UnifiedTransferResponse,
)

# Create backwards compatibility aliases (after all imports)
CurrencyInfo = CurrencyInfoResponse
# Use memory models for database operations
ExpenseReport = ExpenseReportMemory
Invoice = InvoiceMemory
Receipt = ReceiptMemory

# Add missing model aliases for route imports
SpendingLimit = CardLimitResponse
MessageSettings = MessageSettingsResponse
MessageFolder = MessageFolderResponse
RoundUpConfig = RoundUpConfigResponse
SavingsChallenge = SavingsChallengeResponse
SavingsRule = SavingsRuleResponse
CancellationReminder = CancellationReminderResponse
RoundUpTransaction = RoundUpTransactionResponse

# Create placeholder classes for missing database models
# These models are used in routes but don't exist in memory_models yet
from pydantic import BaseModel as _BaseModel

class MessageAttachment(_BaseModel):
    """Placeholder for MessageAttachment model"""
    message_id: int
    filename: str
    file_url: str
    file_size: int | None = None
    content_type: str | None = None

    class Config:
        from_attributes = True

class BlockedUser(_BaseModel):
    """Placeholder for BlockedUser model"""
    user_id: int
    blocked_user_id: int
    reason: str | None = None
    blocked_at: str | None = None

    class Config:
        from_attributes = True

class ChallengeParticipant(_BaseModel):
    """Placeholder for ChallengeParticipant model"""
    challenge_id: int
    user_id: int
    current_amount: float = 0.0
    joined_at: str | None = None

    class Config:
        from_attributes = True

__all__ = [name for name in dir() if not name.startswith('_')]
