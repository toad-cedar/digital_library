import httpx
from app.config.settings import get_settings
from app.integrations.base_adapter import integration_safe_call

def get_ocr_client():
  settings = get_settings()
  return httpx.Client(
    base_url=settings.OCR_SERVICE_URL,
    timeout=30.0,
    verify=settings.VERIFY_TLS,
    limits=httpx.Limits(max_connections=15)
  )

def ocr_safe_call(func, *args, max_retries: int = 3, **kwargs):
  return integration_safe_call(
    func, *args, max_retries=max_retries,
    timeout_exc=(httpx.ReadTimeout, httpx.ConnectTimeout),
    connection_exc=(httpx.ConnectError, httpx.NetworkError),
    service_exc=(httpx.HTTPStatusError,),
    **kwargs
  )