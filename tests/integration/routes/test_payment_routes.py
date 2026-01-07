"""
Integration tests for payment routes.

Phase 3: Controllers, Routes, Config, Logs
Coverage Target: 70%+
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock

from src.main import app
from src.entities.payment_transaction import PaymentTransaction, PaymentStatus


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_container():
    """Mock the DI container."""
    with patch("src.adapters.routes.payment_routes.Container") as mock:
        yield mock


class TestPaymentRoutes:
    """Test payment API routes."""

    def test_request_payment_success(self, client, mock_container):
        """
        Given: Valid payment request
        When: POST /payment/request/{order_id}
        Then: Returns 200 with transaction details
        """
        # Mock controller
        mock_controller = MagicMock()
        mock_controller.request_payment.return_value = {
            "transaction_id": "tx-123",
            "qr_or_link": "https://pay.local/tx/123",
            "expires_at": "2026-01-06T15:00:00+00:00",
        }
        
        mock_container_instance = MagicMock()
        mock_container_instance.payment_repository = MagicMock()
        mock_container_instance.presenter = MagicMock()
        mock_container.return_value = mock_container_instance
        
        with patch("src.adapters.routes.payment_routes.PaymentController", return_value=mock_controller):
            response = client.post(
                "/payment/request/123",
                json={"amount": 100.0, "provider": "mercadopago"}
            )
        
        assert response.status_code == 200
        assert response.json()["transaction_id"] == "tx-123"

    def test_request_payment_invalid_amount(self, client):
        """
        Given: Payment request with invalid amount (<= 0)
        When: POST /payment/request/{order_id}
        Then: Returns 422 validation error
        """
        response = client.post(
            "/payment/request/123",
            json={"amount": -10.0}
        )
        
        assert response.status_code == 422

    def test_request_payment_missing_amount(self, client):
        """
        Given: Payment request without amount
        When: POST /payment/request/{order_id}
        Then: Returns 422 validation error
        """
        response = client.post(
            "/payment/request/123",
            json={}
        )
        
        assert response.status_code == 422

    def test_webhook_success(self, client, mock_container):
        """
        Given: Valid webhook payload
        When: POST /payment/webhook/mercadopago
        Then: Returns 200 with success message
        """
        mock_controller = MagicMock()
        mock_controller.process_webhook = AsyncMock(return_value={
            "message": "Payment processed",
            "transaction_id": "tx-456",
        })
        
        mock_container_instance = MagicMock()
        mock_container_instance.payment_repository = MagicMock()
        mock_container_instance.presenter = MagicMock()
        mock_container.return_value = mock_container_instance
        
        with patch("src.adapters.routes.payment_routes.PaymentController", return_value=mock_controller):
            response = client.post(
                "/payment/webhook/mercadopago",
                json={
                    "transaction_id": "tx-456",
                    "approval_status": True,
                }
            )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Payment processed"

    def test_webhook_with_error_raises_http_exception(self, client, mock_container):
        """
        Given: Webhook returns error dict
        When: POST /payment/webhook/mercadopago
        Then: Raises HTTPException with status code from error
        """
        mock_controller = MagicMock()
        mock_controller.process_webhook = AsyncMock(return_value={
            "error": {
                "status_code": 404,
                "message": "Transaction not found",
            }
        })
        
        mock_container_instance = MagicMock()
        mock_container_instance.payment_repository = MagicMock()
        mock_container_instance.presenter = MagicMock()
        mock_container.return_value = mock_container_instance
        
        with patch("src.adapters.routes.payment_routes.PaymentController", return_value=mock_controller):
            response = client.post(
                "/payment/webhook/mercadopago",
                json={
                    "transaction_id": "tx-999",
                    "approval_status": True,
                }
            )
        
        assert response.status_code == 404

    def test_payment_status_success(self, client, mock_container):
        """
        Given: order_id with existing transaction
        When: GET /payment/status/{order_id}
        Then: Returns 200 with transaction status
        """
        mock_controller = MagicMock()
        mock_controller.status.return_value = {
            "transaction_id": "tx-789",
            "order_id": 789,
            "status": "APPROVED",
            "callback_status": "DELIVERED",
            "qr_or_link": "https://pay.local/qr/789",
            "expires_at": None,
            "last_error": None,
        }
        
        mock_container_instance = MagicMock()
        mock_container_instance.payment_repository = MagicMock()
        mock_container_instance.presenter = MagicMock()
        mock_container.return_value = mock_container_instance
        
        with patch("src.adapters.routes.payment_routes.PaymentController", return_value=mock_controller):
            response = client.get("/payment/status/789")
        
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["transaction_id"] == "tx-789"
        assert json_response["status"] == "APPROVED"

    def test_payment_status_not_found(self, client, mock_container):
        """
        Given: order_id without transaction
        When: GET /payment/status/{order_id}
        Then: Returns 404
        """
        mock_controller = MagicMock()
        mock_controller.status.return_value = {
            "error": {
                "status_code": 404,
                "message": "Transaction not found",
            }
        }
        
        mock_container_instance = MagicMock()
        mock_container_instance.payment_repository = MagicMock()
        mock_container_instance.presenter = MagicMock()
        mock_container.return_value = mock_container_instance
        
        with patch("src.adapters.routes.payment_routes.PaymentController", return_value=mock_controller):
            response = client.get("/payment/status/999")
        
        assert response.status_code == 404

    def test_request_payment_with_all_optional_fields(self, client, mock_container):
        """
        Given: Payment request with all optional fields
        When: POST /payment/request/{order_id}
        Then: Returns 200 with transaction
        """
        mock_controller = MagicMock()
        mock_controller.request_payment.return_value = {
            "transaction_id": "tx-complete",
            "qr_or_link": "https://pay.local/tx/complete",
            "expires_at": "2026-01-06T16:00:00+00:00",
        }
        
        mock_container_instance = MagicMock()
        mock_container_instance.payment_repository = MagicMock()
        mock_container_instance.presenter = MagicMock()
        mock_container.return_value = mock_container_instance
        
        with patch("src.adapters.routes.payment_routes.PaymentController", return_value=mock_controller):
            response = client.post(
                "/payment/request/555",
                json={
                    "amount": 250.0,
                    "callback_url": "http://callback.local/webhook",
                    "provider": "stripe",
                }
            )
        
        assert response.status_code == 200
        assert "transaction_id" in response.json()

    def test_webhook_missing_required_fields(self, client):
        """
        Given: Webhook payload missing required fields
        When: POST /payment/webhook/mercadopago
        Then: Returns 422 validation error
        """
        response = client.post(
            "/payment/webhook/mercadopago",
            json={"transaction_id": "tx-123"}  # Missing approval_status
        )
        
        assert response.status_code == 422
