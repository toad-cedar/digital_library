from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database   import get_db_session
from app.config.deps       import get_current_user
from app.models.orm_models import User
from app.schemas.document  import DocumentOut, DocumentListResponse, PreviewUrlResponse, StatusInfo, FormatInfo
from app.schemas.user      import UserShort
from app.repos.document_repo    import DocumentRepository
from app.services.minio_service import MinioService
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from typing   import List, Optional

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/", response_model=DocumentListResponse, summary="Получить список документов")
async def get_documents(
  offset: int = Query(0, ge=0),
  limit: int = Query(10, ge=1, le=100),
  db_session: AsyncSession = Depends(get_db_session)
):
  """Получает список всех документов (для мин. версии)."""
  repo = DocumentRepository(db_session)
  documents, total_count = await repo.get_all(offset=offset, limit=limit, status=None) # TODO: сделать систему статусов

  document_outs = []
  for doc in documents:
  # Явно формируем Pydantic-объект, преобразуя связи
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
    total=total_count,
    offset=offset,
    limit=limit,
    documents=document_outs
  )


@router.get("/{document_id}", response_model=DocumentOut, summary="Получить метаданные документа")
async def get_document(
  document_id: int,
  db_session: AsyncSession = Depends(get_db_session)
):
  """Получает метаданные конкретного документа."""
  repo = DocumentRepository(db_session)
  doc = await repo.get_by_id(document_id)
  if not doc:
    raise HTTPException(status_code=404, detail="Document not found")
  
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
  return doc_out

# pydantic-схема
class DownloadUrlResponse(BaseModel):
  url: str
  expires_at: datetime


@router.get("/{document_id}/download-url", response_model=DownloadUrlResponse, summary="Получить URL для скачивания")
async def get_download_url(
  document_id: int,
  current_user: User = Depends(get_current_user),
  db_session: AsyncSession = Depends(get_db_session)
):
  """Возвращает предварительно подписанный URL для скачивания файла из MinIO."""
  repo = DocumentRepository(db_session)
  doc  = await repo.get_by_id(document_id)
  if not doc:
    raise HTTPException(status_code=404, detail="Document not found")
  if not doc.status_id: 
    raise HTTPException(status_code=403, detail="Document is not approved yet")
  
  minio_service = MinioService()
  expires_sec = 3600 # 1 час
  url = await minio_service.get_presigned_url(
    bucket_name=doc.minio_bucket,
    object_name=doc.minio_object_path,
    expires=expires_sec 
  )
  time_of_expire = datetime.now(timezone.utc) + timedelta(seconds=expires_sec)
  
  return DownloadUrlResponse(url=url, expires_at=time_of_expire)


@router.get("/{document_id}/preview-url", response_model=PreviewUrlResponse, summary="Получить URL для предпросмотра")
async def get_preview_url(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session)
):
  """
  Возвращает предварительно подписанный URL для предпросмотра файла из MinIO.
  URL может быть использован напрямую в PDF.js или аналоге.
  """
  repo = DocumentRepository(db_session)
  doc  = await repo.get_by_id(document_id)
  if not doc:
    raise HTTPException(status_code=404, detail="Document not found")
  
  if not doc.status_obj.status_name == "approved":
    raise HTTPException(status_code=403, detail="Document is not approved yet")

  minio_service = MinioService()
  
  expires_seconds = 1800 # 30 минут
  url = await minio_service.get_presigned_url(
    bucket_name=doc.minio_bucket,
    object_name=doc.minio_object_path, # Используем путь к ОСНОВНОМУ файлу
    expires=expires_seconds
  )

  # Вычисляем время истечения
  time_of_expire = datetime.now(timezone.utc) + timedelta(seconds=expires_seconds)

  # Возвращаем объект, соответствующий PreviewUrlResponse
  return PreviewUrlResponse(url=url, expires_at=time_of_expire)

# Роутеры для обновления/удаления (для администраторов)
# ...