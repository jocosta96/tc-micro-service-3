from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.application.dto.interfaces.request_interface import RequestInterface
from src.application.dto.interfaces.response_interface import ResponseInterface
from src.entities.payment_transaction import PaymentStatus, CallbackStatus


@dataclass
class PaymentCreateRequest(RequestInterface):
    order_id: int
    amount: float
    callback_url: Optional[str] = None
    provider: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "amount": self.amount,
            "callback_url": self.callback_url,
            "provider": self.provider,
        }


@dataclass
class PaymentCreateResponse(ResponseInterface):
    transaction_id: str
    qr_or_link: Optional[str]
    expires_at: Optional[datetime]

    def to_dict(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "qr_or_link": self.qr_or_link,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @classmethod
    def from_entity(cls, entity):
        raise NotImplementedError("Not used for this DTO")


@dataclass
class PaymentWebhookRequest(RequestInterface):
    transaction_id: str
    approval_status: bool
    message: Optional[str] = None
    date: Optional[datetime] = None
    event_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "approval_status": self.approval_status,
            "message": self.message,
            "date": self.date.isoformat() if self.date else None,
            "event_id": self.event_id,
        }


@dataclass
class PaymentTransactionStatusResponse(ResponseInterface):
    transaction_id: str
    order_id: int
    status: PaymentStatus
    callback_status: CallbackStatus
    qr_or_link: Optional[str]
    expires_at: Optional[datetime]
    last_error: Optional[str]

    def to_dict(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "order_id": self.order_id,
            "status": self.status.value,
            "callback_status": self.callback_status.value,
            "qr_or_link": self.qr_or_link,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_error": self.last_error,
        }

    @classmethod
    def from_entity(cls, entity):
        return cls(
            transaction_id=entity.id,
            order_id=entity.order_id,
            status=entity.status,
            callback_status=entity.callback_status,
            qr_or_link=entity.qr_or_link,
            expires_at=entity.expires_at,
            last_error=entity.last_error,
        )
