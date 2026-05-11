from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.models.processing_models import ConversionJob, HistoryVersion
from app.config.database import ConversionEnum
from app.repos.base_repo import GenericRepository


class ProcessingRepository:
  def __init__(self, db_session: AsyncSession):
    self.db = db_session
    self.jobs = GenericRepository(db_session, ConversionJob)
    self.versions = GenericRepository(db_session, HistoryVersion)

  async def create_job(self, job: ConversionJob) -> ConversionJob:
    return await self.jobs.create(job)

  async def update_job_status(self, job_id: int, status: ConversionEnum, error_log: Optional[str] = None) -> Optional[ConversionJob]:
    values = {"status": status}
    if error_log:
      values["error_log"] = error_log
    
    now = datetime.now(timezone.utc)
    if status in (ConversionEnum.COMPLETED, ConversionEnum.FAILED):
      values["completed_at"] = now
    elif status == ConversionEnum.PROCESSING:
      values["started_at"] = now

    stmt = update(ConversionJob).where(ConversionJob.id == job_id).values(**values).returning(ConversionJob)
    return (await self.db.execute(stmt)).scalar_one_or_none()

  async def get_pending_jobs(self, offset: int = 0, limit: int = 10) -> Tuple[List[ConversionJob], int]:
    base = select(ConversionJob).where(ConversionJob.status == ConversionEnum.PENDING)
    count = (await self.db.execute(select(func.count(ConversionJob.id)).where(ConversionJob.status == ConversionEnum.PENDING))).scalar() or 0
    items = (await self.db.execute(base.order_by(ConversionJob.id.asc()).offset(offset).limit(limit))).scalars().all()
    return items, count

  async def get_versions_by_document(self, document_id: int, offset: int = 0, limit: int = 10) -> Tuple[List[HistoryVersion], int]:
    base = select(HistoryVersion).where(HistoryVersion.document_id == document_id)
    count = (await self.db.execute(select(func.count(HistoryVersion.id)).where(HistoryVersion.document_id == document_id))).scalar() or 0
    items = (await self.db.execute(base.order_by(HistoryVersion.version_number.desc()).offset(offset).limit(limit))).scalars().all()
    return items, count

  async def create_version(self, version: HistoryVersion) -> HistoryVersion:
    return await self.versions.create(version)