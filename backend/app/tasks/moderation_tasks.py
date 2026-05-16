import logging
from datetime import datetime, timedelta, timezone
from app.core.sync_db import SyncSessionLocal
from app.models.document_models import UploadRequest
from app.config.database import WorkflowEnum
from sqlalchemy import select, func
from app.models.user_models import User, Role
from app.models.moderation_models import ModerationAssignment, Report


logger = logging.getLogger(__name__)

def assign_moderator_task(upload_id: int, base_sla_hours: int = 24) -> None:
  session = SyncSessionLocal()
  try:
    # 1. Проверка существования заявки и статуса (устраняет race condition)
    upload = session.execute(
      select(UploadRequest).where(UploadRequest.id == upload_id)
    ).scalar_one_or_none()
    if not upload or upload.workflow_status != WorkflowEnum.PENDING_REVIEW:
      logger.info(f"Upload {upload_id} skipped: status={upload.workflow_status if upload else 'not_found'}")
      return

    # 2. Выбор активных модераторов с фильтрацией по роли
    moderators = session.execute(
      select(User).join(Role, User.role_id == Role.id).where(
        Role.role_name == "moderator",
        User.account_status == "active"
      )
    ).scalars().all()
    if not moderators:
      logger.error("No active moderators available for assignment")
      return

    # 3. Подсчёт текущей нагрузки на модераторов
    load_stmt = (
      select(ModerationAssignment.moderator_id, func.count(ModerationAssignment.id).label("active_count"))
      .where(ModerationAssignment.completed_at.is_(None))
      .group_by(ModerationAssignment.moderator_id)
    )
    loads = {row.moderator_id: row.active_count for row in session.execute(load_stmt).all()}
    
    # 4. Выбор наименее загруженного модератора
    selected_moderator = min(moderators, key=lambda m: loads.get(m.id, 0))

    # 5. Расчёт приоритета и SLA-дедлайна
    priority = upload.processing_metadata.get("risk_score", 0) if upload.processing_metadata else 0
    sla_delta = max(2, base_sla_hours - (priority // 5))
    deadline = datetime.now(timezone.utc) + timedelta(hours=sla_delta)

    # 6. Создание назначения (корректное создание ORM-объекта)
    assignment = ModerationAssignment(
      upload_requests_id=upload_id,
      moderator_id=selected_moderator.id,
      deadline=deadline,
      priority_score=priority,
      assigned_at=datetime.now(timezone.utc)
    )
    session.add(assignment)
    
    session.commit()
    logger.info(f"Upload {upload_id} assigned to moderator {selected_moderator.id} (SLA: {sla_delta}h)")
    
    # workflow_status остаётся PENDING_REVIEW до явного решения модератора: назначение лишь резервирует слот проверки.

  except Exception as e:
    session.rollback()
    logger.error(f"Failed to assign moderator for upload {upload_id}: {e}")
  finally:
    session.close()

def check_sla_deadlines_task() -> None:
  session = SyncSessionLocal()
  try:
    now = datetime.now(timezone.utc)
    expired_stmt = select(ModerationAssignment).where(
      ModerationAssignment.completed_at.is_(None),
      ModerationAssignment.deadline <= now
    )
    expired = session.execute(expired_stmt).scalars().all()
    
    for assignment in expired:
      upload = session.get(UploadRequest, assignment.upload_requests_id)
      if upload and upload.workflow_status == WorkflowEnum.PENDING_REVIEW:
        upload.workflow_status = WorkflowEnum.REJECTED
        upload.rejection_reason = "SLA deadline exceeded. Auto-rejected."
      assignment.completed_at = now
        
    if expired:
      session.commit()
      logger.info(f"SLA check completed. Expired assignments: {len(expired)}")
  
  except Exception as e:
    session.rollback()
    logger.error(f"SLA deadline check failed: {e}")
  finally:
    session.close()