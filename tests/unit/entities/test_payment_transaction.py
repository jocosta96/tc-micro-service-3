"""
Unit tests for PaymentTransaction entity.

Phase 1: Entities + DTOs
Coverage Target: 95%+
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from uuid import UUID

from src.entities.payment_transaction import (
    PaymentTransaction,
    PaymentStatus,
    CallbackStatus,
)


class TestPaymentStatus:
    """Test PaymentStatus enum."""

    def test_payment_status_enum_values(self):
        """Test all PaymentStatus enum values."""
        assert PaymentStatus.PENDING == "PENDING"
        assert PaymentStatus.APPROVED == "APPROVED"
        assert PaymentStatus.DECLINED == "DECLINED"
        assert PaymentStatus.EXPIRED == "EXPIRED"

    def test_payment_status_enum_members(self):
        """Test PaymentStatus has all expected members."""
        assert len(PaymentStatus) == 4
        assert "PENDING" in PaymentStatus.__members__
        assert "APPROVED" in PaymentStatus.__members__
        assert "DECLINED" in PaymentStatus.__members__
        assert "EXPIRED" in PaymentStatus.__members__


class TestCallbackStatus:
    """Test CallbackStatus enum."""

    def test_callback_status_enum_values(self):
        """Test all CallbackStatus enum values."""
        assert CallbackStatus.PENDING == "PENDING"
        assert CallbackStatus.DELIVERED == "DELIVERED"
        assert CallbackStatus.FAILED == "FAILED"

    def test_callback_status_enum_members(self):
        """Test CallbackStatus has all expected members."""
        assert len(CallbackStatus) == 3
        assert "PENDING" in CallbackStatus.__members__
        assert "DELIVERED" in CallbackStatus.__members__
        assert "FAILED" in CallbackStatus.__members__


class TestPaymentTransactionNew:
    """Test PaymentTransaction.new() factory method."""

    @patch("src.entities.payment_transaction.uuid4")
    def test_new_with_minimal_fields(self, mock_uuid):
        """
        Given: order_id and amount
        When: PaymentTransaction.new() is called with minimal fields
        Then: Transaction is created with defaults
        """
        # Create a mock that returns the expected string when str() is called
        class MockUUID:
            def __str__(self):
                return "test-uuid-1234"
        
        mock_uuid.return_value = MockUUID()
        
        transaction = PaymentTransaction.new(order_id=123, amount=100.50)
        
        assert transaction.id == "test-uuid-1234"
        assert transaction.order_id == 123
        assert transaction.amount == 100.50
        assert transaction.status == PaymentStatus.PENDING
        assert transaction.callback_status == CallbackStatus.PENDING
        assert transaction.provider is None
        assert transaction.qr_or_link is None
        assert transaction.expires_at is None
        assert transaction.provider_tx_id is None
        assert transaction.last_error is None
        assert transaction.last_callback_error is None
        assert transaction.metadata == {}
        assert isinstance(transaction.created_at, datetime)
        assert isinstance(transaction.updated_at, datetime)

    @patch("src.entities.payment_transaction.uuid4")
    def test_new_with_all_fields(self, mock_uuid):
        """
        Given: All optional fields provided
        When: PaymentTransaction.new() is called
        Then: Transaction is created with all fields populated
        """
        # Create a mock that returns the expected string when str() is called
        class MockUUID:
            def __str__(self):
                return "test-uuid-5678"
        
        mock_uuid.return_value = MockUUID()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        transaction = PaymentTransaction.new(
            order_id=456,
            amount=250.75,
            provider="mercadopago",
            qr_or_link="https://pay.local/tx/456",
            expires_at=expires_at,
        )
        
        assert transaction.id == "test-uuid-5678"
        assert transaction.order_id == 456
        assert transaction.amount == 250.75
        assert transaction.provider == "mercadopago"
        assert transaction.qr_or_link == "https://pay.local/tx/456"
        assert transaction.expires_at == expires_at
        assert transaction.status == PaymentStatus.PENDING

    def test_new_generates_unique_id(self):
        """
        Given: Multiple calls to PaymentTransaction.new()
        When: Called without mocking uuid
        Then: Each transaction gets a unique UUID
        """
        tx1 = PaymentTransaction.new(order_id=1, amount=10.0)
        tx2 = PaymentTransaction.new(order_id=2, amount=20.0)
        
        assert tx1.id != tx2.id
        # Validate UUIDs are valid
        UUID(tx1.id)  # Will raise ValueError if invalid
        UUID(tx2.id)


class TestPaymentTransactionMarkStatus:
    """Test PaymentTransaction.mark_status() method."""

    def test_mark_status_approved_with_provider_tx_id(self):
        """
        Given: Transaction in PENDING status
        When: mark_status(APPROVED) with provider_tx_id
        Then: Status updated, provider_tx_id set, updated_at changed
        """
        transaction = PaymentTransaction.new(order_id=123, amount=100.0)
        original_updated_at = transaction.updated_at
        
        # Small delay to ensure updated_at changes
        import time
        time.sleep(0.01)
        
        transaction.mark_status(
            status=PaymentStatus.APPROVED,
            provider_tx_id="MP-123456",
        )
        
        assert transaction.status == PaymentStatus.APPROVED
        assert transaction.provider_tx_id == "MP-123456"
        assert transaction.last_error is None
        assert transaction.updated_at > original_updated_at

    def test_mark_status_declined_with_error(self):
        """
        Given: Transaction in PENDING status
        When: mark_status(DECLINED) with error message
        Then: Status updated, error recorded, updated_at changed
        """
        transaction = PaymentTransaction.new(order_id=456, amount=50.0)
        
        transaction.mark_status(
            status=PaymentStatus.DECLINED,
            error="Cartão recusado por falta de fundos",
        )
        
        assert transaction.status == PaymentStatus.DECLINED
        assert transaction.last_error == "Cartão recusado por falta de fundos"
        assert isinstance(transaction.updated_at, datetime)

    def test_mark_status_keeps_existing_provider_tx_id(self):
        """
        Given: Transaction with existing provider_tx_id
        When: mark_status() called without new provider_tx_id
        Then: Existing provider_tx_id is preserved
        """
        transaction = PaymentTransaction.new(order_id=789, amount=75.0)
        transaction.provider_tx_id = "EXISTING-TX-999"
        
        transaction.mark_status(status=PaymentStatus.EXPIRED)
        
        assert transaction.status == PaymentStatus.EXPIRED
        assert transaction.provider_tx_id == "EXISTING-TX-999"

    def test_mark_status_overwrites_provider_tx_id(self):
        """
        Given: Transaction with existing provider_tx_id
        When: mark_status() called with new provider_tx_id
        Then: provider_tx_id is overwritten
        """
        transaction = PaymentTransaction.new(order_id=100, amount=25.0)
        transaction.provider_tx_id = "OLD-TX-123"
        
        transaction.mark_status(
            status=PaymentStatus.APPROVED,
            provider_tx_id="NEW-TX-456",
        )
        
        assert transaction.provider_tx_id == "NEW-TX-456"


class TestPaymentTransactionMarkCallback:
    """Test PaymentTransaction.mark_callback() method."""

    def test_mark_callback_delivered_success(self):
        """
        Given: Transaction with callback_status=PENDING
        When: mark_callback(DELIVERED) is called
        Then: callback_status updated, no error, updated_at changed
        """
        transaction = PaymentTransaction.new(order_id=123, amount=100.0)
        original_updated_at = transaction.updated_at
        
        import time
        time.sleep(0.01)
        
        transaction.mark_callback(status=CallbackStatus.DELIVERED)
        
        assert transaction.callback_status == CallbackStatus.DELIVERED
        assert transaction.last_callback_error is None
        assert transaction.updated_at > original_updated_at

    def test_mark_callback_failed_with_error(self):
        """
        Given: Transaction exists
        When: mark_callback(FAILED) with error message
        Then: callback_status=FAILED, error recorded
        """
        transaction = PaymentTransaction.new(order_id=456, amount=50.0)
        
        transaction.mark_callback(
            status=CallbackStatus.FAILED,
            error="Connection timeout after 30s",
        )
        
        assert transaction.callback_status == CallbackStatus.FAILED
        assert transaction.last_callback_error == "Connection timeout after 30s"
        assert isinstance(transaction.updated_at, datetime)

    def test_mark_callback_clears_previous_error(self):
        """
        Given: Transaction with previous callback error
        When: mark_callback(DELIVERED) without error
        Then: last_callback_error is cleared to None
        """
        transaction = PaymentTransaction.new(order_id=789, amount=75.0)
        transaction.last_callback_error = "Previous error"
        
        transaction.mark_callback(status=CallbackStatus.DELIVERED)
        
        assert transaction.callback_status == CallbackStatus.DELIVERED
        assert transaction.last_callback_error is None


class TestPaymentTransactionToItem:
    """Test PaymentTransaction.to_item() serialization."""

    def test_to_item_with_all_fields(self):
        """
        Given: Transaction with all fields populated
        When: to_item() is called
        Then: Dict contains all fields with correct serialization
        """
        expires_at = datetime(2026, 1, 6, 12, 0, 0, tzinfo=timezone.utc)
        created_at = datetime(2026, 1, 6, 10, 0, 0, tzinfo=timezone.utc)
        updated_at = datetime(2026, 1, 6, 11, 0, 0, tzinfo=timezone.utc)
        
        transaction = PaymentTransaction(
            id="tx-123",
            order_id=456,
            amount=100.50,
            status=PaymentStatus.APPROVED,
            provider="mercadopago",
            provider_tx_id="MP-789",
            qr_or_link="https://pay.local/qr/123",
            expires_at=expires_at,
            created_at=created_at,
            updated_at=updated_at,
            last_error="Some error",
            metadata={"callback_url": "http://callback.local"},
            callback_status=CallbackStatus.DELIVERED,
            last_callback_error="Callback error",
        )
        
        item = transaction.to_item()
        
        assert item["id"] == "tx-123"
        assert item["order_id"] == 456
        assert item["amount"] == 100.50
        assert item["status"] == "APPROVED"
        assert item["provider"] == "mercadopago"
        assert item["provider_tx_id"] == "MP-789"
        assert item["qr_or_link"] == "https://pay.local/qr/123"
        assert item["expires_at"] == "2026-01-06T12:00:00+00:00"
        assert item["created_at"] == "2026-01-06T10:00:00+00:00"
        assert item["updated_at"] == "2026-01-06T11:00:00+00:00"
        assert item["last_error"] == "Some error"
        assert item["metadata"] == {"callback_url": "http://callback.local"}
        assert item["callback_status"] == "DELIVERED"
        assert item["last_callback_error"] == "Callback error"

    def test_to_item_with_optional_fields_none(self):
        """
        Given: Transaction with optional fields as None
        When: to_item() is called
        Then: Dict does NOT contain keys for None fields
        """
        transaction = PaymentTransaction(
            id="tx-456",
            order_id=789,
            amount=50.0,
            status=PaymentStatus.PENDING,
            provider=None,
            provider_tx_id=None,
            qr_or_link=None,
            expires_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_error=None,
            metadata={},
            callback_status=CallbackStatus.PENDING,
            last_callback_error=None,
        )
        
        item = transaction.to_item()
        
        # Required fields present
        assert "id" in item
        assert "order_id" in item
        assert "amount" in item
        assert "status" in item
        assert "created_at" in item
        assert "updated_at" in item
        assert "metadata" in item
        assert "callback_status" in item
        
        # Optional None fields should NOT be in item
        assert "provider" not in item
        assert "provider_tx_id" not in item
        assert "qr_or_link" not in item
        assert "expires_at" not in item
        assert "last_error" not in item
        assert "last_callback_error" not in item

    def test_to_item_enum_values_serialized_as_strings(self):
        """
        Given: Transaction with enum status values
        When: to_item() is called
        Then: Enums are serialized as string values
        """
        transaction = PaymentTransaction.new(order_id=123, amount=100.0)
        
        item = transaction.to_item()
        
        assert isinstance(item["status"], str)
        assert item["status"] == "PENDING"
        assert isinstance(item["callback_status"], str)
        assert item["callback_status"] == "PENDING"


class TestPaymentTransactionFromItem:
    """Test PaymentTransaction.from_item() deserialization."""

    def test_from_item_complete(self):
        """
        Given: DynamoDB item dict with all fields
        When: from_item() is called
        Then: PaymentTransaction entity is reconstructed correctly
        """
        item = {
            "id": "tx-123",
            "order_id": 456,
            "amount": 100.50,
            "status": "APPROVED",
            "provider": "mercadopago",
            "provider_tx_id": "MP-789",
            "qr_or_link": "https://pay.local/qr/123",
            "expires_at": "2026-01-06T12:00:00+00:00",
            "created_at": "2026-01-06T10:00:00+00:00",
            "updated_at": "2026-01-06T11:00:00+00:00",
            "last_error": "Some error",
            "metadata": {"callback_url": "http://callback.local"},
            "callback_status": "DELIVERED",
            "last_callback_error": "Callback error",
        }
        
        transaction = PaymentTransaction.from_item(item)
        
        assert transaction.id == "tx-123"
        assert transaction.order_id == 456
        assert transaction.amount == 100.50
        assert transaction.status == PaymentStatus.APPROVED
        assert transaction.provider == "mercadopago"
        assert transaction.provider_tx_id == "MP-789"
        assert transaction.qr_or_link == "https://pay.local/qr/123"
        assert transaction.expires_at == datetime(2026, 1, 6, 12, 0, 0, tzinfo=timezone.utc)
        assert transaction.created_at == datetime(2026, 1, 6, 10, 0, 0, tzinfo=timezone.utc)
        assert transaction.updated_at == datetime(2026, 1, 6, 11, 0, 0, tzinfo=timezone.utc)
        assert transaction.last_error == "Some error"
        assert transaction.metadata == {"callback_url": "http://callback.local"}
        assert transaction.callback_status == CallbackStatus.DELIVERED
        assert transaction.last_callback_error == "Callback error"

    def test_from_item_minimal(self):
        """
        Given: DynamoDB item with only required fields
        When: from_item() is called
        Then: Optional fields are None, defaults applied
        """
        item = {
            "id": "tx-456",
            "order_id": 789,
            "amount": 50.0,
            "created_at": "2026-01-06T10:00:00+00:00",
            "updated_at": "2026-01-06T10:00:00+00:00",
        }
        
        transaction = PaymentTransaction.from_item(item)
        
        assert transaction.id == "tx-456"
        assert transaction.order_id == 789
        assert transaction.amount == 50.0
        assert transaction.status == PaymentStatus.PENDING  # default
        assert transaction.callback_status == CallbackStatus.PENDING  # default
        assert transaction.provider is None
        assert transaction.provider_tx_id is None
        assert transaction.qr_or_link is None
        assert transaction.expires_at is None
        assert transaction.last_error is None
        assert transaction.metadata == {}  # default empty dict
        assert transaction.last_callback_error is None

    def test_from_item_with_missing_metadata(self):
        """
        Given: Item with metadata field missing or None
        When: from_item() is called
        Then: metadata defaults to empty dict
        """
        item = {
            "id": "tx-789",
            "order_id": 100,
            "amount": 25.0,
            "status": "PENDING",
            "created_at": "2026-01-06T10:00:00+00:00",
            "updated_at": "2026-01-06T10:00:00+00:00",
            "metadata": None,
        }
        
        transaction = PaymentTransaction.from_item(item)
        
        assert transaction.metadata == {}

    def test_from_item_iso_datetime_parsing(self):
        """
        Given: Item with ISO datetime strings
        When: from_item() is called
        Then: Datetimes are correctly parsed with timezone
        """
        item = {
            "id": "tx-999",
            "order_id": 200,
            "amount": 150.0,
            "created_at": "2026-01-06T14:30:45.123456+00:00",
            "updated_at": "2026-01-06T15:45:30.654321+00:00",
            "expires_at": "2026-01-06T16:00:00+00:00",
        }
        
        transaction = PaymentTransaction.from_item(item)
        
        assert transaction.created_at.year == 2026
        assert transaction.created_at.month == 1
        assert transaction.created_at.day == 6
        assert transaction.created_at.tzinfo == timezone.utc
        assert transaction.expires_at.hour == 16

    def test_from_item_without_timestamps(self):
        """
        Given: Item missing created_at or updated_at
        When: from_item() is called
        Then: Defaults to current UTC time
        """
        item = {
            "id": "tx-no-time",
            "order_id": 300,
            "amount": 200.0,
        }
        
        before = datetime.now(timezone.utc)
        transaction = PaymentTransaction.from_item(item)
        after = datetime.now(timezone.utc)
        
        assert before <= transaction.created_at <= after
        assert before <= transaction.updated_at <= after


class TestPaymentTransactionRoundTrip:
    """Test serialization round-trip (to_item -> from_item)."""

    def test_round_trip_preserves_all_data(self):
        """
        Given: Original transaction entity
        When: Serialized to_item() then deserialized from_item()
        Then: All data is preserved exactly
        """
        original = PaymentTransaction(
            id="tx-round-trip",
            order_id=999,
            amount=123.45,
            status=PaymentStatus.DECLINED,
            provider="stripe",
            provider_tx_id="STRIPE-999",
            qr_or_link="https://stripe.com/pay",
            expires_at=datetime(2026, 1, 7, 10, 0, 0, tzinfo=timezone.utc),
            created_at=datetime(2026, 1, 6, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 6, 12, 0, 0, tzinfo=timezone.utc),
            last_error="Card declined",
            metadata={"user_id": "user-123", "ip": "192.168.1.1"},
            callback_status=CallbackStatus.FAILED,
            last_callback_error="HTTP 500",
        )
        
        # Serialize
        item = original.to_item()
        
        # Deserialize
        restored = PaymentTransaction.from_item(item)
        
        # Verify all fields match
        assert restored.id == original.id
        assert restored.order_id == original.order_id
        assert restored.amount == original.amount
        assert restored.status == original.status
        assert restored.provider == original.provider
        assert restored.provider_tx_id == original.provider_tx_id
        assert restored.qr_or_link == original.qr_or_link
        assert restored.expires_at == original.expires_at
        assert restored.created_at == original.created_at
        assert restored.updated_at == original.updated_at
        assert restored.last_error == original.last_error
        assert restored.metadata == original.metadata
        assert restored.callback_status == original.callback_status
        assert restored.last_callback_error == original.last_callback_error
