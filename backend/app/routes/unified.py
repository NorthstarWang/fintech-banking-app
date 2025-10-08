from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..storage.memory_adapter import db, desc
from ..models import (
    UnifiedBalance, AssetBridge, ConversionRate, CollateralPosition,
    UnifiedTransaction, AssetClass, ConversionType, UnifiedTransferStatus
)
from ..models.entities.unified_models import (
    UnifiedBalanceResponse, AssetBridgeRequest, AssetBridgeResponse,
    UnifiedTransferRequest, UnifiedTransferResponse, CollateralPositionResponse,
    CrossAssetOpportunity, PortfolioOptimizationRequest, PortfolioOptimizationResponse,
    UnifiedSearchRequest, UnifiedSearchResponse
)
from ..repositories.unified_manager import UnifiedManager
from ..utils.auth import get_current_user
from ..utils.session_manager import session_manager

router = APIRouter()

@router.get("/balance", response_model=UnifiedBalanceResponse)
async def get_unified_balance(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get unified balance across all asset types for the current user"""
    from ..repositories.data_manager import data_manager
    
    unified_manager = UnifiedManager(data_manager)
    
    # Calculate fresh unified balance
    balance = unified_manager.calculate_unified_balance(current_user['user_id'])
    
    return UnifiedBalanceResponse.from_orm(balance)

@router.post("/bridge", response_model=AssetBridgeResponse, status_code=status.HTTP_201_CREATED)
async def create_asset_bridge(
    request: Request,
    bridge_request: AssetBridgeRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a bridge to convert between different asset types"""
    
    from ..repositories.data_manager import data_manager
    unified_manager = UnifiedManager(data_manager)
    
    try:
        # Create the bridge
        bridge = unified_manager.create_asset_bridge(
            user_id=current_user['user_id'],
            from_asset_class=bridge_request.from_asset_class,
            from_asset_id=bridge_request.from_asset_id,
            from_amount=float(bridge_request.from_amount),
            to_asset_class=bridge_request.to_asset_class,
            to_asset_id=bridge_request.to_asset_id,
            to_asset_type=bridge_request.to_asset_type
        )
        
        # Log the bridge creation
            }
        )
        
        return AssetBridgeResponse.from_orm(bridge)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/bridges", response_model=List[AssetBridgeResponse])
async def get_asset_bridges(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get asset bridge history for the current user"""
    query = db_session.query(AssetBridge).filter(
        AssetBridge.user_id == current_user['user_id']
    )
    
    if status:
        query = query.filter(AssetBridge.status == status)
    
    bridges = query.order_by(desc(AssetBridge.initiated_at)).limit(limit).all()
    
    return [AssetBridgeResponse.from_orm(b) for b in bridges]

@router.post("/transfer/smart", response_model=UnifiedTransferResponse, status_code=status.HTTP_201_CREATED)
async def create_smart_transfer(
    request: Request,
    transfer_request: UnifiedTransferRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a smart transfer that finds the optimal route"""
    
    from ..repositories.data_manager import data_manager
    unified_manager = UnifiedManager(data_manager)
    
    # Find optimal route
    route_info = unified_manager.find_optimal_transfer_route(
        user_id=current_user['user_id'],
        recipient_identifier=transfer_request.recipient_identifier,
        amount_usd=transfer_request.amount_usd,
        preferred_method=transfer_request.preferred_method
    )
    
    if "error" in route_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=route_info["error"]
        )
    
    # Create unified transaction
    recommended_route = route_info["recommended_route"]
    source_asset = recommended_route["source_asset"]
    
    transaction = UnifiedTransaction(
        user_id=current_user['user_id'],
        transaction_type='smart_transfer',
        source_system=source_asset['asset_class'].value,
        destination_system=route_info['recipient_type']['preferred_asset_class'].value,
        amount_usd=transfer_request.amount_usd,
        source_amount=str(transfer_request.amount_usd),
        source_currency=source_asset.get('currency', 'USD'),
        destination_amount=str(transfer_request.amount_usd - recommended_route['fees']['total_fee']),
        destination_currency=transfer_request.preferred_currency,
        route_taken=[recommended_route],
        total_fees_usd=recommended_route['fees']['total_fee'],
        status=UnifiedTransferStatus.PENDING,
        reference_ids={
            'recipient': transfer_request.recipient_identifier,
            'route_id': f"route_{datetime.utcnow().timestamp()}"
        }
    )
    
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    
    # Log the transfer
    
    # Create response
    response = UnifiedTransferResponse(
        id=transaction.id,
        sender_id=current_user['user_id'],
        recipient_identifier=transfer_request.recipient_identifier,
        amount_requested_usd=transfer_request.amount_usd,
        route_taken=[recommended_route],
        source_assets=[source_asset],
        amount_sent=transaction.source_amount,
        amount_sent_currency=transaction.source_currency,
        amount_received=transaction.destination_amount,
        amount_received_currency=transaction.destination_currency,
        total_fees_usd=transaction.total_fees_usd,
        estimated_arrival=datetime.utcnow(),
        status=transaction.status,
        initiated_at=transaction.initiated_at
    )
    
    return response

