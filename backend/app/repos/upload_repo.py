from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.orm_models import UploadRequest, UploadStatus


class UploadRequestRepository:
  def __init__(self, db_session: AsyncSession):
    self.db_session = db_session

  async def get_by_id(self, upload_id: int) -> Optional[UploadRequest]:
    """Получает заявку на загрузку по ID."""
    stmt = select(UploadRequest).where(UploadRequest.id == upload_id)
    result = await self.db_session.execute(stmt)
    return result.scalar_one_or_none()

  async def get_requests_for_user(self, user_id: int, offset: int = 0, limit: int = 10) -> List[UploadRequest]:
    """Получает список заявок пользователя с пагинацией."""
    stmt = select(UploadRequest).where(UploadRequest.user_id == user_id).offset(offset).limit(limit)
    result = await self.db_session.execute(stmt)
    return result.scalars().all()

  async def get_all_requests(self, offset: int = 0, limit: int = 10) -> List[UploadRequest]:
    """Получает список всех заявок (для модераторов) с пагинацией."""
    stmt = select(UploadRequest).offset(offset).limit(limit)
    result = await self.db_session.execute(stmt)
    return result.scalars().all()

  async def create(self, upload_request: UploadRequest) -> UploadRequest:
    """Создаёт новую заявку на загрузку."""
    self.db_session.add(upload_request)
    await self.db_session.flush() # Получаем ID
    return upload_request

  async def update_status(self, upload_id: int, status_id: int, moderator_id: Optional[int] = None) -> Optional[UploadRequest]:
    """Обновляет статус заявки и, опционально, ID модератора."""
    stmt = (
      update(UploadRequest)
      .where(UploadRequest.id == upload_id)
      .values(status_id=status_id, moderator_id=moderator_id)
      .returning(UploadRequest)
    )
    result = await self.db_session.execute(stmt)
    updated_request = result.scalar_one_or_none()
    if updated_request:
      await self.db_session.commit()
      await self.db_session.refresh(updated_request)
    else:
      await self.db_session.rollback()
    return updated_request

  async def delete(self, upload_id: int) -> bool:
    """Удаляет заявку на загрузку по ID."""
    stmt = delete(UploadRequest).where(UploadRequest.id == upload_id)
    result = await self.db_session.execute(stmt)
    if result.rowcount > 0:
      await self.db_session.commit()
      return True
    else:
      await self.db_session.rollback()
      return False

