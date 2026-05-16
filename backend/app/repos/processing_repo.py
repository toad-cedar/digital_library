from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, insert
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
  
  async def get_next_version_number(self, document_id: int) -> int:
    """Атомарно получает следующий номер версии с блокировкой строк"""
    stmt = (
      select(func.coalesce(func.max(HistoryVersion.version_number), 0) + 1)
      .where(HistoryVersion.document_id == document_id)
      .with_for_update()
    )
    return (await self.db.execute(stmt)).scalar_one()

  async def create_version(
    self,
    document_id: int,
    file_hash: str,
    minio_path: str,
    minio_bucket: str,
    file_size: int,
    file_format: str,
    uploaded_by: int,
    change_notes: Optional[str] = None
  ) -> HistoryVersion:
    """Создаёт запись версии, самостоятельно рассчитывая `version_number`"""
    version_number = await self.get_next_version_number(document_id)
    
    version = HistoryVersion(
      document_id=document_id,
      version_number=version_number,
      file_hash=file_hash,
      minio_path=minio_path,
      minio_bucket=minio_bucket,
      file_size=file_size,
      file_format=file_format,
      uploaded_by=uploaded_by,
      change_notes=change_notes
    )
    self.db.add(version)
    await self.db.flush()
    return version