"""
Unit tests for app_logs module.

Phase 3: Controllers, Routes, Config, Logs
Coverage Target: 80%+
"""
import pytest
import logging
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.app_logs import (
    LogLevels,
    StructuredLogger,
    configure_logging,
    get_logger,
)


class TestLogLevels:
    """Test LogLevels enum."""

    def test_log_levels_enum_values(self):
        """
        Given: LogLevels enum
        When: Accessing enum values
        Then: Returns correct string values
        """
        assert LogLevels.info.value == "INFO"
        assert LogLevels.warn.value == "WARN"
        assert LogLevels.error.value == "ERROR"
        assert LogLevels.debug.value == "DEBUG"

    def test_log_levels_as_strings(self):
        """
        Given: LogLevels enum members
        When: Used as strings
        Then: Works correctly in string operations
        """
        assert LogLevels.info.value == "INFO"
        assert LogLevels.error.value == "ERROR"
        # str(enum) returns 'EnumClass.member' format
        assert str(LogLevels.info) == "LogLevels.info"


class TestStructuredLogger:
    """Test StructuredLogger class."""

    @patch("src.app_logs.logging.getLogger")
    def test_structured_logger_initialization(self, mock_get_logger):
        """
        Given: StructuredLogger class
        When: Instantiated with a name
        Then: Creates logger with correct name
        """
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger = StructuredLogger("test-logger")
        
        assert logger.name == "test-logger"
        mock_get_logger.assert_called_once_with("test-logger")

    @patch("src.app_logs.logging.getLogger")
    def test_format_log_creates_json_structure(self, mock_get_logger):
        """
        Given: StructuredLogger instance
        When: _format_log is called
        Then: Returns valid JSON with required fields
        """
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger = StructuredLogger("test")
        formatted = logger._format_log("INFO", "Test message", key="value")
        
        parsed = json.loads(formatted)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["logger"] == "test"
        assert "timestamp" in parsed
        assert parsed["key"] == "value"

    @patch("src.app_logs.logging.getLogger")
    @patch("src.app_logs.datetime")
    def test_format_log_timestamp_format(self, mock_datetime, mock_get_logger):
        """
        Given: StructuredLogger instance
        When: _format_log is called
        Then: Timestamp is in ISO format with Z suffix
        """
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_datetime.utcnow.return_value.isoformat.return_value = "2026-01-06T12:00:00"
        
        logger = StructuredLogger("test")
        formatted = logger._format_log("INFO", "Test")
        
        parsed = json.loads(formatted)
        assert parsed["timestamp"] == "2026-01-06T12:00:00Z"

    @patch("src.app_logs.logging.getLogger")
    def test_format_log_handles_non_serializable_objects(self, mock_get_logger):
        """
        Given: StructuredLogger instance
        When: _format_log is called with complex objects
        Then: Converts objects to strings
        """
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        class CustomObj:
            def __str__(self):
                return "custom-object"
        
        logger = StructuredLogger("test")
        formatted = logger._format_log("INFO", "Test", obj=CustomObj())
        
        parsed = json.loads(formatted)
        assert parsed["obj"] == "custom-object"

    @patch("src.app_logs.logging.getLogger")
    def test_info_logs_at_info_level(self, mock_get_logger):
        """
        Given: StructuredLogger instance
        When: info() is called
        Then: Logs at INFO level
        """
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger = StructuredLogger("test")
        logger.info("Info message", user_id=123)
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        parsed = json.loads(call_args)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Info message"
        assert parsed["user_id"] == "123"

    @patch("src.app_logs.logging.getLogger")
    def test_warning_logs_at_warning_level(self, mock_get_logger):
        """
        Given: StructuredLogger instance
        When: warning() is called
        Then: Logs at WARNING level
        """
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger = StructuredLogger("test")
        logger.warning("Warning message", alert=True)
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        parsed = json.loads(call_args)
        assert parsed["level"] == "WARNING"
        assert parsed["message"] == "Warning message"

    @patch("src.app_logs.logging.getLogger")
    def test_error_logs_at_error_level(self, mock_get_logger):
        """
        Given: StructuredLogger instance
        When: error() is called
        Then: Logs at ERROR level
        """
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger = StructuredLogger("test")
        logger.error("Error message", code=500)
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        parsed = json.loads(call_args)
        assert parsed["level"] == "ERROR"
        assert parsed["message"] == "Error message"

    @patch("src.app_logs.logging.getLogger")
    def test_debug_logs_at_debug_level(self, mock_get_logger):
        """
        Given: StructuredLogger instance
        When: debug() is called
        Then: Logs at DEBUG level
        """
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger = StructuredLogger("test")
        logger.debug("Debug message", trace_id="abc-123")
        
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0][0]
        parsed = json.loads(call_args)
        assert parsed["level"] == "DEBUG"

    @patch("src.app_logs.logging.getLogger")
    def test_exception_logs_with_exception_info(self, mock_get_logger):
        """
        Given: StructuredLogger instance and an exception
        When: exception() is called with exc_info
        Then: Logs exception type and message
        """
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger = StructuredLogger("test")
        exc = ValueError("Invalid value")
        logger.exception("Exception occurred", exc_info=exc, context="test")
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        parsed = json.loads(call_args)
        assert parsed["level"] == "ERROR"
        assert parsed["exception_type"] == "ValueError"
        assert parsed["exception_message"] == "Invalid value"

    @patch("src.app_logs.logging.getLogger")
    def test_exception_logs_without_exception_info(self, mock_get_logger):
        """
        Given: StructuredLogger instance
        When: exception() is called without exc_info
        Then: Logs error without exception details
        """
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger = StructuredLogger("test")
        logger.exception("Generic error", request_id="req-456")
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        parsed = json.loads(call_args)
        assert "exception_type" not in parsed


