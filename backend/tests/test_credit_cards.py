import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.main_banking import app
from app.repositories.data_manager import data_manager
from app.models.enums import (
    CardCategory, ApplicationStatus, EmploymentType
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


class TestCreditScore:
    """Test credit score endpoints."""
    
    def test_get_credit_score(self, auth_headers):
        """Test getting user's credit score."""
        response = client.get("/api/credit-cards/credit-score", headers=auth_headers)
        assert response.status_code == 200
        score_info = response.json()
        assert "score" in score_info
        assert "rating" in score_info
        assert "factors" in score_info
        assert 300 <= score_info["score"] <= 850
        assert score_info["rating"] in ["poor", "fair", "good", "very_good", "excellent"]
    
    def test_update_credit_score(self, auth_headers):
        """Test updating credit score (simulation)."""
        new_score = 750
        response = client.put("/api/credit-cards/credit-score", 
                            json={"score": new_score}, 
                            headers=auth_headers)
        assert response.status_code == 200
        updated_score = response.json()
        assert updated_score["score"] == new_score
        assert updated_score["rating"] == "very_good"


class TestCreditCardOffers:
    """Test credit card offer endpoints."""
    
    def test_get_all_cards(self, auth_headers):
        """Test getting all available credit cards."""
        response = client.get("/api/credit-cards", headers=auth_headers)
        assert response.status_code == 200
        cards = response.json()
        assert isinstance(cards, list)
        if cards:
            card = cards[0]
            assert "id" in card
            assert "card_name" in card
            assert "issuer" in card
            assert "category" in card
            assert "annual_fee" in card
            assert "benefits" in card
    
    def test_get_cards_by_category(self, auth_headers):
        """Test filtering cards by category."""
        response = client.get("/api/credit-cards?category=cash_back", 
                            headers=auth_headers)
        assert response.status_code == 200
        cards = response.json()
        assert isinstance(cards, list)
        for card in cards:
            assert card["category"] == CardCategory.CASH_BACK.value
    
    def test_get_card_details(self, auth_headers):
        """Test getting specific card details."""
        # Get all cards first
        cards = client.get("/api/credit-cards", headers=auth_headers).json()
        if cards:
            card_id = cards[0]["id"]
            
            response = client.get(f"/api/credit-cards/{card_id}", 
                                headers=auth_headers)
            assert response.status_code == 200
            card = response.json()
            assert card["id"] == card_id
    
    def test_get_featured_cards(self, auth_headers):
        """Test getting featured cards."""
        response = client.get("/api/credit-cards/featured", headers=auth_headers)
        assert response.status_code == 200
        cards = response.json()
        assert isinstance(cards, list)
        for card in cards:
            assert card.get("is_featured", False) is True


class TestCreditCardRecommendations:
    """Test recommendation endpoints."""
    
    def test_get_recommendations(self, auth_headers):
        """Test getting card recommendations."""
        response = client.get("/api/credit-cards/recommendations", 
                            headers=auth_headers)
        assert response.status_code == 200
        recommendations = response.json()
        assert isinstance(recommendations, list)
        if recommendations:
            rec = recommendations[0]
            assert "card" in rec
            assert "match_score" in rec
            assert "reasons" in rec
            assert "estimated_approval_odds" in rec
            assert 0 <= rec["match_score"] <= 1
    
    def test_get_personalized_recommendations(self, auth_headers):
        """Test getting personalized recommendations."""
        response = client.get("/api/credit-cards/recommendations/personalized", 
                            headers=auth_headers)
        assert response.status_code == 200
        recommendations = response.json()
        assert isinstance(recommendations, list)
    
    def test_recommendations_with_params(self, auth_headers):
        """Test recommendations with specific parameters."""
        params = {
            "income_level": "high",
            "spending_categories": ["travel", "dining"],
            "preferred_benefits": ["lounge_access", "travel_insurance"],
            "limit": 5
        }
        
        response = client.get("/api/credit-cards/recommendations", 
                            params=params, headers=auth_headers)
        assert response.status_code == 200
        recommendations = response.json()
        assert len(recommendations) <= 5


class TestCreditCardApplications:
    """Test application endpoints."""
    
    def test_submit_application(self, auth_headers):
        """Test submitting a credit card application."""
        # Get a card to apply for
        cards = client.get("/api/credit-cards", headers=auth_headers).json()
        if not cards:
            return
            
        card_id = cards[0]["id"]
        
        application_data = {
            "card_id": card_id,
            "annual_income": 75000,
            "employment_type": EmploymentType.FULL_TIME.value,
            "employment_duration_months": 36,
            "housing_payment": 1500,
            "existing_cards_count": 2,
            "requested_credit_limit": 10000
        }
        
        response = client.post("/api/credit-cards/applications", 
                             json=application_data, headers=auth_headers)
        assert response.status_code == 200
        application = response.json()
        assert application["card_id"] == card_id
        assert application["status"] in [
            ApplicationStatus.PENDING.value,
            ApplicationStatus.APPROVED.value,
            ApplicationStatus.REJECTED.value
        ]
    
    def test_get_applications(self, auth_headers):
        """Test getting user's applications."""
        response = client.get("/api/credit-cards/applications", headers=auth_headers)
        assert response.status_code == 200
        applications = response.json()
        assert isinstance(applications, list)
    
    def test_get_application_details(self, auth_headers):
        """Test getting specific application details."""
        # Submit an application first
        cards = client.get("/api/credit-cards", headers=auth_headers).json()
        if not cards:
            return
            
        application_data = {
            "card_id": cards[0]["id"],
            "annual_income": 60000,
            "employment_type": EmploymentType.FULL_TIME.value,
            "employment_duration_months": 24,
            "housing_payment": 1200,
            "existing_cards_count": 1
        }
        
        app_response = client.post("/api/credit-cards/applications", 
                                 json=application_data, headers=auth_headers)
        app_id = app_response.json()["id"]
        
        # Get application details
        response = client.get(f"/api/credit-cards/applications/{app_id}", 
                            headers=auth_headers)
        assert response.status_code == 200
        application = response.json()
        assert application["id"] == app_id
    
    def test_withdraw_application(self, auth_headers):
        """Test withdrawing an application."""
        # Submit an application
        cards = client.get("/api/credit-cards", headers=auth_headers).json()
        if not cards:
            return
            
        application_data = {
            "card_id": cards[0]["id"],
            "annual_income": 50000,
            "employment_type": EmploymentType.PART_TIME.value,
            "employment_duration_months": 12,
            "housing_payment": 1000,
            "existing_cards_count": 0
        }
        
        app_response = client.post("/api/credit-cards/applications", 
                                 json=application_data, headers=auth_headers)
        app_id = app_response.json()["id"]
        
        # Withdraw the application
        response = client.put(f"/api/credit-cards/applications/{app_id}/withdraw", 
                            headers=auth_headers)
        assert response.status_code == 200
        withdrawn_app = response.json()
        assert withdrawn_app["status"] == ApplicationStatus.WITHDRAWN.value


class TestCreditCardComparison:
    """Test card comparison endpoints."""
    
    def test_compare_cards(self, auth_headers):
        """Test comparing multiple cards."""
        # Get some cards to compare
        cards = client.get("/api/credit-cards?limit=3", headers=auth_headers).json()
        if len(cards) < 2:
            return
            
        card_ids = [card["id"] for card in cards[:3]]
        
        response = client.post("/api/credit-cards/compare", 
                             json={"card_ids": card_ids}, 
                             headers=auth_headers)
        assert response.status_code == 200
        comparison = response.json()
        assert "cards" in comparison
        assert "comparison_matrix" in comparison
        assert len(comparison["cards"]) == len(card_ids)
        
        # Check comparison matrix
        matrix = comparison["comparison_matrix"]
        assert isinstance(matrix, list)
        if matrix:
            assert "feature" in matrix[0]
            assert "values" in matrix[0]
            assert len(matrix[0]["values"]) == len(card_ids)


class TestCreditCardEligibility:
    """Test eligibility check endpoints."""
    
    def test_check_eligibility(self, auth_headers):
        """Test checking eligibility for a card."""
        # Get a card
        cards = client.get("/api/credit-cards", headers=auth_headers).json()
        if not cards:
            return
            
        card_id = cards[0]["id"]
        
        response = client.post(f"/api/credit-cards/{card_id}/check-eligibility", 
                             headers=auth_headers)
        assert response.status_code == 200
        eligibility = response.json()
        assert "eligible" in eligibility
        assert "approval_odds" in eligibility
        assert "reasons" in eligibility
        assert isinstance(eligibility["eligible"], bool)
        assert eligibility["approval_odds"] in ["low", "medium", "high"]


class TestCreditCardAnalytics:
    """Test analytics endpoints."""
    
    def test_get_application_stats(self, auth_headers):
        """Test getting application statistics."""
        response = client.get("/api/credit-cards/applications/stats", 
                            headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()
        assert "total_applications" in stats
        assert "approved_count" in stats
        assert "rejected_count" in stats
        assert "pending_count" in stats
        assert "approval_rate" in stats
        assert "average_credit_limit" in stats
        assert "popular_categories" in stats
        
        # Verify stats consistency
        total = stats["approved_count"] + stats["rejected_count"] + stats["pending_count"]
        assert total <= stats["total_applications"]
        
        if stats["total_applications"] > 0:
            assert 0 <= stats["approval_rate"] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])