"""
Unit tests for Payment DTOs.

Phase 1: Entities + DTOs
Coverage Target: 100%
"""
import pytest
from datetime import datetime, timezone

from src.application.dto.implementation.payment_dto import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentWebhookRequest,
    PaymentTransactionStatusResponse,
)
from src.entities.payment_transaction import (
    PaymentTransaction,
    PaymentStatus,
    CallbackStatus,
)


class TestPaymentCreateRequest:
    """Test PaymentCreateRequest DTO."""

    def test_to_dict_with_all_fields(self):
        """
        Given: PaymentCreateRequest with all fields
        When: to_dict() is called
        Then: Returns dict with all keys
        """
        request = PaymentCreateRequest(
            order_id=123,
            amount=100.50,
            callback_url="http://callback.local/payment",
            provider="mercadopago",
        )
        
        result = request.to_dict()
        
        assert result["order_id"] == 123
        assert result["amount"] == 100.50
        assert result["callback_url"] == "http://callback.local/payment"
        assert result["provider"] == "mercadopago"

    def test_to_dict_with_optional_none(self):
        """
        Given: PaymentCreateRequest with optional fields as None
        When: to_dict() is called
        Then: Returns dict with None values
        """
        request = PaymentCreateRequest(
            order_id=456,
            amount=50.0,
            callback_url=None,
            provider=None,
        )
        
        result = request.to_dict()
        
        assert result["order_id"] == 456
        assert result["amount"] == 50.0
        assert result["callback_url"] is None
        assert result["provider"] is None

    def test_initialization_with_defaults(self):
        """
        Given: PaymentCreateRequest with only required fields
        When: Initialized
        Then: Optional fields default to None
        """
        request = PaymentCreateRequest(order_id=789, amount=75.25)
        
        assert request.order_id == 789
        assert request.amount == 75.25
        assert request.callback_url is None
        assert request.provider is None


class TestPaymentCreateResponse:
    """Test PaymentCreateResponse DTO."""

    def test_to_dict_with_expires_at(self):
        """
        Given: PaymentCreateResponse with expires_at datetime
        When: to_dict() is called
        Then: expires_at is serialized to ISO format string
        """
        expires_at = datetime(2026, 1, 6, 12, 0, 0, tzinfo=timezone.utc)
        response = PaymentCreateResponse(
            transaction_id="tx-123",
            qr_or_link="https://pay.local/qr/123",
            expires_at=expires_at,
        )
        
        result = response.to_dict()
        
        assert result["transaction_id"] == "tx-123"
        assert result["qr_or_link"] == "https://pay.local/qr/123"
        assert result["expires_at"] == "2026-01-06T12:00:00+00:00"
        assert isinstance(result["expires_at"], str)

    def test_to_dict_with_expires_at_none(self):
        """
        Given: PaymentCreateResponse with expires_at=None
        When: to_dict() is called
        Then: expires_at is None in dict
        """
        response = PaymentCreateResponse(
            transaction_id="tx-456",
            qr_or_link="https://pay.local/qr/456",
            expires_at=None,
        )
        
        result = response.to_dict()
        
        assert result["transaction_id"] == "tx-456"
        assert result["qr_or_link"] == "https://pay.local/qr/456"
        assert result["expires_at"] is None

    def test_to_dict_with_qr_or_link_none(self):
        """
        Given: PaymentCreateResponse with qr_or_link=None
        When: to_dict() is called
        Then: qr_or_link is None in dict
        """
        response = PaymentCreateResponse(
            transaction_id="tx-789",
            qr_or_link=None,
            expires_at=None,
        )
        
        result = response.to_dict()
        
        assert result["transaction_id"] == "tx-789"
        assert result["qr_or_link"] is None

    def test_from_entity_not_implemented(self):
        """
        Given: PaymentCreateResponse class
        When: from_entity() is called
        Then: Raises NotImplementedError
        """
        with pytest.raises(NotImplementedError, match="Not used for this DTO"):
            PaymentCreateResponse.from_entity(None)


