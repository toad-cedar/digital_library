from sqlalchemy.ext.asyncio import AsyncSession
from app.repos.audit_repo import AuditRepository
from app.schemas.system import AuditLogRead, AuditLogFilter
from app.schemas.activity import HistoryViewRead, HistoryDownloadRead
from app.models.system_models import AuditLog
from app.models.activity_models import HistoryView, HistoryDownload
from typing import Tuple, List
import logging


logger = logging.getLogger(__name__)

class AuditService:
  def __init__(self, db_session: AsyncSession):
    self.db_session = db_session
    self.audit_repo = AuditRepository(db_session)

  async def log_action(self, log_data: dict) -> AuditLogRead:
    log = AuditLog(**log_data)
    self.db_session.add(log)
    await self.db_session.commit()
    
    return AuditLogRead.model_validate(log)

  async def get_logs(self, filters: AuditLogFilter) -> Tuple[List[AuditLogRead], int]:
    offset = (filters.page - 1) * filters.page_size
    items, total = await self.audit_repo.get_logs(
      user_id=filters.user_id, 
      action=filters.action, 
      offset=offset, 
      limit=filters.page_size
    )
    return [AuditLogRead.model_validate(i) for i in items], total

  async def record_view(self, user_id: int, document_id: int) -> HistoryViewRead:
    view = HistoryView(user_id=user_id, document_id=document_id)
    self.db_session.add(view)
    await self.db_session.commit()
    return HistoryViewRead.model_validate(view)

  async def record_download(self, download_data: dict) -> HistoryDownloadRead:
    download = HistoryDownload(**download_data)
    self.db_session.add(download)
    await self.db_session.commit()

    return HistoryDownloadRead.model_validate(download)