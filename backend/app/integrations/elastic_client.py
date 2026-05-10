from elasticsearch import Elasticsearch
from app.config.settings import get_settings

def get_elastic_client():
  client = Elasticsearch(
    hosts=[f"http://{get_settings().ELASTICSEARCH_HOST}:{get_settings().ELASTICSEARCH_PORT}"],
    basic_auth=("elastic", get_settings().ELASTICSEARCH_PASSWORD),
    verify_certs=False,
    request_timeout=30,
    retry_on_timeout=True,
    max_retries=10
  )
  return client

elastic_client = get_elastic_client()