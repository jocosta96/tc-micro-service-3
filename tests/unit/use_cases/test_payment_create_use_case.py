"""
Unit tests for PaymentCreateUseCase.

Phase 2: Use Cases + Repository
Coverage Target: 90%+
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from src.application.use_cases.payment_use_cases import PaymentCreateUseCase
from src.application.dto.implementation.payment_dto import (
    PaymentCreateRequest,
    PaymentCreateResponse,
)
from src.entities.payment_transaction import PaymentTransaction, PaymentStatus


class TestPaymentCreateUseCase:
    """Test PaymentCreateUseCase."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock payment repository."""
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_repository):
        """Create PaymentCreateUseCase with mock repository."""
        return PaymentCreateUseCase(mock_repository)

    def test_execute_create_new_payment(self, use_case, mock_repository):
        """
        Given: PaymentCreateRequest for new order
        When: execute() is called and repository creates new transaction
        Then: Returns PaymentCreateResponse with transaction details
        """
        request = PaymentCreateRequest(
            order_id=123,
            amount=100.0,
            provider="mercadopago",
            callback_url="http://callback.local/payment",
        )
        
        # Mock repository to return the transaction passed to it
        def mock_upsert(transaction):
            return (transaction, True)
        
        mock_repository.upsert_by_order_if_pending.side_effect = mock_upsert
        
        # Execute
        response = use_case.execute(request)
        
        # Verify
        assert isinstance(response, PaymentCreateResponse)
        assert response.transaction_id is not None
        assert response.qr_or_link == "https://pay.local/tx/123"
        assert response.expires_at is not None
        
        # Verify repository was called
        mock_repository.upsert_by_order_if_pending.assert_called_once()
        call_args = mock_repository.upsert_by_order_if_pending.call_args[0][0]
        assert call_args.order_id == 123
        assert call_args.amount == 100.0
        assert call_args.provider == "mercadopago"

    def test_execute_reuse_pending_payment(self, use_case, mock_repository):
        """
        Given: PaymentCreateRequest for order with existing PENDING transaction
        When: execute() is called
        Then: Returns existing transaction details without creating new one
        """
        request = PaymentCreateRequest(
            order_id=456,
            amount=50.0,
            provider="stripe",
        )
        
        # Existing transaction
        existing_transaction = PaymentTransaction(
            id="existing-tx-456",
            order_id=456,
            amount=50.0,
            status=PaymentStatus.PENDING,
            provider="stripe",
            qr_or_link="https://pay.local/tx/456",
            expires_at=datetime(2026, 1, 6, 15, 0, 0, tzinfo=timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        # Repository returns existing transaction (created=False)
        mock_repository.upsert_by_order_if_pending.return_value = (existing_transaction, False)
        
        # Execute
        response = use_case.execute(request)
        
        # Verify returns existing transaction
        assert response.transaction_id == "existing-tx-456"
        assert response.qr_or_link == "https://pay.local/tx/456"
        assert response.expires_at == datetime(2026, 1, 6, 15, 0, 0, tzinfo=timezone.utc)

    def test_execute_with_callback_url_in_metadata(self, use_case, mock_repository):
        """
        Given: PaymentCreateRequest with callback_url
        When: execute() is called
        Then: Transaction metadata contains callback_url
        """
        request = PaymentCreateRequest(
            order_id=789,
            amount=200.0,
            callback_url="http://order-service:8000/webhook/payment",
        )
        
        def mock_upsert(transaction):
            return (transaction, True)
        
        mock_repository.upsert_by_order_if_pending.side_effect = mock_upsert
        
        # Execute
        use_case.execute(request)
        
        # Verify metadata was set
        call_args = mock_repository.upsert_by_order_if_pending.call_args[0][0]
        assert "callback_url" in call_args.metadata
        assert call_args.metadata["callback_url"] == "http://order-service:8000/webhook/payment"

    def test_execute_without_callback_url(self, use_case, mock_repository):
        """
        Given: PaymentCreateRequest without callback_url
        When: execute() is called
        Then: Transaction metadata does NOT contain callback_url
        """
        request = PaymentCreateRequest(
            order_id=100,
            amount=75.0,
        )
        
        # Mock repository to return transaction passed to it
        def mock_upsert(transaction):
            return (transaction, True)
        
        mock_repository.upsert_by_order_if_pending.side_effect = mock_upsert
        
        # Execute
        use_case.execute(request)
        
        # Verify metadata does not have callback_url
        call_args = mock_repository.upsert_by_order_if_pending.call_args[0][0]
        assert "callback_url" not in call_args.metadata

    def test_execute_expires_at_calculation(self, use_case, mock_repository):
        """
        Given: PaymentCreateRequest
        When: execute() is called
        Then: Transaction expires_at is set to ~15 minutes from now
        """
        request = PaymentCreateRequest(order_id=999, amount=150.0)
        
        def mock_upsert(transaction):
            return (transaction, True)
        
        mock_repository.upsert_by_order_if_pending.side_effect = mock_upsert
        
        before = datetime.now(timezone.utc) + timedelta(minutes=14, seconds=50)
        use_case.execute(request)
        after = datetime.now(timezone.utc) + timedelta(minutes=15, seconds=10)
        
        # Verify expires_at is approximately 15 minutes from now
        call_args = mock_repository.upsert_by_order_if_pending.call_args[0][0]
        assert before <= call_args.expires_at <= after

    def test_execute_qr_or_link_generation(self, use_case, mock_repository):
        """
        Given: PaymentCreateRequest
        When: execute() is called
        Then: Transaction qr_or_link follows expected pattern
        """
        request = PaymentCreateRequest(order_id=555, amount=99.99)
        
        def mock_upsert(transaction):
            return (transaction, True)
        
        mock_repository.upsert_by_order_if_pending.side_effect = mock_upsert
        
        # Execute
        use_case.execute(request)
        
        # Verify qr_or_link pattern
        call_args = mock_repository.upsert_by_order_if_pending.call_args[0][0]
        assert call_args.qr_or_link == "https://pay.local/tx/555"

    def test_execute_sets_default_status(self, use_case, mock_repository):
        """
        Given: New payment request
        When: execute() is called
        Then: Transaction status is PENDING
        """
        request = PaymentCreateRequest(order_id=666, amount=33.33)
        
        def mock_upsert(transaction):
            return (transaction, True)
        
        mock_repository.upsert_by_order_if_pending.side_effect = mock_upsert
        
        # Execute
        use_case.execute(request)
        
        # Verify status is PENDING
        call_args = mock_repository.upsert_by_order_if_pending.call_args[0][0]
        assert call_args.status == PaymentStatus.PENDING

    def test_execute_with_all_optional_fields(self, use_case, mock_repository):
        """
        Given: PaymentCreateRequest with all optional fields
        When: execute() is called
        Then: All fields are properly set in transaction
        """
        request = PaymentCreateRequest(
            order_id=777,
            amount=250.50,
            callback_url="http://full-callback.local",
            provider="paypal",
        )
        
        def mock_upsert(transaction):
            return (transaction, True)
        
        mock_repository.upsert_by_order_if_pending.side_effect = mock_upsert
        
        # Execute
        response = use_case.execute(request)
        
        # Verify all fields
        call_args = mock_repository.upsert_by_order_if_pending.call_args[0][0]
        assert call_args.order_id == 777
        assert call_args.amount == 250.50
        assert call_args.provider == "paypal"
        assert call_args.metadata["callback_url"] == "http://full-callback.local"
        assert response.transaction_id is not None
        assert response.qr_or_link is not None
        assert response.expires_at is not None