class TestPaymentWebhookRequest:
    """Test PaymentWebhookRequest DTO."""

    def test_to_dict_with_all_fields(self):
        """
        Given: PaymentWebhookRequest with all fields
        When: to_dict() is called
        Then: Returns dict with all keys and ISO datetime
        """
        date = datetime(2026, 1, 6, 14, 30, 0, tzinfo=timezone.utc)
        request = PaymentWebhookRequest(
            transaction_id="tx-webhook-123",
            approval_status=True,
            message="Payment approved",
            date=date,
            event_id="event-456",
        )
        
        result = request.to_dict()
        
        assert result["transaction_id"] == "tx-webhook-123"
        assert result["approval_status"] is True
        assert result["message"] == "Payment approved"
        assert result["date"] == "2026-01-06T14:30:00+00:00"
        assert result["event_id"] == "event-456"

    def test_to_dict_with_optional_none(self):
        """
        Given: PaymentWebhookRequest with optional fields as None
        When: to_dict() is called
        Then: Returns dict with None values
        """
        request = PaymentWebhookRequest(
            transaction_id="tx-webhook-456",
            approval_status=False,
            message=None,
            date=None,
            event_id=None,
        )
        
        result = request.to_dict()
        
        assert result["transaction_id"] == "tx-webhook-456"
        assert result["approval_status"] is False
        assert result["message"] is None
        assert result["date"] is None
        assert result["event_id"] is None

    def test_initialization_with_defaults(self):
        """
        Given: PaymentWebhookRequest with only required fields
        When: Initialized
        Then: Optional fields default to None
        """
        request = PaymentWebhookRequest(
            transaction_id="tx-789",
            approval_status=True,
        )
        
        assert request.transaction_id == "tx-789"
        assert request.approval_status is True
        assert request.message is None
        assert request.date is None
        assert request.event_id is None

    def test_approval_status_false(self):
        """
        Given: PaymentWebhookRequest with approval_status=False
        When: Initialized
        Then: approval_status is correctly set to False
        """
        request = PaymentWebhookRequest(
            transaction_id="tx-declined",
            approval_status=False,
            message="Insufficient funds",
        )
        
        assert request.approval_status is False
        assert request.message == "Insufficient funds"


class TestPaymentTransactionStatusResponse:
    """Test PaymentTransactionStatusResponse DTO."""

    def test_to_dict_with_all_fields(self):
        """
        Given: PaymentTransactionStatusResponse with all fields
        When: to_dict() is called
        Then: Returns dict with enum values as strings and ISO datetime
        """
        expires_at = datetime(2026, 1, 6, 15, 0, 0, tzinfo=timezone.utc)
        response = PaymentTransactionStatusResponse(
            transaction_id="tx-status-123",
            order_id=456,
            status=PaymentStatus.APPROVED,
            callback_status=CallbackStatus.DELIVERED,
            qr_or_link="https://pay.local/qr/123",
            expires_at=expires_at,
            last_error="No error",
        )
        
        result = response.to_dict()
        
        assert result["transaction_id"] == "tx-status-123"
        assert result["order_id"] == 456
        assert result["status"] == "APPROVED"
        assert result["callback_status"] == "DELIVERED"
        assert result["qr_or_link"] == "https://pay.local/qr/123"
        assert result["expires_at"] == "2026-01-06T15:00:00+00:00"
        assert result["last_error"] == "No error"

    def test_to_dict_with_optional_none(self):
        """
        Given: PaymentTransactionStatusResponse with optional fields as None
        When: to_dict() is called
        Then: Returns dict with None values
        """
        response = PaymentTransactionStatusResponse(
            transaction_id="tx-status-456",
            order_id=789,
            status=PaymentStatus.PENDING,
            callback_status=CallbackStatus.PENDING,
            qr_or_link=None,
            expires_at=None,
            last_error=None,
        )
        
        result = response.to_dict()
        
        assert result["transaction_id"] == "tx-status-456"
        assert result["order_id"] == 789
        assert result["status"] == "PENDING"
        assert result["callback_status"] == "PENDING"
        assert result["qr_or_link"] is None
        assert result["expires_at"] is None
        assert result["last_error"] is None

    def test_from_entity_complete(self):
        """
        Given: PaymentTransaction entity with all fields
        When: from_entity() is called
        Then: PaymentTransactionStatusResponse is created correctly
        """
        expires_at = datetime(2026, 1, 6, 16, 0, 0, tzinfo=timezone.utc)
        entity = PaymentTransaction(
            id="tx-entity-123",
            order_id=999,
            amount=200.0,
            status=PaymentStatus.DECLINED,
            callback_status=CallbackStatus.FAILED,
            qr_or_link="https://pay.local/qr/999",
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_error="Card expired",
        )
        
        response = PaymentTransactionStatusResponse.from_entity(entity)
        
        assert response.transaction_id == "tx-entity-123"
        assert response.order_id == 999
        assert response.status == PaymentStatus.DECLINED
        assert response.callback_status == CallbackStatus.FAILED
        assert response.qr_or_link == "https://pay.local/qr/999"
        assert response.expires_at == expires_at
        assert response.last_error == "Card expired"

    def test_from_entity_minimal(self):
        """
        Given: PaymentTransaction entity with minimal fields
        When: from_entity() is called
        Then: PaymentTransactionStatusResponse handles None values
        """
        entity = PaymentTransaction(
            id="tx-minimal",
            order_id=100,
            amount=50.0,
            status=PaymentStatus.PENDING,
            callback_status=CallbackStatus.PENDING,
            qr_or_link=None,
            expires_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_error=None,
        )
        
        response = PaymentTransactionStatusResponse.from_entity(entity)
        
        assert response.transaction_id == "tx-minimal"
        assert response.order_id == 100
        assert response.status == PaymentStatus.PENDING
        assert response.callback_status == CallbackStatus.PENDING
        assert response.qr_or_link is None
        assert response.expires_at is None
        assert response.last_error is None

    def test_from_entity_enum_preservation(self):
        """
        Given: PaymentTransaction entity with different status combinations
        When: from_entity() is called
        Then: Enum types are preserved correctly
        """
        entity = PaymentTransaction.new(order_id=555, amount=75.0)
        entity.status = PaymentStatus.EXPIRED
        entity.callback_status = CallbackStatus.FAILED
        
        response = PaymentTransactionStatusResponse.from_entity(entity)
        
        assert isinstance(response.status, PaymentStatus)
        assert response.status == PaymentStatus.EXPIRED
        assert isinstance(response.callback_status, CallbackStatus)
        assert response.callback_status == CallbackStatus.FAILED

    def test_to_dict_serializes_enums_correctly(self):
        """
        Given: PaymentTransactionStatusResponse with enum values
        When: to_dict() is called
        Then: Enums are serialized as string values (not objects)
        """
        response = PaymentTransactionStatusResponse(
            transaction_id="tx-enum-test",
            order_id=300,
            status=PaymentStatus.APPROVED,
            callback_status=CallbackStatus.DELIVERED,
            qr_or_link=None,
            expires_at=None,
            last_error=None,
        )
        
        result = response.to_dict()
        
        assert isinstance(result["status"], str)
        assert result["status"] == "APPROVED"
        assert isinstance(result["callback_status"], str)
        assert result["callback_status"] == "DELIVERED"


