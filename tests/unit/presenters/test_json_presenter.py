"""
Unit tests for JSONPresenter.

Phase 3: Controllers, Routes, Config, Logs
Coverage Target: 85%+
"""
import pytest
from datetime import datetime
from http import HTTPStatus

from src.adapters.presenters.implementations.json_presenter import JSONPresenter
from src.application.dto.implementation.payment_dto import PaymentTransactionStatusResponse
from src.application.exceptions import (
    CustomerValidationException,
    CustomerNotFoundException,
    CustomerAlreadyExistsException,
    CustomerBusinessRuleException,
    IngredientValidationException,
    ProductValidationException,
    ProductNotFoundException,
    AuthenticationException,
    AuthorizationException,
)
from src.entities.payment_transaction import PaymentStatus, CallbackStatus


class TestJSONPresenter:
    """Test JSONPresenter."""

    @pytest.fixture
    def presenter(self):
        """Create JSONPresenter instance."""
        return JSONPresenter()

    def test_present_response_interface(self, presenter):
        """
        Given: Object with to_dict() method (ResponseInterface)
        When: present() is called
        Then: Returns dict with data and timestamp
        """
        response = PaymentTransactionStatusResponse(
            transaction_id="tx-123",
            order_id=123,
            status=PaymentStatus.APPROVED,
            callback_status=CallbackStatus.DELIVERED,
            qr_or_link="https://pay.local/qr/123",
            expires_at=None,
            last_error=None,
        )
        
        result = presenter.present(response)
        
        assert isinstance(result, dict)
        assert result["transaction_id"] == "tx-123"
        assert result["order_id"] == 123
        assert "timestamp" in result

    def test_present_object_with_dict_attribute(self, presenter):
        """
        Given: Object with __dict__ attribute but no to_dict()
        When: present() is called
        Then: Returns __dict__ as dict
        """
        class SimpleObject:
            def __init__(self):
                self.name = "test"
                self.value = 42
        
        obj = SimpleObject()
        result = presenter.present(obj)
        
        assert result["name"] == "test"
        assert result["value"] == 42

    def test_present_primitive_type(self, presenter):
        """
        Given: Primitive type (string)
        When: present() is called
        Then: Returns dict with string representation
        """
        result = presenter.present("simple string")
        
        assert isinstance(result, dict)
        assert result["data"] == "simple string"
        assert "timestamp" in result

    def test_present_list_empty(self, presenter):
        """
        Given: Empty list
        When: present_list() is called
        Then: Returns empty data array with total_count=0
        """
        result = presenter.present_list([])
        
        assert result["data"] == []
        assert result["total_count"] == 0
        assert "timestamp" in result

    def test_present_list_with_items(self, presenter):
        """
        Given: List of ResponseInterface objects
        When: present_list() is called
        Then: Returns array of dicts with total_count
        """
        items = [
            PaymentTransactionStatusResponse(
                transaction_id=f"tx-{i}",
                order_id=i,
                status=PaymentStatus.PENDING,
                callback_status=CallbackStatus.PENDING,
                qr_or_link=None,
                expires_at=None,
                last_error=None,
            )
            for i in range(3)
        ]
        
        result = presenter.present_list(items)
        
        assert len(result["data"]) == 3
        assert result["total_count"] == 3
        assert "timestamp" in result
        assert result["data"][0]["transaction_id"] == "tx-0"

    def test_present_error_validation_400(self, presenter):
        """
        Given: CustomerValidationException
        When: present_error() is called
        Then: Returns error dict with status_code 400
        """
        error = CustomerValidationException("Invalid CPF format")
        
        result = presenter.present_error(error)
        
        assert "error" in result
        assert result["error"]["message"] == "Invalid CPF format"
        assert result["error"]["type"] == "CustomerValidationException"
        assert result["error"]["status_code"] == HTTPStatus.BAD_REQUEST
        assert "timestamp" in result["error"]

    def test_present_error_not_found_404(self, presenter):
        """
        Given: CustomerNotFoundException
        When: present_error() is called
        Then: Returns error dict with status_code 404
        """
        error = CustomerNotFoundException("Customer 123 not found")
        
        result = presenter.present_error(error)
        
        assert result["error"]["status_code"] == HTTPStatus.NOT_FOUND
        assert result["error"]["message"] == "Customer 123 not found"

    def test_present_error_conflict_409(self, presenter):
        """
        Given: CustomerAlreadyExistsException
        When: present_error() is called
        Then: Returns error dict with status_code 409
        """
        error = CustomerAlreadyExistsException("Customer already exists")
        
        result = presenter.present_error(error)
        
        assert result["error"]["status_code"] == HTTPStatus.CONFLICT

    def test_present_error_authentication_401(self, presenter):
        """
        Given: AuthenticationException
        When: present_error() is called
        Then: Returns error dict with status_code 401
        """
        error = AuthenticationException("Invalid credentials")
        
        result = presenter.present_error(error)
        
        assert result["error"]["status_code"] == HTTPStatus.UNAUTHORIZED

    def test_present_error_authorization_403(self, presenter):
        """
        Given: AuthorizationException
        When: present_error() is called
        Then: Returns error dict with status_code 403
        """
        error = AuthorizationException("Access denied")
        
        result = presenter.present_error(error)
        
        assert result["error"]["status_code"] == HTTPStatus.FORBIDDEN

    def test_present_error_generic_500(self, presenter):
        """
        Given: Generic Exception
        When: present_error() is called
        Then: Returns error dict with status_code 500
        """
        error = Exception("Unexpected error occurred")
        
        result = presenter.present_error(error)
        
        assert result["error"]["status_code"] == HTTPStatus.INTERNAL_SERVER_ERROR
        assert result["error"]["message"] == "Unexpected error occurred"

    def test_present_error_value_error_400(self, presenter):
        """
        Given: ValueError
        When: present_error() is called
        Then: Returns error dict with status_code 400
        """
        error = ValueError("Invalid value")
        
        result = presenter.present_error(error)
        
        assert result["error"]["status_code"] == HTTPStatus.BAD_REQUEST

    def test_present_error_file_not_found_404(self, presenter):
        """
        Given: FileNotFoundError
        When: present_error() is called
        Then: Returns error dict with status_code 404
        """
        error = FileNotFoundError("File not found")
        
        result = presenter.present_error(error)
        
        assert result["error"]["status_code"] == HTTPStatus.NOT_FOUND

    def test_present_error_ingredient_validation_400(self, presenter):
        """
        Given: IngredientValidationException
        When: present_error() is called
        Then: Returns error dict with status_code 400
        """
        error = IngredientValidationException("Invalid ingredient")
        
        result = presenter.present_error(error)
        
        assert result["error"]["status_code"] == HTTPStatus.BAD_REQUEST

    def test_present_error_product_not_found_404(self, presenter):
        """
        Given: ProductNotFoundException
        When: present_error() is called
        Then: Returns error dict with status_code 404
        """
        error = ProductNotFoundException("Product not found")
        
        result = presenter.present_error(error)
        
        assert result["error"]["status_code"] == HTTPStatus.NOT_FOUND

    def test_present_error_business_rule_400(self, presenter):
        """
        Given: CustomerBusinessRuleException
        When: present_error() is called
        Then: Returns error dict with status_code 400
        """
        error = CustomerBusinessRuleException("Business rule violated")
        
        result = presenter.present_error(error)
        
        assert result["error"]["status_code"] == HTTPStatus.BAD_REQUEST

    def test_get_timestamp_format(self, presenter):
        """
        Given: Presenter instance
        When: _get_timestamp() is called
        Then: Returns ISO format timestamp with Z suffix
        """
        timestamp = presenter._get_timestamp()
        
        assert isinstance(timestamp, str)
        assert timestamp.endswith("Z")
        # Verify it's a valid ISO format
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_present_error_includes_type_name(self, presenter):
        """
        Given: Any exception
        When: present_error() is called
        Then: Error dict includes exception type name
        """
        error = ProductValidationException("Test error")
        
        result = presenter.present_error(error)
        
        assert result["error"]["type"] == "ProductValidationException"

    def test_present_list_with_mixed_objects(self, presenter):
        """
        Given: List with objects that have to_dict()
        When: present_list() is called
        Then: All objects are converted correctly
        """
        class MockObject:
            def __init__(self, value):
                self.value = value
            
            def to_dict(self):
                return {"value": self.value}
        
        items = [MockObject(i) for i in range(5)]
        
        result = presenter.present_list(items)
        
        assert result["total_count"] == 5
        assert all("value" in item for item in result["data"])
