from datetime import datetime, timedelta, timezone
from typing import Optional
import httpx
import base64

from src.application.dto.implementation.payment_dto import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentWebhookRequest,
    PaymentTransactionStatusResponse,
)
from src.application.repositories.payment_repository import PaymentRepository
from src.config.payment_config import payment_config
from src.entities.payment_transaction import (
    PaymentTransaction,
    PaymentStatus,
    CallbackStatus,
)


class PaymentCreateUseCase:
    """Create or reuse a pending payment transaction with idempotency by order_id."""

    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository

    def execute(self, request: PaymentCreateRequest) -> PaymentCreateResponse:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        transaction = PaymentTransaction.new(
            order_id=request.order_id,
            amount=request.amount,
            provider=request.provider,
            qr_or_link=f"https://pay.local/tx/{request.order_id}",
            expires_at=expires_at,
        )
        if request.callback_url:
            transaction.metadata["callback_url"] = request.callback_url

        saved, created = self.payment_repository.upsert_by_order_if_pending(transaction)
        if not created:
            transaction = saved

        return PaymentCreateResponse(
            transaction_id=transaction.id,
            qr_or_link=transaction.qr_or_link,
            expires_at=transaction.expires_at,
        )


class PaymentWebhookUseCase:
    """Handle webhook notification and update transaction status."""

    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository

    def execute(self, request: PaymentWebhookRequest) -> Optional[PaymentTransaction]:
        transaction = self.payment_repository.get_by_id(request.transaction_id)
        if not transaction:
            return None

        new_status = PaymentStatus.APPROVED if request.approval_status else PaymentStatus.DECLINED
        updated = self.payment_repository.update_status(
            transaction_id=transaction.id,
            status=new_status,
            provider_tx_id=request.transaction_id,
            error=request.message,
        )
        return updated


class PaymentStatusUseCase:
    """Retrieve transaction status by order id."""

    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository

    def execute(self, order_id: int) -> Optional[PaymentTransactionStatusResponse]:
        transaction = self.payment_repository.get_by_order(order_id)
        if not transaction:
            return None
        return PaymentTransactionStatusResponse.from_entity(transaction)


class PaymentCallbackUseCase:
    """Send callback to order-service and track callback status."""

    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository

    async def execute(self, transaction: PaymentTransaction) -> None:
        callback_url = transaction.metadata.get("callback_url") if transaction.metadata else None
        if not callback_url:
            callback_url = f"{payment_config.order_api_host}/order/payment_confirm/{transaction.order_id}"
        payload = {
            "transaction_id": transaction.id,
            "approval_status": transaction.status == PaymentStatus.APPROVED,
            "date": datetime.now(timezone.utc).isoformat(),
            "message": transaction.last_error or "",
        }

        headers = {}
        username = payment_config.order_api_user
        password = payment_config.order_api_password
        if username and password:
            token = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {token}"

        try:
            async with httpx.AsyncClient(timeout=payment_config.callback_timeout_seconds) as client:
                resp = await client.post(callback_url, json=payload, headers=headers)
                if resp.status_code >= 400:
                    raise httpx.HTTPStatusError("Callback failed", request=resp.request, response=resp)
            self.payment_repository.update_callback_status(transaction.id, CallbackStatus.DELIVERED, None)
        except Exception as exc:  # pragma: no cover - network failure paths are environment-specific
            self.payment_repository.update_callback_status(transaction.id, CallbackStatus.FAILED, str(exc))
