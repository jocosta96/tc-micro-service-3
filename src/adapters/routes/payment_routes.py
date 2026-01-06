from typing import Optional
from datetime import datetime

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
    qr_or_link: Optional[str]
    expires_at: Optional[datetime]
    last_error: Optional[str]


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
