from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.document_models import UploadRequest
from app.config.database import WorkflowEnum
from app.repos.base_repo import GenericRepository


class UploadRequestRepository:
  def __init__(self, db_session: AsyncSession):
    self.db_session = db_session
    self.base = GenericRepository(db_session, UploadRequest)

  async def get_by_id(self, upload_id: int) -> Optional[UploadRequest]:
    return await self.base.get_by_id(upload_id)

  async def get_by_user(self, user_id: int, offset: int = 0, limit: int = 10) -> Tuple[List[UploadRequest], int]:
    base = select(UploadRequest).where(UploadRequest.uploader_id == user_id)
    count = (await self.db_session.execute(select(func.count(UploadRequest.id)).where(UploadRequest.uploader_id == user_id))).scalar() or 0
    items = (await self.db_session.execute(base.order_by(UploadRequest.created_at.desc()).offset(offset).limit(limit))).scalars().all()
    return items, count

  async def get_all(
    self,
    workflow_status: Optional[WorkflowEnum] = None,
    offset: int = 0,
    limit: int = 10
  ) -> Tuple[List[UploadRequest], int]:
    base = select(UploadRequest)
    count_stmt = select(func.count(UploadRequest.id))

    if workflow_status is not None:
      base = base.where(UploadRequest.workflow_status == workflow_status)
      count_stmt = count_stmt.where(UploadRequest.workflow_status == workflow_status)

    total = (await self.db_session.execute(count_stmt)).scalar() or 0
    items = (await self.db_session.execute(base.order_by(UploadRequest.created_at.desc()).offset(offset).limit(limit))).scalars().all()
    return items, total

  async def create(self, request: UploadRequest) -> UploadRequest:
    return await self.base.create(request)

  async def update_workflow_status(
    self,
    upload_id: int,
    status: WorkflowEnum,
    moderator_id: Optional[int] = None,
    rejection_reason: Optional[str] = None
  ) -> Optional[UploadRequest]:
    data = {"workflow_status": status, "moderator_id": moderator_id}
    if rejection_reason is not None:
      data["rejection_reason"] = rejection_reason
    return await self.base.update(upload_id, data)

  async def delete(self, upload_id: int) -> bool:
    return await self.base.delete(upload_id)