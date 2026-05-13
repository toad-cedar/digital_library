import time
from app.core.exceptions import IntegrationConnectionError, IntegrationTimeoutError, IntegrationServiceError


def integration_safe_call(func, *args, max_retries: int = 3, timeout_exc=(), connection_exc=(), service_exc=(), **kwargs):
  """
  Универсальная обёртка для retry-логики и маппинга исключений.
  Ожидает кортежи исключений в параметрах timeout_exc, connection_exc, service_exc.
  """
  last_error = None
  for attempt in range(max_retries):
    try:
      return func(*args, **kwargs)
    except timeout_exc as e:
      last_error = e
      if attempt == max_retries - 1:
        raise IntegrationTimeoutError(f"Service timeout: {e}") from e
      time.sleep(2 ** attempt)
    except connection_exc as e:
      last_error = e
      if attempt == max_retries - 1:
        raise IntegrationConnectionError(f"Connection failed: {e}") from e
      time.sleep(2 ** attempt)
    except service_exc as e:
      raise IntegrationServiceError(f"Service API error: {e}") from e
  raise IntegrationConnectionError("Integration call failed after retries") from last_error