from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio  import AsyncSession
from app.config.database     import get_db_session
from app.services.search_service import SearchService
from app.repos.document_repo import DocumentRepository
from app.schemas import SearchQuery
from app.schemas import DocumentListResponse, DocumentOut, StatusInfo, FormatInfo
from app.schemas import UserShort
from app.models.orm_models import Document
from typing import List

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/", summary="Поиск документов")
async def search_documents(
  query_str: str = Query(..., alias="query", min_length=1),
  author: str = Query(None),
  date_from: str = Query(None), # строка формата ISO
  date_to: str = Query(None),   # строка формата ISO
  tags: str = Query(None), # строка, разделённая запятой
  offset: int = Query(0, ge=0),
  limit: int = Query(10, ge=1, le=100),
  db_session: AsyncSession = Depends(get_db_session)
):
  """
  Выполняет поиск по индексу Elasticsearch.
  Возвращает список документов из БД по найденным ID.
  """
  # 1. Подготовка фильтров
  filters = {}
  if author:
    filters["author"] = author
  if date_from:
    filters["date_from"] = date_from
  if date_to:
    filters["date_to"] = date_to
  if tags:
    filters["tags"] = [t.strip() for t in tags.split(",") if t.strip()]

  # 2. Вызов сервиса поиска
  search_service = SearchService()
  search_params  = SearchQuery(query=query_str, filters=filters, offset=offset, limit=limit)
  search_result  = await search_service.search(search_params)

  # 3. Получение полных данных документов из БД по ID
  doc_repo = DocumentRepository(db_session)
  found_doc_ids = search_result["document_ids"]
  if not found_doc_ids:
    # Если ES не нашел ID, возвращаем пустой список
    return DocumentListResponse(
      total=search_result["total"],
      offset=search_result["offset"],
      limit=search_result["limit"],
      documents=[]
    )
  full_docs = await doc_repo.get_by_ids(found_doc_ids)
  
  # ! ОТЛАДКА
  print(f"Found IDs: {found_doc_ids}, Retrieved docs: {[d.id for d in full_docs]}")

  # 4. Формирование ответа
  document_outs = []
  for doc in full_docs:
    doc_out = DocumentOut(
      id=doc.id,
      title=doc.title,
      description=doc.description,
      author=doc.author,
      upload_date=doc.upload_date,
      publish_date=doc.publish_date,
      uploader=UserShort.model_validate(doc.uploader),
      format=FormatInfo(id=doc.format_obj.id, name=doc.format_obj.format_name),
      file_original_name=doc.file_original_name,
      file_size=doc.file_size,
      converted_to_pdf=doc.converted_to_pdf,
      status_name=StatusInfo(id=doc.status_obj.id, name=doc.status_obj.status_name),
      tags=[tag_obj.tag_name for tag_obj in doc.tags],
      minio_bucket=doc.minio_bucket, 
      cover_bucket=doc.cover_bucket, 
      cover_url=doc.cover_url,
    )
    document_outs.append(doc_out)
  
  return DocumentListResponse(
    total=search_result["total"],
    offset=search_result["offset"],
    limit=search_result["limit"],
    documents=document_outs
  )