"""
Virtual currency converter API routes (Airtm-like P2P exchange).
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.entities.currency_converter_models import (
    ConversionHistoryResponse,
    ConversionOrderCreate,
    ConversionOrderResponse,
    ConversionQuoteRequest,
    ConversionQuoteResponse,
    CurrencyBalanceResponse,
    CurrencySupportedResponse,
    CurrencyType,
    ExchangeRateResponse,
    P2PTradeRequest,
    P2PTradeResponse,
    PeerOfferCreate,
    PeerOfferResponse,
    TransferLimitResponse,
    TransferMethod,
    TransferStatus,
)
from app.repositories.currency_converter_manager import CurrencyConverterManager
from app.repositories.data_manager import data_manager
from app.utils.auth import get_current_user

router = APIRouter()

# Initialize currency converter manager
converter_manager = CurrencyConverterManager(data_manager)

# Currency information endpoints
@router.get("/currencies", response_model=list[CurrencySupportedResponse])
async def get_supported_currencies(
    currency_type: CurrencyType | None = Query(None, description="Filter by currency type"),
    current_user = Depends(get_current_user)
) -> list[CurrencySupportedResponse]:
    """Get list of supported currencies."""
    return converter_manager.get_supported_currencies(currency_type)

@router.get("/exchange-rate/{from_currency}/{to_currency}", response_model=ExchangeRateResponse)
async def get_exchange_rate(
    from_currency: str,
    to_currency: str,
    current_user = Depends(get_current_user)
) -> ExchangeRateResponse:
    """Get exchange rate between two currencies."""
    rate = converter_manager.get_exchange_rate(from_currency.upper(), to_currency.upper())
    if not rate:
        raise HTTPException(status_code=404, detail="Currency pair not supported")
    return rate

# Conversion endpoints
@router.post("/quote", response_model=ConversionQuoteResponse)
async def create_conversion_quote(
    request: ConversionQuoteRequest,
    current_user = Depends(get_current_user)
) -> ConversionQuoteResponse:
    """Create a conversion quote."""
    try:
        return converter_manager.create_conversion_quote(current_user["user_id"], request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/orders", response_model=ConversionOrderResponse)
async def create_conversion_order(
    order: ConversionOrderCreate,
    current_user = Depends(get_current_user)
) -> ConversionOrderResponse:
    """Create a conversion order from a quote."""
    try:
        return converter_manager.create_conversion_order(current_user["user_id"], order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/orders", response_model=list[ConversionOrderResponse])
async def get_conversion_orders(
    status: TransferStatus | None = Query(None, description="Filter by status"),
    current_user = Depends(get_current_user)
) -> list[ConversionOrderResponse]:
    """Get user's conversion orders."""
    return converter_manager.get_user_orders(current_user["user_id"], status)

