import os
from dataclasses import dataclass


@dataclass
class PaymentConfig:
    """
    Configuration for payment-service NoSQL storage and callbacks.
    """

    table_name: str = os.getenv("PAYMENT_TABLE_NAME", "payment-transactions")
    order_id_index: str = os.getenv("PAYMENT_ORDER_ID_INDEX", "order_id-index")
    region_name: str = os.getenv("PAYMENT_AWS_REGION", "us-east-1")
    endpoint_url: str = os.getenv("PAYMENT_DYNAMO_ENDPOINT", "")
    order_api_host: str = os.getenv("ORDER_API_HOST", "http://order-service:8000")
    order_api_user: str = os.getenv("ORDER_API_USER", "")
    order_api_password: str = os.getenv("ORDER_API_PASSWORD", "")
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "")
    callback_timeout_seconds: int = int(os.getenv("CALLBACK_TIMEOUT_SECONDS", "10"))


payment_config = PaymentConfig()
