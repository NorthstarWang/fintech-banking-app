from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Import shared enums
from ..dto import ExpenseReportStatus, InvoiceStatus, PaymentTerms, TaxCategory


# Request/Response Models
class InvoiceLineItem(BaseModel):
    description: str
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    tax_rate: float | None = Field(default=0, ge=0, le=100)
    discount_percentage: float | None = Field(default=0, ge=0, le=100)


class InvoiceCreateRequest(BaseModel):
    business_account_id: int | None = None  # For business invoices
    client_name: str
    client_email: str
    client_address: str | None = None
    invoice_number: str | None = None
    issue_date: date
    due_date: date
    payment_terms: PaymentTerms
    line_items: list[InvoiceLineItem]
    notes: str | None = None
    tax_rate: float | None = Field(default=0, ge=0, le=100)
    discount_percentage: float | None = Field(default=0, ge=0, le=100)


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    invoice_number: str
    client_name: str
    client_email: str
    client_address: str | None
    status: InvoiceStatus
    issue_date: date
    due_date: date
    payment_terms: PaymentTerms
    subtotal: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    amount_paid: float
    line_items: list[dict[str, Any]]
    notes: str | None
    created_at: datetime
    sent_at: datetime | None
    paid_at: datetime | None


class ExpenseReportRequest(BaseModel):
    report_name: str
    start_date: date
    end_date: date
    account_ids: list[int]
    category_ids: list[int] | None = None
    include_receipts: bool = True
    notes: str | None = None


class ExpenseReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    report_name: str
    status: ExpenseReportStatus
    start_date: date
    end_date: date
    total_amount: float
    expense_count: int
    expenses_by_category: dict[str, float]
    expenses_by_tax_category: dict[str, float]
    created_at: datetime
    submitted_at: datetime | None
    approved_at: datetime | None
    expenses: list[dict[str, Any]]


class TransactionCategorizationRequest(BaseModel):
    transaction_ids: list[int]
    auto_categorize: bool = True
    apply_tax_categories: bool = True


class TransactionCategorizationResponse(BaseModel):
    categorized_count: int
    tax_categorized_count: int
    categorizations: list[dict[str, Any]]
    tax_deductible_total: float
    suggestions: list[dict[str, Any]]


class ReceiptUploadRequest(BaseModel):
    transaction_id: int | None = None
    amount: float
    merchant_name: str
    date: date
    category_id: int | None = None
    tax_category: TaxCategory | None = None
    notes: str | None = None


class ReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    transaction_id: int | None
    receipt_url: str
    amount: float
    merchant_name: str
    date: date
    category_id: int | None
    tax_category: TaxCategory | None
    extracted_data: dict[str, Any] | None
    created_at: datetime


class TaxEstimateResponse(BaseModel):
    quarter: str  # "Q1 2025"
    year: int
    gross_income: float
    total_expenses: float
    deductible_expenses: float
    estimated_taxable_income: float
    estimated_quarterly_tax: float
    tax_breakdown: dict[str, float]
    deductions_by_category: dict[str, float]
    recommendations: list[str]
    payment_due_date: date


# Business Account Models
class BusinessAccountCreateRequest(BaseModel):
    business_name: str
    business_type: str  # LLC, Corporation, Sole Proprietorship, etc.
    ein: str  # Employer Identification Number
    account_type: str  # business_checking, business_savings
    initial_balance: float = 0.0
    industry: str | None = None
    annual_revenue: float | None = None
    interest_rate: float | None = None  # For savings accounts


class BusinessAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    account_number: str
    business_name: str
    business_type: str
    ein: str
    account_type: str
    balance: float
    interest_rate: float | None
    created_at: datetime
    authorized_users: list[dict[str, Any]] = []


# Credit Line Models
class CreditLineApplicationRequest(BaseModel):
    business_account_id: int
    requested_amount: float
    purpose: str
    term_months: int


class CreditLineResponse(BaseModel):
    requested_amount: float
    approved_amount: float
    interest_rate: float
    status: str
    credit_line_id: int
    created_at: datetime


# Payroll Models
class PayrollEmployee(BaseModel):
    employee_id: str
    gross_pay: float
    net_pay: float


class PayrollRequest(BaseModel):
    business_account_id: int
    payroll_date: datetime
    employees: list[PayrollEmployee]
    total_gross: float
    total_net: float
    total_taxes: float


class PayrollResponse(BaseModel):
    payroll_id: int
    business_account_id: int
    total_gross: float
    total_net: float
    total_taxes: float
    employee_count: int
    processed_at: datetime


# Vendor Models
class VendorCreateRequest(BaseModel):
    vendor_name: str
    vendor_type: str
    contact_email: str
    payment_terms: str
    tax_id: str | None = None


class VendorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vendor_name: str
    vendor_type: str
    contact_email: str
    payment_terms: str
    tax_id: str | None
    created_at: datetime


# Business expense models (update existing)
class BusinessExpenseRequest(BaseModel):
    business_account_id: int
    amount: float
    category: str
    description: str
    vendor: str
    tax_deductible: bool = True
    receipt_url: str | None = None


class BusinessExpenseResponse(BaseModel):
    id: int
    business_account_id: int
    amount: float
    category: str
    description: str
    vendor: str
    tax_deductible: bool
    receipt_url: str | None
    created_at: datetime


# Tax Report Models
class TaxReportResponse(BaseModel):
    year: int
    business_account_id: int
    total_income: float
    total_expenses: float
    deductible_expenses: float
    net_profit: float
    expense_categories: dict[str, float]
    quarterly_breakdown: list[dict[str, Any]]


# Cash Flow Models
class CashFlowAnalysisResponse(BaseModel):
    business_account_id: int
    current_month: dict[str, float]
    past_months: list[dict[str, Any]]
    projections: list[dict[str, Any]]
    recommendations: list[str]
    cash_runway_months: float


# Authorized User Models
class AuthorizedUserRequest(BaseModel):
    username: str
    role: str
    permissions: list[str]


class AuthorizedUserResponse(BaseModel):
    id: int
    username: str
    role: str
    permissions: list[str]
    added_at: datetime


# Recurring Payment Models
class RecurringPaymentRequest(BaseModel):
    business_account_id: int
    payee: str
    amount: float
    frequency: str  # daily, weekly, monthly, quarterly, annually
    category: str
    start_date: datetime
    end_date: datetime | None = None


class RecurringPaymentResponse(BaseModel):
    id: int
    business_account_id: int
    payee: str
    amount: float
    frequency: str
    category: str
    start_date: datetime
    end_date: datetime | None
    next_payment_date: datetime
    is_active: bool


# Business Loan Models
class BusinessLoanApplicationRequest(BaseModel):
    business_account_id: int
    loan_amount: float
    loan_purpose: str
    term_months: int
    annual_revenue: float
    years_in_business: int


class BusinessLoanResponse(BaseModel):
    application_id: int
    business_account_id: int
    loan_amount: float
    loan_purpose: str
    term_months: int
    status: str
    estimated_rate: float
    monthly_payment: float
    applied_at: datetime


# API Key Models
class APIKeyRequest(BaseModel):
    key_name: str
    permissions: list[str]
    expires_in_days: int


class APIKeyResponse(BaseModel):
    key_id: int
    api_key: str
    key_name: str
    permissions: list[str]
    created_at: datetime
    expires_at: datetime
