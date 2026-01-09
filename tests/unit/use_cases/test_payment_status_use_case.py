"""
Unit tests for PaymentStatusUseCase.

Phase 2: Use Cases + Repository
Coverage Target: 90%+
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.application.use_cases.payment_use_cases import PaymentStatusUseCase
from src.application.dto.implementation.payment_dto import PaymentTransactionStatusResponse
from src.entities.payment_transaction import (
    PaymentTransaction,
    PaymentStatus,
    CallbackStatus,
)


class TestPaymentStatusUseCase:
    """Test PaymentStatusUseCase."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock payment repository."""
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_repository):
        """Create PaymentStatusUseCase with mock repository."""
        return PaymentStatusUseCase(mock_repository)

    def test_execute_order_found(self, use_case, mock_repository):
        """
        Given: order_id with existing transaction
        When: execute() is called
        Then: Returns PaymentTransactionStatusResponse with transaction data
        """
        order_id = 123
        
        # Mock transaction
        transaction = PaymentTransaction(
            id="tx-123",
            order_id=123,
            amount=100.0,
            status=PaymentStatus.APPROVED,
            callback_status=CallbackStatus.DELIVERED,
            qr_or_link="https://pay.local/qr/123",
            expires_at=datetime(2026, 1, 6, 15, 0, 0, tzinfo=timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_error=None,
        )
        
        mock_repository.get_by_order.return_value = transaction
        
        # Execute
        result = use_case.execute(order_id)
        
        # Verify
        assert result is not None
        assert isinstance(result, PaymentTransactionStatusResponse)
        assert result.transaction_id == "tx-123"
        assert result.order_id == 123
        assert result.status == PaymentStatus.APPROVED
        assert result.callback_status == CallbackStatus.DELIVERED
        assert result.qr_or_link == "https://pay.local/qr/123"
        assert result.expires_at == datetime(2026, 1, 6, 15, 0, 0, tzinfo=timezone.utc)
        assert result.last_error is None
        
        mock_repository.get_by_order.assert_called_once_with(123)

    def test_execute_order_not_found(self, use_case, mock_repository):
        """
        Given: order_id with no existing transaction
        When: execute() is called
        Then: Returns None
        """
        order_id = 999
        
        mock_repository.get_by_order.return_value = None
        
        # Execute
        result = use_case.execute(order_id)
        
        # Verify
        assert result is None
        mock_repository.get_by_order.assert_called_once_with(999)

    def test_execute_with_pending_status(self, use_case, mock_repository):
        """
        Given: order_id with PENDING transaction
        When: execute() is called
        Then: Returns response with PENDING status
        """
        transaction = PaymentTransaction.new(order_id=456, amount=50.0)
        transaction.id = "tx-456"
        
        mock_repository.get_by_order.return_value = transaction
        
        # Execute
        result = use_case.execute(456)
        
        # Verify
        assert result.status == PaymentStatus.PENDING
        assert result.callback_status == CallbackStatus.PENDING

    def test_execute_with_declined_status(self, use_case, mock_repository):
        """
        Given: order_id with DECLINED transaction
        When: execute() is called
        Then: Returns response with DECLINED status and error
        """
        transaction = PaymentTransaction(
            id="tx-declined",
            order_id=789,
            amount=75.0,
            status=PaymentStatus.DECLINED,
            callback_status=CallbackStatus.PENDING,
            qr_or_link="https://pay.local/qr/789",
            expires_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_error="Card declined - insufficient funds",
        )
        
        mock_repository.get_by_order.return_value = transaction
        
        # Execute
        result = use_case.execute(789)
        
        # Verify
        assert result.status == PaymentStatus.DECLINED
        assert result.last_error == "Card declined - insufficient funds"

    def test_execute_with_expired_status(self, use_case, mock_repository):
        """
        Given: order_id with EXPIRED transaction
        When: execute() is called
        Then: Returns response with EXPIRED status
        """
        transaction = PaymentTransaction(
            id="tx-expired",
            order_id=100,
            amount=25.0,
            status=PaymentStatus.EXPIRED,
            callback_status=CallbackStatus.PENDING,
            qr_or_link="https://pay.local/qr/100",
            expires_at=datetime(2026, 1, 6, 10, 0, 0, tzinfo=timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_error="Payment expired",
        )
        
        mock_repository.get_by_order.return_value = transaction
        
        # Execute
        result = use_case.execute(100)
        
        # Verify
        assert result.status == PaymentStatus.EXPIRED
        assert result.expires_at == datetime(2026, 1, 6, 10, 0, 0, tzinfo=timezone.utc)

    def test_execute_with_callback_failed(self, use_case, mock_repository):
        """
        Given: order_id with transaction where callback failed
        When: execute() is called
        Then: Returns response with FAILED callback_status
        """
        transaction = PaymentTransaction(
            id="tx-callback-failed",
            order_id=200,
            amount=150.0,
            status=PaymentStatus.APPROVED,
            callback_status=CallbackStatus.FAILED,
            qr_or_link="https://pay.local/qr/200",
            expires_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_error=None,
        )
        
        mock_repository.get_by_order.return_value = transaction
        
        # Execute
        result = use_case.execute(200)
        
        # Verify
        assert result.callback_status == CallbackStatus.FAILED
        assert result.status == PaymentStatus.APPROVED

    def test_execute_converts_entity_to_response_dto(self, use_case, mock_repository):
        """
        Given: Transaction entity from repository
        When: execute() is called
        Then: Entity is correctly converted to PaymentTransactionStatusResponse
        """
        transaction = PaymentTransaction(
            id="tx-conversion",
            order_id=300,
            amount=200.0,
            status=PaymentStatus.APPROVED,
            callback_status=CallbackStatus.DELIVERED,
            qr_or_link="https://pay.local/qr/300",
            expires_at=datetime(2026, 1, 6, 16, 0, 0, tzinfo=timezone.utc),
            created_at=datetime(2026, 1, 6, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 6, 12, 0, 0, tzinfo=timezone.utc),
            last_error="",
        )
        
        mock_repository.get_by_order.return_value = transaction
        
        # Execute
        result = use_case.execute(300)
        
        # Verify all fields converted
        assert result.transaction_id == "tx-conversion"
        assert result.order_id == 300
        assert result.status == PaymentStatus.APPROVED
        assert result.callback_status == CallbackStatus.DELIVERED
        assert result.qr_or_link == "https://pay.local/qr/300"
        assert result.expires_at == datetime(2026, 1, 6, 16, 0, 0, tzinfo=timezone.utc)
        # Empty string last_error from entity
        assert result.last_error == ""

    def test_execute_with_minimal_transaction_data(self, use_case, mock_repository):
        """
        Given: Transaction with minimal fields (many None values)
        When: execute() is called
        Then: Response correctly handles None values
        """
        transaction = PaymentTransaction(
            id="tx-minimal",
            order_id=400,
            amount=50.0,
            status=PaymentStatus.PENDING,
            callback_status=CallbackStatus.PENDING,
            qr_or_link=None,
            expires_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_error=None,
        )
        
        mock_repository.get_by_order.return_value = transaction
        
        # Execute
        result = use_case.execute(400)
        
        # Verify None values handled
        assert result.qr_or_link is None
        assert result.expires_at is None
        assert result.last_error is None

    def test_execute_repository_called_with_correct_order_id(self, use_case, mock_repository):
        """
        Given: Specific order_id
        When: execute() is called
        Then: Repository is called with exact order_id parameter
        """
        mock_repository.get_by_order.return_value = None
        
        # Execute with different order_ids
        use_case.execute(12345)
        mock_repository.get_by_order.assert_called_with(12345)
        
        use_case.execute(67890)
        mock_repository.get_by_order.assert_called_with(67890)
