from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.config.database import Base, ReportEnum, ReportTargetEnum, ReportCategoryEnum


class Report(Base):
  __tablename__ = 'reports'
  
  id:              Mapped[int]        = mapped_column(primary_key=True, autoincrement=True, index=True)
  reporter_id:     Mapped[int]        = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True) # Автор жалобы
  target_type:     Mapped[ReportTargetEnum]   = mapped_column(Enum(ReportTargetEnum, name='report_target_enum', native_enum=True)) # ReportTargetEnum(document / user / group)
  target_id:       Mapped[int]        # Динамический FK (логика приложения)
  reason_category: Mapped[ReportCategoryEnum] = mapped_column(Enum(ReportCategoryEnum, name='report_category_enum', native_enum=True)) # copyright / inappropriate / virus / other (ввести свою прчиину). Не ENUM
  description:     Mapped[str | None] = mapped_column(Text) # Текст жалобы
  report_status:   Mapped[ReportEnum] = mapped_column(Enum(ReportEnum, name='report_enum', native_enum=True), default=ReportEnum.PENDING) # ReportEnum(pending / in_review / resolved / rejected)
  created_at:      Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
  resolved_at:     Mapped[datetime | None] = mapped_column(DateTime()) # Время разрешения
  resolved_by:     Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), index=True) # Модератор
  resolution_note: Mapped[str | None] = mapped_column(Text) # Комментарий модератора

  reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reports_made")
  resolver = relationship("User", foreign_keys=[resolved_by], back_populates="reports_resolved")

class ModerationAssignment(Base):
  __tablename__ = 'moderation_assignments'
  
  id:                 Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  upload_requests_id: Mapped[int] = mapped_column(ForeignKey('upload_requests.id', ondelete='CASCADE'), index=True) # Заявка
  moderator_id:       Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), index=True) # Модератор
  deadline:           Mapped[datetime] = mapped_column(DateTime()) # SLA на проверку
  priority_score:     Mapped[int] # Приоритет на основе автора/типа
  assigned_at:        Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  completed_at:       Mapped[datetime | None] = mapped_column(DateTime()) # Время завершения
  
  upload_request = relationship("UploadRequest", back_populates="moderation_assignments")
  moderator      = relationship("User", foreign_keys=[moderator_id], back_populates="moderation_tasks")