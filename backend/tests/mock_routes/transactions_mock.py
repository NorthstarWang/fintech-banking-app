"""
Complete mock implementation for transactions routes.
"""
from fastapi import APIRouter, HTTPException, Header, Depends, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from app.repositories.data_manager import data_manager

router = APIRouter()

class CreateTransactionRequest(BaseModel):
    account_id: str
    amount: float
    description: str
    category: str
    transaction_type: str
    merchant: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

class UpdateTransactionRequest(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    merchant: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: float
    description: Optional[str] = "Transfer"

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
async def get_transactions(
    current_user: Dict[str, Any] = Depends(get_current_user),
    account_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """Get transactions for current user."""
    user_account_ids = [
        acc["id"] for acc in data_manager.accounts 
        if acc["user_id"] == current_user["id"]
    ]
    
    transactions = []
    for t in data_manager.transactions:
        if t.get("account_id") not in user_account_ids:
            continue
        if account_id and t.get("account_id") != account_id:
            continue
        if category and t.get("category") != category:
            continue
        if search and search.lower() not in t.get("description", "").lower():
            continue
        transactions.append(t)
    
    transactions.sort(key=lambda x: x.get("date", ""), reverse=True)
    return transactions[:limit]

@router.post("", status_code=201)
async def create_transaction(
    request: Dict[str, Any],  # Accept dict to handle test variations
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new transaction."""
    # Handle both model and dict inputs
    account_id = request.get("account_id")
    amount = request.get("amount", 0)
    description = request.get("description", "")
    category = request.get("category", "")
    transaction_type = request.get("transaction_type", "expense")
    merchant = request.get("merchant")
    tags = request.get("tags", [])
    
    # Verify account ownership
    account = next(
        (acc for acc in data_manager.accounts 
         if acc["id"] == account_id and acc["user_id"] == current_user["id"]),
        None
    )
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Create transaction with proper amount handling
    if transaction_type == "expense" and amount > 0:
        amount = -amount
    
    transaction = {
        "id": str(len(data_manager.transactions) + 1),
        "account_id": account_id,
        "amount": amount,
        "description": description,
        "category": category,
        "transaction_type": transaction_type,
        "merchant": merchant,
        "tags": tags or [],
        "notes": request.get("notes", ""),
        "date": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Update account balance
    account["balance"] += amount
    
    data_manager.transactions.append(transaction)
    return transaction

@router.post("/transfer", status_code=201)
async def transfer_funds(
    request: TransferRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Transfer funds between accounts."""
    # Get both accounts
    from_account = next(
        (acc for acc in data_manager.accounts 
         if acc["id"] == request.from_account_id and acc["user_id"] == current_user["id"]),
        None
    )
    
    to_account = next(
        (acc for acc in data_manager.accounts 
         if acc["id"] == request.to_account_id),
        None
    )
    
    if not from_account or not to_account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Check sufficient balance
    if from_account["balance"] < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # Perform transfer
    from_account["balance"] -= request.amount
    to_account["balance"] += request.amount
    
    # Create transaction records
    transaction_id = str(len(data_manager.transactions) + 1)
    
    # Debit transaction
    debit_trans = {
        "id": transaction_id,
        "account_id": request.from_account_id,
        "amount": -request.amount,
        "description": request.description,
        "transaction_type": "transfer",
        "category": "Transfer",
        "date": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }
    data_manager.transactions.append(debit_trans)
    
    # Credit transaction
    credit_trans = {
        "id": str(int(transaction_id) + 1),
        "account_id": request.to_account_id,
        "amount": request.amount,
        "description": request.description,
        "transaction_type": "transfer",
        "category": "Transfer",
        "date": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }
    data_manager.transactions.append(credit_trans)
    
    return {
        "id": transaction_id,
        "transaction_id": transaction_id,
        "from_account_id": request.from_account_id,
        "to_account_id": request.to_account_id,
        "amount": request.amount,
        "status": "completed",
        "message": "Transfer successful"
    }

@router.get("/search")
async def search_transactions(
    q: str = Query(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search transactions."""
    user_account_ids = [
        acc["id"] for acc in data_manager.accounts 
        if acc["user_id"] == current_user["id"]
    ]
    
    results = []
    for t in data_manager.transactions:
        if t.get("account_id") not in user_account_ids:
            continue
        if q.lower() in t.get("description", "").lower() or q.lower() in t.get("merchant", "").lower():
            results.append(t)
    
    return results

@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get specific transaction."""
    user_account_ids = [
        acc["id"] for acc in data_manager.accounts 
        if acc["user_id"] == current_user["id"]
    ]
    
    transaction = next(
        (t for t in data_manager.transactions 
         if t["id"] == transaction_id and t.get("account_id") in user_account_ids),
        None
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction

@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    request: UpdateTransactionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update transaction details."""
    user_account_ids = [
        acc["id"] for acc in data_manager.accounts 
        if acc["user_id"] == current_user["id"]
    ]
    
    transaction = next(
        (t for t in data_manager.transactions 
         if t["id"] == transaction_id and t.get("account_id") in user_account_ids),
        None
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if request.description is not None:
        transaction["description"] = request.description
    if request.category is not None:
        transaction["category"] = request.category
    if request.merchant is not None:
        transaction["merchant"] = request.merchant
    if request.tags is not None:
        transaction["tags"] = request.tags
    if request.notes is not None:
        transaction["notes"] = request.notes
    
    transaction["updated_at"] = datetime.utcnow().isoformat()
    return transaction

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a transaction."""
    user_account_ids = [
        acc["id"] for acc in data_manager.accounts 
        if acc["user_id"] == current_user["id"]
    ]
    
    transaction = next(
        (t for t in data_manager.transactions 
         if t["id"] == transaction_id and t.get("account_id") in user_account_ids),
        None
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Check if transaction is pending (can only delete pending transactions)
    if transaction.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Only pending transactions can be deleted")
    
    # Get the account
    account = next(
        (acc for acc in data_manager.accounts if acc["id"] == transaction.get("account_id")),
        None
    )
    
    if account:
        account["balance"] -= transaction["amount"]
    
    data_manager.transactions.remove(transaction)
    return {"message": "Transaction deleted successfully"}

@router.post("/{transaction_id}/tags", status_code=201)
async def add_tags(
    transaction_id: str,
    tags: List[str],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add tags to transaction."""
    user_account_ids = [
        acc["id"] for acc in data_manager.accounts 
        if acc["user_id"] == current_user["id"]
    ]
    
    transaction = next(
        (t for t in data_manager.transactions 
         if t["id"] == transaction_id and t.get("account_id") in user_account_ids),
        None
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if "tags" not in transaction:
        transaction["tags"] = []
    
    transaction["tags"].extend(tags)
    transaction["tags"] = list(set(transaction["tags"]))
    
    return transaction
