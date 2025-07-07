"""
Mock implementation for business routes.
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.repositories.data_manager import data_manager
import uuid

router = APIRouter()

# Add business-specific data stores to data_manager
if not hasattr(data_manager, 'business_accounts'):
    data_manager.business_accounts = []
if not hasattr(data_manager, 'business_credit_lines'):
    data_manager.business_credit_lines = []
if not hasattr(data_manager, 'business_payrolls'):
    data_manager.business_payrolls = []
if not hasattr(data_manager, 'business_invoices'):
    data_manager.business_invoices = []
if not hasattr(data_manager, 'business_expenses'):
    data_manager.business_expenses = []
if not hasattr(data_manager, 'business_vendors'):
    data_manager.business_vendors = []
if not hasattr(data_manager, 'business_authorized_users'):
    data_manager.business_authorized_users = []
if not hasattr(data_manager, 'business_recurring_payments'):
    data_manager.business_recurring_payments = []
if not hasattr(data_manager, 'business_loans'):
    data_manager.business_loans = []
if not hasattr(data_manager, 'business_api_keys'):
    data_manager.business_api_keys = []

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "")
    user = data_manager.auth_service.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user

def generate_account_number():
    """Generate a realistic looking account number"""
    import random
    return f"{random.randint(1000, 9999)}-{random.randint(100000, 999999)}-{random.randint(10, 99)}"

# Business Accounts endpoints
@router.get("/accounts")
async def get_business_accounts(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get all business accounts for current user"""
    user_accounts = [acc for acc in data_manager.business_accounts 
                     if acc.get("user_id") == current_user["id"]]
    return user_accounts

