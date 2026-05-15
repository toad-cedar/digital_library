from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session
from app.config.deps import get_current_user
from app.services.upload_service import UploadService
from app.services.minio_service import MinioService
from app.repos.upload_repo import UploadRequestRepository
from app.models.user_models import User
from app.schemas import UploadRequestRead, ApiResponse
from typing import Optional, List


router = APIRouter(prefix="/api/v1/uploads", tags=["Uploads"])

@router.post("/", response_model=ApiResponse[UploadRequestRead])
async def upload_document(
  file: UploadFile = File(...),
  title: str = Form(...),
  description: Optional[str] = Form(None),
  current_user: User = Depends(get_current_user),
  db_session: AsyncSession = Depends(get_db_session)
):
  file_bytes = await file.read()
  if not file_bytes:
    raise ValueError("File is empty")

  svc = UploadService(db_session=db_session, minio_service=MinioService())
  result = await svc.create_upload_request(
    uploader_id=current_user.id,
    file_bytes=file_bytes,
    original_filename=file.filename or "unknown",
    mime_type=file.content_type or "application/octet-stream",
    title=title,
    description=description,
  )
  return ApiResponse(success=True, data=result)

@router.get("/", response_model=ApiResponse[List[UploadRequestRead]])
async def get_my_uploads(
  page: int = Query(1, ge=1),
  page_size: int = Query(20, ge=1, le=100),
  current_user: User = Depends(get_current_user),
  db_session: AsyncSession = Depends(get_db_session)
):
  repo = UploadRequestRepository(db_session)
  offset = (page - 1) * page_size
  items, _ = await repo.get_by_user(current_user.id, offset=offset, limit=page_size)
  return ApiResponse(success=True, data=[UploadRequestRead.model_validate(i) for i in items])

@router.get("/status/{upload_id}", response_model=ApiResponse[UploadRequestRead])
async def get_upload_status(
  upload_id: int,
  current_user: User = Depends(get_current_user),
  db_session: AsyncSession = Depends(get_db_session)
):
  svc = UploadService(db_session=db_session, minio_service=MinioService())
  result = await svc.get_status(upload_id, current_user.id)
  return ApiResponse(success=True, data=result)