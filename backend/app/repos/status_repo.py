from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.orm_models import UploadStatus

class StatusRepository:
  def __init__(self, db_session: AsyncSession):
    self.db_session = db_session
  
  async def get_status_id_by_name(self, status_name: str) -> Optional[int]:
    """Получает ID статуса по его имени."""
    stmt = select(UploadStatus.id).where(UploadStatus.status_name == status_name)
    result = await self.db_session.execute(stmt)
    return result.scalar_one_or_none()

  async def get_status_by_name(self, status_name: str) -> Optional[UploadStatus]:
    """Получает объект статуса по его имени."""
    stmt = select(UploadStatus).where(UploadStatus.status_name == status_name)
    result = await self.db_session.execute(stmt)
    return result.scalar_one_or_none()
