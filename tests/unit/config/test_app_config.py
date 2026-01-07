"""
Unit tests for app_config module.

Phase 3: Controllers, Routes, Config, Logs
Coverage Target: 80%+
"""
import os
from unittest.mock import patch

from src.config.app_config import AppConfig, app_config


class TestAppConfig:
    """Test AppConfig class."""

    def test_app_config_default_values(self):
        """
        Given: No environment variables set
        When: AppConfig is instantiated
        Then: Uses default values
        """
        with patch.dict(os.environ, {}, clear=True):
            config = AppConfig()
        
        assert config.api_prefix == "/fastfood/api"
        assert config.api_title == "FastFood Ordering System"
        assert config.api_version == "1.0.0"
        assert "clean architecture" in config.api_description.lower()
        
        assert config.allowed_origins == ["*"]
        assert config.allowed_credentials is True
        assert "GET" in config.allowed_methods
        assert "POST" in config.allowed_methods
        
        assert config.log_level == "INFO"
        assert "levelname" in config.log_format.lower()
        
        assert config.rate_limit_enabled is True
        assert config.rate_limit_default == "100/minute"
        
        assert config.anonymous_email == "anonymous@fastfood.local"
        assert config.max_name_length == 50
        assert config.min_name_length == 1

    def test_app_config_from_environment(self):
        """
        Given: Environment variables are set
        When: AppConfig is instantiated
        Then: Uses environment values
        """
        env_vars = {
            "API_PREFIX": "/api/v2",
            "API_TITLE": "Payment Service",
            "API_VERSION": "2.0.0",
            "API_DESCRIPTION": "Payment processing API",
            "ALLOWED_ORIGINS": "http://localhost:3000,https://app.prod.com",
            "ALLOWED_CREDENTIALS": "false",
            "ALLOWED_METHODS": "GET,POST",
            "ALLOWED_HEADERS": "Content-Type,Authorization",
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "%(message)s",
            "RATE_LIMIT_ENABLED": "false",
            "RATE_LIMIT_DEFAULT": "50/hour",
            "ANONYMOUS_EMAIL": "guest@example.com",
            "MAX_NAME_LENGTH": "100",
            "MIN_NAME_LENGTH": "3",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig()
        
        assert config.api_prefix == "/api/v2"
        assert config.api_title == "Payment Service"
        assert config.api_version == "2.0.0"
        assert config.api_description == "Payment processing API"
        
        assert config.allowed_origins == ["http://localhost:3000", "https://app.prod.com"]
        assert config.allowed_credentials is False
        assert config.allowed_methods == ["GET", "POST"]
        assert config.allowed_headers == ["Content-Type", "Authorization"]
        
        assert config.log_level == "DEBUG"
        assert config.log_format == "%(message)s"
        
        assert config.rate_limit_enabled is False
        assert config.rate_limit_default == "50/hour"
        
        assert config.anonymous_email == "guest@example.com"
        assert config.max_name_length == 100
        assert config.min_name_length == 3

    def test_app_config_boolean_parsing_true_values(self):
        """
        Given: Environment variables with various 'true' strings
        When: AppConfig is instantiated
        Then: Parses as True
        """
        true_values = ["true", "TRUE", "True", "TrUe"]
        
        for true_val in true_values:
            with patch.dict(os.environ, {"ALLOWED_CREDENTIALS": true_val}, clear=True):
                config = AppConfig()
                assert config.allowed_credentials is True, f"Failed for {true_val}"

    def test_app_config_boolean_parsing_false_values(self):
        """
        Given: Environment variables with non-'true' strings
        When: AppConfig is instantiated
        Then: Parses as False
        """
        false_values = ["false", "FALSE", "0", "no", "", "anything"]
        
        for false_val in false_values:
            with patch.dict(os.environ, {"RATE_LIMIT_ENABLED": false_val}, clear=True):
                config = AppConfig()
                assert config.rate_limit_enabled is False, f"Failed for {false_val}"

    def test_app_config_integer_parsing(self):
        """
        Given: Environment variables with integer strings
        When: AppConfig is instantiated
        Then: Parses as integers
        """
        env_vars = {
            "MAX_NAME_LENGTH": "200",
            "MIN_NAME_LENGTH": "5",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig()
        
        assert config.max_name_length == 200
        assert isinstance(config.max_name_length, int)
        assert config.min_name_length == 5
        assert isinstance(config.min_name_length, int)

    def test_app_config_csv_parsing(self):
        """
        Given: Environment variables with comma-separated values
        When: AppConfig is instantiated
        Then: Parses as lists
        """
        env_vars = {
            "ALLOWED_ORIGINS": "http://a.com,http://b.com,http://c.com",
            "ALLOWED_METHODS": "GET,POST,PUT,DELETE,PATCH",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig()
        
        assert len(config.allowed_origins) == 3
        assert "http://a.com" in config.allowed_origins
        assert len(config.allowed_methods) == 5
        assert "PATCH" in config.allowed_methods

    def test_app_config_module_singleton(self):
        """
        Given: app_config is imported
        When: Module is loaded
        Then: app_config is an AppConfig instance
        """
        assert isinstance(app_config, AppConfig)
        assert hasattr(app_config, "api_prefix")
        assert hasattr(app_config, "log_level")

    def test_app_config_partial_environment(self):
        """
        Given: Some environment variables are set
        When: AppConfig is instantiated
        Then: Uses environment for set vars, defaults for others
        """
        env_vars = {
            "API_PREFIX": "/custom",
            "LOG_LEVEL": "ERROR",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig()
        
        assert config.api_prefix == "/custom"
        assert config.log_level == "ERROR"
        assert config.api_title == "FastFood Ordering System"  # Default
        assert config.rate_limit_enabled is True  # Default
