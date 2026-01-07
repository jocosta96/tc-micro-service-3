"""
Unit tests for DI container module.

Phase 3: Controllers, Routes, Config, Logs
Coverage Target: 90%+
"""
import pytest
from unittest.mock import patch, MagicMock

from src.adapters.di.container import Container, container
from src.adapters.gateways.dynamo_payment_repository import DynamoPaymentRepository
from src.adapters.presenters.implementations.json_presenter import JSONPresenter


class TestContainer:
    """Test Container dependency injection class."""

    def test_container_initialization(self):
        """
        Given: Container class
        When: Instantiated
        Then: Initializes with None dependencies
        """
        cont = Container()
        
        assert cont._payment_repository is None
        assert cont._presenter is None

    @patch("src.adapters.di.container.DynamoPaymentRepository")
    def test_payment_repository_lazy_initialization(self, mock_dynamo_repo):
        """
        Given: Container instance
        When: payment_repository is accessed for first time
        Then: Creates DynamoPaymentRepository instance
        """
        mock_instance = MagicMock()
        mock_dynamo_repo.return_value = mock_instance
        
        cont = Container()
        repo = cont.payment_repository
        
        assert repo == mock_instance
        mock_dynamo_repo.assert_called_once()

    @patch("src.adapters.di.container.DynamoPaymentRepository")
    def test_payment_repository_singleton_behavior(self, mock_dynamo_repo):
        """
        Given: Container instance
        When: payment_repository is accessed multiple times
        Then: Returns same instance (singleton)
        """
        mock_instance = MagicMock()
        mock_dynamo_repo.return_value = mock_instance
        
        cont = Container()
        repo1 = cont.payment_repository
        repo2 = cont.payment_repository
        
        assert repo1 is repo2
        mock_dynamo_repo.assert_called_once()

    @patch("src.adapters.di.container.JSONPresenter")
    def test_presenter_lazy_initialization(self, mock_presenter):
        """
        Given: Container instance
        When: presenter is accessed for first time
        Then: Creates JSONPresenter instance
        """
        mock_instance = MagicMock()
        mock_presenter.return_value = mock_instance
        
        cont = Container()
        pres = cont.presenter
        
        assert pres == mock_instance
        mock_presenter.assert_called_once()

    @patch("src.adapters.di.container.JSONPresenter")
    def test_presenter_singleton_behavior(self, mock_presenter):
        """
        Given: Container instance
        When: presenter is accessed multiple times
        Then: Returns same instance (singleton)
        """
        mock_instance = MagicMock()
        mock_presenter.return_value = mock_instance
        
        cont = Container()
        pres1 = cont.presenter
        pres2 = cont.presenter
        
        assert pres1 is pres2
        mock_presenter.assert_called_once()

    @patch("src.adapters.di.container.DynamoPaymentRepository")
    @patch("src.adapters.di.container.JSONPresenter")
    def test_reset_clears_all_dependencies(self, mock_presenter, mock_dynamo_repo):
        """
        Given: Container with initialized dependencies
        When: reset() is called
        Then: Clears all dependencies
        """
        mock_repo = MagicMock()
        mock_pres = MagicMock()
        mock_dynamo_repo.return_value = mock_repo
        mock_presenter.return_value = mock_pres
        
        cont = Container()
        _ = cont.payment_repository
        _ = cont.presenter
        
        assert cont._payment_repository is not None
        assert cont._presenter is not None
        
        cont.reset()
        
        assert cont._payment_repository is None
        assert cont._presenter is None

    @patch("src.adapters.di.container.DynamoPaymentRepository")
    @patch("src.adapters.di.container.JSONPresenter")
    def test_reset_allows_reinitialization(self, mock_presenter, mock_dynamo_repo):
        """
        Given: Container after reset()
        When: Dependencies are accessed again
        Then: Creates new instances
        """
        mock_repo1 = MagicMock()
        mock_repo2 = MagicMock()
        mock_dynamo_repo.side_effect = [mock_repo1, mock_repo2]
        
        cont = Container()
        repo1 = cont.payment_repository
        cont.reset()
        repo2 = cont.payment_repository
        
        assert repo1 is not repo2
        assert mock_dynamo_repo.call_count == 2

    def test_module_container_singleton(self):
        """
        Given: container imported from module
        When: Module is loaded
        Then: container is a Container instance
        """
        assert isinstance(container, Container)

    @patch("src.adapters.di.container.DynamoPaymentRepository")
    def test_container_dependency_types(self, mock_dynamo_repo):
        """
        Given: Container with mocked dependencies
        When: Dependencies are accessed
        Then: Returns expected types/interfaces
        """
        cont = Container()
        
        # These will be the actual types when not mocked
        # Just verify they can be accessed without errors
        with patch("src.adapters.di.container.JSONPresenter"):
            repo = cont.payment_repository
            pres = cont.presenter
            
            assert repo is not None
            assert pres is not None
