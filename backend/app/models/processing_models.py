from sqlalchemy     import BigInteger, Text, String, Enum, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from datetime import datetime
from app.config.database import Base, ConversionEnum


class ConversionJob(Base):
  __tablename__ = 'conversion_jobs'
  
  id:                Mapped[int]        = mapped_column(primary_key=True, autoincrement=True)
  source_entity_id:  Mapped[int | None] = mapped_column(ForeignKey('upload_requests.id', ondelete='CASCADE'), index=True) # Только для новых загрузок
  document_id:       Mapped[int | None] = mapped_column(ForeignKey('documents.id', ondelete='CASCADE'), index=True) # Только для повторной конвертации/версий
  conversion_status: Mapped[ConversionEnum] = mapped_column(Enum(ConversionEnum, name='conversion_enum', native_enum=True), default=ConversionEnum.PENDING) # ConversionEnum(pending / processing / completed / failed / retrying)
  original_format:   Mapped[str]        = mapped_column(String(20)) # docx / pptx / txt и т.д.
  target_format:     Mapped[str]        = mapped_column(String(20), default='pdf')
  retry_count:       Mapped[int]        = mapped_column(default=0)
  error_log:         Mapped[str | None] = mapped_column(Text) # Лог ошибки
  output_minio_path: Mapped[str | None] = mapped_column(String(500)) # Путь к результату 
  started_at:        Mapped[datetime | None] = mapped_column(DateTime()) # Начало выполнения
  completed_at:      Mapped[datetime | None] = mapped_column(DateTime()) # Завершение выполнения

  source_upload   = relationship("UploadRequest", back_populates="conversion_jobs")
  target_document = relationship("Document", back_populates="conversion_jobs")

class HistoryVersion(Base):
  __tablename__ = 'history_versions'
  __table_args__ = (
    UniqueConstraint(
      'document_id', 
      'version_number',
      name="uq_document_id_and_version_number"
    ),
  )
  id:             Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
  document_id:    Mapped[int] = mapped_column(ForeignKey('documents.id', ondelete='CASCADE'), index=True)
  version_number: Mapped[int] = mapped_column(index=True) # Номер версии
  minio_path:     Mapped[str] = mapped_column(String(500)) # Путь к архивной версии
  minio_bucket:   Mapped[str] = mapped_column(String(100)) # Бакет
  file_hash:      Mapped[str] = mapped_column(String(64), unique=True)
  file_size:      Mapped[int] = mapped_column(BigInteger)# Размер
  file_format:    Mapped[str] = mapped_column(String(20)) # Формат
  uploaded_by:    Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), index=True) # Автор версии
  change_notes:   Mapped[str | None] = mapped_column(Text)
  created_at:     Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  
  document = relationship("Document", back_populates="history_versions")
  uploader = relationship("User", foreign_keys=[uploaded_by], back_populates="versions_uploaded")