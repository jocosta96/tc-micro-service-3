from fastapi import APIRouter

from src.config.payment_config import payment_config

health_router = APIRouter(tags=["health"])


@health_router.get("/health")
def health_check():
    """Basic health check."""
    return {"status": "healthy", "message": "Payment service is running"}


@health_router.get("/health/config")
def configuration_health_check():
    """Expose minimal runtime configuration for debugging."""
    return {
        "status": "healthy",
        "configuration": {
            "table_name": payment_config.table_name,
            "region": payment_config.region_name,
            "order_api_host": payment_config.order_api_host,
        },
    }
