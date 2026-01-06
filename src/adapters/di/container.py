from src.application.repositories.payment_repository import PaymentRepository
from src.adapters.gateways.dynamo_payment_repository import DynamoPaymentRepository
from src.adapters.presenters.implementations.json_presenter import JSONPresenter
from src.adapters.presenters.interfaces.presenter_interface import PresenterInterface


class Container:
    """
    Dependency Injection Container.

    In Clean Architecture:
    - This wires up all the components
    - It's part of the Frameworks & Drivers layer
    - It creates the concrete implementations
    - It manages the dependency graph
    """

    def __init__(self):
        self._payment_repository: PaymentRepository = None
        self._presenter: PresenterInterface = None

    @property
    def payment_repository(self):
        """Get DynamoDB payment repository instance"""
        if self._payment_repository is None:
            self._payment_repository = DynamoPaymentRepository()
        return self._payment_repository

    @property
    def presenter(self) -> PresenterInterface:
        """Get presenter instance"""
        if self._presenter is None:
            self._presenter = JSONPresenter()
        return self._presenter

    def reset(self):
        """Reset all dependencies (useful for testing)"""
        self._payment_repository = None
        self._presenter = None


# Global container instance
container = Container()
