from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
import uuid
import calendar
import json
import secrets
from decimal import Decimal

from ..storage.memory_adapter import db, desc
from ..models import (
    Invoice, ExpenseReport, Receipt, Transaction, Account,
    User, Category, InvoiceStatus, PaymentTerms, TaxCategory, ExpenseReportStatus,
    TransactionType
, Any)
from ..models import (
    InvoiceCreateRequest, InvoiceResponse, InvoiceLineItem as InvoiceLineItemSchema,
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
from ..utils.auth import get_current_user
from ..utils.validators import ValidationError
from ..utils.session_manager import session_manager

router = APIRouter()

def log_business_action(session_id: str, description: str, table_name: str, values: dict):
    """Helper function to log business actions using DB_UPDATE action type"""

def generate_invoice_number() -> str:
    """Generate unique invoice number"""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"INV-{timestamp}-{random_suffix}"

def calculate_line_item_totals(item: InvoiceLineItemSchema) -> Dict[str, float]:
    """Calculate totals for a line item"""
    subtotal = item.quantity * item.unit_price
    discount_amount = subtotal * (item.discount_percentage or 0) / 100
    subtotal_after_discount = subtotal - discount_amount
    tax_amount = subtotal_after_discount * (item.tax_rate or 0) / 100
    total = subtotal_after_discount + tax_amount
    
    return {
        "subtotal": round(subtotal, 2),
        "discount_amount": round(discount_amount, 2),
        "tax_amount": round(tax_amount, 2),
        "total": round(total, 2)
    }

def categorize_for_tax(description: str, amount: float) -> TaxCategory:
    """Auto-categorize transaction for tax purposes"""
    description_lower = description.lower()
    
    # Simple keyword matching (in production, use ML)
    if any(word in description_lower for word in ["uber", "lyft", "taxi", "gas", "parking"]):
        return TaxCategory.VEHICLE
    elif any(word in description_lower for word in ["lunch", "dinner", "coffee", "restaurant"]):
        return TaxCategory.MEALS_ENTERTAINMENT
    elif any(word in description_lower for word in ["hotel", "airbnb", "flight"]):
        return TaxCategory.TRAVEL
    elif any(word in description_lower for word in ["office depot", "staples", "supplies"]):
        return TaxCategory.OFFICE_SUPPLIES
    elif any(word in description_lower for word in ["internet", "phone", "electric", "water"]):
        return TaxCategory.UTILITIES
    elif any(word in description_lower for word in ["rent", "lease"]):
        return TaxCategory.RENT
    elif any(word in description_lower for word in ["insurance"]):
        return TaxCategory.INSURANCE
    elif any(word in description_lower for word in ["laptop", "computer", "software"]):
        return TaxCategory.EQUIPMENT
    elif any(word in description_lower for word in ["lawyer", "accountant", "consultant"]):
        return TaxCategory.PROFESSIONAL_SERVICES
    elif any(word in description_lower for word in ["ad", "marketing", "promotion"]):
        return TaxCategory.ADVERTISING
    else:
        return TaxCategory.OTHER


@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    status: Optional[InvoiceStatus] = None,
    client_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """List all invoices"""
    query = db_session.query(Invoice).filter(
        Invoice.user_id == current_user['user_id']
    )
    
    if status:
        query = query.filter(Invoice.status == status)
    
    if client_name:
        query = query.filter(Invoice.client_name.ilike(f"%{client_name}%"))
    
    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    results = []
    for invoice in invoices:
        invoice_dict = {
            "id": invoice.id,
            "user_id": invoice.user_id,
            "invoice_number": invoice.invoice_number,
            "client_name": invoice.client_name,
            "client_email": invoice.client_email,
            "client_address": invoice.client_address,
            "status": invoice.status,
            "issue_date": invoice.issue_date,
            "due_date": invoice.due_date,
            "payment_terms": invoice.payment_terms,
            "subtotal": invoice.subtotal,
            "tax_amount": invoice.tax_amount,
            "discount_amount": invoice.discount_amount,
            "total_amount": invoice.total_amount,
            "amount_paid": invoice.amount_paid or 0.0,
            "notes": invoice.notes,
            "created_at": invoice.created_at,
            "sent_at": invoice.sent_at,
            "paid_at": invoice.paid_at,
            "line_items": []  # Simplified for list view
        }
        results.append(InvoiceResponse(**invoice_dict))
    
    return results

# This endpoint was removed - duplicate definition exists at line 1190

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get a specific invoice"""
    invoice = db_session.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user['user_id']
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return InvoiceResponse(
        id=invoice.id,
        user_id=invoice.user_id,
        invoice_number=invoice.invoice_number,
        client_name=invoice.client_name,
        client_email=invoice.client_email,
        client_address=invoice.client_address,
        status=invoice.status,
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        payment_terms=invoice.payment_terms,
        subtotal=invoice.subtotal,
        tax_amount=invoice.tax_amount,
        discount_amount=invoice.discount_amount,
        total_amount=invoice.total_amount,
        amount_paid=invoice.amount_paid,
        notes=invoice.notes,
        created_at=invoice.created_at,
        sent_at=invoice.sent_at,
        paid_at=invoice.paid_at,
        line_items=invoice.line_items
    )

@router.put("/invoices/{invoice_id}/send")
async def send_invoice(
    request: Request,
    invoice_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Send an invoice to client"""
    
    invoice = db_session.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user['user_id']
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft invoices can be sent"
        )
    
    # Update status
    invoice.status = InvoiceStatus.SENT
    invoice.sent_at = datetime.utcnow()

    db_session.commit()

    log_business_action(
        action="send_invoice",
        user_id=current_user['user_id'],
        details={"invoice_id": invoice.id}
    )

    # In production, send actual email here
    return {"message": f"Invoice #{invoice.invoice_number} sent successfully"}

