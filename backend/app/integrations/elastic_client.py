from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionTimeout, ConnectionError, ApiError
from app.config.settings import get_settings
from app.integrations.base_adapter import integration_safe_call


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
  return integration_safe_call(
    func, *args, max_retries=max_retries,
    timeout_exc=(ConnectionTimeout,),
    connection_exc=(ConnectionError,),
    service_exc=(ApiError,),
    **kwargs
  )