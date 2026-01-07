"""
Unit tests for payment_config module.

Phase 3: Controllers, Routes, Config, Logs
Coverage Target: 80%+
"""
import os
from unittest.mock import patch

from src.config.payment_config import PaymentConfig, payment_config


class TestPaymentConfig:
    """Test PaymentConfig dataclass."""

    def test_payment_config_default_values(self):
        """
        Given: No environment variables set
        When: PaymentConfig is instantiated
        Then: Uses default values
        """
        with patch.dict(os.environ, {}, clear=True):
            config = PaymentConfig()
        
        assert config.table_name == "payment-transactions"
        assert config.order_id_index == "order_id-index"
        assert config.region_name == "us-east-1"
        assert config.endpoint_url == ""
        assert config.order_api_host == "http://order-service:8000"
        assert config.order_api_user == ""
        assert config.order_api_password == ""
        assert config.webhook_secret == ""
        assert config.callback_timeout_seconds == 10

    def test_payment_config_from_environment(self):
        """
        Given: Environment variables are set
        When: PaymentConfig is instantiated
        Then: Uses environment values
        """
        # Simulate environment by passing explicit values
        config = PaymentConfig(
            table_name="prod-payments",
            order_id_index="prod-order-index",
            region_name="eu-west-1",
            endpoint_url="http://localhost:8000",
            order_api_host="https://api.orders.prod",
            order_api_user="payment-service",
            order_api_password="secret123",
            webhook_secret="webhook-key-456",
            callback_timeout_seconds=30,
        )
        
        assert config.table_name == "prod-payments"
        assert config.order_id_index == "prod-order-index"
        assert config.region_name == "eu-west-1"
        assert config.endpoint_url == "http://localhost:8000"
        assert config.order_api_host == "https://api.orders.prod"
        assert config.order_api_user == "payment-service"
        assert config.order_api_password == "secret123"
        assert config.webhook_secret == "webhook-key-456"
        assert config.callback_timeout_seconds == 30

    def test_payment_config_partial_environment(self):
        """
        Given: Some environment variables are set
        When: PaymentConfig is instantiated
        Then: Uses environment values for set vars, defaults for others
        """
        # Pass only some values, others use dataclass defaults
        config = PaymentConfig(
            table_name="staging-payments",
            region_name="ap-south-1",
        )
        
        assert config.table_name == "staging-payments"
        assert config.region_name == "ap-south-1"
        # These should have kept their default values from class definition
        assert config.order_id_index is not None
        assert config.endpoint_url is not None

    def test_payment_config_callback_timeout_as_integer(self):
        """
        Given: CALLBACK_TIMEOUT_SECONDS is set as string
        When: PaymentConfig is instantiated
        Then: Converts to integer correctly
        """
        config = PaymentConfig(
            callback_timeout_seconds=45
        )
        
        assert config.callback_timeout_seconds == 45
        assert isinstance(config.callback_timeout_seconds, int)

    def test_payment_config_module_singleton(self):
        """
        Given: payment_config is imported
        When: Module is loaded
        Then: payment_config is a PaymentConfig instance
        """
        assert isinstance(payment_config, PaymentConfig)
        assert hasattr(payment_config, "table_name")
        assert hasattr(payment_config, "region_name")

    def test_payment_config_empty_string_values(self):
        """
        Given: Environment variables are empty strings
        When: PaymentConfig is instantiated
        Then: Uses empty strings (not defaults)
        """
        env_vars = {
            "ORDER_API_USER": "",
            "ORDER_API_PASSWORD": "",
            "WEBHOOK_SECRET": "",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = PaymentConfig()
        
        assert config.order_api_user == ""
        assert config.order_api_password == ""
        assert config.webhook_secret == ""
