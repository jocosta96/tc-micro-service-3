from typing import Optional, Tuple

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from datetime import datetime, timezone

from src.application.repositories.payment_repository import PaymentRepository
from src.config.payment_config import payment_config
from src.entities.payment_transaction import PaymentTransaction, PaymentStatus, CallbackStatus


class DynamoPaymentRepository(PaymentRepository):
    """
    DynamoDB-backed repository for payment transactions.
    """

    def __init__(self, table_name: str = None):
        self.table_name = table_name or payment_config.table_name
        session = boto3.resource(
            "dynamodb",
            region_name=payment_config.region_name,
            endpoint_url=payment_config.endpoint_url or None,
        )
        self.table = session.Table(self.table_name)

    def create_pending(self, transaction: PaymentTransaction) -> PaymentTransaction:
        self.table.put_item(Item=transaction.to_item(), ConditionExpression="attribute_not_exists(id)")
        return transaction

    def get_by_order(self, order_id: int) -> Optional[PaymentTransaction]:
        try:
            resp = self.table.query(
                IndexName=payment_config.order_id_index,
                KeyConditionExpression=Key("order_id").eq(order_id),
                Limit=1,
                ScanIndexForward=False,
            )
        except ClientError:
            resp = {"Items": []}

        items = resp.get("Items") or []
        if not items:
            return None
        return PaymentTransaction.from_item(items[0])

    def get_by_id(self, transaction_id: str) -> Optional[PaymentTransaction]:
        resp = self.table.get_item(Key={"id": transaction_id})
        if "Item" not in resp:
            return None
        return PaymentTransaction.from_item(resp["Item"])

    def update_status(
        self,
        transaction_id: str,
        status: PaymentStatus,
        provider_tx_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[PaymentTransaction]:
        provider_value = provider_tx_id or transaction_id
        error_value = error or ""
        try:
            self.table.update_item(
                Key={"id": transaction_id},
                UpdateExpression="SET #s = :s, provider_tx_id = if_not_exists(provider_tx_id, :p), last_error = :e, updated_at = :u",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":s": status.value,
                    ":p": provider_value,
                    ":e": error_value,
                    ":u": datetime.now(timezone.utc).isoformat(),
                },
            )
        except ClientError:
            return None
        return self.get_by_id(transaction_id)

    def update_callback_status(
        self,
        transaction_id: str,
        status: CallbackStatus,
        error: Optional[str] = None,
    ) -> Optional[PaymentTransaction]:
        error_value = error or ""
        try:
            self.table.update_item(
                Key={"id": transaction_id},
                UpdateExpression="SET callback_status = :c, last_callback_error = :e, updated_at = :u",
                ExpressionAttributeValues={
                    ":c": status.value,
                    ":e": error_value,
                    ":u": datetime.now(timezone.utc).isoformat(),
                },
            )
        except ClientError:
            return None
        return self.get_by_id(transaction_id)

    def upsert_by_order_if_pending(self, transaction: PaymentTransaction) -> Tuple[PaymentTransaction, bool]:
        existing = self.get_by_order(transaction.order_id)
        if existing and existing.status != PaymentStatus.PENDING:
            return existing, False
        if existing:
            return existing, False
        created = self.create_pending(transaction)
        return created, True
