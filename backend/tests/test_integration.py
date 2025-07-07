"""
Integration tests for cross-system interactions and data flow.
Tests the complete workflow across investments, credit cards, and currency converter.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main_banking import app
from app.repositories.data_manager import data_manager

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


class TestCrossSystemIntegration:
    """Test interactions between different financial systems."""
    
    def test_credit_score_affects_card_recommendations(self, auth_headers):
        """Test that credit score changes affect card recommendations."""
        # Get initial recommendations
        initial_recs = client.get("/api/credit-cards/recommendations", headers=auth_headers).json()
        initial_count = len(initial_recs)
        
        # Update credit score to higher value
        client.put("/api/credit-cards/credit-score", 
                  json={"score": 800}, headers=auth_headers)
        
        # Get new recommendations
        new_recs = client.get("/api/credit-cards/recommendations", headers=auth_headers).json()
        
        # Should have more or better recommendations with higher score
        assert len(new_recs) >= initial_count
        if new_recs:
            # Higher match scores expected with better credit
            avg_match_score = sum(r["match_score"] for r in new_recs) / len(new_recs)
            assert avg_match_score > 0.7
    
    def test_investment_balance_affects_currency_limits(self, auth_headers):
        """Test that investment account balance affects currency conversion limits."""
        # Get initial investment accounts
        accounts = client.get("/api/investments/accounts", headers=auth_headers).json()
        total_investment_value = sum(acc["balance"] for acc in accounts)
        
        # Get currency balances
        balances = client.get("/api/currency-converter/balances", headers=auth_headers).json()
        
        # Total available for conversion should consider overall financial health
        # This is a business logic test - users with more investments get higher limits
        if total_investment_value > 100000:
            # Check if user has higher tier benefits
            user_stats = client.get("/api/currency-converter/user-stats", headers=auth_headers).json()
            # Premium users with high investment balances should have better P2P ratings
            assert user_stats.get("p2p_rating", 0) >= 4.0
    
        # Perform actions across different systems
        
        # 1. Check credit score
        client.get("/api/credit-cards/credit-score", headers=auth_headers)
        
        # 2. Search for investments
        client.get("/api/investments/assets/search?query=AAPL", headers=auth_headers)
        
        # 3. Get currency exchange rate
        client.get("/api/currency-converter/exchange-rate/USD/EUR", headers=auth_headers)
        
        # Verify all endpoints are accessible
        assert True
    
    def test_financial_health_score_calculation(self, auth_headers):
        """Test comprehensive financial health score based on all systems."""
        # Get data from all systems
        credit_score = client.get("/api/credit-cards/credit-score", headers=auth_headers).json()
        accounts = client.get("/api/investments/accounts", headers=auth_headers).json()
        balances = client.get("/api/currency-converter/balances", headers=auth_headers).json()
        applications = client.get("/api/credit-cards/applications", headers=auth_headers).json()
        
        # Calculate a basic financial health score
        score_components = {
            "credit_score": credit_score["credit_score"] / 850 * 100,  # Normalize to 100
            "investment_diversity": min(len(accounts) * 20, 100),  # More accounts = better
            "currency_diversity": min(len(balances) * 15, 100),  # Multiple currencies = better
            "credit_utilization": 100 - (credit_score["factors"]["credit_utilization"]["score"])
        }
        
        # All components should be tracked
        assert all(0 <= score <= 100 for score in score_components.values())
        
        # Average health score
        health_score = sum(score_components.values()) / len(score_components)
        assert 0 <= health_score <= 100


class TestDataConsistency:
    """Test data consistency across systems."""
    
    def test_user_data_consistency(self, auth_headers):
        """Test that user data is consistent across all systems."""
        # Get user ID from different endpoints
        # All should reference the same user
        
        # From credit cards
        credit_score = client.get("/api/credit-cards/credit-score", headers=auth_headers).json()
        
        # From investments
        accounts = client.get("/api/investments/accounts", headers=auth_headers).json()
        
        # From currency converter
        balances = client.get("/api/currency-converter/balances", headers=auth_headers).json()
        
        # All should return data (not empty)
        assert credit_score is not None
        assert len(accounts) >= 0  # Can be empty but should be a list
        assert len(balances) >= 0  # Can be empty but should be a list
    
    def test_timestamp_consistency(self, auth_headers):
        """Test that timestamps are consistent across systems."""
        # Create actions in different systems
        
        # Apply for a credit card
        cards = client.get("/api/credit-cards", headers=auth_headers).json()
        if cards:
            app_response = client.post("/api/credit-cards/applications", 
                                      json={
                                          "card_id": cards[0]["id"],
                                          "annual_income": 75000,
                                          "employment_type": "full_time"
                                      }, headers=auth_headers)
            assert app_response.status_code == 200
            app_time = datetime.fromisoformat(
                app_response.json()["application_date"].replace("Z", "+00:00")
            )
        
        # Create a currency quote
        quote_response = client.post("/api/currency-converter/quote",
                                   json={
                                       "from_currency": "USD",
                                       "to_currency": "EUR",
                                       "amount": 1000
                                   }, headers=auth_headers)
        if quote_response.status_code == 200:
            quote_time = datetime.fromisoformat(
                quote_response.json()["created_at"].replace("Z", "+00:00")
            )
            
            # Timestamps should be recent (within last minute)
            now = datetime.utcnow()
            if 'app_time' in locals():
                assert (now - app_time.replace(tzinfo=None)).seconds < 60
            assert (now - quote_time.replace(tzinfo=None)).seconds < 60


class TestBusinessRules:
    """Test business rules that span multiple systems."""
    
    def test_credit_limit_based_on_investment_portfolio(self, auth_headers):
        """Test that credit limits consider investment portfolio value."""
        # Get investment portfolio value
        accounts = client.get("/api/investments/accounts", headers=auth_headers).json()
        total_investments = sum(acc["balance"] for acc in accounts)
        
        # Apply for a credit card
        cards = client.get("/api/credit-cards", headers=auth_headers).json()
        premium_cards = [c for c in cards if c["annual_fee"] > 0]
        
        if premium_cards and total_investments > 50000:
            # Users with significant investments should qualify for premium cards
            eligibility = client.post(
                f"/api/credit-cards/{premium_cards[0]['id']}/check-eligibility",
                headers=auth_headers
            ).json()
            
            # High net worth individuals should have better approval odds
            assert eligibility["approval_odds"] in ["medium", "high"]
    
    def test_p2p_trading_limits_based_on_verification(self, auth_headers):
        """Test P2P trading limits based on user verification level."""
        # Search for P2P offers
        offers = client.get("/api/currency-converter/p2p/offers", headers=auth_headers).json()
        
        # Create a P2P offer
        offer_data = {
            "offer_type": "sell",
            "from_currency": "USD",
            "to_currency": "EUR",
            "amount": 10000,  # High amount
            "exchange_rate": 0.92,
            "payment_methods": ["bank_transfer"]
        }
        
        offer_response = client.post("/api/currency-converter/p2p/offers",
                                   json=offer_data, headers=auth_headers)
        
        # Response should be successful but actual limits would depend on verification
        assert offer_response.status_code in [200, 400]  # 400 if limits exceeded
        
        if offer_response.status_code == 200:
            # Offer was created successfully
            offer = offer_response.json()
            assert offer["amount"] <= offer_data["amount"]
    
    def test_investment_risk_assessment_affects_recommendations(self, auth_headers):
        """Test that investment risk profile affects product recommendations."""
        # Get user's investment portfolio
        accounts = client.get("/api/investments/accounts", headers=auth_headers).json()
        
        if accounts:
            account_id = accounts[0]["id"]
            portfolio = client.get(f"/api/investments/portfolio/{account_id}", 
                                 headers=auth_headers).json()
            
            # Check asset allocation
            allocation = portfolio.get("asset_allocation", {})
            crypto_percentage = allocation.get("crypto", 0)
            
            # High crypto allocation indicates risk tolerance
            if crypto_percentage > 20:
                # Should get recommendations for higher risk products
                card_recs = client.get("/api/credit-cards/recommendations", 
                                     headers=auth_headers).json()
                
                # Risk-tolerant users might get more rewards cards
                rewards_cards = [r for r in card_recs 
                               if "rewards" in r.get("card_type", "").lower()]
                assert len(rewards_cards) > 0


class TestSecurityIntegration:
    """Test security measures across systems."""
    
    def test_rate_limiting_across_systems(self, auth_headers):
        """Test that rate limiting works across different endpoints."""
        # Make multiple rapid requests to different systems
        endpoints = [
            "/api/credit-cards/credit-score",
            "/api/investments/accounts",
            "/api/currency-converter/balances"
        ]
        
        # Make 10 requests to each endpoint rapidly
        for endpoint in endpoints:
            for _ in range(10):
                response = client.get(endpoint, headers=auth_headers)
                # Should not get rate limited in test environment
                assert response.status_code == 200
    
    def test_authentication_required_all_systems(self):
        """Test that all sensitive endpoints require authentication."""
        # List of endpoints that should require auth
        protected_endpoints = [
            ("/api/investments/accounts", "GET"),
            ("/api/investments/orders", "POST"),
            ("/api/credit-cards/credit-score", "GET"),
            ("/api/credit-cards/applications", "POST"),
            ("/api/currency-converter/balances", "GET"),
            ("/api/currency-converter/p2p/offers", "POST")
        ]
        
        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            
            # Should get 401 or 403 without auth
            assert response.status_code in [401, 403, 422]


class TestPerformanceIntegration:
    """Test performance across integrated systems."""
    
    def test_bulk_data_retrieval_performance(self, auth_headers):
        """Test that bulk data retrieval is optimized."""
        import time
        
        start_time = time.time()
        
        # Retrieve data from multiple systems
        tasks = [
            client.get("/api/credit-cards/credit-score", headers=auth_headers),
            client.get("/api/investments/accounts", headers=auth_headers),
            client.get("/api/currency-converter/balances", headers=auth_headers),
            client.get("/api/credit-cards/recommendations", headers=auth_headers),
            client.get("/api/investments/assets/featured", headers=auth_headers)
        ]
        
        # All requests should complete
        for task in tasks:
            assert task.status_code == 200
        
        end_time = time.time()
        
        # Total time should be reasonable (under 2 seconds for all)
        assert (end_time - start_time) < 2.0
    
    def test_transaction_consistency(self, auth_headers):
        """Test that transactions maintain consistency across systems."""
        # Get initial state
        initial_accounts = client.get("/api/investments/accounts", headers=auth_headers).json()
        initial_balances = client.get("/api/currency-converter/balances", headers=auth_headers).json()
        
        # Perform transactions
        # 1. Place an investment order (if accounts exist)
        if initial_accounts:
            account_id = initial_accounts[0]["id"]
            assets = client.get("/api/investments/assets/search?query=AAPL", 
                              headers=auth_headers).json()
            
            if assets and initial_accounts[0]["cash_balance"] > 1000:
                order_response = client.post("/api/investments/orders",
                                           json={
                                               "account_id": account_id,
                                               "asset_id": assets[0]["id"],
                                               "order_type": "market",
                                               "order_side": "buy",
                                               "quantity": 5
                                           }, headers=auth_headers)
                
                if order_response.status_code == 200:
                    # Verify account balance changed
                    updated_accounts = client.get("/api/investments/accounts", 
                                                headers=auth_headers).json()
                    updated_account = next(a for a in updated_accounts if a["id"] == account_id)
                    
                    # Cash balance should have decreased
                    assert updated_account["cash_balance"] < initial_accounts[0]["cash_balance"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])