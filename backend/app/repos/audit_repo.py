from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.models.system_models import AuditLog, Notification
# История активности согласно структуре проекта
from app.models.activity_models import HistoryView, HistoryDownload

class AuditRepository:
  def __init__(self, db_session: AsyncSession):
    self.db = db_session

  async def create_log(self, log: AuditLog) -> AuditLog:
    self.db.add(log)
    await self.db.flush()
    return log

  async def get_logs(self, user_id: Optional[int] = None, action: Optional[str] = None, offset: int = 0, limit: int = 10) -> Tuple[List[AuditLog], int]:
    stmt = select(AuditLog)
    count_stmt = select(func.count(AuditLog.id))
    if user_id:
      stmt = stmt.where(AuditLog.user_id == user_id)
      count_stmt = count_stmt.where(AuditLog.user_id == user_id)
    if action:
      stmt = stmt.where(AuditLog.action == action)
      count_stmt = count_stmt.where(AuditLog.action == action)

    total = (await self.db.execute(count_stmt)).scalar() or 0
    items = (await self.db.execute(stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit))).scalars().all()
    return items, total

  async def get_notifications(self, user_id: int, offset: int = 0, limit: int = 10) -> Tuple[List[Notification], int]:
    base = select(Notification).where(Notification.user_id == user_id)
    count = (await self.db.execute(select(func.count(Notification.id)).where(Notification.user_id == user_id))).scalar() or 0
    items = (await self.db.execute(base.order_by(Notification.created_at.desc()).offset(offset).limit(limit))).scalars().all()
    return items, count

  async def mark_notification_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
    stmt = update(Notification).where(Notification.id == notification_id, Notification.user_id == user_id).values(is_read=True, read_at=datetime.now(timezone.utc)).returning(Notification)
    return (await self.db.execute(stmt)).scalar_one_or_none()

  async def mark_all_notifications_read(self, user_id: int) -> int:
    stmt = update(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False)).values(is_read=True, read_at=datetime.now(timezone.utc))
    result = await self.db.execute(stmt)
    return result.rowcount

  async def record_view(self, view: HistoryView) -> HistoryView:
    self.db.add(view)
    await self.db.flush()
    return view

  async def record_download(self, download: HistoryDownload) -> HistoryDownload:
    self.db.add(download)
    await self.db.flush()
    return download