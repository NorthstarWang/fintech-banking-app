import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main_banking import app
from app.repositories.data_manager import data_manager
from app.models.entities.currency_models import (
    TradeStatus, OfferStatus, PaymentMethod
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
    response = client.post("/api/auth/login", json={
        "username": "john_doe",
        "password": "password123"
    })
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


class TestCurrencies:
    """Test currency endpoints."""
    
    def test_get_supported_currencies(self, auth_headers):
        """Test getting supported currencies."""
        response = client.get("/api/currency-converter/currencies", headers=auth_headers)
        assert response.status_code == 200
        currencies = response.json()
        assert isinstance(currencies, list)
        assert len(currencies) > 0
        
        # Check currency structure
        currency = currencies[0]
        assert "code" in currency
        assert "name" in currency
        assert "symbol" in currency
        assert "is_crypto" in currency
        assert "is_supported" in currency
    
    def test_get_currency_details(self, auth_headers):
        """Test getting specific currency details."""
        response = client.get("/api/currency-converter/currencies/USD", headers=auth_headers)
        assert response.status_code == 200
        currency = response.json()
        assert currency["code"] == "USD"
        assert currency["name"] == "US Dollar"
        assert currency["symbol"] == "$"
        assert currency["is_crypto"] is False


class TestExchangeRates:
    """Test exchange rate endpoints."""
    
    def test_get_all_rates(self, auth_headers):
        """Test getting all exchange rates."""
        response = client.get("/api/currency-converter/rates", headers=auth_headers)
        assert response.status_code == 200
        rates = response.json()
        assert isinstance(rates, list)
        assert len(rates) > 0
        
        # Check rate structure
        rate = rates[0]
        assert "from_currency" in rate
        assert "to_currency" in rate
        assert "rate" in rate
        assert "bid" in rate
        assert "ask" in rate
        assert "spread_percentage" in rate
    
    def test_get_rates_for_base_currency(self, auth_headers):
        """Test getting rates for specific base currency."""
        response = client.get("/api/currency-converter/rates?base=EUR", headers=auth_headers)
        assert response.status_code == 200
        rates = response.json()
        assert all(rate["from_currency"] == "EUR" for rate in rates)
    
    def test_get_specific_rate(self, auth_headers):
        """Test getting specific currency pair rate."""
        response = client.get("/api/currency-converter/rates/USD/EUR", headers=auth_headers)
        assert response.status_code == 200
        rate = response.json()
        assert rate["from_currency"] == "USD"
        assert rate["to_currency"] == "EUR"
        assert rate["rate"] > 0
        assert rate["bid"] <= rate["rate"] <= rate["ask"]


class TestCurrencyConversion:
    """Test conversion endpoints."""
    
    def test_create_conversion_quote(self, auth_headers):
        """Test creating a conversion quote."""
        quote_request = {
            "from_currency": "USD",
            "to_currency": "EUR",
            "amount": 1000.0,
            "conversion_type": "standard"
        }
        
        response = client.post("/api/currency-converter/quote", 
                             json=quote_request, headers=auth_headers)
        assert response.status_code == 200
        quote = response.json()
        assert quote["from_currency"] == "USD"
        assert quote["to_currency"] == "EUR"
        assert quote["from_amount"] == 1000.0
        assert "to_amount" in quote
        assert "exchange_rate" in quote
        assert "fee_amount" in quote
        assert "quote_id" in quote
        assert "expires_at" in quote
    
    def test_execute_conversion(self, auth_headers):
        """Test executing a conversion from quote."""
        # Create quote first
        quote_request = {
            "from_currency": "USD",
            "to_currency": "GBP",
            "amount": 500.0
        }
        
        quote_response = client.post("/api/currency-converter/quote", 
                                   json=quote_request, headers=auth_headers)
        quote_id = quote_response.json()["quote_id"]
        
        # Execute conversion
        response = client.post(f"/api/currency-converter/convert/{quote_id}", 
                             headers=auth_headers)
        assert response.status_code == 200
        result = response.json()
        assert "transaction_id" in result
        assert result["status"] in ["completed", "pending"]
        assert "from_amount" in result
        assert "to_amount" in result
    
    def test_get_conversion_history(self, auth_headers):
        """Test getting conversion history."""
        response = client.get("/api/currency-converter/conversions", headers=auth_headers)
        assert response.status_code == 200
        conversions = response.json()
        assert isinstance(conversions, list)


class TestUserBalances:
    """Test balance endpoints."""
    
    def test_get_all_balances(self, auth_headers):
        """Test getting all user balances."""
        response = client.get("/api/currency-converter/balances", headers=auth_headers)
        assert response.status_code == 200
        balances = response.json()
        assert isinstance(balances, list)
        
        if balances:
            balance = balances[0]
            assert "currency" in balance
            assert "balance" in balance
            assert "available_balance" in balance
            assert "locked_balance" in balance
    
    def test_get_specific_balance(self, auth_headers):
        """Test getting balance for specific currency."""
        # First ensure user has some balances
        balances = client.get("/api/currency-converter/balances", headers=auth_headers).json()
        if balances:
            currency = balances[0]["currency"]
            
            response = client.get(f"/api/currency-converter/balances/{currency}", 
                                headers=auth_headers)
            assert response.status_code == 200
            balance = response.json()
            assert balance["currency"] == currency


class TestP2POffers:
    """Test P2P offer endpoints."""
    
    def test_search_offers(self, auth_headers):
        """Test searching P2P offers."""
        response = client.get("/api/currency-converter/p2p/offers", headers=auth_headers)
        assert response.status_code == 200
        offers = response.json()
        assert isinstance(offers, list)
        
        if offers:
            offer = offers[0]
            assert "id" in offer
            assert "offer_type" in offer
            assert "from_currency" in offer
            assert "to_currency" in offer
            assert "amount" in offer
            assert "exchange_rate" in offer
            assert "payment_methods" in offer
    
    def test_search_offers_with_filters(self, auth_headers):
        """Test searching offers with filters."""
        params = {
            "from_currency": "USD",
            "to_currency": "EUR",
            "offer_type": "sell",
            "min_amount": 100,
            "max_amount": 1000
        }
        
        response = client.get("/api/currency-converter/p2p/offers", 
                            params=params, headers=auth_headers)
        assert response.status_code == 200
        offers = response.json()
        
        for offer in offers:
            assert offer["from_currency"] == "USD"
            assert offer["to_currency"] == "EUR"
            assert offer["offer_type"] == "sell"
            assert offer["amount"] >= 100
            assert offer["amount"] <= 1000
    
    def test_create_offer(self, auth_headers):
        """Test creating a P2P offer."""
        offer_data = {
            "offer_type": "sell",
            "from_currency": "USD",
            "to_currency": "EUR",
            "amount": 1000.0,
            "exchange_rate": 0.92,
            "min_amount": 100.0,
            "max_amount": 1000.0,
            "payment_methods": [PaymentMethod.BANK_TRANSFER.value, PaymentMethod.PAYPAL.value],
            "expires_in_hours": 24
        }
        
        response = client.post("/api/currency-converter/p2p/offers", 
                             json=offer_data, headers=auth_headers)
        assert response.status_code == 200
        offer = response.json()
        assert offer["offer_type"] == "sell"
        assert offer["from_currency"] == "USD"
        assert offer["to_currency"] == "EUR"
        assert offer["status"] == OfferStatus.ACTIVE.value
    
    def test_get_offer_details(self, auth_headers):
        """Test getting specific offer details."""
        # Get existing offers
        offers = client.get("/api/currency-converter/p2p/offers", headers=auth_headers).json()
        if offers:
            offer_id = offers[0]["id"]
            
            response = client.get(f"/api/currency-converter/p2p/offers/{offer_id}", 
                                headers=auth_headers)
            assert response.status_code == 200
            offer = response.json()
            assert offer["id"] == offer_id
    
    def test_cancel_offer(self, auth_headers):
        """Test cancelling an offer."""
        # Create an offer first
        offer_data = {
            "offer_type": "buy",
            "from_currency": "EUR",
            "to_currency": "USD",
            "amount": 500.0,
            "exchange_rate": 1.08,
            "payment_methods": [PaymentMethod.BANK_TRANSFER.value]
        }
        
        create_response = client.post("/api/currency-converter/p2p/offers", 
                                    json=offer_data, headers=auth_headers)
        offer_id = create_response.json()["id"]
        
        # Cancel the offer
        response = client.delete(f"/api/currency-converter/p2p/offers/{offer_id}", 
                               headers=auth_headers)
        assert response.status_code == 204


class TestP2PTrades:
    """Test P2P trade endpoints."""
    
    def test_create_trade(self, auth_headers):
        """Test creating a P2P trade."""
        # Get an active offer
        offers = client.get("/api/currency-converter/p2p/offers", headers=auth_headers).json()
        suitable_offer = None
        for offer in offers:
            if offer["status"] == OfferStatus.ACTIVE.value:
                suitable_offer = offer
                break
        
        if not suitable_offer:
            return
        
        trade_data = {
            "offer_id": suitable_offer["id"],
            "amount": suitable_offer["min_amount"],
            "payment_method": suitable_offer["payment_methods"][0]
        }
        
        response = client.post("/api/currency-converter/p2p/trades", 
                             json=trade_data, headers=auth_headers)
        assert response.status_code == 200
        trade = response.json()
        assert trade["offer_id"] == suitable_offer["id"]
        assert trade["status"] in [TradeStatus.PENDING.value, TradeStatus.IN_ESCROW.value]
    
    def test_get_trades(self, auth_headers):
        """Test getting user's trades."""
        response = client.get("/api/currency-converter/p2p/trades", headers=auth_headers)
        assert response.status_code == 200
        trades = response.json()
        assert isinstance(trades, list)
    
    def test_get_trades_by_status(self, auth_headers):
        """Test getting trades filtered by status."""
        response = client.get("/api/currency-converter/p2p/trades?status=completed", 
                            headers=auth_headers)
        assert response.status_code == 200
        trades = response.json()
        
        for trade in trades:
            assert trade["status"] == TradeStatus.COMPLETED.value
    
    def test_confirm_payment(self, auth_headers):
        """Test confirming payment for a trade."""
        # This would need a trade in the right state
        # For testing, we'll create a trade and attempt confirmation
        trades = client.get("/api/currency-converter/p2p/trades", headers=auth_headers).json()
        
        for trade in trades:
            if trade["status"] == TradeStatus.PENDING.value:
                response = client.put(f"/api/currency-converter/p2p/trades/{trade['id']}/confirm-payment", 
                                    headers=auth_headers)
                assert response.status_code in [200, 400]  # 400 if not buyer
                break
    
    def test_release_escrow(self, auth_headers):
        """Test releasing escrow for a trade."""
        trades = client.get("/api/currency-converter/p2p/trades", headers=auth_headers).json()
        
        for trade in trades:
            if trade["status"] == TradeStatus.IN_ESCROW.value:
                response = client.put(f"/api/currency-converter/p2p/trades/{trade['id']}/release-escrow", 
                                    headers=auth_headers)
                assert response.status_code in [200, 403]  # 403 if not seller
                break
    
    def test_dispute_trade(self, auth_headers):
        """Test disputing a trade."""
        trades = client.get("/api/currency-converter/p2p/trades", headers=auth_headers).json()
        
        for trade in trades:
            if trade["status"] in [TradeStatus.PENDING.value, TradeStatus.IN_ESCROW.value]:
                response = client.put(f"/api/currency-converter/p2p/trades/{trade['id']}/dispute", 
                                    json={"reason": "Payment not received"},
                                    headers=auth_headers)
                assert response.status_code in [200, 403]
                break


class TestCurrencyAnalytics:
    """Test analytics endpoints."""
    
    def test_get_exchange_stats(self, auth_headers):
        """Test getting exchange statistics."""
        response = client.get("/api/currency-converter/stats", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()
        assert "total_volume_24h" in stats
        assert "total_trades_24h" in stats
        assert "popular_pairs" in stats
        assert "average_rates" in stats
        
        assert isinstance(stats["popular_pairs"], list)
        if stats["popular_pairs"]:
            pair = stats["popular_pairs"][0]
            assert "from_currency" in pair
            assert "to_currency" in pair
            assert "volume" in pair
            assert "trade_count" in pair
    
    def test_get_user_stats(self, auth_headers):
        """Test getting user-specific statistics."""
        response = client.get("/api/currency-converter/user-stats", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()
        assert "total_conversions" in stats
        assert "total_volume" in stats
        assert "p2p_trades_completed" in stats
        assert "p2p_rating" in stats
        assert "favorite_currencies" in stats
        
        assert isinstance(stats["favorite_currencies"], list)
        assert stats["total_conversions"] >= 0
        assert stats["p2p_trades_completed"] >= 0
        assert 0 <= stats["p2p_rating"] <= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])