@router.put("/invoices/{invoice_id}/mark-paid")
async def mark_invoice_paid(
    request: Request,
    invoice_id: int,
    amount_paid: Optional[float] = None,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Mark an invoice as paid"""
    
    invoice = db_session.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user['user_id']
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    if invoice.status == InvoiceStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot mark cancelled invoice as paid"
        )
    
    # Update payment
    if amount_paid is None:
        amount_paid = invoice.total_amount
    
    invoice.amount_paid = min(amount_paid, invoice.total_amount)
    
    # Update status based on payment
    if invoice.amount_paid >= invoice.total_amount:
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = datetime.utcnow()
    elif invoice.amount_paid > 0:
        invoice.status = InvoiceStatus.PENDING
    
    db_session.commit()

    log_business_action(
        action="mark_invoice_paid",
        user_id=current_user['user_id'],
        details={"invoice_id": invoice.id, "amount_paid": invoice.amount_paid}
    )

    return {"message": f"Invoice #{invoice.invoice_number} updated successfully", "status": invoice.status}

@router.post("/invoices/{invoice_id}/duplicate", response_model=InvoiceResponse)
async def duplicate_invoice(
    request: Request,
    invoice_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Duplicate an existing invoice"""
    
    # Get original invoice
    original = db_session.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user['user_id']
    ).first()
    
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Create duplicate
    duplicate = Invoice(
        user_id=current_user['user_id'],
        business_account_id=original.business_account_id,
        invoice_number=generate_invoice_number(),
        client_name=original.client_name,
        client_email=original.client_email,
        client_address=original.client_address,
        status=InvoiceStatus.DRAFT,
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        payment_terms=original.payment_terms,
        subtotal=original.subtotal,
        tax_amount=original.tax_amount,
        discount_amount=original.discount_amount,
        total_amount=original.total_amount,
        amount_paid=0,
        notes=original.notes,
        line_items=original.line_items
    )
    
    db_session.add(duplicate)
    db_session.commit()
    db_session.refresh(duplicate)

    log_business_action(
        action="duplicate_invoice",
        user_id=current_user['user_id'],
        details={"original_id": original.id, "duplicate_id": duplicate.id}
    )

    return InvoiceResponse(
        id=duplicate.id,
        user_id=duplicate.user_id,
        invoice_number=duplicate.invoice_number,
        client_name=duplicate.client_name,
        client_email=duplicate.client_email,
        client_address=duplicate.client_address,
        status=duplicate.status,
        issue_date=duplicate.issue_date,
        due_date=duplicate.due_date,
        payment_terms=duplicate.payment_terms,
        subtotal=duplicate.subtotal,
        tax_amount=duplicate.tax_amount,
        discount_amount=duplicate.discount_amount,
        total_amount=duplicate.total_amount,
        amount_paid=duplicate.amount_paid,
        notes=duplicate.notes,
        created_at=duplicate.created_at,
        sent_at=duplicate.sent_at,
        paid_at=duplicate.paid_at,
        line_items=duplicate.line_items
    )

