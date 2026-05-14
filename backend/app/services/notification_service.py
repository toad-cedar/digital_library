from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repos.audit_repo import AuditRepository
from app.schemas.system import NotificationRead
from app.schemas.common import PaginationResponse
from app.models.system_models import Notification
import logging


logger = logging.getLogger(__name__)

class NotificationService:
  def __init__(self, db_session: AsyncSession):
    self.db_session = db_session
    self.audit_repo = AuditRepository(db_session)

  async def get_user_notifications(self, user_id: int, page: int, page_size: int) -> PaginationResponse[NotificationRead]:
    offset = (page - 1) * page_size
    items, total = await self.audit_repo.get_notifications(user_id, offset, page_size)
    valid = [n for n in items if not n.expires_at or n.expires_at > datetime.now(timezone.utc)]
    
    return PaginationResponse(
      data=[NotificationRead.model_validate(n) for n in valid],
      total=total, page=page, page_size=page_size
    )

  async def mark_as_read(self, notification_id: int, user_id: int) -> NotificationRead:
    updated = await self.audit_repo.mark_notification_read(notification_id, user_id)
    if not updated: 
      raise ValueError("Notification not found")
    
    return NotificationRead.model_validate(updated)

  async def mark_all_read(self, user_id: int) -> int:
    return await self.audit_repo.mark_all_notifications_read(user_id)
  
  async def create_notification(self, user_id: int, source_type: str, event_type: str, title: str, content: dict, channel: str, expires_at: datetime | None = None) -> NotificationRead:
    notification = Notification(
      user_id=user_id,
      source_type=source_type,
      source_id=0, # Заполняется при привязке к сущности, если нужно
      event_type=event_type,
      title=title,
      content=content,
      channel=channel,
      expires_at=expires_at
    )
    self.db_session.add(notification)
    await self.db_session.commit()
    return NotificationRead.model_validate(notification)