from typing import Optional
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.adapters.controllers.payment_controller import PaymentController
from src.adapters.di.container import Container


class PaymentRequestBody(BaseModel):
    amount: float = Field(..., gt=0)
    callback_url: Optional[str] = None
    provider: Optional[str] = None


class WebhookBody(BaseModel):
    transaction_id: str
    approval_status: bool
    message: Optional[str] = None
    date: Optional[datetime] = None
    event_id: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    transaction_id: str
    order_id: int
    status: str
    callback_status: str
    qr_or_link: Optional[str] = None
    expires_at: Optional[datetime] = None
    last_error: Optional[str] = None


payment_router = APIRouter(tags=["payment"], prefix="/payment")


def get_payment_controller() -> PaymentController:
    container = Container()
    return PaymentController(
        payment_repository=container.payment_repository,
        presenter=container.presenter,
    )


@payment_router.post("/request/{order_id}")
async def request_payment(
    order_id: int,
    body: PaymentRequestBody,
    controller: PaymentController = Depends(get_payment_controller),
):
    return controller.request_payment(order_id, body.dict())


@payment_router.post("/webhook/mercadopago")
async def payment_webhook(
    payload: WebhookBody,
    controller: PaymentController = Depends(get_payment_controller),
):
    result = await controller.process_webhook(payload.dict())
    if "error" in result:
        raise HTTPException(
            status_code=result["error"].get("status_code", 400),
            detail=result["error"].get("message"),
        )
    return result


@payment_router.get("/status/{order_id}", response_model=PaymentStatusResponse)
async def payment_status(
    order_id: int,
    controller: PaymentController = Depends(get_payment_controller),
):
    result = controller.status(order_id)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=result["error"].get("status_code", 404),
            detail=result["error"].get("message"),
        )
    return result


class PaymentSimulationRequest(BaseModel):
    """Modelo para simular pagamento aprovado/rejeitado"""
    approved: bool = True  # True = aprovado, False = rejeitado
    message: Optional[str] = None


@payment_router.post("/simulate-payment/{order_id}")
async def simulate_payment(
    order_id: int,
    simulation: PaymentSimulationRequest,
    controller: PaymentController = Depends(get_payment_controller),
):
    """
    🔧 ENDPOINT DE TESTE/POC
    
    Simula recebimento de webhook do Mercado Pago para testar fluxo completo.
    
    **Fluxo de Uso**:
    1. Cliente cria pedido no Order Service
    2. Order Service chama `POST /payment/request/{order_id}`
    3. Payment retorna `transaction_id` + QRCode mock
    4. Para simular pagamento: `POST /simulate-payment/{order_id} {"approved": true}`
    5. Payment processa e notifica Order automaticamente
    
    ⚠️ **Em produção**, este endpoint seria removido (webhook real do MP faria isso).
    """
    # Buscar transação diretamente pelo repository usando order_id
    container = Container()
    transaction = container.payment_repository.get_by_order(order_id)
    
    if not transaction:
        raise HTTPException(
            status_code=404,
            detail=f"No payment found for order {order_id}"
        )
    
    # Montar payload do webhook simulado usando o ID correto
    webhook_payload = {
        "transaction_id": transaction.id,  # UUID correto da transação
        "approval_status": simulation.approved,
        "message": simulation.message or (
            "Pagamento aprovado via PIX [SIMULADO]" if simulation.approved 
            else "Pagamento rejeitado [SIMULADO]"
        ),
        "date": datetime.now(timezone.utc).isoformat(),
        "event_id": f"sim-{uuid.uuid4()}"  # Event ID mock
    }
    
    # Processar webhook
    result = await controller.process_webhook(webhook_payload)
    
    return {
        "message": "✅ Payment simulation completed",
        "simulation": {
            "order_id": order_id,
            "approved": simulation.approved,
            "transaction_id": transaction.id
        },
        "webhook_result": result
    }
