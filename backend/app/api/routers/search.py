from fastapi import APIRouter, Query

from app.services.search_service import SearchService
from app.schemas import SearchRequest, SearchResponse, ApiResponse
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/v1/search", tags=["Search"])

@router.get("/", response_model=ApiResponse[SearchResponse])
async def search_documents(
  q: str = Query(..., min_length=1),
  page: int = Query(1, ge=1),
  page_size: int = Query(20, ge=1, le=100),
  tags: Optional[str] = Query(None),
  format: Optional[str] = Query(None),
  date_from: Optional[datetime] = Query(None),
  date_to: Optional[datetime] = Query(None),
):
  req = SearchRequest(
    q=q, page=page, page_size=page_size,
    tags=[t.strip() for t in tags.split(",")] if tags else None,
    format=format,
    date_from=None if not date_from else date_from, # Pydantic автоматически распарсит ISO, если указать datetime в схеме
    date_to=None if not date_to else date_to
  )
  svc = SearchService()
  return ApiResponse(success=True, data=await svc.search(req))