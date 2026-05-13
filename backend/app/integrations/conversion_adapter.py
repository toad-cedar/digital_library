import httpx
from app.config.settings import get_settings
from app.integrations.base_adapter import integration_safe_call


def get_conversion_client():
  settings = get_settings()
  return httpx.Client(
    base_url=settings.CONVERSION_SERVICE_URL,
    timeout=60.0,  # Конвертация крупных документов занимает больше времени
    verify=settings.VERIFY_TLS,
    limits=httpx.Limits(max_connections=10)
  )

def conversion_safe_call(func, *args, max_retries: int = 3, **kwargs):
  return integration_safe_call(
    func, *args, max_retries=max_retries,
    timeout_exc=(httpx.ReadTimeout, httpx.ConnectTimeout),
    connection_exc=(httpx.ConnectError, httpx.NetworkError),
    service_exc=(httpx.HTTPStatusError,),
    **kwargs
  )