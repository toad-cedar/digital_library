from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session, VisibilityEnum
from app.config.deps import get_current_user
from app.services.document_service import DocumentService
from app.services.minio_service import MinioService
from app.auth.casbin.dependencies import require_permission
from app.models.user_models import User
from app.schemas import (
  DocumentRead, DocumentListResponse, DownloadUrlResponse,
  VisibilityUpdate, TagAssignRequest, VersionRead, ApiResponse
)
from typing import List, Optional


router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])

def _parse_visibility(status_str: Optional[str]) -> Optional[VisibilityEnum]:
  if not status_str:
    return None
  try:
    return VisibilityEnum(status_str.lower())
  except ValueError:
    return None

@router.get("/", response_model=ApiResponse[DocumentListResponse])
async def get_documents(
  page: int = Query(1, ge=1),
  page_size: int = Query(20, ge=1, le=100),
  visibility_status: Optional[str] = Query(None),
  format: Optional[str] = Query(None),
  db_session: AsyncSession = Depends(get_db_session)
):
  svc = DocumentService(db_session=db_session, minio_service=MinioService())
  offset = (page - 1) * page_size
  docs, total = await svc.doc_repo.get_all(
    visibility=_parse_visibility(visibility_status), 
    format_filter=format, 
    offset=offset, 
    limit=page_size
  )
  items = [DocumentRead.model_validate(d) for d in docs]
  return ApiResponse(
    success=True, 
    data=DocumentListResponse(
      documents=items, 
      total=total, 
      page=page, 
      page_size=page_size
    )
  )

@router.get("/{document_id}", response_model=ApiResponse[DocumentRead])
async def get_document(
  document_id: int,
  current_user: User = Depends(get_current_user),
  _: None = Depends(require_permission("document.read")),
  db_session: AsyncSession = Depends(get_db_session)
):
  svc = DocumentService(db_session=db_session, minio_service=MinioService())
  doc = await svc.get_by_id(document_id)
  return ApiResponse(success=True, data=doc)

@router.get("/{document_id}/download-url", response_model=ApiResponse[DownloadUrlResponse])
async def get_download_url(
  document_id: int,
  current_user: User = Depends(get_current_user),
  _: None = Depends(require_permission("document.download")),
  db_session: AsyncSession = Depends(get_db_session)
):
  svc = DocumentService(db_session=db_session, minio_service=MinioService())
  return ApiResponse(success=True, data=await svc.get_download_url(document_id))

@router.get("/{document_id}/preview-url", response_model=ApiResponse[DownloadUrlResponse])
async def get_preview_url(
  document_id: int,
  current_user: User = Depends(get_current_user),
  _: None = Depends(require_permission("document.read")),
  db_session: AsyncSession = Depends(get_db_session)
):
  svc = DocumentService(db_session=db_session, minio_service=MinioService())
  return ApiResponse(success=True, data=await svc.get_download_url(document_id, expires_seconds=1800))

@router.get("/{document_id}/versions", response_model=ApiResponse[List[VersionRead]])
async def get_versions(
  document_id: int,
  current_user: User = Depends(get_current_user),
  _: None = Depends(require_permission("document.read")),
  db_session: AsyncSession = Depends(get_db_session)
):
  svc = DocumentService(db_session=db_session, minio_service=MinioService())
  return ApiResponse(success=True, data=await svc.get_versions(document_id))

@router.patch("/{document_id}/visibility", response_model=ApiResponse[DocumentRead])
async def update_visibility(
  document_id: int,
  data: VisibilityUpdate,
  current_user: User = Depends(get_current_user),
  _: None = Depends(require_permission("document.manage")),
  db_session: AsyncSession = Depends(get_db_session)
):
  svc = DocumentService(db_session=db_session, minio_service=MinioService())
  return ApiResponse(success=True, data=await svc.update_visibility(document_id, data, current_user.id))

@router.post("/{document_id}/tags", response_model=ApiResponse[DocumentRead])
async def assign_tags(
  document_id: int,
  data: TagAssignRequest,
  current_user: User = Depends(get_current_user),
  _: None = Depends(require_permission("document.manage")),
  db_session: AsyncSession = Depends(get_db_session)
):
  svc = DocumentService(db_session=db_session, minio_service=MinioService())
  return ApiResponse(success=True, data=await svc.assign_tags(document_id, data, current_user.id))