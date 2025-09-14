"""
Complete mock implementation for accounts routes.
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from app.repositories.data_manager import data_manager

router = APIRouter()

class CreateAccountRequest(BaseModel):
    name: str
    account_type: str
    initial_balance: float = 0.0
    credit_limit: Optional[float] = None
    interest_rate: Optional[float] = None

class UpdateAccountRequest(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Get current user from auth header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    user = data_manager.auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user

@router.get("")
async def get_accounts(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get all active accounts for current user."""
    raw_accounts = [
        acc for acc in data_manager.accounts 
        if acc["user_id"] == current_user["id"] and acc.get("is_active", True)
    ]
    
    # Normalize field names for compatibility
    user_accounts = []
    for acc in raw_accounts:
        normalized_acc = acc.copy()
        # Rename account_name to name if it exists
        if "account_name" in normalized_acc and "name" not in normalized_acc:
            normalized_acc["name"] = normalized_acc["account_name"]
        # Ensure account_number exists
        if "account_number" not in normalized_acc:
            normalized_acc["account_number"] = f"ACC{normalized_acc.get('id', '0'):0>6}"
        user_accounts.append(normalized_acc)
    
    return user_accounts

@router.post("", status_code=201)
async def create_account(
    request: CreateAccountRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new account."""
    account_number = f"ACC{len(data_manager.accounts) + 1001:06d}"
    
    account = {
        "id": str(len(data_manager.accounts) + 1),
        "user_id": current_user["id"],
        "name": request.name,
        "account_type": request.account_type,
        "account_number": account_number,
        "balance": request.initial_balance,
        "currency": "USD",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }
    
    if request.credit_limit is not None:
        account["credit_limit"] = request.credit_limit
    if request.interest_rate is not None:
        account["interest_rate"] = request.interest_rate
    
    data_manager.accounts.append(account)
    return account

@router.get("/summary")
async def get_account_summary(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get account summary for user."""
    raw_accounts = [
        acc for acc in data_manager.accounts 
        if acc["user_id"] == current_user["id"] and acc.get("is_active", True)
    ]
    
    # Normalize field names for compatibility
    user_accounts = []
    for acc in raw_accounts:
        normalized_acc = acc.copy()
        # Rename account_name to name if it exists
        if "account_name" in normalized_acc and "name" not in normalized_acc:
            normalized_acc["name"] = normalized_acc["account_name"]
        # Ensure account_number exists
        if "account_number" not in normalized_acc:
            normalized_acc["account_number"] = f"ACC{normalized_acc.get('id', '0'):0>6}"
        user_accounts.append(normalized_acc)
    
    total_balance = sum(acc["balance"] for acc in user_accounts)
    
    return {
        "total_accounts": len(user_accounts),
        "total_balance": total_balance,
        "total_assets": total_balance,
        "total_liabilities": 0,
        "net_worth": total_balance,
        "accounts": user_accounts
    }

@router.get("/{account_id}")
async def get_account(
    account_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get specific account."""
    account = next(
        (acc for acc in data_manager.accounts 
         if acc["id"] == account_id and acc["user_id"] == current_user["id"]),
        None
    )
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Check if account is soft-deleted
    if not account.get("is_active", True):
        raise HTTPException(status_code=400, detail="Account is closed")
    
    return account

@router.put("/{account_id}")
async def update_account(
    account_id: str,
    request: UpdateAccountRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update account details."""
    account = next(
        (acc for acc in data_manager.accounts 
         if acc["id"] == account_id and acc["user_id"] == current_user["id"]),
        None
    )
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if request.name is not None:
        account["name"] = request.name
    if request.is_active is not None:
        account["is_active"] = request.is_active
    
    account["updated_at"] = datetime.utcnow().isoformat()
    return account

@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete/close an account."""
    account = next(
        (acc for acc in data_manager.accounts 
         if acc["id"] == account_id and acc["user_id"] == current_user["id"]),
        None
    )
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if account["balance"] > 0:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete account with positive balance"
        )
    
    # Soft delete - mark as inactive
    account["is_active"] = False
    account["closed_at"] = datetime.utcnow().isoformat()
    
    return {"message": "Account closed successfully"}

@router.get("/{account_id}/transactions")
async def get_account_transactions(
    account_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get transactions for specific account."""
    account = next(
        (acc for acc in data_manager.accounts 
         if acc["id"] == account_id and acc["user_id"] == current_user["id"]),
        None
    )
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    transactions = [
        t for t in data_manager.transactions 
        if t.get("account_id") == account_id
    ]
    
    return transactions



@router.get("/{account_id}/balance-history")
async def get_balance_history(
    account_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get balance history for account."""
    account = next(
        (acc for acc in data_manager.accounts 
         if acc["id"] == account_id and acc["user_id"] == current_user["id"]),
        None
    )
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Return balance history with change field
    current_balance = account["balance"]
    return [{
        "date": datetime.utcnow().isoformat(),
        "balance": current_balance,
        "change": 0.0  # No change for the current entry
    }]

@router.get("/{account_id}/permissions")
async def get_account_permissions(
    account_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get account permissions."""
    account = next(
        (acc for acc in data_manager.accounts 
         if acc["id"] == account_id),
        None
    )
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if account["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "account_id": account_id,
        "permissions": ["view", "edit", "transfer"]
    }

@router.post("/joint", status_code=201)
async def create_joint_account(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a joint account."""
    # Since the request is not a Pydantic model, initial_balance might be in the request directly
    # Extract fields - handle both direct fields and nested structure
    account_name = request.get("name", "Joint Account")
    account_type = request.get("account_type", "checking")
    initial_balance = float(request.get("initial_balance", 0.0))
    joint_owner_username = request.get("joint_owner_username")
    
    # Build owners list
    owners = [current_user["id"]]
    
    # Add joint owner if specified
    if joint_owner_username:
        # Find the user by username
        joint_user = next(
            (u for u in data_manager.users if u["username"] == joint_owner_username),
            None
        )
        if joint_user:
            owners.append(joint_user["id"])
    
    # Create account with all fields
    account = {
        "id": str(len(data_manager.accounts) + 1),
        "name": account_name,
        "account_type": account_type,
        "balance": initial_balance,
        "currency": "USD",
        "user_id": current_user["id"],
        "owners": owners,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }
    
    data_manager.accounts.append(account)
    return account
