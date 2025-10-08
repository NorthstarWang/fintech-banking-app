from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import csv
import json
import io
import uuid
import os

from ..storage.memory_adapter import db, desc
from ..models import (
    Transaction, Account, Category, User,
    TransactionType, ExportFormat
, Any)
from ..models import ExportRequest, ExportResponse
from ..utils.auth import get_current_user
from ..utils.validators import ValidationError
from ..utils.session_manager import session_manager

router = APIRouter()

@router.post("/transactions", response_model=ExportResponse)
async def export_transactions(
    request: Request,
    export_data: ExportRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Export transactions in various formats"""
    
    # Query transactions with filters
    query = db_session.query(Transaction).filter(
        Transaction.user_id == current_user['user_id']
    )
    
    # Apply date filters
    if export_data.start_date:
        query = query.filter(Transaction.transaction_date >= export_data.start_date)
    if export_data.end_date:
        query = query.filter(Transaction.transaction_date <= export_data.end_date)
    
    # Apply account filter
    if export_data.account_ids:
        query = query.filter(Transaction.account_id.in_(export_data.account_ids))
    
    # Apply category filter
    if export_data.category_ids:
        query = query.filter(Transaction.category_id.in_(export_data.category_ids))
    
    transactions = query.order_by(Transaction.transaction_date.desc()).all()
    
    # Generate export based on format
    export_id = str(uuid.uuid4())
    filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if export_data.format == ExportFormat.CSV:
        content = generate_csv(transactions)
        filename += ".csv"
        content_type = "text/csv"
    elif export_data.format == ExportFormat.JSON:
        content = generate_json(transactions)
        filename += ".json"
        content_type = "application/json"
    else:
        raise ValidationError(f"Export format {export_data.format} not yet implemented")
    
    # Log the export
            "page_url": "/exports",
            "export_id": export_id,
            "format": export_data.format.value,
            "transaction_count": len(transactions)
        }
    )
    
    # Return export info
    return ExportResponse(
        export_id=export_id,
        filename=filename,
        format=export_data.format,
        size_bytes=len(content.encode('utf-8')),
        transaction_count=len(transactions),
        created_at=datetime.now(),
        download_url=f"/api/exports/download/{export_id}"
    )

@router.get("/download/{export_id}")
async def download_export(
    export_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download an exported file"""
    # In a real app, this would retrieve the file from storage
    # For now, return a simple response
    return JSONResponse(
        content={"message": "Export download not yet implemented"},
        status_code=status.HTTP_501_NOT_IMPLEMENTED
    )

def generate_csv(transactions: List[Transaction]) -> str:
    """Generate CSV content from transactions"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Date", "Description", "Amount", "Type", "Category", 
        "Account", "Status", "Notes"
    ])
    
    # Write transactions
    for txn in transactions:
        writer.writerow([
            txn.transaction_date.strftime("%Y-%m-%d"),
            txn.description.strip() if txn.description else '',  # Strip any leading/trailing spaces
            f"{txn.amount:.2f}",
            txn.transaction_type.value,
            txn.category.name if txn.category else "Uncategorized",
            txn.account.name if txn.account else "Unknown",
            txn.status.value,
            txn.notes or ""
        ])
    
    return output.getvalue()

def generate_json(transactions: List[Transaction]) -> str:
    """Generate JSON content from transactions"""
    data = []
    for txn in transactions:
        data.append({
            "id": txn.id,
            "date": txn.transaction_date.isoformat(),
            "description": txn.description,
            "amount": float(txn.amount),
            "type": txn.transaction_type.value,
            "category": txn.category.name if txn.category else None,
            "category_id": txn.category_id,
            "account": txn.account.name if txn.account else None,
            "account_id": txn.account_id,
            "status": txn.status.value,
            "notes": txn.notes
        })
    
    return json.dumps(data, indent=2)