import os

from dataclasses import dataclass
from src.config.aws_ssm import get_ssm_client

@dataclass
class PaymentConfig:
    """
    Configuration for payment-service NoSQL storage and callbacks.
    """

    table_name: str = os.getenv("PAYMENT_TABLE_NAME", "payment-transactions")
    order_id_index: str = os.getenv("PAYMENT_ORDER_ID_INDEX", "order_id-index")
    region_name: str = os.getenv("PAYMENT_AWS_REGION", "us-east-1")
    endpoint_url: str = os.getenv("PAYMENT_DYNAMO_ENDPOINT", "")
    order_api_host: str = get_ssm_client().get_parameter(
            "/ordering-system/order/apigateway/url",
            decrypt=True
        ) or \
    os.getenv("ORDER_API_HOST", "http://order-service:8000")

    order_token: str = get_ssm_client().get_parameter(
            "/ordering-system/order/apigateway/token",
            decrypt=True
        ) or \
    os.getenv("ORDER_API_TOKEN", "")

    dynamo_access_key_id: str = get_ssm_client().get_parameter(
            "/ordering-system/payment/aws/access_key_id",
            decrypt=True
        ) or \
    os.getenv("PAYMENT_AWS_ACCESS_KEY_ID", "")


    dynamo_secret_access_key: str = get_ssm_client().get_parameter(
            "/ordering-system/payment/aws/secret_access_key",
            decrypt=True
        ) or \
    os.getenv("PAYMENT_AWS_SECRET_ACCESS_KEY", "")

    dynamo_session_token: str = get_ssm_client().get_parameter(
            "/ordering-system/payment/aws/session_token",
            decrypt=True
        ) or \
    os.getenv("PAYMENT_AWS_SESSION_TOKEN", "")

    callback_timeout_seconds: int = int(os.getenv("CALLBACK_TIMEOUT_SECONDS", "10"))


payment_config = PaymentConfig()
