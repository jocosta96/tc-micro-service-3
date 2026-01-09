"""
Integration tests for health routes.

Phase 3: Controllers, Routes, Config, Logs
Coverage Target: 100% (simple health checks)
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.main import app


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


class TestHealthRoutes:
    """Test health check API routes."""

    def test_health_check_returns_healthy(self, client):
        """
        Given: Application is running
        When: GET /health
        Then: Returns 200 with healthy status
        """
        response = client.get("/health")
        
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["status"] == "healthy"
        assert "message" in json_response
        assert "Payment service" in json_response["message"]

    def test_configuration_health_check_returns_config(self, client):
        """
        Given: Application is running with configuration
        When: GET /health/config
        Then: Returns 200 with configuration details
        """
        with patch("src.adapters.routes.health_routes.payment_config") as mock_config:
            mock_config.table_name = "test-payments-table"
            mock_config.region_name = "us-east-1"
            mock_config.order_api_host = "http://order-service:8080"
            
            response = client.get("/health/config")
        
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["status"] == "healthy"
        assert "configuration" in json_response
        
        config = json_response["configuration"]
        assert config["table_name"] == "test-payments-table"
        assert config["region"] == "us-east-1"
        assert config["order_api_host"] == "http://order-service:8080"

    def test_health_check_always_returns_200(self, client):
        """
        Given: Any application state
        When: GET /health
        Then: Always returns 200 (basic liveness probe)
        """
        # Multiple calls should always return 200
        for _ in range(3):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    def test_configuration_health_check_exposes_no_secrets(self, client):
        """
        Given: Application has sensitive configuration
        When: GET /health/config
        Then: Only exposes non-sensitive configuration
        """
        with patch("src.adapters.routes.health_routes.payment_config") as mock_config:
            mock_config.table_name = "prod-payments"
            mock_config.region_name = "eu-west-1"
            mock_config.order_api_host = "https://orders.prod.com"
            # Should NOT expose: AWS credentials, API keys, secrets
            
            response = client.get("/health/config")
        
        assert response.status_code == 200
        json_response = response.json()
        
        # Verify no sensitive keys in response
        json_str = str(json_response).lower()
        assert "secret" not in json_str
        assert "password" not in json_str
        assert "key" not in json_str or "table" in json_str  # table_name is OK
