from typing import Any, Dict, Optional

from src.application.dto.implementation.payment_dto import (
    PaymentCreateRequest,
    PaymentWebhookRequest,
)
from src.application.use_cases.payment_use_cases import (
    PaymentCreateUseCase,
    PaymentWebhookUseCase,
    PaymentStatusUseCase,
    PaymentCallbackUseCase,
)
from src.application.repositories.payment_repository import PaymentRepository
from src.adapters.presenters.interfaces.presenter_interface import PresenterInterface


class PaymentController:
    """Controller for payment-service endpoints."""

    def __init__(self, payment_repository: PaymentRepository, presenter: PresenterInterface):
        self.payment_repository = payment_repository
        self.presenter = presenter
        self.create_use_case = PaymentCreateUseCase(payment_repository)
        self.webhook_use_case = PaymentWebhookUseCase(payment_repository)
        self.status_use_case = PaymentStatusUseCase(payment_repository)
        self.callback_use_case = PaymentCallbackUseCase(payment_repository)

    def request_payment(self, order_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        request_dto = PaymentCreateRequest(
            order_id=order_id,
            amount=float(data.get("amount")),
            callback_url=data.get("callback_url"),
            provider=data.get("provider"),
        )
        response = self.create_use_case.execute(request_dto)
        return response.to_dict()

    async def process_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        request_dto = PaymentWebhookRequest(
            transaction_id=data["transaction_id"],
            approval_status=data["approval_status"],
            message=data.get("message"),
            date=data.get("date"),
            event_id=data.get("event_id"),
        )
        transaction = self.webhook_use_case.execute(request_dto)
        if not transaction:
            return self.presenter.present_error(ValueError("Transaction not found"))
        await self.callback_use_case.execute(transaction)
        return {"message": "Payment processed", "transaction_id": transaction.id}

    def status(self, order_id: int) -> Dict[str, Any]:
        response = self.status_use_case.execute(order_id)
        if not response:
            return self.presenter.present_error(ValueError("Transaction not found"))
        return response.to_dict()
