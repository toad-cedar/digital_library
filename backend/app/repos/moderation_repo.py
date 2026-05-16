from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, and_
from app.models.moderation_models import ModerationAssignment, Report
from app.config.database import ReportEnum
from app.repos.base_repo import GenericRepository


class ModerationRepository:
  def __init__(self, db_session: AsyncSession):
    self.db = db_session
    self.assignments = GenericRepository(db_session, ModerationAssignment)
    self.reports = GenericRepository(db_session, Report)

  async def get_queue(
    self,
    moderator_id: Optional[int] = None,
    min_priority: Optional[int] = None,
    deadline_before: Optional[datetime] = None,
    offset: int = 0,
    limit: int = 10
  ) -> Tuple[List[ModerationAssignment], int]:
    conditions = [ModerationAssignment.completed_at.is_(None)]
    if moderator_id:
      conditions.append(ModerationAssignment.moderator_id == moderator_id)
    if min_priority is not None:
      conditions.append(ModerationAssignment.priority_score >= min_priority)
    if deadline_before:
      conditions.append(ModerationAssignment.deadline <= deadline_before)

    base = select(ModerationAssignment).where(and_(*conditions))
    count = select(func.count(ModerationAssignment.id)).where(and_(*conditions))

    total = (await self.db.execute(count)).scalar() or 0
    items = (await self.db.execute(
      base.order_by(
        ModerationAssignment.priority_score.desc(), 
        ModerationAssignment.deadline.asc()
      ).offset(offset).limit(limit)
    )).scalars().all()
    return items, total

  async def assign_task(
    self, 
    upload_id: int, 
    moderator_id: int, 
    deadline: datetime, 
    priority_score: int = 0
  ) -> ModerationAssignment:
    assignment = ModerationAssignment(
      upload_requests_id=upload_id,
      moderator_id=moderator_id,
      deadline=deadline,
      priority_score=priority_score,
      assigned_at=datetime.now(timezone.utc)
    )
    self.db.add(assignment)
    await self.db.flush()
    return assignment
  
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