from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"


class CallbackStatus(str, Enum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


@dataclass
class PaymentTransaction:
    """
    Payment transaction aggregate stored in NoSQL.
    """

    id: str
    order_id: int
    amount: float
    status: PaymentStatus = PaymentStatus.PENDING
    provider: Optional[str] = None
    provider_tx_id: Optional[str] = None
    qr_or_link: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    callback_status: CallbackStatus = CallbackStatus.PENDING
    last_callback_error: Optional[str] = None

    @classmethod
    def new(
        cls,
        order_id: int,
        amount: float,
        provider: Optional[str] = None,
        qr_or_link: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> "PaymentTransaction":
        return cls(
            id=str(uuid4()),
            order_id=order_id,
            amount=amount,
            provider=provider,
            qr_or_link=qr_or_link,
            expires_at=expires_at,
        )

    def mark_status(self, status: PaymentStatus, provider_tx_id: Optional[str] = None, error: Optional[str] = None) -> None:
        self.status = status
        self.provider_tx_id = provider_tx_id or self.provider_tx_id
        self.last_error = error
        self.updated_at = datetime.now(timezone.utc)

    def mark_callback(self, status: CallbackStatus, error: Optional[str] = None) -> None:
        self.callback_status = status
        self.last_callback_error = error
        self.updated_at = datetime.now(timezone.utc)

    def to_item(self) -> Dict[str, Any]:
        item = {
            "id": self.id,
            "order_id": self.order_id,
            "amount": self.amount,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "callback_status": self.callback_status.value,
        }

        optional_fields = {
            "provider": self.provider,
            "provider_tx_id": self.provider_tx_id,
            "qr_or_link": self.qr_or_link,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_error": self.last_error,
            "last_callback_error": self.last_callback_error,
        }

        for key, value in optional_fields.items():
            if value is not None:
                item[key] = value

        return item

    @classmethod
    def from_item(cls, item: Dict[str, Any]) -> "PaymentTransaction":
        return cls(
            id=item["id"],
            order_id=int(item["order_id"]),
            amount=float(item["amount"]),
            status=PaymentStatus(item.get("status", PaymentStatus.PENDING.value)),
            provider=item.get("provider"),
            provider_tx_id=item.get("provider_tx_id"),
            qr_or_link=item.get("qr_or_link"),
            expires_at=datetime.fromisoformat(item["expires_at"]) if item.get("expires_at") else None,
            created_at=datetime.fromisoformat(item["created_at"]) if item.get("created_at") else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(item["updated_at"]) if item.get("updated_at") else datetime.now(timezone.utc),
            last_error=item.get("last_error"),
            metadata=item.get("metadata") or {},
            callback_status=CallbackStatus(item.get("callback_status", CallbackStatus.PENDING.value)),
            last_callback_error=item.get("last_callback_error"),
        )
