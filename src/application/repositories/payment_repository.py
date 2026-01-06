from abc import ABC, abstractmethod
from typing import Optional, Tuple

from src.entities.payment_transaction import PaymentTransaction, PaymentStatus, CallbackStatus


class PaymentRepository(ABC):
    """Abstraction for persisting payment transactions in NoSQL."""

    @abstractmethod
    def create_pending(self, transaction: PaymentTransaction) -> PaymentTransaction:
        raise NotImplementedError

    @abstractmethod
    def get_by_order(self, order_id: int) -> Optional[PaymentTransaction]:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, transaction_id: str) -> Optional[PaymentTransaction]:
        raise NotImplementedError

    @abstractmethod
    def update_status(
        self,
        transaction_id: str,
        status: PaymentStatus,
        provider_tx_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[PaymentTransaction]:
        raise NotImplementedError

    @abstractmethod
    def update_callback_status(
        self,
        transaction_id: str,
        status: CallbackStatus,
        error: Optional[str] = None,
    ) -> Optional[PaymentTransaction]:
        raise NotImplementedError

    @abstractmethod
    def upsert_by_order_if_pending(self, transaction: PaymentTransaction) -> Tuple[PaymentTransaction, bool]:
        """
        Insert a new pending transaction if none exists or if the existing one is still pending.
        Returns the transaction and a flag indicating whether it was newly created.
        """
        raise NotImplementedError
