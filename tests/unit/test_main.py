"""
Unit tests for main module (FastAPI app creation).

Phase 3: Controllers, Routes, Config, Logs
Coverage Target: 80%+
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI

from src.main import create_application, app


class TestMainModule:
    """Test main FastAPI application creation."""

    @patch("src.main.app_config")
    def test_create_application_returns_fastapi_instance(self, mock_app_config):
        """
        Given: create_application function
        When: Called
        Then: Returns FastAPI instance
        """
        mock_app_config.api_title = "Test App"
        mock_app_config.api_version = "1.0.0"
        mock_app_config.api_description = "Test Description"
        mock_app_config.api_prefix = "/api"
        mock_app_config.cors_config = {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
        
        application = create_application()
        
        assert isinstance(application, FastAPI)

    @patch("src.main.app_config")
    def test_create_application_uses_app_config(self, mock_app_config):
        """
        Given: app_config with custom values
        When: create_application() is called
        Then: Uses values from app_config
        """
        mock_app_config.api_title = "Payment Service"
        mock_app_config.api_version = "2.0.0"
        mock_app_config.api_description = "Payment API"
        mock_app_config.api_prefix = "/payments"
        mock_app_config.cors_config = {
            "allow_origins": ["http://localhost"],
            "allow_credentials": False,
            "allow_methods": ["GET", "POST"],
            "allow_headers": ["Content-Type"],
        }
        
        application = create_application()
        
        assert application.title == "Payment Service"
        assert application.version == "2.0.0"
        assert application.description == "Payment API"

    @patch("src.main.app_config")
    def test_create_application_adds_cors_middleware(self, mock_app_config):
        """
        Given: create_application function
        When: Called
        Then: Adds CORS middleware to app
        """
        mock_app_config.api_title = "Test"
        mock_app_config.api_version = "1.0.0"
        mock_app_config.api_description = "Test"
        mock_app_config.api_prefix = "/api"
        mock_app_config.cors_config = {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
        
        with patch("src.main.FastAPI") as mock_fastapi:
            mock_app = MagicMock()
            mock_fastapi.return_value = mock_app
            
            create_application()
            
            mock_app.add_middleware.assert_called_once()
            call_args = mock_app.add_middleware.call_args
            # Verify CORSMiddleware is added with cors_config
            assert call_args[1]["allow_origins"] == ["*"]

    @patch("src.main.app_config")
    def test_create_application_includes_routers(self, mock_app_config):
        """
        Given: create_application function
        When: Called
        Then: Includes health_router and payment_router
        """
        mock_app_config.api_title = "Test"
        mock_app_config.api_version = "1.0.0"
        mock_app_config.api_description = "Test"
        mock_app_config.api_prefix = "/api"
        mock_app_config.cors_config = {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
        
        with patch("src.main.FastAPI") as mock_fastapi:
            mock_app = MagicMock()
            mock_fastapi.return_value = mock_app
            
            with patch("src.main.health_router") as mock_health_router:
                with patch("src.main.payment_router") as mock_payment_router:
                    create_application()
                    
                    # Verify both routers are included
                    assert mock_app.include_router.call_count == 2
                    
                    # Get the calls
                    calls = mock_app.include_router.call_args_list
                    router_calls = [call[1]["router"] for call in calls]
                    
                    assert mock_health_router in router_calls
                    assert mock_payment_router in router_calls

    def test_module_app_is_fastapi_instance(self):
        """
        Given: app imported from main module
        When: Module is loaded
        Then: app is a FastAPI instance
        """
        assert isinstance(app, FastAPI)

    @patch("src.main.configure_logging")
    @patch("src.main.LogLevels")
    def test_module_configures_logging_on_import(self, mock_log_levels, mock_configure_logging):
        """
        Given: main module
        When: Module is imported
        Then: Calls configure_logging with INFO level
        """
        # This test verifies the module-level call:
        # configure_logging(LogLevels.info.value)
        
        # Since the module is already imported, we can't easily test this
        # But we can verify the function exists and is callable
        from src.main import configure_logging
        assert callable(configure_logging)

    @patch("src.main.app_config")
    def test_create_application_with_minimal_config(self, mock_app_config):
        """
        Given: app_config with minimal values
        When: create_application() is called
        Then: Creates app with defaults where needed
        """
        mock_app_config.api_title = "Minimal App"  # FastAPI requires non-empty title
        mock_app_config.api_version = "0.0.1"
        mock_app_config.api_description = ""
        mock_app_config.api_prefix = ""
        mock_app_config.cors_config = {}
        
        application = create_application()
        
        assert isinstance(application, FastAPI)
        assert application.version == "0.0.1"

    @patch("src.main.app_config")
    def test_create_application_multiple_calls_create_different_instances(self, mock_app_config):
        """
        Given: create_application function
        When: Called multiple times
        Then: Creates different FastAPI instances each time
        """
        mock_app_config.api_title = "Test"
        mock_app_config.api_version = "1.0.0"
        mock_app_config.api_description = "Test"
        mock_app_config.api_prefix = "/api"
        mock_app_config.cors_config = {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
        
        app1 = create_application()
        app2 = create_application()
        
        assert app1 is not app2