@router.post("/accounts")
async def create_business_account(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Create a new business account"""
    account_id = str(uuid.uuid4())
    
    # Calculate interest rate for savings accounts
    interest_rate = data.get("interest_rate", 0.0)
    if data.get("account_type") == "business_savings" and interest_rate == 0:
        interest_rate = 2.5  # Default for business savings
    
    account = {
        "id": account_id,
        "user_id": current_user["id"],
        "business_name": data.get("business_name"),
        "business_type": data.get("business_type"),
        "ein": data.get("ein"),
        "account_type": data.get("account_type"),
        "account_number": generate_account_number(),
        "balance": data.get("initial_balance", 0.0),
        "interest_rate": interest_rate,
        "industry": data.get("industry", ""),
        "annual_revenue": data.get("annual_revenue", 0.0),
        "created_at": datetime.utcnow().isoformat(),
        "authorized_users": [current_user["username"]]
    }
    
    data_manager.business_accounts.append(account)
    return account

@router.get("/accounts/{account_id}")
async def get_business_account(account_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get specific business account details"""
    account = next((acc for acc in data_manager.business_accounts 
                    if acc["id"] == account_id and acc["user_id"] == current_user["id"]), None)
    
    if not account:
        raise HTTPException(status_code=404, detail="Business account not found")
    
    return account

# Credit Line endpoints
@router.post("/credit-line")
async def apply_for_credit_line(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Apply for business credit line"""
    # Verify business account exists
    account = next((acc for acc in data_manager.business_accounts 
                    if acc["id"] == data["business_account_id"] and acc["user_id"] == current_user["id"]), None)
    
    if not account:
        raise HTTPException(status_code=404, detail="Business account not found")
    
    # Calculate approved amount and interest rate based on annual revenue
    annual_revenue = account.get("annual_revenue", 0)
    if annual_revenue > 500000:
        approved_amount = min(data["requested_amount"], annual_revenue * 0.1)
        interest_rate = 7.5
    else:
        approved_amount = min(data["requested_amount"], 25000)
        interest_rate = 9.5
    
    credit_line = {
        "id": str(uuid.uuid4()),
        "business_account_id": data["business_account_id"],
        "requested_amount": data["requested_amount"],
        "approved_amount": approved_amount,
        "purpose": data.get("purpose", ""),
        "term_months": data.get("term_months", 24),
        "interest_rate": interest_rate,
        "status": "approved",
        "created_at": datetime.utcnow().isoformat()
    }
    
    data_manager.business_credit_lines.append(credit_line)
    return credit_line

# Payroll endpoints
@router.post("/payroll")
async def process_payroll(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Process business payroll"""
    # Verify business account exists
    account = next((acc for acc in data_manager.business_accounts 
                    if acc["id"] == data["business_account_id"] and acc["user_id"] == current_user["id"]), None)
    
    if not account:
        raise HTTPException(status_code=404, detail="Business account not found")
    
    payroll_id = str(uuid.uuid4())
    
    payroll = {
        "payroll_id": payroll_id,
        "business_account_id": data["business_account_id"],
        "payroll_date": data.get("payroll_date", datetime.utcnow().isoformat()),
        "employees": data.get("employees", []),
        "total_gross": data.get("total_gross", 0.0),
        "total_net": data.get("total_net", 0.0),
        "total_taxes": data.get("total_taxes", 0.0),
        "processed_at": datetime.utcnow().isoformat(),
        "status": "completed"
    }
    
    # Deduct payroll from account balance
    account["balance"] -= payroll["total_net"]
    
    data_manager.business_payrolls.append(payroll)
    return payroll

# Invoice endpoints
@router.post("/invoices")
async def create_invoice(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Create a business invoice"""
    # Verify business account exists
    account = next((acc for acc in data_manager.business_accounts 
                    if acc["id"] == data["business_account_id"] and acc["user_id"] == current_user["id"]), None)
    
    if not account:
        raise HTTPException(status_code=404, detail="Business account not found")
    
    # Calculate total from line items
    total_amount = 0.0
    for item in data.get("line_items", []):
        total_amount += item.get("quantity", 0) * item.get("unit_price", 0)
    
    invoice = {
        "id": str(uuid.uuid4()),
        "business_account_id": data["business_account_id"],
        "invoice_number": data.get("invoice_number"),
        "client_name": data.get("client_name"),
        "client_email": data.get("client_email"),
        "issue_date": data.get("issue_date"),
        "due_date": data.get("due_date"),
        "payment_terms": data.get("payment_terms", "net_30"),
        "line_items": data.get("line_items", []),
        "total_amount": total_amount,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    
    data_manager.business_invoices.append(invoice)
    return invoice

# Expense endpoints
@router.post("/expenses")
async def record_expense(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Record a business expense"""
    # Verify business account exists
    account = next((acc for acc in data_manager.business_accounts 
                    if acc["id"] == data["business_account_id"] and acc["user_id"] == current_user["id"]), None)
    
    if not account:
        raise HTTPException(status_code=404, detail="Business account not found")
    
    expense = {
        "id": str(uuid.uuid4()),
        "business_account_id": data["business_account_id"],
        "amount": data.get("amount"),
        "category": data.get("category"),
        "description": data.get("description", ""),
        "vendor": data.get("vendor", ""),
        "tax_deductible": data.get("tax_deductible", False),
        "receipt_url": data.get("receipt_url", ""),
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Deduct expense from account balance
    account["balance"] -= expense["amount"]
    
    data_manager.business_expenses.append(expense)
    return expense

# Tax Report endpoints
@router.get("/tax-report/{account_id}/{year}")
async def get_tax_report(account_id: str, year: int, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get business tax report for a specific year"""
    # Verify business account exists
    account = next((acc for acc in data_manager.business_accounts 
                    if acc["id"] == account_id and acc["user_id"] == current_user["id"]), None)
    
    if not account:
        raise HTTPException(status_code=404, detail="Business account not found")
    
    # Calculate income from invoices
    total_income = sum(inv["total_amount"] for inv in data_manager.business_invoices 
                       if inv["business_account_id"] == account_id and inv["status"] == "paid")
    
    # Calculate expenses
    business_expenses = [exp for exp in data_manager.business_expenses 
                        if exp["business_account_id"] == account_id]
    
    total_expenses = sum(exp["amount"] for exp in business_expenses)
    deductible_expenses = sum(exp["amount"] for exp in business_expenses if exp["tax_deductible"])
    
    # Group expenses by category
    expense_categories = {}
    for exp in business_expenses:
        category = exp["category"]
        if category not in expense_categories:
            expense_categories[category] = 0
        expense_categories[category] += exp["amount"]
    
    return {
        "year": year,
        "business_account_id": account_id,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "deductible_expenses": deductible_expenses,
        "net_profit": total_income - total_expenses,
        "expense_categories": expense_categories
    }

# Vendor endpoints
@router.post("/vendors")
async def create_vendor(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Create a new vendor"""
    vendor = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "vendor_name": data.get("vendor_name"),
        "vendor_type": data.get("vendor_type", "supplier"),
        "contact_email": data.get("contact_email", ""),
        "payment_terms": data.get("payment_terms", "net_30"),
        "tax_id": data.get("tax_id", ""),
        "created_at": datetime.utcnow().isoformat()
    }
    
    data_manager.business_vendors.append(vendor)
    return vendor

# Cash Flow Analysis
@router.get("/cash-flow/{account_id}")
async def get_cash_flow_analysis(account_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get cash flow analysis for business account"""
    # Verify business account exists
    account = next((acc for acc in data_manager.business_accounts 
                    if acc["id"] == account_id and acc["user_id"] == current_user["id"]), None)
    
    if not account:
        raise HTTPException(status_code=404, detail="Business account not found")
    
    # Calculate inflows and outflows
    current_month_start = datetime.utcnow().replace(day=1)
    
    # Inflows from paid invoices
    inflows = sum(inv["total_amount"] for inv in data_manager.business_invoices 
                  if inv["business_account_id"] == account_id and inv["status"] == "paid")
    
    # Outflows from expenses and payroll
    expense_outflows = sum(exp["amount"] for exp in data_manager.business_expenses 
                          if exp["business_account_id"] == account_id)
    
    payroll_outflows = sum(pay["total_net"] for pay in data_manager.business_payrolls 
                          if pay["business_account_id"] == account_id)
    
    total_outflows = expense_outflows + payroll_outflows
    
    return {
        "account_id": account_id,
        "current_month": {
            "month": current_month_start.strftime("%Y-%m"),
            "inflows": inflows,
            "outflows": total_outflows,
            "net_flow": inflows - total_outflows
        },
        "projections": {
            "next_month": {
                "projected_inflows": inflows * 1.05,  # 5% growth projection
                "projected_outflows": total_outflows * 1.02,  # 2% increase
                "projected_net_flow": (inflows * 1.05) - (total_outflows * 1.02)
            }
        },
        "recommendations": [
            "Consider negotiating better payment terms with vendors",
            "Review recurring expenses for cost optimization",
            "Implement automated invoicing to improve cash collection"
        ]
    }

# Authorized Users endpoints
@router.post("/accounts/{account_id}/users")
async def add_authorized_user(account_id: str, data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Add authorized user to business account"""
    # Verify business account exists and user owns it
    account = next((acc for acc in data_manager.business_accounts 
                    if acc["id"] == account_id and acc["user_id"] == current_user["id"]), None)
    
    if not account:
        raise HTTPException(status_code=404, detail="Business account not found")
    
    authorized_user = {
        "id": str(uuid.uuid4()),
        "business_account_id": account_id,
        "username": data.get("username"),
        "role": data.get("role"),
        "permissions": data.get("permissions", []),
        "added_by": current_user["username"],
        "added_at": datetime.utcnow().isoformat()
    }
    
    # Add username to account's authorized users list
    if "authorized_users" not in account:
        account["authorized_users"] = []
    account["authorized_users"].append(data.get("username"))
    
    data_manager.business_authorized_users.append(authorized_user)
    return authorized_user

# Recurring Payments endpoints
@router.post("/recurring-payments")
async def create_recurring_payment(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Set up recurring business payment"""
    # Verify business account exists
    account = next((acc for acc in data_manager.business_accounts 
                    if acc["id"] == data["business_account_id"] and acc["user_id"] == current_user["id"]), None)
    
    if not account:
        raise HTTPException(status_code=404, detail="Business account not found")
    
    # Calculate next payment date based on frequency
    start_date = datetime.fromisoformat(data["start_date"].replace("Z", "+00:00").replace("+00:00", ""))
    if data["frequency"] == "monthly":
        next_payment_date = start_date + timedelta(days=30)
    elif data["frequency"] == "weekly":
        next_payment_date = start_date + timedelta(days=7)
    else:
        next_payment_date = start_date + timedelta(days=1)
    
    recurring_payment = {
        "id": str(uuid.uuid4()),
        "business_account_id": data["business_account_id"],
        "payee": data.get("payee"),
        "amount": data.get("amount"),
        "frequency": data.get("frequency"),
        "category": data.get("category", ""),
        "start_date": data.get("start_date"),
        "end_date": data.get("end_date"),
        "next_payment_date": next_payment_date.isoformat(),
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    
    data_manager.business_recurring_payments.append(recurring_payment)
    return recurring_payment

# Loan Application endpoints
@router.post("/loans/apply")
async def apply_for_loan(data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Apply for business loan"""
    # Verify business account exists
    account = next((acc for acc in data_manager.business_accounts 
                    if acc["id"] == data["business_account_id"] and acc["user_id"] == current_user["id"]), None)
    
    if not account:
        raise HTTPException(status_code=404, detail="Business account not found")
    
    # Calculate estimated rate based on business metrics
    annual_revenue = data.get("annual_revenue", 0)
    years_in_business = data.get("years_in_business", 0)
    
    if annual_revenue > 1000000 and years_in_business > 3:
        estimated_rate = 6.5
        status = "pre-approved"
    elif annual_revenue > 500000 and years_in_business > 1:
        estimated_rate = 8.5
        status = "under_review"
    else:
        estimated_rate = 10.5
        status = "pending"
    
    loan_application = {
        "application_id": str(uuid.uuid4()),
        "business_account_id": data["business_account_id"],
        "loan_amount": data.get("loan_amount"),
        "loan_purpose": data.get("loan_purpose", ""),
        "term_months": data.get("term_months", 60),
        "annual_revenue": annual_revenue,
        "years_in_business": years_in_business,
        "estimated_rate": estimated_rate,
        "status": status,
        "applied_at": datetime.utcnow().isoformat()
    }
    
    data_manager.business_loans.append(loan_application)
    return loan_application

# API Key Management endpoints
@router.post("/accounts/{account_id}/api-keys")
async def generate_api_key(account_id: str, data: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Generate API key for business integrations"""
    # Verify business account exists and user owns it
    account = next((acc for acc in data_manager.business_accounts 
                    if acc["id"] == account_id and acc["user_id"] == current_user["id"]), None)
    
    if not account:
        raise HTTPException(status_code=404, detail="Business account not found")
    
    # Generate API key
    api_key = f"bk_{uuid.uuid4().hex}"
    key_id = str(uuid.uuid4())
    
    api_key_record = {
        "key_id": key_id,
        "api_key": api_key,
        "business_account_id": account_id,
        "key_name": data.get("key_name"),
        "permissions": data.get("permissions", []),
        "expires_in_days": data.get("expires_in_days", 365),
        "expires_at": (datetime.utcnow() + timedelta(days=data.get("expires_in_days", 365))).isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "created_by": current_user["username"]
    }
    
    data_manager.business_api_keys.append(api_key_record)
    return api_key_record