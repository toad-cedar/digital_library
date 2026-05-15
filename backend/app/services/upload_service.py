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
    self.__class__._dispatch_processing_task(created.id)
    
    return UploadRequestRead.model_validate(created)

  async def get_status(self, upload_id: int, uploader_id: int) -> UploadRequestRead:
    req = await self.upload_repo.get_by_id(upload_id)
    if not req or req.uploader_id != uploader_id:
      logger.error(f"Upload request not found or access denied")
      raise ValueError("Upload request not found or access denied")
    
    return UploadRequestRead.model_validate(req)

  @staticmethod
  def _dispatch_processing_task(upload_id: int) -> None:
    from rq import Retry
    from app.config.worker_config import default_queue, heavy_queue
    from app.tasks.file_pipeline import (
      validate_file_task, extract_text_task, finalize_upload_task, publish_document_task, convert_to_pdf_task
    )

    retry_policy = Retry(max=3, interval=[15, 60, 180])

    try:
      validate_job = default_queue.enqueue(
        validate_file_task,
        upload_id,
        retry=retry_policy,
        job_timeout='5m',
        meta={'upload_id': upload_id}
      )

      extract_job = heavy_queue.enqueue(
        extract_text_task,
        upload_id,
        depends_on=validate_job,
        retry=retry_policy,
        job_timeout='15m'
      )

      finalize_job = default_queue.enqueue(
        finalize_upload_task,
        upload_id,
        depends_on=extract_job,
        retry=retry_policy,
        job_timeout='5m'
      )

      heavy_queue.enqueue(
        publish_document_task, 
        upload_id, 
        depends_on=finalize_job, 
        retry=Retry(max=2, interval=[30, 60])
      )

      heavy_queue.enqueue(
        convert_to_pdf_task, 
        upload_id, 
        depends_on=finalize_job, 
        retry=Retry(max=2, interval=[30, 60]), 
        job_timeout="10m"
      )
      
      
      logger.info(
        f"Pipeline dispatched: validate={validate_job.id}, "
        f"extract={extract_job.id}, finalize={finalize_job.id}"
      )
      
    except Exception as e:
      logger.error(f"Failed to enqueue pipeline: {e}")
      raise