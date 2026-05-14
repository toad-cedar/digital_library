from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.repos.document_repo import DocumentRepository
from app.repos.tag_repo import TagRepository
from app.services.minio_service import MinioService
from app.config.database import VisibilityEnum
from app.schemas.document import (
    DocumentRead, DocumentUpdate, VisibilityUpdate, 
    TagAssignRequest, VersionRead, DownloadUrlResponse
)
import logging


logger = logging.getLogger(__name__)

class DocumentService:
  def __init__(self, db_session: AsyncSession, minio_service: MinioService):
    self.doc_repo = DocumentRepository(db_session)
    self.tag_repo = TagRepository(db_session)
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

  async def update_visibility(self, doc_id: int, data: VisibilityUpdate, uploader_id: int) -> DocumentRead: 
    doc = await self.doc_repo.get_by_id(doc_id)
    if not doc or doc.uploader_id != uploader_id:
      raise ValueError("Access denied")
    
    target_status = VisibilityEnum(data.visibility_status)
    updated = await self.doc_repo.update(doc_id, {"visibility_status": target_status})
    await self.db_session.commit()
    return DocumentRead.model_validate(updated)

  async def update_metadata(self, doc_id: int, data: DocumentUpdate, uploader_id: int) -> DocumentRead:
    doc = await self.doc_repo.get_by_id(doc_id)
    if not doc or doc.uploader_id != uploader_id:
      raise ValueError("Access denied")
        
    update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not update_data:
      return DocumentRead.model_validate(doc)
        
    updated = await self.doc_repo.update(doc_id, update_data)
    await self.db_session.commit()
    return DocumentRead.model_validate(updated)

  async def assign_tags(self, doc_id: int, data: TagAssignRequest, uploader_id: int) -> DocumentRead:
    doc = await self.doc_repo.get_by_id(doc_id)
    if not doc or doc.uploader_id != uploader_id:
      raise ValueError("Access denied")
    
    await self.tag_repo.unlink_document(doc_id)
    tags = [await self.tag_repo.get_or_create_by_name(t) for t in data.tags]
    await self.tag_repo.link_document(doc_id, [t.id for t in tags])
    await self.db_session.commit()
    return DocumentRead.model_validate(await self.doc_repo.get_by_id(doc_id))

  async def get_versions(self, doc_id: int) -> List[VersionRead]:
    versions, _ = await self.doc_repo.get_versions_by_document(doc_id)
    return [VersionRead.model_validate(v) for v in versions]