class TestConfigureLogging:
    """Test configure_logging function."""

    @patch("src.app_logs.logging.basicConfig")
    def test_configure_logging_uses_default_from_app_config(self, mock_basic_config):
        """
        Given: No log_level argument
        When: configure_logging() is called
        Then: Uses log_level from app_config (defaults to INFO)
        """
        # The function will use the real app_config.log_level
        # which defaults to "INFO" unless overridden
        configure_logging()
        
        # Verify basicConfig was called
        mock_basic_config.assert_called_once()
        # Get the actual call arguments
        call_kwargs = mock_basic_config.call_args[1]
        assert "level" in call_kwargs
        # Should be uppercase string
        assert isinstance(call_kwargs["level"], str)
        assert call_kwargs["level"] == call_kwargs["level"].upper()

    @patch("src.app_logs.logging.basicConfig")
    def test_configure_logging_with_explicit_level(self, mock_basic_config):
        """
        Given: Explicit log_level argument
        When: configure_logging(log_level="ERROR") is called
        Then: Uses provided log_level
        """
        configure_logging(log_level="ERROR")
        
        mock_basic_config.assert_called_once_with(level="ERROR")

    @patch("src.app_logs.logging.basicConfig")
    def test_configure_logging_converts_enum_to_string(self, mock_basic_config):
        """
        Given: log_level as LogLevels enum
        When: configure_logging() is called
        Then: Converts enum to string value
        """
        configure_logging(log_level=LogLevels.debug)
        
        # DEBUG uses custom format
        assert mock_basic_config.called

    @patch("src.app_logs.logging.basicConfig")
    def test_configure_logging_uppercases_level(self, mock_basic_config):
        """
        Given: log_level in lowercase
        When: configure_logging() is called
        Then: Uppercases log_level
        """
        configure_logging(log_level="info")
        
        mock_basic_config.assert_called_once_with(level="INFO")

    @patch("src.app_logs.logging.basicConfig")
    def test_configure_logging_invalid_level_defaults_to_error(self, mock_basic_config):
        """
        Given: Invalid log_level
        When: configure_logging() is called
        Then: Defaults to ERROR level
        """
        configure_logging(log_level="INVALID")
        
        mock_basic_config.assert_called_once_with(level="ERROR")

    @patch("src.app_logs.logging.basicConfig")
    @patch("src.app_logs.app_config")
    def test_configure_logging_debug_uses_custom_format(self, mock_app_config, mock_basic_config):
        """
        Given: log_level is DEBUG
        When: configure_logging() is called
        Then: Uses custom log_format from app_config
        """
        mock_app_config.log_format = "%(levelname)s - %(message)s"
        
        configure_logging(log_level="DEBUG")
        
        mock_basic_config.assert_called_once_with(
            level="DEBUG",
            format="%(levelname)s - %(message)s"
        )

    @patch("src.app_logs.logging.basicConfig")
    def test_configure_logging_non_debug_uses_default_format(self, mock_basic_config):
        """
        Given: log_level is not DEBUG
        When: configure_logging() is called
        Then: Uses default basicConfig format (no format arg)
        """
        configure_logging(log_level="INFO")
        
        mock_basic_config.assert_called_once_with(level="INFO")
        # Verify no 'format' keyword argument
        call_kwargs = mock_basic_config.call_args[1]
        assert "format" not in call_kwargs


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_returns_structured_logger(self):
        """
        Given: get_logger function
        When: Called with a name
        Then: Returns StructuredLogger instance
        """
        logger = get_logger("my-logger")
        
        assert isinstance(logger, StructuredLogger)
        assert logger.name == "my-logger"

    def test_get_logger_creates_different_instances(self):
        """
        Given: get_logger function
        When: Called multiple times with different names
        Then: Returns different StructuredLogger instances
        """
        logger1 = get_logger("logger-1")
        logger2 = get_logger("logger-2")
        
        assert logger1 is not logger2
        assert logger1.name == "logger-1"
        assert logger2.name == "logger-2"
