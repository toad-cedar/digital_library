from sqlalchemy.ext.asyncio import AsyncSession
from app.repos.moderation_repo import ModerationRepository
from app.repos.upload_repo import UploadRequestRepository
from app.repos.document_repo import DocumentRepository
from app.services.minio_service import MinioService
from app.config.database import WorkflowEnum, VisibilityEnum
from app.schemas.moderation import ModerationQueueResponse, ModerationQueueItem, ModerationDecision
from app.models.document_models import Document
import logging


logger = logging.getLogger(__name__)

class ModerationService:
  def __init__(self, db_session: AsyncSession, minio_service: MinioService):
    self.db_session = db_session
    self.mod_repo = ModerationRepository(db_session)
    self.upload_repo = UploadRequestRepository(db_session)
    self.doc_repo = DocumentRepository(db_session)
    self.minio_service = minio_service

  async def get_queue(self, page: int, page_size: int) -> ModerationQueueResponse:
    offset = (page - 1) * page_size
    items, total = await self.mod_repo.get_pending_queue(offset, page_size)
    return ModerationQueueResponse(
      items=[ModerationQueueItem.model_validate(i) for i in items],
      total=total, page=page, page_size=page_size
    )

  async def make_decision(self, upload_id: int, moderator_id: int, decision: ModerationDecision) -> bool:
    upload = await self.upload_repo.get_by_id(upload_id)
    if not upload or upload.workflow_status != WorkflowEnum.PENDING_REVIEW:
      raise ValueError("Invalid upload state")

    await self.mod_repo.complete_assignment(upload_id)
    await self.db_session.flush()

    if decision.decision == "approve":
      await self._publish_document(upload, moderator_id)
    else:
      await self.upload_repo.update_workflow_status(
        upload_id, WorkflowEnum.REJECTED, moderator_id, decision.reason
      )
      await self.minio_service.delete_file("temporary", upload.temporary_minio_path)

    await self.db_session.commit()
    return True

  async def _publish_document(self, upload, moderator_id: int) -> None:
    main_path = f"documents/{upload.uploader_id}/{upload.file_hash}/{upload.file_original_name}"
    await self.minio_service.copy_file("temporary", upload.temporary_minio_path, "documents", main_path)
    
    doc = Document(
      title=upload.title, description=upload.description, uploader_id=upload.uploader_id,
      moderator_id=moderator_id, minio_bucket="documents", minio_object_path=main_path,
      file_original_name=upload.file_original_name, file_mime=upload.file_mime,
      file_size=upload.file_size, file_hash=upload.file_hash, 
      format=self._guess_format(upload.file_original_name),
      converted_to_pdf=False, visibility_status=VisibilityEnum.PUBLISHED
    )
    await self.doc_repo.create(doc)
    
    await self.upload_repo.update_workflow_status(upload.id, WorkflowEnum.ACCEPTED, moderator_id)
    logger.info(f"Document prepared for commit from upload {upload.id}")

  @staticmethod
  def _guess_format(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"
    return ext if ext in ("pdf", "docx", "pptx", "txt", "md") else "unknown"