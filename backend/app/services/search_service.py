from app.integrations.elastic_client import async_elastic_safe_call
from app.schemas.search import SearchRequest, SearchResponse, SearchResponseItem
from typing import Dict, Optional
import logging


logger = logging.getLogger(__name__)
INDEX_NAME = "documents_v1"

class SearchService:
  async def search(self, query: SearchRequest) -> SearchResponse:
    offset = (query.page - 1) * query.page_size
      
    es_query = {
      "query": {
        "bool": {
          "must": [{"multi_match": {"query": query.q, "fields": ["title^3", "description", "ocr_text"], "fuzziness": "AUTO"}}],
          "filter": []
        }
      },
      "from": offset,
      "size": query.page_size,
      "highlight": {"fields": {"title": {}, "description": {}, "ocr_text": {}}, "pre_tags": ["<mark>"], "post_tags": ["</mark>"]}
    }

    if query.format:
      es_query["query"]["bool"]["filter"].append({"term": {"format.keyword": query.format}})
    if query.tags:
      es_query["query"]["bool"]["filter"].append({"terms": {"tags": query.tags}})
    if query.date_from or query.date_to:
      date_range = {}
      if query.date_from: date_range["gte"] = query.date_from.isoformat()
      if query.date_to: date_range["lte"] = query.date_to.isoformat()
      es_query["query"]["bool"]["filter"].append({"range": {"publish_date": date_range}})

    result = await async_elastic_safe_call(
      lambda client: client.search(index=INDEX_NAME, body=es_query)
    )
      
    hits = result["hits"]["hits"]
    total = result["hits"]["total"]["value"]
    items = [SearchResponseItem(**hit["_source"], snippet=self._extract_highlight(hit)) for hit in hits]
    
    return SearchResponse(items=items, total=total, page=query.page, page_size=query.page_size)

  async def index_document(self, doc_data: Dict):
    await async_elastic_safe_call(
      lambda client: client.index(index=INDEX_NAME, id=doc_data["id"], document=doc_data)
    )

  async def delete_document(self, doc_id: int):
    await async_elastic_safe_call(
      lambda client: client.delete(index=INDEX_NAME, id=doc_id, ignore=[404])
    )

  @staticmethod
  def _extract_highlight(hit: Dict) -> Optional[str]:
    hl = hit.get("highlight", {})
    return " ".join(hl.get("description", hl.get("ocr_text", hl.get("title", []))))