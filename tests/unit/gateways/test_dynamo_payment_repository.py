"""
Unit tests for DynamoPaymentRepository.

Phase 2: Use Cases + Repository
Coverage Target: 85%+
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

from src.adapters.gateways.dynamo_payment_repository import DynamoPaymentRepository
from src.entities.payment_transaction import (
    PaymentTransaction,
    PaymentStatus,
    CallbackStatus,
)


class TestDynamoPaymentRepository:
    """Test DynamoPaymentRepository."""

    @pytest.fixture
    def mock_table(self):
        """Create a mock DynamoDB table."""
        return MagicMock()

    @pytest.fixture
    def mock_payment_config(self):
        """Mock payment_config."""
        with patch("src.adapters.gateways.dynamo_payment_repository.payment_config") as mock_config:
            mock_config.table_name = "test-payment-table"
            mock_config.order_id_index = "order_id-index"
            mock_config.region_name = "us-east-1"
            mock_config.endpoint_url = None
            yield mock_config

    @pytest.fixture
    def repository(self, mock_table, mock_payment_config):
        """Create repository with mocked table."""
        with patch("src.adapters.gateways.dynamo_payment_repository.boto3.resource") as mock_resource:
            mock_session = MagicMock()
            mock_session.Table.return_value = mock_table
            mock_resource.return_value = mock_session
            
            repo = DynamoPaymentRepository()
            repo.table = mock_table
            return repo

    def test_create_pending_success(self, repository, mock_table):
        """
        Given: New PaymentTransaction
        When: create_pending() is called
        Then: put_item() called with ConditionExpression and transaction returned
        """
        transaction = PaymentTransaction.new(order_id=123, amount=100.0)
        
        # Execute
        result = repository.create_pending(transaction)
        
        # Verify
        assert result == transaction
        mock_table.put_item.assert_called_once()
        call_kwargs = mock_table.put_item.call_args[1]
        assert "Item" in call_kwargs
        assert "ConditionExpression" in call_kwargs
        assert call_kwargs["ConditionExpression"] == "attribute_not_exists(id)"

    def test_get_by_order_found(self, repository, mock_table):
        """
        Given: order_id with existing transaction in DynamoDB
        When: get_by_order() is called
        Then: Returns PaymentTransaction from query result
        """
        item_dict = {
            "id": "tx-123",
            "order_id": 123,
            "amount": 100.0,
            "status": "PENDING",
            "created_at": "2026-01-06T10:00:00+00:00",
            "updated_at": "2026-01-06T10:00:00+00:00",
            "callback_status": "PENDING",
        }
        
        mock_table.query.return_value = {"Items": [item_dict]}
        
        # Execute
        result = repository.get_by_order(123)
        
        # Verify
        assert result is not None
        assert result.id == "tx-123"
        assert result.order_id == 123
        assert result.amount == 100.0
        
        # Verify query parameters
        mock_table.query.assert_called_once()
        call_kwargs = mock_table.query.call_args[1]
        assert call_kwargs["IndexName"] == "order_id-index"
        assert call_kwargs["Limit"] == 1
        assert call_kwargs["ScanIndexForward"] is False

    def test_get_by_order_not_found(self, repository, mock_table):
        """
        Given: order_id with no transaction
        When: get_by_order() is called
        Then: Returns None
        """
        mock_table.query.return_value = {"Items": []}
        
        # Execute
        result = repository.get_by_order(999)
        
        # Verify
        assert result is None

    def test_get_by_order_empty_items_key(self, repository, mock_table):
        """
        Given: DynamoDB response without Items key
        When: get_by_order() is called
        Then: Returns None
        """
        mock_table.query.return_value = {}
        
        # Execute
        result = repository.get_by_order(456)
        
        # Verify
        assert result is None

    def test_get_by_order_client_error(self, repository, mock_table):
        """
        Given: DynamoDB query raises ClientError
        When: get_by_order() is called
        Then: Exception caught and returns None
        """
        mock_table.query.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Table not found"}},
            "Query"
        )
        
        # Execute
        result = repository.get_by_order(789)
        
        # Verify
        assert result is None

    def test_get_by_id_found(self, repository, mock_table):
        """
        Given: transaction_id exists in DynamoDB
        When: get_by_id() is called
        Then: Returns PaymentTransaction
        """
        item_dict = {
            "id": "tx-456",
            "order_id": 456,
            "amount": 50.0,
            "status": "APPROVED",
            "created_at": "2026-01-06T11:00:00+00:00",
            "updated_at": "2026-01-06T11:30:00+00:00",
            "callback_status": "DELIVERED",
        }
        
        mock_table.get_item.return_value = {"Item": item_dict}
        
        # Execute
        result = repository.get_by_id("tx-456")
        
        # Verify
        assert result is not None
        assert result.id == "tx-456"
        assert result.status == PaymentStatus.APPROVED
        
        mock_table.get_item.assert_called_once_with(Key={"id": "tx-456"})

    def test_get_by_id_not_found(self, repository, mock_table):
        """
        Given: transaction_id does not exist
        When: get_by_id() is called
        Then: Returns None
        """
        mock_table.get_item.return_value = {}
        
        # Execute
        result = repository.get_by_id("tx-999")
        
        # Verify
        assert result is None

    def test_update_status_success(self, repository, mock_table):
        """
        Given: Valid transaction_id and new status
        When: update_status() is called
        Then: UpdateExpression executed and updated transaction returned
        """
        updated_item = {
            "id": "tx-789",
            "order_id": 789,
            "amount": 75.0,
            "status": "DECLINED",
            "provider_tx_id": "MP-789",
            "last_error": "Card declined",
            "created_at": "2026-01-06T10:00:00+00:00",
            "updated_at": "2026-01-06T12:00:00+00:00",
            "callback_status": "PENDING",
        }
        
        mock_table.get_item.return_value = {"Item": updated_item}
        
        # Execute
        result = repository.update_status(
            transaction_id="tx-789",
            status=PaymentStatus.DECLINED,
            provider_tx_id="MP-789",
            error="Card declined",
        )
        
        # Verify
        assert result is not None
        assert result.status == PaymentStatus.DECLINED
        assert result.provider_tx_id == "MP-789"
        
        # Verify update_item called
        mock_table.update_item.assert_called_once()
        call_kwargs = mock_table.update_item.call_args[1]
        assert call_kwargs["Key"] == {"id": "tx-789"}
        assert "UpdateExpression" in call_kwargs
        assert "ExpressionAttributeValues" in call_kwargs

    def test_update_status_without_provider_tx_id(self, repository, mock_table):
        """
        Given: update_status() called without provider_tx_id
        When: Executed
        Then: Uses transaction_id as fallback for provider_tx_id
        """
        updated_item = {
            "id": "tx-100",
            "order_id": 100,
            "amount": 25.0,
            "status": "APPROVED",
            "created_at": "2026-01-06T10:00:00+00:00",
            "updated_at": "2026-01-06T13:00:00+00:00",
            "callback_status": "PENDING",
        }
        
        mock_table.get_item.return_value = {"Item": updated_item}
        
        # Execute
        repository.update_status(
            transaction_id="tx-100",
            status=PaymentStatus.APPROVED,
        )
        
        # Verify provider_tx_id defaults to transaction_id
        call_kwargs = mock_table.update_item.call_args[1]
        attr_values = call_kwargs["ExpressionAttributeValues"]
        assert attr_values[":p"] == "tx-100"

    def test_update_status_client_error(self, repository, mock_table):
        """
        Given: DynamoDB update_item raises ClientError
        When: update_status() is called
        Then: Returns None
        """
        mock_table.update_item.side_effect = ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException", "Message": "Item not found"}},
            "UpdateItem"
        )
        
        # Execute
        result = repository.update_status(
            transaction_id="tx-error",
            status=PaymentStatus.APPROVED,
        )
        
        # Verify
        assert result is None

    def test_update_callback_status_success(self, repository, mock_table):
        """
        Given: Valid transaction_id and callback status
        When: update_callback_status() is called
        Then: Callback status updated in DynamoDB
        """
        updated_item = {
            "id": "tx-callback",
            "order_id": 200,
            "amount": 150.0,
            "status": "APPROVED",
            "callback_status": "DELIVERED",
            "last_callback_error": "",
            "created_at": "2026-01-06T10:00:00+00:00",
            "updated_at": "2026-01-06T14:00:00+00:00",
        }
        
        mock_table.get_item.return_value = {"Item": updated_item}
        
        # Execute
        result = repository.update_callback_status(
            transaction_id="tx-callback",
            status=CallbackStatus.DELIVERED,
        )
        
        # Verify
        assert result is not None
        assert result.callback_status == CallbackStatus.DELIVERED
        
        mock_table.update_item.assert_called_once()
        call_kwargs = mock_table.update_item.call_args[1]
        assert call_kwargs["UpdateExpression"] == "SET callback_status = :c, last_callback_error = :e, updated_at = :u"

    def test_update_callback_status_with_error(self, repository, mock_table):
        """
        Given: Callback failed with error message
        When: update_callback_status() is called with error
        Then: Error message stored in last_callback_error
        """
        updated_item = {
            "id": "tx-failed",
            "order_id": 300,
            "amount": 200.0,
            "status": "APPROVED",
            "callback_status": "FAILED",
            "last_callback_error": "Connection timeout",
            "created_at": "2026-01-06T10:00:00+00:00",
            "updated_at": "2026-01-06T15:00:00+00:00",
        }
        
        mock_table.get_item.return_value = {"Item": updated_item}
        
        # Execute
        result = repository.update_callback_status(
            transaction_id="tx-failed",
            status=CallbackStatus.FAILED,
            error="Connection timeout",
        )
        
        # Verify
        assert result is not None
        assert result.callback_status == CallbackStatus.FAILED
        assert result.last_callback_error == "Connection timeout"

    def test_update_callback_status_client_error(self, repository, mock_table):
        """
        Given: DynamoDB update_item raises ClientError
        When: update_callback_status() is called
        Then: Returns None
        """
        mock_table.update_item.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException"}},
            "UpdateItem"
        )
        
        # Execute
        result = repository.update_callback_status(
            transaction_id="tx-error",
            status=CallbackStatus.FAILED,
        )
        
        # Verify
        assert result is None

    def test_upsert_not_exists_creates_new(self, repository, mock_table):
        """
        Given: order_id with no existing transaction
        When: upsert_by_order_if_pending() is called
        Then: New transaction created, returns (transaction, True)
        """
        transaction = PaymentTransaction.new(order_id=400, amount=250.0)
        
        # Mock: get_by_order returns None (doesn't exist)
        with patch.object(repository, 'get_by_order', return_value=None):
            with patch.object(repository, 'create_pending', return_value=transaction):
                # Execute
                result_tx, created = repository.upsert_by_order_if_pending(transaction)
                
                # Verify
                assert created is True
                assert result_tx == transaction
                repository.create_pending.assert_called_once_with(transaction)

    def test_upsert_pending_exists_returns_existing(self, repository, mock_table):
        """
        Given: order_id with existing PENDING transaction
        When: upsert_by_order_if_pending() is called
        Then: Returns existing transaction, created=False
        """
        existing_transaction = PaymentTransaction(
            id="tx-existing",
            order_id=500,
            amount=100.0,
            status=PaymentStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        new_transaction = PaymentTransaction.new(order_id=500, amount=100.0)
        
        # Mock: get_by_order returns existing PENDING
        with patch.object(repository, 'get_by_order', return_value=existing_transaction):
            with patch.object(repository, 'create_pending') as mock_create:
                # Execute
                result_tx, created = repository.upsert_by_order_if_pending(new_transaction)
                
                # Verify
                assert created is False
                assert result_tx == existing_transaction
                mock_create.assert_not_called()

    def test_upsert_approved_exists_returns_existing(self, repository, mock_table):
        """
        Given: order_id with existing APPROVED transaction
        When: upsert_by_order_if_pending() is called
        Then: Returns existing transaction, created=False, does not create new
        """
        existing_transaction = PaymentTransaction(
            id="tx-approved",
            order_id=600,
            amount=150.0,
            status=PaymentStatus.APPROVED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        new_transaction = PaymentTransaction.new(order_id=600, amount=150.0)
        
        # Mock: get_by_order returns existing APPROVED
        with patch.object(repository, 'get_by_order', return_value=existing_transaction):
            with patch.object(repository, 'create_pending') as mock_create:
                # Execute
                result_tx, created = repository.upsert_by_order_if_pending(new_transaction)
                
                # Verify
                assert created is False
                assert result_tx == existing_transaction
                mock_create.assert_not_called()

    def test_upsert_declined_exists_returns_existing(self, repository, mock_table):
        """
        Given: order_id with existing DECLINED transaction
        When: upsert_by_order_if_pending() is called
        Then: Returns existing, does not create new
        """
        existing_transaction = PaymentTransaction(
            id="tx-declined",
            order_id=700,
            amount=200.0,
            status=PaymentStatus.DECLINED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        new_transaction = PaymentTransaction.new(order_id=700, amount=200.0)
        
        with patch.object(repository, 'get_by_order', return_value=existing_transaction):
            with patch.object(repository, 'create_pending') as mock_create:
                # Execute
                result_tx, created = repository.upsert_by_order_if_pending(new_transaction)
                
                # Verify
                assert created is False
                assert result_tx == existing_transaction
                mock_create.assert_not_called()

    def test_repository_initialization_with_custom_table_name(self, mock_payment_config):
        """
        Given: DynamoPaymentRepository initialized with custom table_name
        When: Repository created
        Then: boto3 resource created with correct parameters
        """
        with patch("src.adapters.gateways.dynamo_payment_repository.boto3.resource") as mock_resource:
            mock_session = MagicMock()
            mock_resource.return_value = mock_session
            
            # Execute
            repo = DynamoPaymentRepository(table_name="custom-table")
            
            # Verify
            assert repo.table_name == "custom-table"
            mock_resource.assert_called_once_with(
                "dynamodb",
                region_name="us-east-1",
                endpoint_url=None,
            )

    def test_repository_initialization_with_config_defaults(self, mock_payment_config):
        """
        Given: DynamoPaymentRepository initialized without parameters
        When: Repository created
        Then: Uses payment_config defaults
        """
        with patch("src.adapters.gateways.dynamo_payment_repository.boto3.resource") as mock_resource:
            mock_session = MagicMock()
            mock_resource.return_value = mock_session
            
            # Execute
            repo = DynamoPaymentRepository()
            
            # Verify
            assert repo.table_name == "test-payment-table"
