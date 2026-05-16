from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repos.processing_repo import ProcessingRepository
from app.repos.document_repo import DocumentRepository
from app.repos.tag_repo import TagRepository
from app.repos.audit_repo import AuditRepository
from app.services.minio_service import MinioService
from app.config.database import VisibilityEnum, AuditTargetEnum
from app.schemas.document import (
  DocumentRead, DocumentUpdate, VisibilityUpdate,
  TagAssignRequest, VersionRead, DownloadUrlResponse
)
from app.models.system_models import AuditLog
import logging
import uuid


logger = logging.getLogger(__name__)

class DocumentService:
  def __init__(self, db_session: AsyncSession, minio_service: MinioService):
    self.db_session = db_session
    self.doc_repo = DocumentRepository(db_session)
    self.tag_repo = TagRepository(db_session)
    self.proc_repo = ProcessingRepository(db_session)
    self.audit_repo = AuditRepository(db_session)
    self.minio_service = minio_service

  async def get_by_id(self, doc_id: int) -> DocumentRead:
    doc = await self.doc_repo.get_by_id(doc_id)
    if not doc or doc.visibility_status == VisibilityEnum.ARCHIVED:
      logger.error("Document not found")
      raise ValueError("Document not found")
    
    return DocumentRead.model_validate(doc)

  async def get_download_url(self, doc_id: int, expires_seconds: int = 3600) -> DownloadUrlResponse:
    doc = await self.doc_repo.get_by_id(doc_id)
    if not doc: 
      logger.error("Document not found")
      raise ValueError("Document not found")
    
    url = await self.minio_service.get_presigned_url(doc.minio_bucket, doc.minio_object_path, expires_seconds)  
    return DownloadUrlResponse(url=url, expires_at=datetime.now(timezone.utc)+ timedelta(seconds=expires_seconds))

  async def update_visibility(self, doc_id: int, data: VisibilityUpdate) -> DocumentRead: 
    # Проверка прав делегирована Casbin на уровне API
    doc = await self.doc_repo.get_by_id(doc_id)
    if not doc:
      raise ValueError("Document not found")
    target_status = VisibilityEnum(data.visibility_status)
    updated = await self.doc_repo.update(doc_id, {"visibility_status": target_status})
    await self.db_session.commit()
    return DocumentRead.model_validate(updated)

  async def update_metadata(self, doc_id: int, data: DocumentUpdate) -> DocumentRead:
    doc = await self.doc_repo.get_by_id(doc_id)
    if not doc:
      raise ValueError("Document not found")
    update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not update_data:
      return DocumentRead.model_validate(doc)
    updated = await self.doc_repo.update(doc_id, update_data)
    await self.db_session.commit()
    return DocumentRead.model_validate(updated)

  async def assign_tags(self, doc_id: int, data: TagAssignRequest) -> DocumentRead:
    doc = await self.doc_repo.get_by_id(doc_id)
    if not doc:
      raise ValueError("Document not found")
    
    await self.tag_repo.unlink_document(doc_id)
    tags = [await self.tag_repo.get_or_create_by_name(t) for t in data.tags]
    await self.tag_repo.link_document(doc_id, [t.id for t in tags])
    await self.db_session.commit()
    return DocumentRead.model_validate(await self.doc_repo.get_by_id(doc_id))

  async def get_versions(self, doc_id: int) -> List[VersionRead]:
    versions, _ = await self.proc_repo.get_versions_by_document(doc_id)
    return [VersionRead.model_validate(v) for v in versions]
  
  async def handle_version(
    self,
    document_id: int,
    new_file_hash: str,
    new_minio_path: str,
    new_bucket: str,
    new_size: int,
    new_format: str,
    uploaded_by: int,
    change_notes: Optional[str] = None,
    ip_address: Optional[str] = None
  ) -> DocumentRead:
    doc = await self.doc_repo.get_by_id(document_id)
    if not doc:
      raise ValueError("Document not found")

    async with self.db_session.begin():
      # 1. Архивация текущей версии в историю
      await self.proc_repo.create_version(
        document_id=doc.id,
        file_hash=doc.file_hash,
        minio_path=doc.minio_object_path,
        minio_bucket=doc.minio_bucket,
        file_size=doc.file_size,
        file_format=doc.format,
        uploaded_by=uploaded_by,
        change_notes=change_notes
      )

      # 2. Обновление метаданных документа
      updated = await self.doc_repo.update(doc.id, {
        "file_hash": new_file_hash,
        "minio_object_path": new_minio_path,
        "minio_bucket": new_bucket,
        "file_size": new_size,
        "format": new_format,
        "moderator_id": uploaded_by
      })

      # 3. Запись в audit_logs
      audit_entry = AuditLog(
        user_id=uploaded_by,
        action="document.version_created",
        target_uuid=uuid.UUID(int=doc.id),
        target_type=AuditTargetEnum.DOCUMENT,
        details={
          "old_hash": doc.file_hash,
          "new_hash": new_file_hash,
          "change_notes": change_notes
        },
        ip_address=ip_address,
        success=True
      )
      await self.audit_repo.create_log(audit_entry)

    return DocumentRead.model_validate(updated)