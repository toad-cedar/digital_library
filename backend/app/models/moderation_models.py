from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.config.database import Base, ReportEnum, ReportCategoryEnum


class Report(Base):
  __tablename__ = 'reports'
  
  id:              Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  reporter_id:     Mapped[int] = mapped_column(ForeignKey('users.id')) # Автор жалобы
  target_type:     Mapped[ReportCategoryEnum] = mapped_column(Enum(ReportCategoryEnum, native_enum=True)) # ReportCategoryEnum(document / user / group)
  target_id:       Mapped[int] # Динамический FK (логика приложения)
  reason_category: Mapped[str] = mapped_column(String(50)) # copyright / inappropriate / virus / other (ввести свою прчиину). Не ENUM
  description:     Mapped[str | None] = mapped_column(Text) # Текст жалобы
  report_status:   Mapped[ReportEnum] = mapped_column(Enum(ReportEnum, native_enum=True), default=ReportEnum.PENDING) # ReportEnum(pending / in_review / resolved / rejected)
  created_at:      Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  resolved_at:     Mapped[datetime | None] # Время разрешения
  resolved_by:     Mapped[int | None] = mapped_column(ForeignKey('users.id')) # Модератор
  resolution_note: Mapped[str | None] = mapped_column(Text)# Комментарий модератора


class ModerationAssignment(Base):
  __tablename__ = 'moderation_assignments'
  
  id:                 Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  upload_requests_id: Mapped[int] = mapped_column(ForeignKey('upload_requests.id')) # Заявка
  moderator_id:       Mapped[int] = mapped_column(ForeignKey('users.id')) # Модератор
  deadline:           Mapped[datetime] # SLA на проверку
  priority_score:     Mapped[int] # Приоритет на основе автора/типа
  assigned_at:        Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  completed_at:       Mapped[datetime | None] # Время завершения
  