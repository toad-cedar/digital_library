from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.models.moderation_models import ModerationAssignment, Report
from app.config.database import ReportEnum
from app.repos.base_repo import GenericRepository


class ModerationRepository:
  def __init__(self, db_session: AsyncSession):
    self.db = db_session
    self.assignments = GenericRepository(db_session, ModerationAssignment)
    self.reports = GenericRepository(db_session, Report)

  async def get_pending_queue(self, offset: int = 0, limit: int = 10) -> Tuple[List[ModerationAssignment], int]:
    base = select(ModerationAssignment).where(ModerationAssignment.completed_at.is_(None))
    count = (await self.db.execute(select(func.count(ModerationAssignment.id)).where(ModerationAssignment.completed_at.is_(None)))).scalar() or 0
    items = (await self.db.execute(base.order_by(ModerationAssignment.priority_score.desc()).offset(offset).limit(limit))).scalars().all()
    return items, count

  async def create_assignment(self, assignment: ModerationAssignment) -> ModerationAssignment:
    return await self.assignments.create(assignment)

  async def complete_assignment(self, assignment_id: int) -> None:
    stmt = update(ModerationAssignment).where(ModerationAssignment.id == assignment_id).values(completed_at=datetime.now(timezone.utc))
    await self.db.execute(stmt)

  async def get_reports_by_target(self, target_id: int, target_type, offset: int = 0, limit: int = 10) -> Tuple[List[Report], int]:
    base = select(Report).where(Report.target_id == target_id, Report.target_type == target_type)
    count = (await self.db.execute(select(func.count(Report.id)).where(Report.target_id == target_id, Report.target_type == target_type))).scalar() or 0
    items = (await self.db.execute(base.offset(offset).limit(limit))).scalars().all()
    return items, count

  async def update_report_status(self, report_id: int, status: ReportEnum, resolver_id: int, note: Optional[str] = None) -> Optional[Report]:
    values = {"report_status": status, "resolved_by": resolver_id, "resolved_at": datetime.now(timezone.utc)}
    if note:
      values["resolution_note"] = note
    stmt = update(Report).where(Report.id == report_id).values(**values).returning(Report)
    return (await self.db.execute(stmt)).scalar_one_or_none()