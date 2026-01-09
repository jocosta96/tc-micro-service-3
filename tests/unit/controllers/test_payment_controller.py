"""
Unit tests for PaymentController.

Phase 3: Controllers, Routes, Config, Logs
Coverage Target: 90%+
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

from src.adapters.controllers.payment_controller import PaymentController
from src.entities.payment_transaction import PaymentTransaction, PaymentStatus


class TestPaymentController:
    """Test PaymentController."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock payment repository."""
        return MagicMock()

    @pytest.fixture
    def mock_presenter(self):
        """Create a mock presenter."""
        return MagicMock()

    @pytest.fixture
    def controller(self, mock_repository, mock_presenter):
        """Create PaymentController with mocks."""
        return PaymentController(mock_repository, mock_presenter)

    def test_request_payment_success(self, controller, mock_repository):
        """
        Given: Valid payment request data
        When: request_payment() is called
        Then: Returns payment response dict
        """
        data = {
            "amount": 100.0,
            "callback_url": "http://callback.local",
            "provider": "mercadopago",
        }
        
        # Mock repository to return transaction
        def mock_upsert(transaction):
            return (transaction, True)
        
        mock_repository.upsert_by_order_if_pending.side_effect = mock_upsert
        
        # Execute
        result = controller.request_payment(order_id=123, data=data)
        
        # Verify
        assert isinstance(result, dict)
        assert "transaction_id" in result
        assert "qr_or_link" in result
        assert "expires_at" in result

    def test_request_payment_extracts_data_correctly(self, controller, mock_repository):
        """
        Given: Payment request with specific data
        When: request_payment() is called
        Then: DTO is created with correct values
        """
        data = {
            "amount": 250.50,
            "callback_url": "http://custom-callback.local",
            "provider": "stripe",
        }
        
        def mock_upsert(transaction):
            return (transaction, True)
        
        mock_repository.upsert_by_order_if_pending.side_effect = mock_upsert
        
        # Execute
        controller.request_payment(order_id=456, data=data)
        
        # Verify repository was called with correct transaction
        call_args = mock_repository.upsert_by_order_if_pending.call_args[0][0]
        assert call_args.order_id == 456
        assert call_args.amount == 250.50

    @pytest.mark.asyncio
    async def test_process_webhook_success(self, controller, mock_repository):
        """
        Given: Valid webhook data with existing transaction
        When: process_webhook() is called
        Then: Returns success message with transaction_id
        """
        data = {
            "transaction_id": "tx-123",
            "approval_status": True,
            "message": "Payment approved",
            "date": "2026-01-06T12:00:00Z",
            "event_id": "event-123",
        }
        
        # Mock transaction
        transaction = PaymentTransaction(
            id="tx-123",
            order_id=123,
            amount=100.0,
            status=PaymentStatus.APPROVED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        mock_repository.get_by_id.return_value = transaction
        mock_repository.update_status.return_value = transaction
        
        # Execute
        result = await controller.process_webhook(data)
        
        # Verify
        assert result["message"] == "Payment processed"
        assert result["transaction_id"] == "tx-123"

    @pytest.mark.asyncio
    async def test_process_webhook_not_found(self, controller, mock_repository, mock_presenter):
        """
        Given: Webhook data for non-existent transaction
        When: process_webhook() is called
        Then: Returns error from presenter
        """
        data = {
            "transaction_id": "tx-999",
            "approval_status": True,
        }
        
        mock_repository.get_by_id.return_value = None
        mock_presenter.present_error.return_value = {
            "error": {"message": "Transaction not found", "status_code": 404}
        }
        
        # Execute
        result = await controller.process_webhook(data)
        
        # Verify
        assert "error" in result
        mock_presenter.present_error.assert_called_once()
        error_arg = mock_presenter.present_error.call_args[0][0]
        assert isinstance(error_arg, ValueError)
        assert "Transaction not found" in str(error_arg)

    @pytest.mark.asyncio
    async def test_process_webhook_calls_callback_use_case(self, controller, mock_repository):
        """
        Given: Successful webhook processing
        When: process_webhook() is called
        Then: callback_use_case.execute() is called
        """
        data = {
            "transaction_id": "tx-callback",
            "approval_status": True,
        }
        
        transaction = PaymentTransaction.new(order_id=789, amount=75.0)
        transaction.id = "tx-callback"
        
        mock_repository.get_by_id.return_value = transaction
        mock_repository.update_status.return_value = transaction
        
        # Mock the callback use case execute method
        controller.callback_use_case.execute = AsyncMock()
        
        # Execute
        await controller.process_webhook(data)
        
        # Verify callback was called
        controller.callback_use_case.execute.assert_called_once_with(transaction)

    def test_status_found(self, controller, mock_repository):
        """
        Given: order_id with existing transaction
        When: status() is called
        Then: Returns transaction status response dict
        """
        transaction = PaymentTransaction(
            id="tx-status",
            order_id=100,
            amount=50.0,
            status=PaymentStatus.APPROVED,
            qr_or_link="https://pay.local/qr/100",
            expires_at=datetime(2026, 1, 6, 15, 0, 0, tzinfo=timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        mock_repository.get_by_order.return_value = transaction
        
        # Execute
        result = controller.status(order_id=100)
        
        # Verify
        assert isinstance(result, dict)
        assert result["transaction_id"] == "tx-status"
        assert result["order_id"] == 100
        assert result["status"] == "APPROVED"

    def test_status_not_found(self, controller, mock_repository, mock_presenter):
        """
        Given: order_id with no transaction
        When: status() is called
        Then: Returns error from presenter
        """
        mock_repository.get_by_order.return_value = None
        mock_presenter.present_error.return_value = {
            "error": {"message": "Transaction not found", "status_code": 404}
        }
        
        # Execute
        result = controller.status(order_id=999)
        
        # Verify
        assert "error" in result
        mock_presenter.present_error.assert_called_once()

    def test_controller_initializes_use_cases(self, mock_repository, mock_presenter):
        """
        Given: PaymentController initialization
        When: Controller is created
        Then: All use cases are initialized
        """
        controller = PaymentController(mock_repository, mock_presenter)
        
        # Verify use cases exist
        assert controller.create_use_case is not None
        assert controller.webhook_use_case is not None
        assert controller.status_use_case is not None
        assert controller.callback_use_case is not None
        
        # Verify they have the repository
        assert controller.create_use_case.payment_repository == mock_repository
        assert controller.webhook_use_case.payment_repository == mock_repository
        assert controller.status_use_case.payment_repository == mock_repository
        assert controller.callback_use_case.payment_repository == mock_repository

    def test_request_payment_with_minimal_data(self, controller, mock_repository):
        """
        Given: Payment request with only amount
        When: request_payment() is called
        Then: Handles optional fields as None
        """
        data = {
            "amount": 75.0,
        }
        
        def mock_upsert(transaction):
            return (transaction, True)
        
        mock_repository.upsert_by_order_if_pending.side_effect = mock_upsert
        
        # Execute
        result = controller.request_payment(order_id=200, data=data)
        
        # Verify
        assert isinstance(result, dict)
        assert "transaction_id" in result
