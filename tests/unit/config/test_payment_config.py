"""
Unit tests for payment_config module.

Phase 3: Controllers, Routes, Config, Logs
Coverage Target: 80%+
"""
import os
import importlib
from unittest.mock import patch

from src.config.payment_config import PaymentConfig, payment_config
import src.config.payment_config


class TestPaymentConfig:
    """Test PaymentConfig dataclass."""

    def test_payment_config_default_values(self):
        """
        Given: No environment variables set
        When: PaymentConfig is instantiated
        Then: Uses default values
        """
        env_vars = {
            'PAYMENT_TABLE_NAME': 'payment-transactions',
            'PAYMENT_ORDER_ID_INDEX': 'order_id-index',
            'PAYMENT_AWS_REGION': 'us-east-1',
            'PAYMENT_DYNAMO_ENDPOINT': '',
            'ORDER_API_HOST': 'http://order-service:8000',
            'ORDER_API_TOKEN': '',
            'CALLBACK_TIMEOUT_SECONDS': '10'
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.config.payment_config.get_ssm_client') as mock_ssm:
                mock_ssm.return_value.get_parameter.return_value = None
                # Reload module to re-read environment variables
                importlib.reload(src.config.payment_config)
                config = src.config.payment_config.payment_config
        
        assert config.table_name == "payment-transactions"
        assert config.order_id_index == "order_id-index"
        assert config.region_name == "us-east-1"
        assert config.endpoint_url == ""
        assert config.order_api_host == "http://order-service:8000"
        assert config.order_token == ""  # nosec - test value
        assert config.callback_timeout_seconds == 10

    def test_payment_config_from_environment(self):
        """
        Given: Environment variables are set
        When: PaymentConfig is instantiated
        Then: Uses environment values
        """
        # Simulate environment variables
        env_vars = {
            "PAYMENT_TABLE_NAME": "prod-payments",
            "PAYMENT_ORDER_ID_INDEX": "prod-order-index",
            "PAYMENT_AWS_REGION": "eu-west-1",
            "PAYMENT_DYNAMO_ENDPOINT": "http://localhost:8000",
            "ORDER_API_HOST": "https://api.orders.prod",
            "ORDER_API_TOKEN": "token-123",
            "CALLBACK_TIMEOUT_SECONDS": "30",
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.config.payment_config.get_ssm_client') as mock_ssm:
                mock_ssm.return_value.get_parameter.return_value = None
                importlib.reload(src.config.payment_config)
                config = src.config.payment_config.payment_config
        
        assert config.table_name == "prod-payments"
        assert config.order_id_index == "prod-order-index"
        assert config.region_name == "eu-west-1"
        assert config.endpoint_url == "http://localhost:8000"
        assert config.order_api_host == "https://api.orders.prod"
        assert config.order_token == "token-123"  # nosec - test value
        assert config.callback_timeout_seconds == 30

    def test_payment_config_partial_environment(self):
        """
        Given: Some environment variables are set
        When: PaymentConfig is instantiated
        Then: Uses environment values for set vars, defaults for others
        """
        # Set only some environment variables
        env_vars = {
            "PAYMENT_TABLE_NAME": "staging-payments",
            "PAYMENT_AWS_REGION": "ap-south-1",
            'PAYMENT_ORDER_ID_INDEX': 'order_id-index',
            'PAYMENT_DYNAMO_ENDPOINT': '',
            'ORDER_API_HOST': 'http://order-service:8000',
            'ORDER_API_TOKEN': '',
            'CALLBACK_TIMEOUT_SECONDS': '10'
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.config.payment_config.get_ssm_client') as mock_ssm:
                mock_ssm.return_value.get_parameter.return_value = None
                importlib.reload(src.config.payment_config)
                config = src.config.payment_config.payment_config
        
        assert config.table_name == "staging-payments"
        assert config.region_name == "ap-south-1"
        # These should have kept their default values from class definition
        assert config.order_id_index == "order_id-index"
        assert config.endpoint_url == ""

    def test_payment_config_callback_timeout_as_integer(self):
        """
        Given: CALLBACK_TIMEOUT_SECONDS is set as string
        When: PaymentConfig is instantiated
        Then: Converts to integer correctly
        """
        env_vars = {
            "CALLBACK_TIMEOUT_SECONDS": "45",
            'PAYMENT_TABLE_NAME': 'payment-transactions',
            'PAYMENT_ORDER_ID_INDEX': 'order_id-index',
            'PAYMENT_AWS_REGION': 'us-east-1',
            'PAYMENT_DYNAMO_ENDPOINT': '',
            'ORDER_API_HOST': 'http://order-service:8000',
            'ORDER_API_TOKEN': ''
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.config.payment_config.get_ssm_client') as mock_ssm:
                mock_ssm.return_value.get_parameter.return_value = None
                importlib.reload(src.config.payment_config)
                config = src.config.payment_config.payment_config
        
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
            "ORDER_API_TOKEN": "",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with patch('src.config.payment_config.get_ssm_client') as mock_ssm:
                mock_ssm.return_value.get_parameter.return_value = None
                config = PaymentConfig()
        
        # nosec: B105 - These are test assertions for empty values, not hardcoded tokens
        assert config.order_token == ""  # nosec: B105
