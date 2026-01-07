"""
Unit tests for PaymentWebhookUseCase.

Phase 2: Use Cases + Repository
Coverage Target: 90%+
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.application.use_cases.payment_use_cases import PaymentWebhookUseCase
from src.application.dto.implementation.payment_dto import PaymentWebhookRequest
from src.entities.payment_transaction import PaymentTransaction, PaymentStatus


class TestPaymentWebhookUseCase:
    """Test PaymentWebhookUseCase."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock payment repository."""
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_repository):
        """Create PaymentWebhookUseCase with mock repository."""
        return PaymentWebhookUseCase(mock_repository)

    def test_execute_webhook_approved(self, use_case, mock_repository):
        """
        Given: PaymentWebhookRequest with approval_status=True
        When: execute() is called and transaction exists
        Then: Transaction status updated to APPROVED
        """
        request = PaymentWebhookRequest(
            transaction_id="tx-123",
            approval_status=True,
        )
        
        # Existing transaction
        existing_transaction = PaymentTransaction(
            id="tx-123",
            order_id=123,
            amount=100.0,
            status=PaymentStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        updated_transaction = PaymentTransaction(
            id="tx-123",
            order_id=123,
            amount=100.0,
            status=PaymentStatus.APPROVED,
            provider_tx_id="tx-123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        mock_repository.get_by_id.return_value = existing_transaction
        mock_repository.update_status.return_value = updated_transaction
        
        # Execute
        result = use_case.execute(request)
        
        # Verify
        assert result is not None
        assert result.status == PaymentStatus.APPROVED
        mock_repository.get_by_id.assert_called_once_with("tx-123")
        mock_repository.update_status.assert_called_once_with(
            transaction_id="tx-123",
            status=PaymentStatus.APPROVED,
            provider_tx_id="tx-123",
            error=None,
        )

    def test_execute_webhook_declined(self, use_case, mock_repository):
        """
        Given: PaymentWebhookRequest with approval_status=False
        When: execute() is called
        Then: Transaction status updated to DECLINED
        """
        request = PaymentWebhookRequest(
            transaction_id="tx-456",
            approval_status=False,
        )
        
        existing_transaction = PaymentTransaction(
            id="tx-456",
            order_id=456,
            amount=50.0,
            status=PaymentStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        updated_transaction = PaymentTransaction(
            id="tx-456",
            order_id=456,
            amount=50.0,
            status=PaymentStatus.DECLINED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        mock_repository.get_by_id.return_value = existing_transaction
        mock_repository.update_status.return_value = updated_transaction
        
        # Execute
        result = use_case.execute(request)
        
        # Verify
        assert result is not None
        assert result.status == PaymentStatus.DECLINED
        mock_repository.update_status.assert_called_once_with(
            transaction_id="tx-456",
            status=PaymentStatus.DECLINED,
            provider_tx_id="tx-456",
            error=None,
        )

    def test_execute_transaction_not_found(self, use_case, mock_repository):
        """
        Given: PaymentWebhookRequest for non-existent transaction
        When: execute() is called
        Then: Returns None
        """
        request = PaymentWebhookRequest(
            transaction_id="tx-999",
            approval_status=True,
        )
        
        mock_repository.get_by_id.return_value = None
        
        # Execute
        result = use_case.execute(request)
        
        # Verify
        assert result is None
        mock_repository.get_by_id.assert_called_once_with("tx-999")
        mock_repository.update_status.assert_not_called()

    def test_execute_with_error_message(self, use_case, mock_repository):
        """
        Given: PaymentWebhookRequest with error message
        When: execute() is called with approval_status=False
        Then: Error message is passed to update_status
        """
        request = PaymentWebhookRequest(
            transaction_id="tx-789",
            approval_status=False,
            message="Insufficient funds",
        )
        
        existing_transaction = PaymentTransaction.new(order_id=789, amount=75.0)
        existing_transaction.id = "tx-789"
        updated_transaction = PaymentTransaction.new(order_id=789, amount=75.0)
        updated_transaction.id = "tx-789"
        updated_transaction.status = PaymentStatus.DECLINED
        
        mock_repository.get_by_id.return_value = existing_transaction
        mock_repository.update_status.return_value = updated_transaction
        
        # Execute
        use_case.execute(request)
        
        # Verify error message passed
        mock_repository.update_status.assert_called_once_with(
            transaction_id="tx-789",
            status=PaymentStatus.DECLINED,
            provider_tx_id="tx-789",
            error="Insufficient funds",
        )

    def test_execute_with_success_message(self, use_case, mock_repository):
        """
        Given: PaymentWebhookRequest with approval_status=True and message
        When: execute() is called
        Then: Message is passed to update_status
        """
        request = PaymentWebhookRequest(
            transaction_id="tx-success",
            approval_status=True,
            message="Payment completed successfully",
        )
        
        existing_transaction = PaymentTransaction.new(order_id=100, amount=25.0)
        existing_transaction.id = "tx-success"
        updated_transaction = PaymentTransaction.new(order_id=100, amount=25.0)
        updated_transaction.id = "tx-success"
        updated_transaction.status = PaymentStatus.APPROVED
        
        mock_repository.get_by_id.return_value = existing_transaction
        mock_repository.update_status.return_value = updated_transaction
        
        # Execute
        use_case.execute(request)
        
        # Verify
        mock_repository.update_status.assert_called_once_with(
            transaction_id="tx-success",
            status=PaymentStatus.APPROVED,
            provider_tx_id="tx-success",
            error="Payment completed successfully",
        )

    def test_execute_without_message(self, use_case, mock_repository):
        """
        Given: PaymentWebhookRequest without message
        When: execute() is called
        Then: Error parameter is None
        """
        request = PaymentWebhookRequest(
            transaction_id="tx-no-msg",
            approval_status=True,
            message=None,
        )
        
        existing_transaction = PaymentTransaction.new(order_id=200, amount=50.0)
        existing_transaction.id = "tx-no-msg"
        updated_transaction = PaymentTransaction.new(order_id=200, amount=50.0)
        updated_transaction.id = "tx-no-msg"
        
        mock_repository.get_by_id.return_value = existing_transaction
        mock_repository.update_status.return_value = updated_transaction
        
        # Execute
        use_case.execute(request)
        
        # Verify error is None
        call_kwargs = mock_repository.update_status.call_args[1]
        assert call_kwargs["error"] is None

    def test_execute_uses_transaction_id_as_provider_tx_id(self, use_case, mock_repository):
        """
        Given: PaymentWebhookRequest
        When: execute() is called
        Then: transaction_id is used as provider_tx_id
        """
        request = PaymentWebhookRequest(
            transaction_id="tx-provider-123",
            approval_status=True,
        )
        
        existing_transaction = PaymentTransaction.new(order_id=300, amount=100.0)
        existing_transaction.id = "tx-provider-123"
        updated_transaction = PaymentTransaction.new(order_id=300, amount=100.0)
        
        mock_repository.get_by_id.return_value = existing_transaction
        mock_repository.update_status.return_value = updated_transaction
        
        # Execute
        use_case.execute(request)
        
        # Verify provider_tx_id matches transaction_id
        mock_repository.update_status.assert_called_once()
        call_kwargs = mock_repository.update_status.call_args[1]
        assert call_kwargs["provider_tx_id"] == "tx-provider-123"

    def test_execute_returns_updated_transaction(self, use_case, mock_repository):
        """
        Given: Successful webhook processing
        When: execute() is called
        Then: Returns the updated transaction from repository
        """
        request = PaymentWebhookRequest(
            transaction_id="tx-return",
            approval_status=True,
        )
        
        existing_transaction = PaymentTransaction.new(order_id=400, amount=150.0)
        existing_transaction.id = "tx-return"
        
        updated_transaction = PaymentTransaction(
            id="tx-return",
            order_id=400,
            amount=150.0,
            status=PaymentStatus.APPROVED,
            provider_tx_id="tx-return",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        mock_repository.get_by_id.return_value = existing_transaction
        mock_repository.update_status.return_value = updated_transaction
        
        # Execute
        result = use_case.execute(request)
        
        # Verify returned transaction is the updated one
        assert result == updated_transaction
        assert result.status == PaymentStatus.APPROVED
        assert result.provider_tx_id == "tx-return"
