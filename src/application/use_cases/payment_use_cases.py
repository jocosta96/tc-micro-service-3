from datetime import datetime, timedelta, timezone
from typing import Optional
import httpx
import uuid
import logging

logger = logging.getLogger(__name__)

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
        logger.info(f"🔵 Creating payment for order {request.order_id}, amount: R${request.amount:.2f}")
        
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        # Gerar provider_tx_id mock único (simula ID do Mercado Pago)
        provider_tx_id = str(abs(hash(f"mp-{request.order_id}-{uuid.uuid4()}")) % (10 ** 10))
        
        # Gerar QRCode PIX mock realista (formato simplificado)
        qr_code_mock = self._generate_pix_qr_code_mock(
            provider_tx_id=provider_tx_id,
            amount=request.amount,
            order_id=request.order_id
        )
        
        transaction = PaymentTransaction.new(
            order_id=request.order_id,
            amount=request.amount,
            provider=request.provider or "mercadopago",
            qr_or_link=qr_code_mock,
            expires_at=expires_at,
        )
        
        # Salvar provider_tx_id mock
        transaction.provider_tx_id = provider_tx_id
        
        if request.callback_url:
            transaction.metadata["callback_url"] = request.callback_url
        
        # Salvar URL de pagamento mock (para exibir no frontend)
        transaction.metadata["payment_url"] = f"https://www.mercadopago.com.br/payments/{provider_tx_id}/ticket"

        saved, created = self.payment_repository.upsert_by_order_if_pending(transaction)
        
        if not created:
            logger.info(f"♻️  Reusing existing transaction {saved.id} for order {request.order_id}")
            transaction = saved
        else:
            logger.info(f"✅ Created transaction {transaction.id} with provider_tx_id {provider_tx_id}")

        return PaymentCreateResponse(
            transaction_id=transaction.id,
            qr_or_link=transaction.qr_or_link,
            expires_at=transaction.expires_at,
        )
    
    def _generate_pix_qr_code_mock(self, provider_tx_id: str, amount: float, order_id: int) -> str:
        """
        Gera QRCode PIX mock (formato simplificado mas realista).
        Em produção real, viria da API do Mercado Pago.
        
        Formato real PIX: 00020126...LANCHONETE...5802BR...(códigos EMV)
        """
        # Simplificado: string que parece PIX mas é mock
        payload = f"LANCHONETE|PEDIDO#{order_id}|R${amount:.2f}|MP:{provider_tx_id}"
        # Em produção, seria base64 ou EMV code real
        qr_mock = f"00020126{len(payload):02d}{payload}6304MOCK"
        logger.debug(f"Generated QRCode mock: {qr_mock[:50]}...")
        return qr_mock


class PaymentWebhookUseCase:
    """Handle webhook notification and update transaction status."""

    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository

    def execute(self, request: PaymentWebhookRequest) -> Optional[PaymentTransaction]:
        logger.info(f"📩 Webhook received: tx_id={request.transaction_id}, approved={request.approval_status}")
        
        transaction = self.payment_repository.get_by_id(request.transaction_id)
        if not transaction:
            logger.warning(f"❌ Transaction {request.transaction_id} not found")
            return None

        new_status = PaymentStatus.APPROVED if request.approval_status else PaymentStatus.DECLINED
        logger.info(f"🔄 Updating tx {transaction.id}: {transaction.status} → {new_status}")
        
        updated = self.payment_repository.update_status(
            transaction_id=transaction.id,
            status=new_status,
            provider_tx_id=request.transaction_id,
            error=request.message,
        )
        
        logger.info(f"✅ Transaction {transaction.id} updated successfully")
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
        
        logger.info(f"📤 Sending callback to Order: tx={transaction.id}, order={transaction.order_id}, url={callback_url}")
        
        payload = {
            "transaction_id": transaction.id,
            "approval_status": transaction.status == PaymentStatus.APPROVED,
            "date": datetime.now(timezone.utc).isoformat(),
            "message": transaction.last_error or "",
        }

        headers={"Authorization": f"{payment_config.order_token}"} if payment_config.order_token else {}
        try:
            async with httpx.AsyncClient(timeout=payment_config.callback_timeout_seconds) as client:
                resp = await client.post(callback_url, json=payload, headers=headers)
                if resp.status_code >= 400:
                    raise httpx.HTTPStatusError("Callback failed", request=resp.request, response=resp)
            
            logger.info(f"✅ Callback delivered: tx={transaction.id}, status_code={resp.status_code}")
            self.payment_repository.update_callback_status(transaction.id, CallbackStatus.DELIVERED, None)
        
        except Exception as exc:  # pragma: no cover - network failure paths are environment-specific
            logger.error(f"❌ Callback failed: tx={transaction.id}, error={exc}")
            self.payment_repository.update_callback_status(transaction.id, CallbackStatus.FAILED, str(exc))