@router.get("/orders/{order_id}", response_model=ConversionOrderResponse)
async def get_conversion_order(
    order_id: int,
    current_user = Depends(get_current_user)
) -> ConversionOrderResponse:
    """Get specific conversion order details."""
    orders = converter_manager.get_user_orders(current_user["user_id"])
    order = next((o for o in orders if o.id == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# P2P trading endpoints
@router.post("/p2p/offers", response_model=PeerOfferResponse)
async def create_peer_offer(
    offer: PeerOfferCreate,
    current_user = Depends(get_current_user)
) -> PeerOfferResponse:
    """Create a P2P currency exchange offer."""
    return converter_manager.create_peer_offer(current_user["user_id"], offer)

@router.get("/p2p/offers/search", response_model=list[PeerOfferResponse])
async def search_peer_offers(
    currency: str = Query(..., description="Currency code"),
    amount: float = Query(..., description="Amount to exchange"),
    transfer_method: TransferMethod | None = Query(None, description="Preferred transfer method"),
    current_user = Depends(get_current_user)
) -> list[PeerOfferResponse]:
    """Search for P2P offers."""
    return converter_manager.search_peer_offers(currency.upper(), amount, transfer_method)

@router.get("/p2p/offers/mine", response_model=list[PeerOfferResponse])
async def get_my_offers(
    current_user = Depends(get_current_user)
) -> list[PeerOfferResponse]:
    """Get user's own P2P offers."""
    if not hasattr(data_manager, 'peer_offers'):
        return []

    offers = [o for o in data_manager.peer_offers if o['peer_id'] == current_user["user_id"]]
    return [converter_manager._offer_to_response(
        o, o['peer_id'], converter_manager._get_user_verification_level(o['peer_id'])
    ) for o in offers]

@router.delete("/p2p/offers/{offer_id}")
async def cancel_peer_offer(
    offer_id: int,
    current_user = Depends(get_current_user)
) -> dict:
    """Cancel a P2P offer."""
    if not hasattr(data_manager, 'peer_offers'):
        raise HTTPException(status_code=404, detail="Offer not found")

    offer = next((o for o in data_manager.peer_offers
                 if o['id'] == offer_id and o['peer_id'] == current_user["user_id"]), None)

    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    offer['is_active'] = False
    return {"message": "Offer cancelled successfully"}

@router.post("/p2p/trades", response_model=P2PTradeResponse)
async def create_p2p_trade(
    trade: P2PTradeRequest,
    current_user = Depends(get_current_user)
) -> P2PTradeResponse:
    """Create a P2P trade from an offer."""
    try:
        return converter_manager.create_p2p_trade(current_user["user_id"], trade)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/p2p/trades", response_model=list[P2PTradeResponse])
async def get_p2p_trades(
    role: str | None = Query(None, description="Filter by role: buyer or seller"),
    status: TransferStatus | None = Query(None, description="Filter by status"),
    current_user = Depends(get_current_user)
) -> list[P2PTradeResponse]:
    """Get user's P2P trades."""
    if not hasattr(data_manager, 'p2p_trades'):
        return []

    trades = []
    for trade in data_manager.p2p_trades:
        if role == "buyer" and trade['buyer_id'] != current_user["user_id"]:
            continue
        if role == "seller" and trade['seller_id'] != current_user["user_id"]:
            continue
        if not role and trade['buyer_id'] != current_user["user_id"] and trade['seller_id'] != current_user["user_id"]:
            continue
        if status and trade['status'] != status.value:
            continue

        trades.append(converter_manager._trade_to_response(trade))

    return trades

@router.put("/p2p/trades/{trade_id}/confirm")
async def confirm_p2p_payment(
    trade_id: int,
    current_user = Depends(get_current_user)
) -> dict:
    """Confirm payment for a P2P trade (buyer action)."""
    if not hasattr(data_manager, 'p2p_trades'):
        raise HTTPException(status_code=404, detail="Trade not found")

    trade = next((t for t in data_manager.p2p_trades
                 if t['id'] == trade_id and t['buyer_id'] == current_user["user_id"]), None)

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    if trade['status'] != TransferStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Trade not in pending status")

    trade['status'] = TransferStatus.PROCESSING.value
    return {"message": "Payment confirmed, waiting for seller to release funds"}

@router.put("/p2p/trades/{trade_id}/release")
async def release_p2p_funds(
    trade_id: int,
    current_user = Depends(get_current_user)
) -> dict:
    """Release funds for a P2P trade (seller action)."""
    if not hasattr(data_manager, 'p2p_trades'):
        raise HTTPException(status_code=404, detail="Trade not found")

    trade = next((t for t in data_manager.p2p_trades
                 if t['id'] == trade_id and t['seller_id'] == current_user["user_id"]), None)

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    if trade['status'] != TransferStatus.PROCESSING.value:
        raise HTTPException(status_code=400, detail="Payment not confirmed by buyer")

    trade['status'] = TransferStatus.COMPLETED.value
    trade['escrow_released'] = True
    trade['completed_at'] = datetime.utcnow()

    return {"message": "Funds released successfully"}

# Balance and history endpoints
@router.get("/balances", response_model=list[CurrencyBalanceResponse])
async def get_currency_balances(
    current_user = Depends(get_current_user)
) -> list[CurrencyBalanceResponse]:
    """Get user's currency balances."""
    return converter_manager.get_user_balances(current_user["user_id"])

@router.get("/history", response_model=ConversionHistoryResponse)
async def get_conversion_history(
    current_user = Depends(get_current_user)
) -> ConversionHistoryResponse:
    """Get user's conversion history and statistics."""
    return converter_manager.get_conversion_history(current_user["user_id"])

@router.get("/limits", response_model=TransferLimitResponse)
async def get_transfer_limits(
    current_user = Depends(get_current_user)
) -> TransferLimitResponse:
    """Get user's transfer limits based on verification level."""
    return converter_manager.get_transfer_limits(current_user["user_id"])

# Mock data generation endpoint
@router.post("/generate-mock-data")
async def generate_mock_converter_data(
    num_offers: int = Query(10, description="Number of P2P offers to generate"),
    current_user = Depends(get_current_user)
) -> dict:
    """Generate mock currency converter data for testing."""
    import random

    # Create some peer offers
    currencies = ['USD', 'EUR', 'MXN', 'BRL', 'BTC', 'ETH']
    generated_offers = []

    for i in range(num_offers):
        currency = random.choice(currencies)
        offer_data = PeerOfferCreate(
            currency=currency,
            currency_type=CurrencyType.CRYPTO if currency in ['BTC', 'ETH'] else CurrencyType.FIAT,
            amount_available=random.uniform(100, 10000),
            rate_adjustment=random.uniform(-2, 2),  # -2% to +2% from market rate
            transfer_methods=[
                TransferMethod.BANK_TRANSFER,
                TransferMethod.CRYPTO_WALLET if currency in ['BTC', 'ETH'] else TransferMethod.WIRE_TRANSFER
            ],
            min_transaction=10,
            max_transaction=5000,
            availability_hours={"all": "00:00-23:59"}
        )

        # Use different user IDs for offers
        peer_id = random.randint(1, 100)
        offer = converter_manager.create_peer_offer(peer_id, offer_data)
        generated_offers.append(offer.id)

    # Create some conversion orders for the current user
    generated_orders = []
    pairs = [('USD', 'EUR'), ('USD', 'MXN'), ('BTC', 'USD'), ('EUR', 'GBP')]

    for pair in pairs:
        quote_request = ConversionQuoteRequest(
            from_currency=pair[0],
            to_currency=pair[1],
            amount=random.uniform(100, 1000)
        )

        quote = converter_manager.create_conversion_quote(current_user["user_id"], quote_request)

        order_data = ConversionOrderCreate(
            quote_id=quote.quote_id,
            recipient_details={
                "account_number": f"ACC{random.randint(100000, 999999)}",
                "bank_name": "Mock Bank",
                "recipient_name": "John Doe"
            },
            purpose="Personal transfer",
            reference=f"REF-{random.randint(1000, 9999)}"
        )

        order = converter_manager.create_conversion_order(current_user["user_id"], order_data)
        generated_orders.append(order.order_number)

    return {
        "message": "Mock data generated successfully",
        "peer_offers_created": len(generated_offers),
        "conversion_orders_created": len(generated_orders),
        "offer_ids": generated_offers[:5],  # Show first 5
        "order_numbers": generated_orders
    }
