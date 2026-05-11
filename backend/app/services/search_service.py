from typing import Dict, List
from app.integrations.elastic_client import elastic_client
from app.models.orm_models import Document
from app.schemas import SearchQuery
import logging

logger = logging.getLogger(__name__)

INDEX_NAME = "documents"


class SearchService:
  def __init__(self):
    self.client = elastic_client
    self._ensure_index_exists()

  def _ensure_index_exists(self):
    """Проверяет существование индекса и создает его с маппингом, если нужно"""
    mapping = {
      "mappings": {
        "properties": {
          "id": {"type": "integer"},
          "title": {"type": "text", "analyzer": "standard"},
          "description": {"type": "text", "analyzer": "standard"},
          "author": {"type": "keyword"}, # Для фильтрации
          "upload_date": {"type": "date"},
          "publish_date": {"type": "date"},
          "uploader_id": {"type": "integer"},
          "format_id": {"type": "integer"},
          "tags": {"type": "keyword"}, # Для фильтрации,
          "cover_url": {"type": "keyword"},
        }
      }
    }
    if not self.client.indices.exists(index=INDEX_NAME):
      self.client.indices.create(index=INDEX_NAME, body=mapping)
      logger.info(f"Elasticsearch index '{INDEX_NAME}' created.")

  async def index_document(self, document: Document, tag_names: List[str] = None):
    """Индексирует один документ"""
    doc_body = {
      "id": document.id,
      "title": document.title,
      "description": document.description,
      "author": document.author,
      "upload_date": document.upload_date.isoformat(),
      "publish_date": document.publish_date.isoformat(),
      "uploader_id": document.uploader_id,
      "format_id": document.format_id,
      "tags": tag_names or [],
      "cover_url": document.cover_url,
    }
    try:
      resp = self.client.index(index=INDEX_NAME, id=document.id, body=doc_body)
      logger.debug(f"Document {document.id} indexed. Result: {resp['result']}")
    except Exception as e:
      logger.error(f"Failed to index document {document.id}: {e}")
      raise e

  async def search(self, query_params: SearchQuery) -> Dict:
    """Выполняет поиск по индексу"""
    es_query = {
      "query": {
        "bool": {
          "must": [
            {"multi_match": {"query": query_params.query, "fields": ["title^2", "description"]}}
          ],
          "filter": []
        }
      },
      "from": query_params.offset,
      "size": query_params.limit,
    }

    # Добавляем фильтры, если они есть
    if query_params.filters:
      filters = query_params.filters
      if filters.get("author"):
        es_query["query"]["bool"]["filter"].append({"term": {"author": filters["author"]}})
      if filters.get("date_from"):
        es_query["query"]["bool"]["filter"].append({"range": {"publish_date": {"gte": filters["date_from"]}}})
      if filters.get("date_to"):
        es_query["query"]["bool"]["filter"].append({"range": {"publish_date": {"lte": filters["date_to"]}}})
      if filters.get("tags"):
        # Используем terms для поиска по массиву тегов
        es_query["query"]["bool"]["filter"].append({"terms": {"tags": filters["tags"]}})

    try:
      result = self.client.search(index=INDEX_NAME, body=es_query)
      hits = result["hits"]["hits"]
      total = result["hits"]["total"]["value"]

      # Возвращаем только ID документов, остальные поля можно подгрузить из БД
      found_doc_ids = [hit["_source"]["id"] for hit in hits]
      return {
        "total": total,
        "offset": query_params.offset,
        "limit": query_params.limit,
        "document_ids": found_doc_ids,
        "raw_es_response": result # Для отладки
      }
    except Exception as e:
      logger.error(f"Search failed: {e}")
      raise e
  
  async def delete_from_index(self, doc_id: int):
    """Удаляет документ из индекса по ID"""
    try:
      resp = self.client.delete(index=INDEX_NAME, id=doc_id, ignore=[404]) # игнорируем 404 (если нет)
      logger.debug(f"Document {doc_id} deleted from index. Result: {resp['result']}")
    except Exception as e:
      logger.error(f"Failed to delete document {doc_id} from index: {e}")
      raise e
