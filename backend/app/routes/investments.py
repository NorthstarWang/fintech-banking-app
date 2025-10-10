"""
Investment management API routes for ETF, stock, and crypto trading.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.entities.investment_models import (
    AssetResponse,
    AssetType,
    ETFDetailResponse,
    InvestmentAccountCreate,
    InvestmentAccountResponse,
    InvestmentAccountType,
    InvestmentSummaryResponse,
    MarketDataResponse,
    OrderSide,
    OrderStatus,
    OrderType,
    PortfolioAnalysisResponse,
    PortfolioResponse,
    PortfolioRiskLevel,
    PositionResponse,
    StockDetailResponse,
    TradeOrderCreate,
    TradeOrderResponse,
    WatchlistCreate,
    WatchlistResponse,
)
from app.repositories.data_manager import data_manager
from app.repositories.investment_manager import InvestmentManager
from app.utils.auth import get_current_user

router = APIRouter()

# Initialize investment manager
investment_manager = InvestmentManager(data_manager)

# Account endpoints
@router.post("/accounts", response_model=InvestmentAccountResponse)
async def create_investment_account(
    account: InvestmentAccountCreate,
    current_user = Depends(get_current_user)
) -> InvestmentAccountResponse:
    """Create a new investment account."""
    try:
        return investment_manager.create_investment_account(current_user["user_id"], account)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/accounts", response_model=list[InvestmentAccountResponse])
async def get_investment_accounts(
    current_user = Depends(get_current_user)
) -> list[InvestmentAccountResponse]:
    """Get all investment accounts for the current user."""
    return investment_manager.get_user_accounts(current_user["user_id"])

@router.get("/accounts/{account_id}", response_model=InvestmentAccountResponse)
async def get_investment_account(
    account_id: int,
    current_user = Depends(get_current_user)
) -> InvestmentAccountResponse:
    """Get specific investment account details."""
    account = investment_manager.get_account(account_id, current_user["user_id"])
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

# Portfolio endpoints
@router.get("/accounts/{account_id}/portfolio", response_model=PortfolioResponse)
async def get_portfolio(
    account_id: int,
    current_user = Depends(get_current_user)
) -> PortfolioResponse:
    """Get portfolio details for an account."""
    portfolio = investment_manager.get_portfolio(account_id, current_user["user_id"])
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio

@router.get("/portfolios/{portfolio_id}/positions", response_model=list[PositionResponse])
async def get_positions(
    portfolio_id: int,
    current_user = Depends(get_current_user)
) -> list[PositionResponse]:
    """Get all positions in a portfolio."""
    return investment_manager.get_positions(portfolio_id, current_user["user_id"])

@router.get("/portfolios/{portfolio_id}/analysis", response_model=PortfolioAnalysisResponse)
async def analyze_portfolio(
    portfolio_id: int,
    current_user = Depends(get_current_user)
) -> PortfolioAnalysisResponse:
    """Get portfolio analysis and recommendations."""
    analysis = investment_manager.analyze_portfolio(portfolio_id, current_user["user_id"])
    if not analysis:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return analysis

# Trading endpoints
@router.post("/orders", response_model=TradeOrderResponse)
async def place_order(
    order: TradeOrderCreate,
    current_user = Depends(get_current_user)
) -> TradeOrderResponse:
    """Place a new trade order."""
    try:
        return investment_manager.place_order(current_user["user_id"], order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.delete("/orders/{order_id}")
async def cancel_order(
    order_id: int,
    current_user = Depends(get_current_user)
) -> dict:
    """Cancel a pending order."""
    success = investment_manager.cancel_order(order_id, current_user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Order not found or cannot be cancelled")
    return {"message": "Order cancelled successfully"}

@router.get("/accounts/{account_id}/orders", response_model=list[TradeOrderResponse])
async def get_orders(
    account_id: int,
    status: OrderStatus | None = Query(None, description="Filter by order status"),
    current_user = Depends(get_current_user)
) -> list[TradeOrderResponse]:
    """Get orders for an account."""
    return investment_manager.get_orders(account_id, current_user["user_id"], status)

# Watchlist endpoints
@router.get("/watchlists", response_model=list[WatchlistResponse])
async def get_watchlists(
    current_user = Depends(get_current_user)
) -> list[WatchlistResponse]:
    """Get all watchlists for the current user."""
    return investment_manager.get_watchlists(current_user["user_id"])

@router.post("/watchlists", response_model=WatchlistResponse)
async def create_watchlist(
    watchlist: WatchlistCreate,
    current_user = Depends(get_current_user)
) -> WatchlistResponse:
    """Create a new watchlist."""
    return investment_manager.create_watchlist(current_user["user_id"], watchlist)

@router.put("/watchlists/{watchlist_id}")
async def update_watchlist(
    watchlist_id: int,
    symbols: list[str],
    current_user = Depends(get_current_user)
) -> dict:
    """Update watchlist symbols."""
    # Find watchlist
    watchlist = next((w for w in data_manager.investment_watchlists
                     if w['id'] == watchlist_id and w['user_id'] == current_user["user_id"]), None)

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    watchlist['symbols'] = symbols
    return {"message": "Watchlist updated successfully"}

@router.delete("/watchlists/{watchlist_id}")
async def delete_watchlist(
    watchlist_id: int,
    current_user = Depends(get_current_user)
) -> dict:
    """Delete a watchlist."""
    watchlist = next((w for w in data_manager.investment_watchlists
                     if w['id'] == watchlist_id and w['user_id'] == current_user["user_id"]), None)

    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    data_manager.investment_watchlists.remove(watchlist)
    return {"message": "Watchlist deleted successfully"}

# Asset detail endpoints
@router.get("/etf/{symbol}", response_model=ETFDetailResponse)
async def get_etf_detail(
    symbol: str,
    current_user = Depends(get_current_user)
) -> ETFDetailResponse:
    """Get detailed information about an ETF."""
    etf_detail = investment_manager.get_etf_detail(symbol.upper())
    if not etf_detail:
        raise HTTPException(status_code=404, detail="ETF not found")
    return etf_detail

@router.get("/stock/{symbol}", response_model=StockDetailResponse)
async def get_stock_detail(
    symbol: str,
    current_user = Depends(get_current_user)
) -> StockDetailResponse:
    """Get detailed information about a stock."""
    stock_detail = investment_manager.get_stock_detail(symbol.upper())
    if not stock_detail:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock_detail

@router.get("/crypto/{symbol}", response_model=AssetResponse)
async def get_crypto_detail(
    symbol: str,
    current_user = Depends(get_current_user)
) -> AssetResponse:
    """Get detailed information about a cryptocurrency."""
    crypto_detail = investment_manager.get_crypto_detail(symbol.upper())
    if not crypto_detail:
        raise HTTPException(status_code=404, detail="Cryptocurrency not found")
    return crypto_detail

# Market data endpoints
@router.get("/market-data/{symbol}", response_model=MarketDataResponse)
async def get_market_data(
    symbol: str,
    current_user = Depends(get_current_user)
) -> MarketDataResponse:
    """Get real-time market data for a symbol."""
    return investment_manager.get_market_data(symbol.upper())

@router.get("/market-data/batch/{symbols}")
async def get_batch_market_data(
    symbols: str,
    current_user = Depends(get_current_user)
) -> list[MarketDataResponse]:
    """Get market data for multiple symbols (comma-separated)."""
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    return [investment_manager.get_market_data(symbol) for symbol in symbol_list]

# Summary and analytics
@router.get("/summary", response_model=InvestmentSummaryResponse)
async def get_investment_summary(
    current_user = Depends(get_current_user)
) -> InvestmentSummaryResponse:
    """Get comprehensive investment summary for the current user."""
    return investment_manager.get_investment_summary(current_user["user_id"])

@router.get("/portfolio-summary")
async def get_portfolio_summary(
    current_user = Depends(get_current_user)
) -> dict:
    """
    Get comprehensive portfolio summary across all accounts.
    Includes total portfolio value, asset allocation, top gainers/losers, and performance history.
    """
    return investment_manager.get_portfolio_summary(current_user["user_id"])

# Market overview endpoints
@router.get("/market-summary")
async def get_market_summary(
    current_user = Depends(get_current_user)
) -> dict:
    """Get market summary including indices, top gainers/losers, and trending."""
    return investment_manager.get_market_summary()

@router.get("/assets")
async def get_all_assets(
    asset_type: str | None = Query(None, description="Filter by asset type (etf, stock, crypto)"),
    current_user = Depends(get_current_user)
) -> list:
    """Get all available investment assets."""
    return investment_manager.get_all_assets(asset_type)

# Asset search endpoints
@router.get("/search/etfs")
async def search_etfs(
    query: str = Query(..., description="Search query"),
    category: str | None = Query(None, description="Filter by category"),
    current_user = Depends(get_current_user)
) -> list:
    """Search for ETFs."""
    results = []

    for etf in data_manager.etf_assets:
        if query.lower() in etf['symbol'].lower() or query.lower() in etf['name'].lower():
            if not category or etf.get('category', '').lower() == category.lower():
                results.append({
                    'symbol': etf['symbol'],
                    'name': etf['name'],
                    'category': etf.get('category', ''),
                    'expense_ratio': etf.get('expense_ratio', 0),
                    'price': etf.get('price', 0),
                    'change_percent': etf.get('change_percent', 0)
                })

    return results[:20]  # Limit to 20 results

@router.get("/search/stocks")
async def search_stocks(
    query: str = Query(..., description="Search query"),
    sector: str | None = Query(None, description="Filter by sector"),
    current_user = Depends(get_current_user)
) -> list:
    """Search for stocks."""
    results = []

    for stock in data_manager.stock_assets:
        if query.lower() in stock['symbol'].lower() or query.lower() in stock['name'].lower():
            if not sector or stock.get('sector', '').lower() == sector.lower():
                results.append({
                    'symbol': stock['symbol'],
                    'name': stock['name'],
                    'sector': stock.get('sector', ''),
                    'price': stock.get('price', 0),
                    'change_percent': stock.get('change_percent', 0),
                    'market_cap': stock.get('market_cap', 0),
                    'pe_ratio': stock.get('pe_ratio', 0)
                })

    return results[:20]  # Limit to 20 results

# Mock data generation endpoint (for development)
@router.post("/generate-mock-data")
async def generate_mock_investment_data(
    num_accounts: int = Query(2, description="Number of accounts to generate"),
    current_user = Depends(get_current_user)
) -> dict:
    """Generate mock investment data for testing."""
    import random

    generated_accounts = []

    for i in range(num_accounts):
        # Create account
        account_types = list(InvestmentAccountType)
        account_data = InvestmentAccountCreate(
            account_type=random.choice(account_types),
            account_name=f"Investment Account {i+1}",
            initial_deposit=random.uniform(1000, 50000),
            is_retirement=random.choice([True, False]),
            risk_tolerance=random.choice(list(PortfolioRiskLevel))
        )

        account = investment_manager.create_investment_account(current_user["user_id"], account_data)
        generated_accounts.append(account.id)

        # Get portfolio
        portfolio = investment_manager.get_portfolio(account.id, current_user["user_id"])

        if portfolio and account.balance > 1000:
            # Place some orders
            symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'SPY', 'QQQ', 'VTI']

            for _ in range(random.randint(2, 5)):
                symbol = random.choice(symbols)
                order_data = TradeOrderCreate(
                    account_id=account.id,
                    symbol=symbol,
                    asset_type=AssetType.STOCK if symbol not in ['SPY', 'QQQ', 'VTI'] else AssetType.ETF,
                    order_type=OrderType.MARKET,
                    order_side=OrderSide.BUY,
                    quantity=random.randint(1, 10),
                    time_in_force="day"
                )

                try:
                    investment_manager.place_order(current_user["user_id"], order_data)
                except (ValueError, KeyError, Exception):
                    pass  # Skip if insufficient funds

    return {
        "message": f"Generated {len(generated_accounts)} investment accounts with positions",
        "account_ids": generated_accounts
    }
