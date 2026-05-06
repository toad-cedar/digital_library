from elasticsearch import Elasticsearch
from app.config.settings import settings

def get_elastic_client():
  client = Elasticsearch(
    hosts=[f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"],
    basic_auth=("elastic", settings.ELASTICSEARCH_PASSWORD),
    verify_certs=False,
    request_timeout=30,
    retry_on_timeout=True,
    max_retries=10
  )
  return client

elastic_client = get_elastic_client()