@router.post("/expenses/report", response_model=ExpenseReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_expense_report(
    request: Request,
    report_data: ExpenseReportRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Generate an expense report"""
    
    # Verify account ownership
    for account_id in report_data.account_ids:
        account = db_session.query(Account).filter(
            Account.id == account_id,
            Account.user_id == current_user['user_id']
        ).first()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account {account_id} not found"
            )
    
    # Get transactions in date range
    query = db_session.query(Transaction).filter(
        Transaction.account_id.in_(report_data.account_ids),
        Transaction.transaction_date >= report_data.start_date,
        Transaction.transaction_date <= report_data.end_date,
        Transaction.transaction_type == TransactionType.DEBIT
    )
    
    if report_data.category_ids:
        query = query.filter(Transaction.category_id.in_(report_data.category_ids))
    
    transactions = query.all()
    
    # Calculate totals by category
    expenses_by_category = {}
    expenses_by_tax_category = {}
    total_amount = 0
    
    expense_details = []
    for tx in transactions:
        # Regular category
        if tx.category:
            cat_name = tx.category.name
            expenses_by_category[cat_name] = expenses_by_category.get(cat_name, 0) + tx.amount
        
        # Tax category (auto-categorize)
        tax_cat = categorize_for_tax(tx.description, tx.amount)
        tax_cat_name = tax_cat.value
        expenses_by_tax_category[tax_cat_name] = expenses_by_tax_category.get(tax_cat_name, 0) + tx.amount
        
        total_amount += tx.amount
        
        # Add to details
        expense_details.append({
            "transaction_id": tx.id,
            "date": tx.transaction_date,
            "description": tx.description,
            "amount": tx.amount,
            "category": tx.category.name if tx.category else "Uncategorized",
            "tax_category": tax_cat.value,
            "has_receipt": len(tx.receipts) > 0 if hasattr(tx, 'receipts') else False
        })
    
    # Create expense report
    expense_report = ExpenseReport(
        user_id=current_user['user_id'],
        report_name=report_data.report_name,
        status=ExpenseReportStatus.DRAFT,
        start_date=report_data.start_date,
        end_date=report_data.end_date,
        total_amount=total_amount,
        expense_count=len(transactions),
        notes=report_data.notes
    )
    
    db_session.add(expense_report)
    
    # Link transactions to report
    for tx in transactions:
        expense_report.transactions.append(tx)
    
    db_session.commit()
    db_session.refresh(expense_report)

    log_business_action(
        action="create_expense_report",
        user_id=current_user['user_id'],
        details={
            "report_id": expense_report.id,
            "total_amount": total_amount,
            "created_at": datetime.utcnow().isoformat()
        }
    )

    return ExpenseReportResponse(
        id=expense_report.id,
        user_id=expense_report.user_id,
        report_name=expense_report.report_name,
        status=expense_report.status,
        start_date=expense_report.start_date,
        end_date=expense_report.end_date,
        total_amount=expense_report.total_amount,
        expense_count=expense_report.expense_count,
        expenses_by_category=expenses_by_category,
        expenses_by_tax_category=expenses_by_tax_category,
        created_at=expense_report.created_at,
        submitted_at=expense_report.submitted_at,
        approved_at=expense_report.approved_at,
        expenses=expense_details
    )

@router.post("/transactions/categorize", response_model=TransactionCategorizationResponse)
async def categorize_transactions(
    request: Request,
    categorization_data: TransactionCategorizationRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Auto-categorize transactions for tax purposes"""
    
    # Get transactions
    transactions = db_session.query(Transaction).join(
        Account
    ).filter(
        Transaction.id.in_(categorization_data.transaction_ids),
        Account.user_id == current_user['user_id']
    ).all()
    
    if len(transactions) != len(categorization_data.transaction_ids):
        raise ValidationError("Some transactions not found or not owned by user")
    
    categorizations = []
    tax_deductible_total = 0
    categorized_count = 0
    tax_categorized_count = 0
    
    for tx in transactions:
        updates = {}
        
        # Auto-categorize if requested
        if categorization_data.auto_categorize and not tx.category_id:
            # Simple keyword matching for demo
            description_lower = tx.description.lower()
            
            # Try to find matching category
            categories = db_session.query(Category).filter(
                Category.user_id.in_([None, current_user['user_id']])
            ).all()
            
            for category in categories:
                if category.name.lower() in description_lower:
                    tx.category_id = category.id
                    updates["category"] = category.name
                    categorized_count += 1
                    break
        
        # Apply tax category
        if categorization_data.apply_tax_categories:
            tax_category = categorize_for_tax(tx.description, tx.amount)
            # In a real app, you'd store this on the transaction
            updates["tax_category"] = tax_category.value
            tax_categorized_count += 1
            
            # Calculate if deductible (simplified)
            if tax_category != TaxCategory.OTHER:
                tax_deductible_total += tx.amount
        
        categorizations.append({
            "transaction_id": tx.id,
            "description": tx.description,
            "amount": tx.amount,
            "original_category": tx.category.name if tx.category else None,
            "suggested_category": updates.get("category"),
            "tax_category": updates.get("tax_category"),
            "is_deductible": updates.get("tax_category") != TaxCategory.OTHER.value if "tax_category" in updates else False
        })
    
    # Generate suggestions for better categorization
    suggestions = [
        {
            "tip": "Review transactions marked as 'OTHER' for potential deductions",
            "action": "Manual review recommended"
        },
        {
            "tip": "Keep receipts for all business expenses over $75",
            "action": "Upload receipts to maximize deductions"
        }
    ]
    
    db_session.commit()
    
    log_business_action(
        "transactions",
        {
            "transaction_count": len(transactions),
            "tax_deductible_total": tax_deductible_total,
            "categorized_count": categorized_count,
            "updated_at": datetime.utcnow().isoformat()
        }
    )
    
    return TransactionCategorizationResponse(
        categorized_count=categorized_count,
        tax_categorized_count=tax_categorized_count,
        categorizations=categorizations,
        tax_deductible_total=tax_deductible_total,
        suggestions=suggestions
    )

@router.post("/receipts", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    request: Request,
    receipt_data: ReceiptUploadRequest,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Upload a receipt"""
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "application/pdf"]
    if file.content_type not in allowed_types:
        raise ValidationError(f"File type {file.content_type} not allowed")
    
    # Validate file size (5MB max)
    if file.size > 5 * 1024 * 1024:
        raise ValidationError("File size exceeds 5MB limit")
    
    # Mock file upload (in production, upload to S3)
    file_extension = file.filename.split(".")[-1]
    receipt_filename = f"receipt_{uuid.uuid4().hex}.{file_extension}"
    receipt_url = f"https://mock-s3-bucket.com/receipts/{receipt_filename}"
    thumbnail_url = f"https://mock-s3-bucket.com/receipts/thumb_{receipt_filename}"
    
    # Mock OCR extraction
    extracted_data = {
        "merchant": receipt_data.merchant_name,
        "amount": receipt_data.amount,
        "date": receipt_data.date.isoformat(),
        "items": ["Mock extracted item 1", "Mock extracted item 2"],
        "confidence": 0.95
    }
    
    # Auto-categorize if not provided
    if not receipt_data.tax_category:
        receipt_data.tax_category = categorize_for_tax(receipt_data.merchant_name, receipt_data.amount)
    
    # Create receipt record
    receipt = Receipt(
        user_id=current_user['user_id'],
        transaction_id=receipt_data.transaction_id,
        receipt_url=receipt_url,
        thumbnail_url=thumbnail_url,
        amount=receipt_data.amount,
        merchant_name=receipt_data.merchant_name,
        date=receipt_data.date,
        category_id=receipt_data.category_id,
        tax_category=receipt_data.tax_category,
        extracted_data=extracted_data,
        notes=receipt_data.notes
    )
    
    db_session.add(receipt)
    db_session.commit()
    db_session.refresh(receipt)

    log_business_action(
        action="upload_receipt",
        user_id=current_user['user_id'],
        details={"receipt_id": receipt.id, "amount": receipt.amount}
    )

    return ReceiptResponse.from_orm(receipt)

@router.get("/tax/estimate", response_model=TaxEstimateResponse)
async def get_tax_estimate(
    year: int = None,
    quarter: int = None,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get quarterly tax estimate"""
    # Default to current quarter if not specified
    if not year:
        year = datetime.utcnow().year
    
    if not quarter:
        month = datetime.utcnow().month
        quarter = (month - 1) // 3 + 1
    
    # Calculate date range for quarter
    quarter_start_month = (quarter - 1) * 3 + 1
    quarter_start = date(year, quarter_start_month, 1)
    
    if quarter == 4:
        quarter_end = date(year, 12, 31)
    else:
        next_quarter_month = quarter * 3 + 1
        quarter_end = date(year, next_quarter_month, 1) - timedelta(days=1)
    
    # Get income (credits) for the quarter
    income_transactions = db_session.query(Transaction).join(
        Account
    ).filter(
        Account.user_id == current_user['user_id'],
        Transaction.transaction_date >= quarter_start,
        Transaction.transaction_date <= quarter_end,
        Transaction.transaction_type == TransactionType.CREDIT
    ).all()
    
    gross_income = sum(tx.amount for tx in income_transactions)
    
    # Get business expenses (debits)
    expense_transactions = db_session.query(Transaction).join(
        Account
    ).filter(
        Account.user_id == current_user['user_id'],
        Transaction.transaction_date >= quarter_start,
        Transaction.transaction_date <= quarter_end,
        Transaction.transaction_type == TransactionType.DEBIT
    ).all()
    
    # Categorize expenses for deductions
    deductions_by_category = {}
    total_expenses = 0
    deductible_expenses = 0
    
    for tx in expense_transactions:
        total_expenses += tx.amount
        
        # Check if business expense (simplified)
        tax_category = categorize_for_tax(tx.description, tx.amount)
        
        if tax_category != TaxCategory.OTHER:
            deductible_expenses += tx.amount
            cat_name = tax_category.value
            deductions_by_category[cat_name] = deductions_by_category.get(cat_name, 0) + tx.amount
    
    # Calculate taxable income
    estimated_taxable_income = gross_income - deductible_expenses
    
    # Simple tax calculation (15.3% self-employment + 22% federal estimate)
    self_employment_tax = estimated_taxable_income * 0.153
    federal_tax = estimated_taxable_income * 0.22
    estimated_quarterly_tax = (self_employment_tax + federal_tax) / 4
    
    # Tax breakdown
    tax_breakdown = {
        "self_employment": round(self_employment_tax / 4, 2),
        "federal": round(federal_tax / 4, 2),
        "state": 0,  # Varies by state
        "local": 0   # Varies by location
    }
    
    # Recommendations
    recommendations = []
    
    if deductible_expenses / total_expenses < 0.5:
        recommendations.append("Review expenses for additional tax deductions")
    
    if not deductions_by_category.get(TaxCategory.RETIREMENT.value):
        recommendations.append("Consider retirement contributions for tax savings")
    
    recommendations.append("Keep detailed records of all business expenses")
    recommendations.append("Set aside 25-30% of income for taxes")
    
    # Payment due date
    quarter_due_dates = {
        1: date(year, 4, 15),
        2: date(year, 6, 15),
        3: date(year, 9, 15),
        4: date(year + 1, 1, 15)
    }
    
    return TaxEstimateResponse(
        quarter=f"Q{quarter} {year}",
        year=year,
        gross_income=gross_income,
        total_expenses=total_expenses,
        deductible_expenses=deductible_expenses,
        estimated_taxable_income=estimated_taxable_income,
        estimated_quarterly_tax=round(estimated_quarterly_tax, 2),
        tax_breakdown=tax_breakdown,
        deductions_by_category=deductions_by_category,
        recommendations=recommendations,
        payment_due_date=quarter_due_dates[quarter]
    )


# Business Account endpoints
@router.post("/accounts", response_model=BusinessAccountResponse)
async def create_business_account(
    request: Request,
    account_data: BusinessAccountCreateRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a new business account"""
    
    # Generate account number
    account_number = f"BUS{str(uuid.uuid4().int)[:10]}"
    
    # Create business account using the Account model with special metadata
    business_account = Account(
        user_id=current_user['user_id'],
        name=f"{account_data.business_name} - {account_data.account_type.replace('_', ' ').title()}",
        account_number=account_number,
        account_type=account_data.account_type,
        balance=account_data.initial_balance,
        interest_rate=account_data.interest_rate,
        extra_data={
            "business_name": account_data.business_name,
            "business_type": account_data.business_type,
            "ein": account_data.ein,
            "industry": account_data.industry,
            "annual_revenue": account_data.annual_revenue,
            "is_business": True,
            "authorized_users": []
        }
    )
    
    db_session.add(business_account)
    db_session.commit()
    db_session.refresh(business_account)
    
    
    return BusinessAccountResponse(
        id=business_account.id,
        user_id=business_account.user_id,
        account_number=business_account.account_number,
        business_name=account_data.business_name,
        business_type=account_data.business_type,
        ein=account_data.ein,
        account_type=business_account.account_type,
        balance=business_account.balance,
        interest_rate=business_account.interest_rate,
        created_at=business_account.created_at,
        authorized_users=business_account.extra_data.get("authorized_users", [])
    )


@router.get("/accounts/{account_id}", response_model=BusinessAccountResponse)
async def get_business_account(
    account_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get business account details"""
    account = db_session.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user['user_id']
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business account not found"
        )
    
    # Check if it's a business account
    if not account.extra_data or not account.extra_data.get("is_business"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business account not found"
        )
    
    return BusinessAccountResponse(
        id=account.id,
        user_id=account.user_id,
        account_number=account.account_number,
        business_name=account.extra_data.get("business_name"),
        business_type=account.extra_data.get("business_type"),
        ein=account.extra_data.get("ein"),
        account_type=account.account_type,
        balance=account.balance,
        interest_rate=account.interest_rate,
        created_at=account.created_at,
        authorized_users=account.extra_data.get("authorized_users", [])
    )


@router.get("/accounts", response_model=List[BusinessAccountResponse])
async def list_business_accounts(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """List all business accounts"""
    accounts = db_session.query(Account).filter(
        Account.user_id == current_user['user_id']
    ).all()
    
    business_accounts = []
    for account in accounts:
        if account.extra_data and account.extra_data.get("is_business"):
            business_accounts.append(BusinessAccountResponse(
                id=account.id,
                user_id=account.user_id,
                account_number=account.account_number,
                business_name=account.extra_data.get("business_name"),
                business_type=account.extra_data.get("business_type"),
                ein=account.extra_data.get("ein"),
                account_type=account.account_type,
                balance=account.balance,
                interest_rate=account.interest_rate,
                created_at=account.created_at,
                authorized_users=account.extra_data.get("authorized_users", [])
            ))
    
    return business_accounts


@router.post("/credit-line", response_model=CreditLineResponse)
async def apply_for_credit_line(
    request: Request,
    application: CreditLineApplicationRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Apply for business credit line"""
    
    # Verify business account ownership
    account = db_session.query(Account).filter(
        Account.id == application.business_account_id,
        Account.user_id == current_user['user_id']
    ).first()
    
    if not account or not account.extra_data.get("is_business"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business account not found"
        )
    
    # Calculate approval (simplified logic)
    annual_revenue = account.extra_data.get("annual_revenue", 0)
    if annual_revenue > 500000:
        approved_amount = min(application.requested_amount, annual_revenue * 0.1)
        interest_rate = 8.5
        status = "approved"
    elif annual_revenue > 100000:
        approved_amount = min(application.requested_amount * 0.7, annual_revenue * 0.05)
        interest_rate = 12.5
        status = "approved"
    else:
        approved_amount = 0
        interest_rate = 0
        status = "pending_review"
    
    # Store in account metadata (in production, use separate table)
    credit_line_id = uuid.uuid4().int % 1000000
    credit_lines = account.extra_data.get("credit_lines", [])
    credit_lines.append({
        "id": credit_line_id,
        "requested_amount": application.requested_amount,
        "approved_amount": approved_amount,
        "interest_rate": interest_rate,
        "status": status,
        "purpose": application.purpose,
        "term_months": application.term_months,
        "created_at": datetime.utcnow().isoformat()
    })
    account.extra_data["credit_lines"] = credit_lines
    
    db_session.commit()
    
    log_business_action(
        action="business_action",
        user_id=current_user['user_id'],
        details={}
    )
    
    return CreditLineResponse(
        requested_amount=application.requested_amount,
        approved_amount=approved_amount,
        interest_rate=interest_rate,
        status=status,
        credit_line_id=credit_line_id,
        created_at=datetime.utcnow()
    )


@router.post("/payroll", response_model=PayrollResponse)
async def process_payroll(
    request: Request,
    payroll_data: PayrollRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Process business payroll"""
    
    # Verify business account
    account = db_session.query(Account).filter(
        Account.id == payroll_data.business_account_id,
        Account.user_id == current_user['user_id']
    ).first()
    
    if not account or not account.extra_data.get("is_business"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business account not found"
        )
    
    # Check sufficient balance
    if account.balance < payroll_data.total_gross:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance for payroll"
        )
    
    # Process payroll
    payroll_id = uuid.uuid4().int % 1000000
    
    # Create payroll transaction
    payroll_transaction = Transaction(
        account_id=account.id,
        amount=payroll_data.total_gross,
        transaction_type=TransactionType.DEBIT,
        description=f"Payroll - {len(payroll_data.employees)} employees",
        category_id=None,  # Would need payroll category
        transaction_date=payroll_data.payroll_date.date(),
        extra_data={
            "payroll_id": payroll_id,
            "employee_count": len(payroll_data.employees),
            "total_net": payroll_data.total_net,
            "total_taxes": payroll_data.total_taxes
        }
    )
    
    # Update account balance
    account.balance -= payroll_data.total_gross
    
    db_session.add(payroll_transaction)
    
    # Store payroll details in metadata
    payrolls = account.extra_data.get("payrolls", [])
    payrolls.append({
        "payroll_id": payroll_id,
        "payroll_date": payroll_data.payroll_date.isoformat(),
        "employees": [e.dict() for e in payroll_data.employees],
        "total_gross": payroll_data.total_gross,
        "total_net": payroll_data.total_net,
        "total_taxes": payroll_data.total_taxes,
        "processed_at": datetime.utcnow().isoformat()
    })
    account.extra_data["payrolls"] = payrolls
    
    db_session.commit()
    
    log_business_action(
        "payroll",
        {
            "account_id": account.id,
            "payroll_id": payroll_id,
            "total_gross": payroll_data.total_gross,
            "employee_count": len(payroll_data.employees),
            "created_at": datetime.utcnow().isoformat()
        }
    )
    
    return PayrollResponse(
        payroll_id=payroll_id,
        business_account_id=payroll_data.business_account_id,
        total_gross=payroll_data.total_gross,
        total_net=payroll_data.total_net,
        total_taxes=payroll_data.total_taxes,
        employee_count=len(payroll_data.employees),
        processed_at=datetime.utcnow()
    )


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    request: Request,
    invoice_data: InvoiceCreateRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a new invoice"""
    
    # Handle both regular and business invoice creation
    business_account_id = None
    if hasattr(invoice_data, 'business_account_id') and invoice_data.business_account_id:
        # Verify business account ownership
        account = db_session.query(Account).filter(
            Account.id == invoice_data.business_account_id,
            Account.user_id == current_user['user_id']
        ).first()
        
        if not account or not account.extra_data.get("is_business"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business account not found"
            )
        business_account_id = invoice_data.business_account_id
    
    # Generate invoice number if not provided
    invoice_number = invoice_data.invoice_number or generate_invoice_number()
    
    # Check for duplicate invoice number
    existing = db_session.query(Invoice).filter(
        Invoice.invoice_number == invoice_number
    ).first()
    
    if existing:
        raise ValidationError(f"Invoice number {invoice_number} already exists")
    
    # Create invoice
    invoice = Invoice(
        user_id=current_user['user_id'],
        invoice_number=invoice_number,
        client_name=invoice_data.client_name,
        client_email=invoice_data.client_email,
        client_address=invoice_data.client_address,
        status=InvoiceStatus.DRAFT if not hasattr(invoice_data, 'status') else InvoiceStatus.PENDING,
        issue_date=invoice_data.issue_date,
        due_date=invoice_data.due_date,
        payment_terms=invoice_data.payment_terms,
        notes=invoice_data.notes,
        amount_paid=0.0,  # Initialize amount_paid
        line_items=[],  # Initialize as empty list for JSON column
        extra_data={"business_account_id": business_account_id} if business_account_id else {}
    )
    
    # Add line items and calculate totals
    total_subtotal = 0
    total_tax = 0
    total_discount = 0
    line_items_json = []
    
    for item_data in invoice_data.line_items:
        totals = calculate_line_item_totals(item_data)
        
        line_item = {
            "description": item_data.description,
            "quantity": item_data.quantity,
            "unit_price": item_data.unit_price,
            "tax_rate": item_data.tax_rate or 0,
            "discount_percentage": item_data.discount_percentage or 0,
            "subtotal": totals["subtotal"],
            "tax_amount": totals["tax_amount"],
            "discount_amount": totals["discount_amount"],
            "total": totals["total"]
        }
        
        line_items_json.append(line_item)
        
        total_subtotal += totals["subtotal"]
        total_tax += totals["tax_amount"]
        total_discount += totals["discount_amount"]
    
    # Apply invoice-level discount if any
    if invoice_data.discount_percentage:
        invoice_discount = total_subtotal * invoice_data.discount_percentage / 100
        total_discount += invoice_discount
    
    # Apply invoice-level tax if any
    if invoice_data.tax_rate:
        taxable_amount = total_subtotal - total_discount
        invoice_tax = taxable_amount * invoice_data.tax_rate / 100
        total_tax += invoice_tax
    
    # Set invoice totals and line items
    invoice.subtotal = round(total_subtotal, 2)
    invoice.tax_amount = round(total_tax, 2)
    invoice.discount_amount = round(total_discount, 2)
    invoice.total_amount = round(total_subtotal - total_discount + total_tax, 2)
    invoice.line_items = line_items_json  # Set the JSON column
    
    db_session.add(invoice)
    db_session.commit()
    db_session.refresh(invoice)
    
    log_business_action(
        action="business_action",
        user_id=current_user['user_id'],
        details={}
    )
    
    # Prepare response with line items
    invoice_dict = {
        "id": invoice.id,
        "user_id": invoice.user_id,
        "invoice_number": invoice.invoice_number,
        "client_name": invoice.client_name,
        "client_email": invoice.client_email,
        "client_address": invoice.client_address,
        "status": invoice.status,
        "issue_date": invoice.issue_date,
        "due_date": invoice.due_date,
        "payment_terms": invoice.payment_terms,
        "subtotal": invoice.subtotal,
        "tax_amount": invoice.tax_amount,
        "discount_amount": invoice.discount_amount,
        "total_amount": invoice.total_amount,
        "amount_paid": invoice.amount_paid or 0.0,
        "notes": invoice.notes,
        "created_at": invoice.created_at,
        "sent_at": invoice.sent_at,
        "paid_at": invoice.paid_at,
        "line_items": line_items_json
    }
    
    return InvoiceResponse(**invoice_dict)


@router.post("/expenses", response_model=BusinessExpenseResponse)
async def record_business_expense(
    request: Request,
    expense_data: BusinessExpenseRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Record a business expense"""
    
    # Verify business account
    account = db_session.query(Account).filter(
        Account.id == expense_data.business_account_id,
        Account.user_id == current_user['user_id']
    ).first()
    
    if not account or not account.extra_data.get("is_business"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business account not found"
        )
    
    # Create expense transaction
    expense_transaction = Transaction(
        account_id=account.id,
        amount=expense_data.amount,
        transaction_type=TransactionType.DEBIT,
        description=expense_data.description,
        transaction_date=datetime.utcnow().date(),
        extra_data={
            "category": expense_data.category,
            "vendor": expense_data.vendor,
            "tax_deductible": expense_data.tax_deductible,
            "receipt_url": expense_data.receipt_url,
            "is_business_expense": True
        }
    )
    
    # Update account balance
    account.balance -= expense_data.amount
    
    db_session.add(expense_transaction)
    db_session.commit()
    db_session.refresh(expense_transaction)
    
    
    return BusinessExpenseResponse(
        id=expense_transaction.id,
        business_account_id=expense_data.business_account_id,
        amount=expense_data.amount,
        category=expense_data.category,
        description=expense_data.description,
        vendor=expense_data.vendor,
        tax_deductible=expense_data.tax_deductible,
        receipt_url=expense_data.receipt_url,
        created_at=expense_transaction.created_at
    )


@router.get("/tax-report/{account_id}/{year}", response_model=TaxReportResponse)
async def get_tax_report(
    account_id: int,
    year: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get tax report for a business account"""
    # Verify business account
    account = db_session.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user['user_id']
    ).first()
    
    if not account or not account.extra_data.get("is_business"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business account not found"
        )
    
    # Get all transactions for the year
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    transactions = db_session.query(Transaction).filter(
        Transaction.account_id == account_id,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).all()
    
    # Calculate totals
    total_income = 0
    total_expenses = 0
    deductible_expenses = 0
    expense_categories = {}
    quarterly_breakdown = []
    
    # Process by quarter
    for quarter in range(1, 5):
        q_start_month = (quarter - 1) * 3 + 1
        q_start = date(year, q_start_month, 1)
        
        if quarter == 4:
            q_end = date(year, 12, 31)
        else:
            q_end_month = quarter * 3 + 1
            q_end = date(year, q_end_month, 1) - timedelta(days=1)
        
        q_income = 0
        q_expenses = 0
        q_deductible = 0
        
        for tx in transactions:
            if q_start <= tx.transaction_date <= q_end:
                if tx.transaction_type == TransactionType.CREDIT:
                    q_income += tx.amount
                else:
                    q_expenses += tx.amount
                    
                    # Check if deductible
                    if tx.extra_data and tx.extra_data.get("tax_deductible", False):
                        q_deductible += tx.amount
                        deductible_expenses += tx.amount
                    
                    # Categorize expenses
                    category = tx.extra_data.get("category", "Other") if tx.extra_data else "Other"
                    expense_categories[category] = expense_categories.get(category, 0) + tx.amount
        
        quarterly_breakdown.append({
            "quarter": f"Q{quarter}",
            "income": q_income,
            "expenses": q_expenses,
            "deductible_expenses": q_deductible,
            "net_profit": q_income - q_expenses
        })
        
        total_income += q_income
        total_expenses += q_expenses
    
    net_profit = total_income - total_expenses
    
    return TaxReportResponse(
        year=year,
        business_account_id=account_id,
        total_income=total_income,
        total_expenses=total_expenses,
        deductible_expenses=deductible_expenses,
        net_profit=net_profit,
        expense_categories=expense_categories,
        quarterly_breakdown=quarterly_breakdown
    )


@router.post("/vendors", response_model=VendorResponse)
async def create_vendor(
    request: Request,
    vendor_data: VendorCreateRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a vendor for business transactions"""
    
    # Store vendor in user metadata (in production, use separate table)
    user = db_session.query(User).filter(
        User.id == current_user['user_id']
    ).first()
    
    vendor_id = uuid.uuid4().int % 1000000
    vendors = user.extra_data.get("vendors", []) if user.extra_data else []
    
    vendor = {
        "id": vendor_id,
        "vendor_name": vendor_data.vendor_name,
        "vendor_type": vendor_data.vendor_type,
        "contact_email": vendor_data.contact_email,
        "payment_terms": vendor_data.payment_terms,
        "tax_id": vendor_data.tax_id,
        "created_at": datetime.utcnow().isoformat()
    }
    
    vendors.append(vendor)
    
    if not user.extra_data:
        user.extra_data = {}
    user.extra_data["vendors"] = vendors
    
    db_session.commit()
    
    log_business_action(
        action="business_action",
        user_id=current_user['user_id'],
        details={}
    )
    
    return VendorResponse(
        id=vendor_id,
        vendor_name=vendor_data.vendor_name,
        vendor_type=vendor_data.vendor_type,
        contact_email=vendor_data.contact_email,
        payment_terms=vendor_data.payment_terms,
        tax_id=vendor_data.tax_id,
        created_at=datetime.utcnow()
    )


@router.get("/cash-flow/{account_id}", response_model=CashFlowAnalysisResponse)
async def get_cash_flow_analysis(
    account_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get cash flow analysis for business account"""
    # Verify business account
    account = db_session.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user['user_id']
    ).first()
    
    if not account or not account.extra_data.get("is_business"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business account not found"
        )
    
    # Get current month data
    now = datetime.utcnow()
    current_month_start = date(now.year, now.month, 1)
    current_month_end = date(now.year, now.month, calendar.monthrange(now.year, now.month)[1])
    
    current_month_transactions = db_session.query(Transaction).filter(
        Transaction.account_id == account_id,
        Transaction.transaction_date >= current_month_start,
        Transaction.transaction_date <= current_month_end
    ).all()
    
    current_inflows = sum(tx.amount for tx in current_month_transactions if tx.transaction_type == TransactionType.CREDIT)
    current_outflows = sum(tx.amount for tx in current_month_transactions if tx.transaction_type == TransactionType.DEBIT)
    current_net_flow = current_inflows - current_outflows
    
    # Get past 6 months data
    past_months = []
    for i in range(6):
        month_offset = i + 1
        month_date = now - timedelta(days=30 * month_offset)
        month_start = date(month_date.year, month_date.month, 1)
        month_end = date(month_date.year, month_date.month, calendar.monthrange(month_date.year, month_date.month)[1])
        
        month_transactions = db_session.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.transaction_date >= month_start,
            Transaction.transaction_date <= month_end
        ).all()
        
        inflows = sum(tx.amount for tx in month_transactions if tx.transaction_type == TransactionType.CREDIT)
        outflows = sum(tx.amount for tx in month_transactions if tx.transaction_type == TransactionType.DEBIT)
        
        past_months.append({
            "month": month_start.strftime("%B %Y"),
            "inflows": inflows,
            "outflows": outflows,
            "net_flow": inflows - outflows
        })
    
    # Calculate average monthly burn rate
    avg_monthly_outflow = sum(m["outflows"] for m in past_months) / len(past_months) if past_months else current_outflows
    avg_monthly_inflow = sum(m["inflows"] for m in past_months) / len(past_months) if past_months else current_inflows
    
    # Calculate cash runway
    if avg_monthly_outflow > avg_monthly_inflow:
        monthly_burn = avg_monthly_outflow - avg_monthly_inflow
        cash_runway_months = account.balance / monthly_burn if monthly_burn > 0 else float('inf')
    else:
        cash_runway_months = float('inf')
    
    # Generate projections
    projections = []
    projected_balance = account.balance
    for i in range(3):
        month_offset = i + 1
        future_date = now + timedelta(days=30 * month_offset)
        
        projected_inflow = avg_monthly_inflow * (1 + (0.05 * i))  # 5% growth
        projected_outflow = avg_monthly_outflow
        projected_net = projected_inflow - projected_outflow
        projected_balance += projected_net
        
        projections.append({
            "month": future_date.strftime("%B %Y"),
            "projected_inflows": projected_inflow,
            "projected_outflows": projected_outflow,
            "projected_net_flow": projected_net,
            "projected_balance": projected_balance
        })
    
    # Generate recommendations
    recommendations = []
    
    if cash_runway_months < 6:
        recommendations.append("Consider increasing revenue or reducing expenses - cash runway is less than 6 months")
    
    if current_outflows > current_inflows * 1.2:
        recommendations.append("Current month expenses exceed income by 20% - review spending")
    
    if avg_monthly_inflow < 10000:
        recommendations.append("Focus on revenue growth strategies to increase monthly income")
    
    recommendations.append("Maintain 3-6 months of operating expenses in reserve")
    
    return CashFlowAnalysisResponse(
        business_account_id=account_id,
        current_month={
            "inflows": current_inflows,
            "outflows": current_outflows,
            "net_flow": current_net_flow
        },
        past_months=past_months,
        projections=projections,
        recommendations=recommendations,
        cash_runway_months=round(cash_runway_months, 1) if cash_runway_months != float('inf') else 999
    )


@router.post("/accounts/{account_id}/users", response_model=AuthorizedUserResponse)
async def add_authorized_user(
    account_id: int,
    request: Request,
    user_data: AuthorizedUserRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Add authorized user to business account"""
    
    # Verify business account ownership
    account = db_session.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user['user_id']
    ).first()
    
    if not account or not account.extra_data.get("is_business"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business account not found"
        )
    
    # Add authorized user to metadata
    authorized_users = account.extra_data.get("authorized_users", [])
    
    user_id = uuid.uuid4().int % 1000000
    new_user = {
        "id": user_id,
        "username": user_data.username,
        "role": user_data.role,
        "permissions": user_data.permissions,
        "added_at": datetime.utcnow().isoformat()
    }
    
    authorized_users.append(new_user)
    account.extra_data["authorized_users"] = authorized_users
    
    db_session.commit()
    
    log_business_action(
        action="business_action",
        user_id=current_user['user_id'],
        details={}
    )
    
    return AuthorizedUserResponse(
        id=user_id,
        username=user_data.username,
        role=user_data.role,
        permissions=user_data.permissions,
        added_at=datetime.utcnow()
    )


@router.post("/recurring-payments", response_model=RecurringPaymentResponse)
async def setup_recurring_payment(
    request: Request,
    payment_data: RecurringPaymentRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Set up recurring business payment"""
    
    # Verify business account
    account = db_session.query(Account).filter(
        Account.id == payment_data.business_account_id,
        Account.user_id == current_user['user_id']
    ).first()
    
    if not account or not account.extra_data.get("is_business"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business account not found"
        )
    
    # Calculate next payment date
    frequency_days = {
        "daily": 1,
        "weekly": 7,
        "monthly": 30,
        "quarterly": 90,
        "annually": 365
    }
    
    next_payment_date = payment_data.start_date + timedelta(days=frequency_days.get(payment_data.frequency, 30))
    
    # Store recurring payment in metadata
    payment_id = uuid.uuid4().int % 1000000
    recurring_payments = account.extra_data.get("recurring_payments", [])
    
    new_payment = {
        "id": payment_id,
        "payee": payment_data.payee,
        "amount": payment_data.amount,
        "frequency": payment_data.frequency,
        "category": payment_data.category,
        "start_date": payment_data.start_date.isoformat(),
        "end_date": payment_data.end_date.isoformat() if payment_data.end_date else None,
        "next_payment_date": next_payment_date.isoformat(),
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }
    
    recurring_payments.append(new_payment)
    account.extra_data["recurring_payments"] = recurring_payments

    db_session.commit()

    log_business_action(
        action="setup_recurring_payment",
        user_id=current_user['user_id'],
        details={"payment_id": payment_id, "amount": payment_data.amount}
    )

    return RecurringPaymentResponse(
        id=payment_id,
        business_account_id=payment_data.business_account_id,
        payee=payment_data.payee,
        amount=payment_data.amount,
        frequency=payment_data.frequency,
        category=payment_data.category,
        start_date=payment_data.start_date,
        end_date=payment_data.end_date,
        next_payment_date=next_payment_date,
        is_active=True
    )


@router.post("/loans/apply", response_model=BusinessLoanResponse)
async def apply_for_business_loan(
    request: Request,
    loan_data: BusinessLoanApplicationRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Apply for a business loan"""
    
    # Verify business account
    account = db_session.query(Account).filter(
        Account.id == loan_data.business_account_id,
        Account.user_id == current_user['user_id']
    ).first()
    
    if not account or not account.extra_data.get("is_business"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business account not found"
        )
    
    # Simple loan approval logic
    if loan_data.annual_revenue > 1000000 and loan_data.years_in_business >= 3:
        status = "pre_approved"
        estimated_rate = 6.5
    elif loan_data.annual_revenue > 500000 and loan_data.years_in_business >= 2:
        status = "pending_review"
        estimated_rate = 8.5
    else:
        status = "additional_info_required"
        estimated_rate = 12.0
    
    # Calculate monthly payment
    monthly_rate = estimated_rate / 100 / 12
    num_payments = loan_data.term_months
    
    if monthly_rate > 0:
        monthly_payment = loan_data.loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    else:
        monthly_payment = loan_data.loan_amount / num_payments
    
    # Store loan application in metadata
    application_id = uuid.uuid4().int % 1000000
    loan_applications = account.extra_data.get("loan_applications", [])
    
    new_application = {
        "application_id": application_id,
        "loan_amount": loan_data.loan_amount,
        "loan_purpose": loan_data.loan_purpose,
        "term_months": loan_data.term_months,
        "annual_revenue": loan_data.annual_revenue,
        "years_in_business": loan_data.years_in_business,
        "status": status,
        "estimated_rate": estimated_rate,
        "monthly_payment": round(monthly_payment, 2),
        "applied_at": datetime.utcnow().isoformat()
    }
    
    loan_applications.append(new_application)
    account.extra_data["loan_applications"] = loan_applications

    db_session.commit()

    log_business_action(
        action="apply_for_business_loan",
        user_id=current_user['user_id'],
        details={"application_id": application_id, "loan_amount": loan_data.loan_amount}
    )

    return BusinessLoanResponse(
        application_id=application_id,
        business_account_id=loan_data.business_account_id,
        loan_amount=loan_data.loan_amount,
        loan_purpose=loan_data.loan_purpose,
        term_months=loan_data.term_months,
        status=status,
        estimated_rate=estimated_rate,
        monthly_payment=round(monthly_payment, 2),
        applied_at=datetime.utcnow()
    )


@router.post("/accounts/{account_id}/api-keys", response_model=APIKeyResponse)
async def generate_api_key(
    account_id: int,
    request: Request,
    api_key_data: APIKeyRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Generate API key for business account integration"""
    
    # Verify business account ownership
    account = db_session.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user['user_id']
    ).first()
    
    if not account or not account.extra_data.get("is_business"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business account not found"
        )
    
    # Generate API key
    api_key = f"bk_{secrets.token_urlsafe(32)}"
    key_id = uuid.uuid4().int % 1000000
    
    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_in_days)
    
    # Store API key in metadata
    api_keys = account.extra_data.get("api_keys", [])
    
    new_key = {
        "key_id": key_id,
        "api_key_hash": api_key[:10] + "..." + api_key[-4:],  # Store partial for display
        "key_name": api_key_data.key_name,
        "permissions": api_key_data.permissions,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expires_at.isoformat(),
        "is_active": True
    }
    
    api_keys.append(new_key)
    account.extra_data["api_keys"] = api_keys

    db_session.commit()

    log_business_action(
        action="generate_api_key",
        user_id=current_user['user_id'],
        details={"key_id": key_id, "key_name": api_key_data.key_name}
    )

    return APIKeyResponse(
        key_id=key_id,
        api_key=api_key,
        key_name=api_key_data.key_name,
        permissions=api_key_data.permissions,
        created_at=datetime.utcnow(),
        expires_at=expires_at
    )