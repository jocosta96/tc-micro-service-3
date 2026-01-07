"""
Unit tests for PaymentCallbackUseCase (async).

Phase 2: Use Cases + Repository
Coverage Target: 90%+
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
import base64

from src.application.use_cases.payment_use_cases import PaymentCallbackUseCase
from src.entities.payment_transaction import (
    PaymentTransaction,
    PaymentStatus,
    CallbackStatus,
)


@pytest.mark.asyncio
class TestPaymentCallbackUseCase:
    """Test PaymentCallbackUseCase (async tests)."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock payment repository."""
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_repository):
        """Create PaymentCallbackUseCase with mock repository."""
        return PaymentCallbackUseCase(mock_repository)

    @pytest.fixture
    def mock_payment_config(self):
        """Mock payment_config module."""
        with patch("src.application.use_cases.payment_use_cases.payment_config") as mock_config:
            mock_config.order_api_host = "http://order-service:8000"
            mock_config.order_api_user = ""
            mock_config.order_api_password = ""
            mock_config.callback_timeout_seconds = 10
            yield mock_config

    async def test_execute_with_callback_url_in_metadata(self, use_case, mock_repository, mock_payment_config):
        """
        Given: Transaction with callback_url in metadata
        When: execute() is called
        Then: POST to callback_url from metadata
        """
        transaction = PaymentTransaction(
            id="tx-123",
            order_id=123,
            amount=100.0,
            status=PaymentStatus.APPROVED,
            callback_status=CallbackStatus.PENDING,
            metadata={"callback_url": "http://custom-callback:8000/webhook"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_error=None,
        )
        
        with patch("src.application.use_cases.payment_use_cases.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            # Execute
            await use_case.execute(transaction)
            
            # Verify POST called with metadata callback_url
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://custom-callback:8000/webhook"
            
            # Verify payload
            payload = call_args[1]["json"]
            assert payload["transaction_id"] == "tx-123"
            assert payload["approval_status"] is True
            assert "date" in payload
            assert payload["message"] == ""
            
            # Verify callback status updated to DELIVERED
            mock_repository.update_callback_status.assert_called_once_with(
                "tx-123", CallbackStatus.DELIVERED, None
            )

    async def test_execute_with_default_callback_url(self, use_case, mock_repository, mock_payment_config):
        """
        Given: Transaction without callback_url in metadata
        When: execute() is called
        Then: POST to default order_api_host URL
        """
        transaction = PaymentTransaction(
            id="tx-456",
            order_id=456,
            amount=50.0,
            status=PaymentStatus.DECLINED,
            callback_status=CallbackStatus.PENDING,
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_error="Card declined",
        )
        
        with patch("src.application.use_cases.payment_use_cases.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            # Execute
            await use_case.execute(transaction)
            
            # Verify default URL used
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://order-service:8000/order/payment_confirm/456"
            
            # Verify payload has declined status
            payload = call_args[1]["json"]
            assert payload["approval_status"] is False
            assert payload["message"] == "Card declined"

    async def test_execute_with_metadata_none(self, use_case, mock_repository, mock_payment_config):
        """
        Given: Transaction with metadata=None
        When: execute() is called
        Then: Uses default callback_url
        """
        transaction = PaymentTransaction(
            id="tx-no-meta",
            order_id=789,
            amount=75.0,
            status=PaymentStatus.APPROVED,
            callback_status=CallbackStatus.PENDING,
            metadata=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        with patch("src.application.use_cases.payment_use_cases.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            # Execute
            await use_case.execute(transaction)
            
            # Verify default URL
            call_url = mock_client.post.call_args[0][0]
            assert "order-service:8000/order/payment_confirm/789" in call_url

    async def test_execute_with_basic_auth(self, use_case, mock_repository, mock_payment_config):
        """
        Given: payment_config has order_api_user and order_api_password
        When: execute() is called
        Then: Authorization header with Basic Auth is sent
        """
        mock_payment_config.order_api_user = "admin"
        mock_payment_config.order_api_password = "secret123"
        
        transaction = PaymentTransaction.new(order_id=100, amount=25.0)
        transaction.id = "tx-auth"
        transaction.status = PaymentStatus.APPROVED
        
        with patch("src.application.use_cases.payment_use_cases.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            # Execute
            await use_case.execute(transaction)
            
            # Verify Authorization header
            headers = mock_client.post.call_args[1]["headers"]
            expected_token = base64.b64encode(b"admin:secret123").decode()
            assert headers["Authorization"] == f"Basic {expected_token}"

    async def test_execute_without_auth_credentials(self, use_case, mock_repository, mock_payment_config):
        """
        Given: payment_config has empty user/password
        When: execute() is called
        Then: No Authorization header is sent
        """
        mock_payment_config.order_api_user = ""
        mock_payment_config.order_api_password = ""
        
        transaction = PaymentTransaction.new(order_id=200, amount=50.0)
        transaction.id = "tx-no-auth"
        
        with patch("src.application.use_cases.payment_use_cases.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            # Execute
            await use_case.execute(transaction)
            
            # Verify no Authorization header
            headers = mock_client.post.call_args[1]["headers"]
            assert "Authorization" not in headers or headers == {}

    async def test_execute_success_http_200(self, use_case, mock_repository, mock_payment_config):
        """
        Given: HTTP response status code 200
        When: execute() is called
        Then: Callback status updated to DELIVERED with no error
        """
        transaction = PaymentTransaction.new(order_id=300, amount=100.0)
        transaction.id = "tx-200"
        
        with patch("src.application.use_cases.payment_use_cases.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            # Execute
            await use_case.execute(transaction)
            
            # Verify DELIVERED status
            mock_repository.update_callback_status.assert_called_once_with(
                "tx-200", CallbackStatus.DELIVERED, None
            )

    async def test_execute_success_http_201(self, use_case, mock_repository, mock_payment_config):
        """
        Given: HTTP response status code 201
        When: execute() is called
        Then: Callback status updated to DELIVERED
        """
        transaction = PaymentTransaction.new(order_id=400, amount=150.0)
        transaction.id = "tx-201"
        
        with patch("src.application.use_cases.payment_use_cases.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            # Execute
            await use_case.execute(transaction)
            
            # Verify DELIVERED
            mock_repository.update_callback_status.assert_called_once_with(
                "tx-201", CallbackStatus.DELIVERED, None
            )

    async def test_execute_failure_http_400(self, use_case, mock_repository, mock_payment_config):
        """
        Given: HTTP response status code 400
        When: execute() is called
        Then: HTTPStatusError raised and callback status updated to FAILED
        """
        transaction = PaymentTransaction.new(order_id=500, amount=200.0)
        transaction.id = "tx-400"
        
        with patch("src.application.use_cases.payment_use_cases.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.request = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            # Execute
            await use_case.execute(transaction)
            
            # Verify FAILED status with error message
            call_args = mock_repository.update_callback_status.call_args
            assert call_args[0][0] == "tx-400"
            assert call_args[0][1] == CallbackStatus.FAILED
            assert "Callback failed" in call_args[0][2]

    async def test_execute_failure_http_500(self, use_case, mock_repository, mock_payment_config):
        """
        Given: HTTP response status code 500
        When: execute() is called
        Then: Callback status updated to FAILED
        """
        transaction = PaymentTransaction.new(order_id=600, amount=250.0)
        transaction.id = "tx-500"
        
        with patch("src.application.use_cases.payment_use_cases.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.request = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            # Execute
            await use_case.execute(transaction)
            
            # Verify FAILED
            call_args = mock_repository.update_callback_status.call_args
            assert call_args[0][1] == CallbackStatus.FAILED

    async def test_execute_payload_structure(self, use_case, mock_repository, mock_payment_config):
        """
        Given: Transaction with specific data
        When: execute() is called
        Then: Payload has correct structure and fields
        """
        transaction = PaymentTransaction(
            id="tx-payload",
            order_id=700,
            amount=300.0,
            status=PaymentStatus.APPROVED,
            callback_status=CallbackStatus.PENDING,
            last_error="",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        with patch("src.application.use_cases.payment_use_cases.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            # Execute
            await use_case.execute(transaction)
            
            # Verify payload structure
            payload = mock_client.post.call_args[1]["json"]
            assert "transaction_id" in payload
            assert "approval_status" in payload
            assert "date" in payload
            assert "message" in payload
            assert payload["transaction_id"] == "tx-payload"
            assert payload["approval_status"] is True
            assert payload["message"] == ""

    async def test_execute_uses_correct_timeout(self, use_case, mock_repository, mock_payment_config):
        """
        Given: payment_config.callback_timeout_seconds is set
        When: execute() is called
        Then: httpx.AsyncClient is created with correct timeout
        """
        mock_payment_config.callback_timeout_seconds = 30
        
        transaction = PaymentTransaction.new(order_id=800, amount=350.0)
        transaction.id = "tx-timeout"
        
        with patch("src.application.use_cases.payment_use_cases.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            # Execute
            await use_case.execute(transaction)
            
            # Verify timeout passed to AsyncClient
            mock_client_class.assert_called_once_with(timeout=30)
