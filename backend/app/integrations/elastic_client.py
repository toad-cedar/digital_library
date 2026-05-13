import time
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionTimeout, ConnectionError, ApiError
from app.config.settings import get_settings
from app.core.exceptions import IntegrationConnectionError, IntegrationTimeoutError, IntegrationServiceError


def get_elastic_client() -> Elasticsearch:
  settings = get_settings()
  scheme = 'https' if settings.ELASTICSEARCH_SECURE else 'http'
  return Elasticsearch(
    hosts=[f"{scheme}://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"],
    basic_auth=(settings.ELASTICSEARCH_USER, settings.ELASTICSEARCH_PASSWORD),
    verify_certs=settings.VERIFY_TLS,
    request_timeout=10,
    retry_on_timeout=True,
    max_retries=2,
    maxsize=10,
  )

def elastic_safe_call(func, *args, max_retries: int = 3, **kwargs):
  last_error = None
  
  for attempt in range(max_retries):
    try:
      return func(*args, **kwargs)
    except ConnectionTimeout as e:
      last_error = e
      if attempt == max_retries - 1:
        raise IntegrationTimeoutError(f"Elasticsearch timeout: {e}") from e
      time.sleep(2 ** attempt)
    except ConnectionError as e:
      last_error = e
      if attempt == max_retries - 1:
        raise IntegrationConnectionError(f"Elasticsearch connection failed: {e}") from e
      time.sleep(2 ** attempt)
    except ApiError as e:
      raise IntegrationServiceError(f"Elasticsearch API error: {e.error}") from e
  raise IntegrationConnectionError("Elasticsearch call failed after retries") from last_error