import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.main_banking import app
from app.repositories.data_manager import data_manager
from app.models.entities.investment_models import (
    InvestmentAccountType, AssetType, OrderType, OrderSide, OrderStatus
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Reset data before each test."""
    data_manager.reset(demo_mode=True)
    yield
    data_manager.reset(demo_mode=True)


@pytest.fixture
def auth_headers():
    """Get authentication headers for test user."""
    # Login as test user
    response = client.post("/api/auth/login", json={
        "username": "john_doe",
        "password": "password123"
    })
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


class TestInvestmentAccounts:
    """Test investment account endpoints."""
    
    def test_get_accounts(self, auth_headers):
        """Test getting user's investment accounts."""
        response = client.get("/api/investments/accounts", headers=auth_headers)
        assert response.status_code == 200
        accounts = response.json()
        assert isinstance(accounts, list)
        if accounts:
            account = accounts[0]
            assert "id" in account
            assert "account_type" in account
            assert "balance" in account
    
    def test_create_account(self, auth_headers):
        """Test creating a new investment account."""
        account_data = {
            "account_type": InvestmentAccountType.INDIVIDUAL.value,
            "account_name": "Test Investment Account",
            "initial_deposit": 5000.0
        }
        response = client.post("/api/investments/accounts", 
                             json=account_data, headers=auth_headers)
        assert response.status_code == 200
        account = response.json()
        assert account["account_name"] == account_data["account_name"]
        assert account["account_type"] == account_data["account_type"]
        assert account["cash_balance"] == account_data["initial_deposit"]
    
    def test_get_account_details(self, auth_headers):
        """Test getting specific account details."""
        # First get accounts
        accounts_response = client.get("/api/investments/accounts", headers=auth_headers)
        if accounts_response.json():
            account_id = accounts_response.json()[0]["id"]
            
            # Get specific account
            response = client.get(f"/api/investments/accounts/{account_id}", 
                                headers=auth_headers)
            assert response.status_code == 200
            account = response.json()
            assert account["id"] == account_id


class TestInvestmentPortfolio:
    """Test portfolio endpoints."""
    
    def test_get_portfolio(self, auth_headers):
        """Test getting portfolio data."""
        # Get account first
        accounts = client.get("/api/investments/accounts", headers=auth_headers).json()
        if accounts:
            account_id = accounts[0]["id"]
            
            response = client.get(f"/api/investments/portfolio/{account_id}", 
                                headers=auth_headers)
            assert response.status_code == 200
            portfolio = response.json()
            assert "total_value" in portfolio
            assert "cash_balance" in portfolio
            assert "positions" in portfolio
            assert "asset_allocation" in portfolio
    
    def test_get_positions(self, auth_headers):
        """Test getting account positions."""
        accounts = client.get("/api/investments/accounts", headers=auth_headers).json()
        if accounts:
            account_id = accounts[0]["id"]
            
            response = client.get(f"/api/investments/accounts/{account_id}/positions", 
                                headers=auth_headers)
            assert response.status_code == 200
            positions = response.json()
            assert isinstance(positions, list)


class TestInvestmentTrading:
    """Test trading endpoints."""
    
    def test_search_assets(self, auth_headers):
        """Test asset search functionality."""
        response = client.get("/api/investments/assets/search?query=AAPL", 
                            headers=auth_headers)
        assert response.status_code == 200
        assets = response.json()
        assert isinstance(assets, list)
        if assets:
            asset = assets[0]
            assert "symbol" in asset
            assert "name" in asset
            assert "current_price" in asset
    
    def test_search_assets_by_type(self, auth_headers):
        """Test searching assets by type."""
        response = client.get("/api/investments/assets/search?asset_type=etf", 
                            headers=auth_headers)
        assert response.status_code == 200
        assets = response.json()
        assert isinstance(assets, list)
        if assets:
            assert all(asset["asset_type"] == AssetType.ETF.value for asset in assets)
    
    def test_place_market_order(self, auth_headers):
        """Test placing a market order."""
        # Get account
        accounts = client.get("/api/investments/accounts", headers=auth_headers).json()
        if not accounts:
            return
            
        account_id = accounts[0]["id"]
        
        # Search for an asset
        assets = client.get("/api/investments/assets/search?query=AAPL", 
                          headers=auth_headers).json()
        if not assets:
            return
            
        asset_id = assets[0]["id"]
        
        # Place order
        order_data = {
            "account_id": account_id,
            "asset_id": asset_id,
            "order_type": OrderType.MARKET.value,
            "order_side": OrderSide.BUY.value,
            "quantity": 10
        }
        
        response = client.post("/api/investments/orders", 
                             json=order_data, headers=auth_headers)
        assert response.status_code == 200
        order = response.json()
        assert order["account_id"] == account_id
        assert order["asset_id"] == asset_id
        assert order["quantity"] == 10
        assert order["status"] in [OrderStatus.PENDING.value, OrderStatus.EXECUTED.value]
    
    def test_place_limit_order(self, auth_headers):
        """Test placing a limit order."""
        accounts = client.get("/api/investments/accounts", headers=auth_headers).json()
        if not accounts:
            return
            
        account_id = accounts[0]["id"]
        assets = client.get("/api/investments/assets/search?query=GOOGL", 
                          headers=auth_headers).json()
        if not assets:
            return
            
        asset_id = assets[0]["id"]
        
        order_data = {
            "account_id": account_id,
            "asset_id": asset_id,
            "order_type": OrderType.LIMIT.value,
            "order_side": OrderSide.BUY.value,
            "quantity": 5,
            "price": 2500.00
        }
        
        response = client.post("/api/investments/orders", 
                             json=order_data, headers=auth_headers)
        assert response.status_code == 200
        order = response.json()
        assert order["order_type"] == OrderType.LIMIT.value
        assert order["price"] == 2500.00
    
    def test_get_orders(self, auth_headers):
        """Test getting user's orders."""
        response = client.get("/api/investments/orders", headers=auth_headers)
        assert response.status_code == 200
        orders = response.json()
        assert isinstance(orders, list)
    
    def test_cancel_order(self, auth_headers):
        """Test cancelling an order."""
        # First place an order
        accounts = client.get("/api/investments/accounts", headers=auth_headers).json()
        if not accounts:
            return
            
        account_id = accounts[0]["id"]
        assets = client.get("/api/investments/assets/search?query=TSLA", 
                          headers=auth_headers).json()
        if not assets:
            return
            
        # Place a limit order (can be cancelled)
        order_data = {
            "account_id": account_id,
            "asset_id": assets[0]["id"],
            "order_type": OrderType.LIMIT.value,
            "order_side": OrderSide.BUY.value,
            "quantity": 10,
            "price": 200.00
        }
        
        order_response = client.post("/api/investments/orders", 
                                   json=order_data, headers=auth_headers)
        assert order_response.status_code == 200
        order_id = order_response.json()["id"]
        
        # Cancel the order
        cancel_response = client.put(f"/api/investments/orders/{order_id}/cancel", 
                                   headers=auth_headers)
        assert cancel_response.status_code == 200
        cancelled_order = cancel_response.json()
        assert cancelled_order["status"] == OrderStatus.CANCELLED.value


class TestInvestmentWatchlists:
    """Test watchlist endpoints."""
    
    def test_create_watchlist(self, auth_headers):
        """Test creating a watchlist."""
        response = client.post("/api/investments/watchlists", 
                             json={"name": "Tech Stocks"}, 
                             headers=auth_headers)
        assert response.status_code == 200
        watchlist = response.json()
        assert watchlist["name"] == "Tech Stocks"
        assert "id" in watchlist
    
    def test_get_watchlists(self, auth_headers):
        """Test getting user's watchlists."""
        response = client.get("/api/investments/watchlists", headers=auth_headers)
        assert response.status_code == 200
        watchlists = response.json()
        assert isinstance(watchlists, list)
    
    def test_add_to_watchlist(self, auth_headers):
        """Test adding asset to watchlist."""
        # Create watchlist
        watchlist_response = client.post("/api/investments/watchlists", 
                                       json={"name": "My Watchlist"}, 
                                       headers=auth_headers)
        watchlist_id = watchlist_response.json()["id"]
        
        # Get an asset
        assets = client.get("/api/investments/assets/search?query=AAPL", 
                          headers=auth_headers).json()
        if not assets:
            return
            
        asset_id = assets[0]["id"]
        
        # Add to watchlist
        response = client.post(f"/api/investments/watchlists/{watchlist_id}/assets", 
                             json={"asset_id": asset_id}, 
                             headers=auth_headers)
        assert response.status_code == 200
        updated_watchlist = response.json()
        assert len(updated_watchlist["assets"]) > 0
    
    def test_remove_from_watchlist(self, auth_headers):
        """Test removing asset from watchlist."""
        # Create watchlist with asset
        watchlist_response = client.post("/api/investments/watchlists", 
                                       json={"name": "Test Watchlist"}, 
                                       headers=auth_headers)
        watchlist_id = watchlist_response.json()["id"]
        
        # Add asset
        assets = client.get("/api/investments/assets/search?query=GOOGL", 
                          headers=auth_headers).json()
        if not assets:
            return
            
        asset_id = assets[0]["id"]
        client.post(f"/api/investments/watchlists/{watchlist_id}/assets", 
                   json={"asset_id": asset_id}, 
                   headers=auth_headers)
        
        # Remove asset
        response = client.delete(
            f"/api/investments/watchlists/{watchlist_id}/assets/{asset_id}", 
            headers=auth_headers
        )
        assert response.status_code == 200


class TestInvestmentAnalytics:
    """Test analytics endpoints."""
    
    def test_get_performance_history(self, auth_headers):
        """Test getting performance history."""
        accounts = client.get("/api/investments/accounts", headers=auth_headers).json()
        if accounts:
            account_id = accounts[0]["id"]
            
            response = client.get(
                f"/api/investments/accounts/{account_id}/performance?period=1M", 
                headers=auth_headers
            )
            assert response.status_code == 200
            performance = response.json()
            assert "dates" in performance
            assert "values" in performance
            assert "returns" in performance
            assert isinstance(performance["dates"], list)
            assert isinstance(performance["values"], list)
            assert isinstance(performance["returns"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])