@router.get("/collateral/positions", response_model=List[CollateralPositionResponse])
async def get_collateral_positions(
    active_only: bool = Query(True),
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get collateral positions for the current user"""
    query = db_session.query(CollateralPosition).filter(
        CollateralPosition.user_id == current_user['user_id']
    )
    
    if active_only:
        query = query.filter(CollateralPosition.is_active == True)
    
    positions = query.all()
    
    return [CollateralPositionResponse.from_orm(p) for p in positions]

@router.post("/collateral/create", response_model=CollateralPositionResponse, status_code=status.HTTP_201_CREATED)
async def create_collateral_position(
    request: Request,
    collateral_assets: List[Dict[str, Any]],
    borrow_amount: float,
    currency: str = "USD",
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a new collateral position"""
    
    from ..repositories.data_manager import data_manager
    unified_manager = UnifiedManager(data_manager)
    
    try:
        position = unified_manager.create_collateral_position(
            user_id=current_user['user_id'],
            collateral_assets=collateral_assets,
            borrow_amount=borrow_amount,
            currency=currency
        )
        
        # Log the creation
        
        return CollateralPositionResponse.from_orm(position)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/opportunities", response_model=List[CrossAssetOpportunity])
async def get_cross_asset_opportunities(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get cross-asset optimization opportunities"""
    from ..repositories.data_manager import data_manager
    unified_manager = UnifiedManager(data_manager)
    
    opportunities = unified_manager.identify_cross_asset_opportunities(current_user['user_id'])
    
    return [
        CrossAssetOpportunity(
            opportunity_type=opp['type'],
            description=opp['description'],
            potential_gain_usd=opp.get('potential_gain', opp.get('potential_savings', 0)),
            risk_level=opp['risk_level'],
            actions_required=opp['actions'],
            assets_involved=[],  # Would be populated with specific assets
            expires_at=None,
            optimal_execution_time=None,
            minimum_capital=None,
            prerequisites=[]
        )
        for opp in opportunities
    ]

@router.post("/portfolio/optimize", response_model=PortfolioOptimizationResponse)
async def optimize_portfolio(
    request: Request,
    optimization_request: PortfolioOptimizationRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get portfolio optimization recommendations"""
    from ..repositories.data_manager import data_manager
    unified_manager = UnifiedManager(data_manager)
    
    # Get current balance
    balance = unified_manager.calculate_unified_balance(current_user['user_id'])
    
    # Calculate current allocation
    total = balance.total_net_worth_usd
    current_allocation = {
        AssetClass.FIAT.value: (balance.total_fiat_usd / total * 100) if total > 0 else 0,
        AssetClass.CRYPTO.value: (balance.total_crypto_usd / total * 100) if total > 0 else 0,
        AssetClass.NFT.value: (balance.nft_collection_value / total * 100) if total > 0 else 0,
        AssetClass.CREDIT.value: (balance.total_credit_available / total * 100) if total > 0 else 0,
    }
    
    # Generate recommendations based on goal
    if optimization_request.optimization_goal == "maximize_yield":
        recommended_allocation = {
            AssetClass.FIAT.value: 20,
            AssetClass.CRYPTO.value: 60,  # High crypto for yield
            AssetClass.NFT.value: 5,
            AssetClass.CREDIT.value: 15,
        }
        expected_return = 12.5
        risk_score = 7
    elif optimization_request.optimization_goal == "minimize_risk":
        recommended_allocation = {
            AssetClass.FIAT.value: 60,  # High fiat for stability
            AssetClass.CRYPTO.value: 20,
            AssetClass.NFT.value: 0,
            AssetClass.CREDIT.value: 20,
        }
        expected_return = 4.5
        risk_score = 3
    else:  # balance
        recommended_allocation = {
            AssetClass.FIAT.value: 40,
            AssetClass.CRYPTO.value: 40,
            AssetClass.NFT.value: 5,
            AssetClass.CREDIT.value: 15,
        }
        expected_return = 8.0
        risk_score = 5
    
    # Generate action steps
    actions = []
    if current_allocation[AssetClass.CRYPTO.value] < recommended_allocation[AssetClass.CRYPTO.value]:
        actions.append({
            "action": "increase_crypto",
            "description": f"Convert ${(recommended_allocation[AssetClass.CRYPTO.value] - current_allocation[AssetClass.CRYPTO.value]) * total / 100:.2f} from fiat to crypto",
            "priority": "high"
        })
    
    return PortfolioOptimizationResponse(
        current_allocation=current_allocation,
        recommended_allocation=recommended_allocation,
        recommended_actions=actions,
        expected_return_annual=expected_return,
        risk_score=risk_score,
        estimated_additional_yield=(expected_return - 5.0) * total / 100,  # Assume 5% baseline
        risk_reduction=max(0, 5 - risk_score),
        execution_steps=[
            {"step": 1, "action": "Review recommendations", "estimated_time": "5 minutes"},
            {"step": 2, "action": "Execute transfers", "estimated_time": "30 minutes"},
            {"step": 3, "action": "Monitor performance", "estimated_time": "ongoing"}
        ],
        estimated_fees=50.0  # Mock fee estimate
    )

@router.get("/conversion-rates", response_model=Dict[str, Any])
async def get_conversion_rates(
    from_asset: Optional[str] = Query(None),
    to_asset: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get current conversion rates"""
    from ..repositories.data_manager import data_manager
    from ..utils.asset_converter import AssetConverter
    
    converter = AssetConverter(data_manager)
    
    if from_asset and to_asset:
        # Get specific rate
        # Determine asset classes (simplified)
        from_class = AssetClass.FIAT if from_asset in converter.FIAT_RATES else AssetClass.CRYPTO
        to_class = AssetClass.FIAT if to_asset in converter.FIAT_RATES else AssetClass.CRYPTO
        
        rate, valid_until = converter.get_conversion_rate(
            from_asset, to_asset, from_class, to_class
        )
        
        return {
            "from": from_asset,
            "to": to_asset,
            "rate": rate,
            "inverse_rate": 1/rate,
            "valid_until": valid_until.isoformat(),
            "fees": converter.calculate_conversion_fees(
                1000,  # Sample amount
                converter._determine_conversion_type(from_class, to_class)
            )
        }
    else:
        # Get all rates
        return converter.get_all_conversion_rates()

@router.get("/transactions/unified", response_model=List[Dict[str, Any]])
async def get_unified_transactions(
    limit: int = Query(50, le=100),
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get unified transaction history across all systems"""
    from ..repositories.data_manager import data_manager
    unified_manager = UnifiedManager(data_manager)
    
    transactions = unified_manager.get_unified_transaction_history(
        current_user['user_id'],
        limit=limit
    )
    
    return transactions

@router.post("/search", response_model=UnifiedSearchResponse)
async def search_unified_transactions(
    search_request: UnifiedSearchRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Search across all transaction systems"""
    from ..repositories.data_manager import data_manager
    
    results = []
    total_results = 0
    grouping = {}
    aggregations = {}
    
    # Search traditional transactions
    if not search_request.asset_classes or AssetClass.FIAT in search_request.asset_classes:
        fiat_txs = [
            t for t in data_manager.transactions
            if t.get('user_id') == current_user['user_id']
            and (not search_request.query or search_request.query.lower() in str(t).lower())
        ]
        
        for tx in fiat_txs:
            if search_request.min_amount and abs(tx['amount']) < search_request.min_amount:
                continue
            if search_request.max_amount and abs(tx['amount']) > search_request.max_amount:
                continue
                
            results.append({
                'type': 'fiat',
                'data': tx
            })
        
        grouping[AssetClass.FIAT.value] = fiat_txs
        total_results += len(fiat_txs)
    
    # Search crypto transactions
    if not search_request.asset_classes or AssetClass.CRYPTO in search_request.asset_classes:
        crypto_txs = [
            t for t in data_manager.crypto_transactions
            if t.get('user_id') == current_user['user_id']
            and (not search_request.query or search_request.query.lower() in str(t).lower())
        ]
        
        grouping[AssetClass.CRYPTO.value] = crypto_txs
        total_results += len(crypto_txs)
    
    return UnifiedSearchResponse(
        results=results[:50],  # Limit results
        total_results=total_results,
        grouping=grouping,
        aggregations=aggregations
    )