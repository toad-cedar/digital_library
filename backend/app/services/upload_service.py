from sqlalchemy.ext.asyncio import AsyncSession
from app.repos.upload_repo import UploadRequestRepository
from app.repos.user_repo import UserRepository
from app.services.minio_service import MinioService
from app.models.document_models import UploadRequest
from app.schemas.upload import UploadRequestRead
from app.config.database import WorkflowEnum
from typing import Optional
import logging
import hashlib
import uuid


logger = logging.getLogger(__name__)

class UploadService:
  def __init__(self, db_session: AsyncSession, minio_service: MinioService):
    self.db_session = db_session
    self.upload_repo = UploadRequestRepository(db_session)
    self.user_repo = UserRepository(db_session)
    self.minio_service = minio_service
  
  async def create_upload_request(
    self,
    uploader_id: int,
    file_bytes: bytes,
    original_filename: str,
    mime_type: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
  ) -> UploadRequestRead:
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    temp_object_name = f"temp/{uploader_id}/{uuid.uuid4()}/{original_filename}"
    
    # Загрузка во временный бакет
    await self.minio_service.upload_file("temporary", temp_object_name, file_bytes, mime_type)

    upload_req = UploadRequest(
      uploader_id=uploader_id,
      title=title or original_filename,
      description=description,
      temporary_minio_path=temp_object_name,
      file_original_name=original_filename,
      file_mime=mime_type,
      file_size=len(file_bytes),
      file_hash=file_hash,
      workflow_status=WorkflowEnum.UPLOADED,
    )

    created = await self.upload_repo.create(upload_req)
    await self.db_session.commit()
    
    # Диспетчеризация фоновой задачи (OCR + антивирус + конвертация)
    await self._dispatch_processing_task(created.id)
    
    return UploadRequestRead.model_validate(created)

  async def get_status(self, upload_id: int, uploader_id: int) -> UploadRequestRead:
    req = await self.upload_repo.get_by_id(upload_id)
    if not req or req.uploader_id != uploader_id:
      logger.error(f"Upload request not found or access denied")
      raise ValueError("Upload request not found or access denied")
    
    return UploadRequestRead.model_validate(req)

  async def _dispatch_processing_task(self, upload_id: int):
    # ! Здесь подключение к очереди (Celery/RQ/ARQ)
    # await redis_client.lpush("processing_queue", json.dumps({"upload_id": upload_id}))
    logger.info(f"Processing task dispatched for upload_id={upload_id}")
