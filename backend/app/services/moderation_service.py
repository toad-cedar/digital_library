from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.repos.moderation_repo import ModerationRepository
from app.repos.upload_repo import UploadRequestRepository
from app.repos.document_repo import DocumentRepository
from app.services.minio_service import MinioService
from app.config.database import WorkflowEnum, VisibilityEnum, ReportEnum
from app.schemas.moderation import ModerationQueueResponse, ModerationQueueItem, ModerationDecision, ReportRead
from app.models.document_models import Document
from app.models.moderation_models import ModerationAssignment, Report
from datetime import datetime, timezone, timedelta
import logging



logger = logging.getLogger(__name__)

# State machine transitions
ALLOWED_WORKFLOW_TRANSITIONS = {
  WorkflowEnum.PENDING_REVIEW: [WorkflowEnum.ACCEPTED, WorkflowEnum.REJECTED]
}
CRITICAL_REPORT_CATEGORIES = {"virus", "copyright"}

class ModerationService:
  def __init__(self, db_session: AsyncSession, minio_service: MinioService):
    self.db_session = db_session
    self.mod_repo = ModerationRepository(db_session)
    self.upload_repo = UploadRequestRepository(db_session)
    self.doc_repo = DocumentRepository(db_session)
    self.minio_service = minio_service

  async def auto_assign(self, upload_id: int, moderator_id: int, base_sla_hours: int = 24) -> ModerationAssignment:
    upload = await self.upload_repo.get_by_id(upload_id)
    if not upload or upload.workflow_status != WorkflowEnum.PENDING_REVIEW:
      raise ValueError("Upload must be in pending_review state for auto-assignment")
    
    priority = upload.processing_metadata.get("risk_score", 0) if upload.processing_metadata else 0
    # SLA сокращается пропорционально приоритету (минимум 2 часа)
    sla_delta = max(2, base_sla_hours - (priority // 5))
    deadline = datetime.now(timezone.utc) + timedelta(hours=sla_delta)

  
    return await self.mod_repo.create_assignment(ModerationAssignment(
      upload_requests_id=upload_id, moderator_id=moderator_id,
      deadline=deadline, priority_score=priority, assigned_at=datetime.now(timezone.utc)
    ))

  async def process_decision(self, upload_id: int, moderator_id: int, decision: ModerationDecision) -> bool:
    upload = await self.upload_repo.get_by_id(upload_id)
    if not upload:
      raise ValueError("Upload request not found")

    if upload.workflow_status not in ALLOWED_WORKFLOW_TRANSITIONS:
      raise ValueError(f"Invalid workflow state for decision: {upload.workflow_status}")

    target_status = WorkflowEnum.ACCEPTED if decision.decision == "approve" else WorkflowEnum.REJECTED
    if target_status not in ALLOWED_WORKFLOW_TRANSITIONS[upload.workflow_status]:
      raise ValueError("Forbidden status transition")

    await self.db_session.execute(update(ModerationAssignment).where(
      ModerationAssignment.upload_requests_id == upload_id,
      ModerationAssignment.completed_at.is_(None)
    ).values(completed_at=datetime.now(timezone.utc)))
    await self.db_session.flush()
    
    if target_status == WorkflowEnum.ACCEPTED:
      await self._publish_document(upload, moderator_id)
    else:
      await self.upload_repo.update_workflow_status(upload_id, target_status, moderator_id, decision.reason)
      await self.minio_service.delete_file("temporary", upload.temporary_minio_path)

    await self.db_session.commit()
    return True
  
  async def handle_report(
    self,
    reporter_id: int,
    target_type: str,
    target_id: int,
    category: str,
    description: str
  ) -> ReportRead:
    report = Report(
      reporter_id=reporter_id,
      target_type=target_type,
      target_id=target_id,
      reason_category=category,
      description=description,
      report_status=ReportEnum.PENDING
    )
    self.db_session.add(report)
    await self.db_session.flush()

    # Критические жалобы автоматически скрывают документ
    if target_type == 'document' and category in CRITICAL_REPORT_CATEGORIES:
      doc = await self.doc_repo.get_by_id(target_id)
      if doc:
        await self.doc_repo.update(target_id, {"visibility_status": VisibilityEnum.UNLISTED})

    await self.db_session.commit()
    return ReportRead.model_validate(report)
  
  async def get_queue(self, page: int, page_size: int) -> ModerationQueueResponse:
    offset = (page - 1) * page_size
    items, total = await self.mod_repo.get_pending_queue(offset, page_size)
    return ModerationQueueResponse(
      items=[ModerationQueueItem.model_validate(i) for i in items],
      total=total, page=page, page_size=page_size
    )

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
    await self.db_session.flush()
    await self.upload_repo.update_workflow_status(upload.id, WorkflowEnum.ACCEPTED, moderator_id)
    logger.info(f"Document prepared for commit from upload {upload.id}")

  @staticmethod
  def _guess_format(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"
    return ext if ext in ("pdf", "docx", "pptx", "txt", "md") else "unknown"