class TestDTOsIntegration:
    """Integration tests between DTOs and entities."""

    def test_create_request_to_create_response_flow(self):
        """
        Given: PaymentCreateRequest and newly created PaymentTransaction
        When: Creating PaymentCreateResponse from transaction
        Then: Response contains correct data
        """
        request = PaymentCreateRequest(
            order_id=123,
            amount=100.0,
            callback_url="http://callback.local",
            provider="mercadopago",
        )
        
        # Simulate transaction creation
        transaction = PaymentTransaction.new(
            order_id=request.order_id,
            amount=request.amount,
            provider=request.provider,
            qr_or_link="https://pay.local/tx/123",
            expires_at=datetime.now(timezone.utc),
        )
        
        response = PaymentCreateResponse(
            transaction_id=transaction.id,
            qr_or_link=transaction.qr_or_link,
            expires_at=transaction.expires_at,
        )
        
        assert response.transaction_id == transaction.id
        assert response.qr_or_link == "https://pay.local/tx/123"
        assert response.expires_at == transaction.expires_at

    def test_entity_to_status_response_flow(self):
        """
        Given: PaymentTransaction entity
        When: Converting to PaymentTransactionStatusResponse
        Then: All status information is preserved
        """
        transaction = PaymentTransaction.new(order_id=456, amount=200.0)
        transaction.mark_status(PaymentStatus.APPROVED, provider_tx_id="MP-123")
        transaction.mark_callback(CallbackStatus.DELIVERED)
        
        response = PaymentTransactionStatusResponse.from_entity(transaction)
        result = response.to_dict()
        
        assert result["order_id"] == 456
        assert result["status"] == "APPROVED"
        assert result["callback_status"] == "DELIVERED"
        assert "transaction_id" in result

    def test_webhook_request_processing_simulation(self):
        """
        Given: PaymentWebhookRequest with approval
        When: Processing webhook data
        Then: Data is correctly structured for use case
        """
        webhook_request = PaymentWebhookRequest(
            transaction_id="tx-webhook",
            approval_status=True,
            message="Payment completed",
            date=datetime.now(timezone.utc),
            event_id="event-123",
        )
        
        data = webhook_request.to_dict()
        
        assert data["transaction_id"] == "tx-webhook"
        assert data["approval_status"] is True
        assert data["message"] == "Payment completed"
        assert data["event_id"] == "event-123"
        assert isinstance(data["date"], str)  # Serialized to ISO
